"""
features/schedule.py
====================
Time-of-day aware travel-time calculation.

Priority order for arrival/departure times:
  1. Real GTFS schedule times (from stop_times.txt)
  2. Google Maps Distance Matrix API (with live traffic) if API key set
  3. Speed-model fallback (peak/day/night km/h estimate)

BMTC operational hours: 05:00 – 23:30
Buses outside that window are filtered at the routing level.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt

import requests

from core.config import (
    SPEED_PEAK, SPEED_DAY, SPEED_NIGHT,
    WAITING_TIME, TRANSFER_TIME,
    FAST_QUERY_MODE,
)
from core.loader import stops_df, _rev_df
from features.fare import segment_fare_breakdown

_route_cache: dict[str, dict] = {}
_gtfs_segment_cache: dict[tuple, tuple[datetime, datetime]] = {}  # Cache GTFS lookups


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _register_route_cache(df) -> None:
    for route_no, group in df.groupby("route_no"):
        ordered = group.sort_values("stop_sequence").reset_index(drop=True)
        norms = ordered["stop_norm"].tolist()
        cumulative_km = [0.0]
        for i in range(len(ordered) - 1):
            cumulative_km.append(
                cumulative_km[-1] + haversine(
                    ordered.iloc[i].latitude,
                    ordered.iloc[i].longitude,
                    ordered.iloc[i + 1].latitude,
                    ordered.iloc[i + 1].longitude,
                )
            )
        stop_index: dict[str, int] = {}
        for idx, stop_norm in enumerate(norms):
            stop_index.setdefault(stop_norm, idx)
        _route_cache[str(route_no)] = {
            "norms": norms,
            "stop_index": stop_index,
            "cumulative_km": cumulative_km,
            "ordered": ordered,
        }


_register_route_cache(stops_df)
if not _rev_df.empty:
    _register_route_cache(_rev_df)

# ── BMTC operational window ────────────────────────────────────────────────────
BMTC_START_HOUR = 5
BMTC_END_HOUR   = 23
BMTC_END_MINUTE = 30


def is_bmtc_operational(dt: datetime) -> bool:
    """Return True if dt falls within BMTC service hours (05:00–23:30)."""
    t = dt.hour * 60 + dt.minute
    return (BMTC_START_HOUR * 60) <= t <= (BMTC_END_HOUR * 60 + BMTC_END_MINUTE)


def normalize_search_start_time(dt: datetime | None = None) -> datetime:
    """Normalize a lookup start time to the next BMTC operational window."""
    dt = dt or datetime.now()
    minutes = dt.hour * 60 + dt.minute
    start_min = BMTC_START_HOUR * 60
    end_min = BMTC_END_HOUR * 60 + BMTC_END_MINUTE
    if minutes < start_min:
        return dt.replace(hour=BMTC_START_HOUR, minute=0, second=0, microsecond=0)
    if minutes > end_min:
        next_day = dt + timedelta(days=1)
        return next_day.replace(hour=BMTC_START_HOUR, minute=0, second=0, microsecond=0)
    return dt


# ── Speed helpers (fallback) ───────────────────────────────────────────────────

def get_bus_speed_kmh(dt: datetime | None = None) -> float:
    dt   = dt or datetime.now()
    hour = dt.hour
    if (7 <= hour < 10) or (17 <= hour < 21):
        return SPEED_PEAK
    elif 10 <= hour < 17:
        return SPEED_DAY
    return SPEED_NIGHT


def calculate_travel_time(distance_km: float, dt: datetime | None = None) -> float:
    """Travel time in minutes using time-of-day speed model (fallback)."""
    return (distance_km / get_bus_speed_kmh(dt)) * 60


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def time_difference_minutes(t1: datetime, t2: datetime) -> float:
    return abs((t1 - t2).total_seconds() / 60)


# ── Google Maps ETA (with traffic) ────────────────────────────────────────────

def _google_maps_eta_minutes(
    origin_lat: float, origin_lng: float,
    dest_lat: float,   dest_lng: float,
    departure_dt: datetime,
) -> float | None:
    """
    Call Google Distance Matrix API with traffic model.
    Returns travel time in minutes, or None on failure.
    API key loaded from env var or .env file automatically.
    """
    from core.config import GOOGLE_MAPS_API_KEY
    api_key = GOOGLE_MAPS_API_KEY or os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return None

    import time as _time
    dep_ts = max(int(departure_dt.timestamp()), int(_time.time()) + 10)

    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins":         f"{origin_lat},{origin_lng}",
            "destinations":    f"{dest_lat},{dest_lng}",
            "mode":            "driving",
            "departure_time":  dep_ts,
            "traffic_model":   "best_guess",
            "key":             api_key,
        }
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        element = data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            return None
        dur = element.get("duration_in_traffic") or element.get("duration")
        return dur["value"] / 60.0
    except Exception:
        return None


# ── GTFS real-schedule lookup ──────────────────────────────────────────────────

def _gtfs_segment_times(
    route_no: str,
    src_norm: str,
    dst_norm: str,
    after_dt: datetime,
) -> tuple[datetime, datetime] | None:
    """
    Find next real GTFS trip for route_no departing src_norm after after_dt.
    Returns (departure_dt, arrival_dt) or None if not found.
    Only returns trips within BMTC service window (05:00–23:30).
    CACHED for speed on repeated lookups.
    """
    # Cache key: (route_no, src_norm, dst_norm)
    cache_key = (route_no, src_norm, dst_norm)
    if cache_key in _gtfs_segment_cache:
        cached_dep, cached_arr = _gtfs_segment_cache[cache_key]
        # Return cached result if it's still valid for this lookup time
        if cached_dep >= after_dt:
            return cached_dep, cached_arr
    
    try:
        from core.gtfs import _get_gtfs, _stop_ids_for_norm, _parse_gtfs_time
        gtfs_data, _ = _get_gtfs()
        if not gtfs_data:
            return None

        src_ids = _stop_ids_for_norm(src_norm)
        dst_ids = _stop_ids_for_norm(dst_norm)
        if not src_ids or not dst_ids:
            return None

        stop_times = gtfs_data["stop_times"]
        trips      = gtfs_data["trips"]
        routes     = gtfs_data["routes"]

        base_route = route_no.replace("_REV", "")
        route_row  = routes[routes["route_short_name"] == base_route]
        if route_row.empty:
            return None
        route_ids = route_row["route_id"].tolist()
        trip_ids  = trips[trips["route_id"].isin(route_ids)]["trip_id"].tolist()
        if not trip_ids:
            return None

        relevant = stop_times[stop_times["trip_id"].isin(trip_ids)]

        src_times = (
            relevant[relevant["stop_id"].isin(src_ids)]
            [["trip_id", "stop_sequence", "departure_time"]]
            .rename(columns={"stop_sequence": "src_seq", "departure_time": "src_dep"})
        )
        dst_times = (
            relevant[relevant["stop_id"].isin(dst_ids)]
            [["trip_id", "stop_sequence", "arrival_time"]]
            .rename(columns={"stop_sequence": "dst_seq", "arrival_time": "dst_arr"})
        )

        merged = src_times.merge(dst_times, on="trip_id")
        merged = merged[merged["src_seq"] < merged["dst_seq"]]
        if merged.empty:
            return None

        after_td   = timedelta(hours=after_dt.hour, minutes=after_dt.minute, seconds=after_dt.second)
        bmtc_start = timedelta(hours=BMTC_START_HOUR)
        bmtc_end   = timedelta(hours=BMTC_END_HOUR, minutes=BMTC_END_MINUTE)

        candidates = []
        for _, row in merged.iterrows():
            dep_td = _parse_gtfs_time(row["src_dep"])
            arr_td = _parse_gtfs_time(row["dst_arr"])
            if dep_td is None or arr_td is None:
                continue
            if dep_td >= after_td and bmtc_start <= dep_td <= bmtc_end:
                candidates.append((dep_td, arr_td))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        dep_td, arr_td = candidates[0]

        base = after_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        result = (base + dep_td, base + arr_td)
        
        # Cache the result for future lookups
        _gtfs_segment_cache[cache_key] = result
        return result

    except Exception:
        return None


# ── Per-segment timing ─────────────────────────────────────────────────────────

def calculate_segment_times(
    segments: list[tuple],
    start_time: datetime | None = None,
) -> list[dict]:
    """
    Return a list of timing dicts, one per segment.

    Each dict: route_no, departure, arrival, duration,
               distance, fare, base_fare, toll, fare_category, time_source.

    Time resolution priority:
      1. Real GTFS stop_times.txt schedule
      2. Google Maps Distance Matrix (traffic-aware) ETA
      3. Speed-model fallback
    """
    current_time  = start_time or datetime.now()
    segment_times = []

    for i, (route_no, start, end, seg_stops) in enumerate(segments):
        base_route   = route_no.replace("_REV", "")
        route_data   = _route_cache.get(route_no) or _route_cache.get(base_route)
        if not route_data:
            continue

        stop_index = route_data["stop_index"]
        start_idx = stop_index.get(start)
        end_idx = stop_index.get(end)
        if start_idx is None or end_idx is None:
            continue

        lo = min(start_idx, end_idx)
        hi = max(start_idx, end_idx)
        ordered = route_data["ordered"]
        cumulative_km = route_data["cumulative_km"]
        segment_distance = cumulative_km[hi] - cumulative_km[lo]
        sub_norms = route_data["norms"][lo:hi + 1]
        if start_idx > end_idx:
            sub_norms = list(reversed(sub_norms))

        wait_time     = WAITING_TIME if i == 0 else TRANSFER_TIME
        current_time += timedelta(minutes=wait_time)

        departure_dt = current_time
        arrival_dt   = None
        time_source  = "estimate"
        travel_mins  = 0.0

        # ── 1. Real GTFS schedule ──────────────────────────────────────────
        gtfs_result = _gtfs_segment_times(route_no, start, end, current_time)
        if gtfs_result:
            departure_dt, arrival_dt = gtfs_result
            travel_mins = (arrival_dt - departure_dt).total_seconds() / 60
            time_source = "schedule"

        # ── 2. Google Maps traffic ETA ─────────────────────────────────────
        # SKIPPED for performance: speed-model fallback is fast enough
        # (Google Maps API calls add 5+ sec per segment — too slow for multiple routes)

        # ── 3. Speed-model fallback ────────────────────────────────────────
        if arrival_dt is None:
            travel_mins = calculate_travel_time(segment_distance, departure_dt)
            arrival_dt  = departure_dt + timedelta(minutes=travel_mins)
            time_source = "estimate"

        current_time = arrival_dt

        fare_info = segment_fare_breakdown(route_no, segment_distance, sub_norms)

        segment_times.append({
            "route_no":    route_no.replace("_REV", ""),
            "departure":   format_time(departure_dt),
            "arrival":     format_time(arrival_dt),
            "duration":    int(travel_mins),
            "distance":    round(segment_distance, 2),
            "fare":        fare_info["total_fare"],
            "base_fare":   fare_info["base_fare"],
            "toll":        fare_info["toll"],
            "fare_category": fare_info["fare_category"],
            "has_toll":    fare_info["has_toll"],
            "time_source": time_source,  # "schedule" | "google_traffic" | "estimate"
        })

    return segment_times


def estimate_segment_fast(
    route_no: str,
    start: str,
    end: str,
    start_time: datetime | None = None,
) -> dict | None:
    """
    Fast distance/time/fare estimate for result cards.

    This intentionally skips GTFS schedule lookups. Listing many candidate buses
    should stay sub-second; detailed route views can still call
    calculate_segment_times() when the user expands a specific option.
    """
    current_time = start_time or datetime.now()
    route_data = _route_cache.get(route_no) or _route_cache.get(route_no.replace("_REV", ""))
    if not route_data:
        return None

    stop_index = route_data["stop_index"]
    start_idx = stop_index.get(start)
    end_idx = stop_index.get(end)
    if start_idx is None or end_idx is None:
        return None

    lo = min(start_idx, end_idx)
    hi = max(start_idx, end_idx)
    segment_distance = route_data["cumulative_km"][hi] - route_data["cumulative_km"][lo]
    sub_norms = route_data["norms"][lo:hi + 1]
    if start_idx > end_idx:
        sub_norms = list(reversed(sub_norms))

    departure_dt = current_time + timedelta(minutes=WAITING_TIME)
    travel_mins = calculate_travel_time(segment_distance, departure_dt)
    arrival_dt = departure_dt + timedelta(minutes=travel_mins)
    fare_info = segment_fare_breakdown(route_no, segment_distance, sub_norms)
    return {
        "duration": int(travel_mins),
        "fare": fare_info["total_fare"],
        "distance": round(segment_distance, 2),
        "departure": format_time(departure_dt),
        "arrival": format_time(arrival_dt),
    }
