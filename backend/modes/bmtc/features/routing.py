"""
features/routing.py
===================
High-level routing API consumed by the UI.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from math import atan2, cos, radians, sin, sqrt

import pandas as pd

from core.config import WAITING_TIME, TRANSFER_TIME, FAST_QUERY_MODE
from core.config import GTFS_TRIPS, GTFS_ROUTES
from core.loader import stops_df, _rev_df, canonical_stop_name
from core.stops import get_route_stop_list


def _load_route_trips() -> dict[str, int]:
    try:
        trips_df = pd.read_csv(GTFS_TRIPS, dtype={"route_id": str, "trip_id": str})
        routes_df = pd.read_csv(GTFS_ROUTES, dtype={"route_id": str, "route_short_name": str})
        merged = trips_df.merge(routes_df[["route_id", "route_short_name"]], on="route_id", how="left")
        return merged.groupby("route_short_name").size().to_dict()
    except Exception:
        return {}


_route_trips = _load_route_trips()


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * atan2(sqrt(a), sqrt(1 - a))


def _normalize_search_start_time(dt: datetime | None = None) -> datetime:
    dt = dt or datetime.now()
    minutes = dt.hour * 60 + dt.minute
    if minutes < 5 * 60:
        return dt.replace(hour=5, minute=0, second=0, microsecond=0)
    if minutes > 23 * 60 + 30:
        next_day = dt + timedelta(days=1)
        return next_day.replace(hour=5, minute=0, second=0, microsecond=0)
    return dt


def _bus_speed_kmh(dt: datetime) -> float:
    hour = dt.hour
    if (7 <= hour < 10) or (17 <= hour < 21):
        return 10.0
    if 10 <= hour < 17:
        return 20.0
    return 35.0


_combined_routes_df = pd.concat([stops_df, _rev_df], ignore_index=True) if not _rev_df.empty else stops_df
_direct_route_index: list[dict] = []
_direct_route_index_map: dict[str, dict] = {}
_routes_by_stop: dict[str, list[dict]] = {}

for _route_no, _group in _combined_routes_df.groupby("route_no"):
    _ordered = _group.sort_values("stop_sequence")
    _norms = list(_ordered["stop_norm"])
    _cumulative_km = [0.0]
    _rows = list(_ordered.itertuples(index=False))
    for _idx in range(len(_rows) - 1):
        _a = _rows[_idx]
        _b = _rows[_idx + 1]
        _cumulative_km.append(
            _cumulative_km[-1] + _haversine(_a.latitude, _a.longitude, _b.latitude, _b.longitude)
        )
    _positions: dict[str, list[int]] = {}
    for _idx, _stop_norm in enumerate(_norms):
        _positions.setdefault(_stop_norm, []).append(_idx)
    _route_info = {
        "route_no": str(_route_no),
        "base_route": str(_route_no).replace("_REV", ""),
        "norms": _norms,
        "positions": _positions,
        "stop_set": set(_norms),
        "cumulative_km": _cumulative_km,
        "coords": [(row.latitude, row.longitude) for row in _rows],
    }
    _direct_route_index.append(_route_info)
    _direct_route_index_map[_route_info["route_no"]] = _route_info
    for _stop_norm in _positions:
        _routes_by_stop.setdefault(_stop_norm, []).append(_route_info)


_other_buses_cache: dict[tuple[str, str], list[str]] = {}

def get_other_buses_fast(src_norm: str, dst_norm: str, current_route: str) -> list[str]:
    """Get list of other routes connecting src_norm and dst_norm directly."""
    cache_key = (src_norm, dst_norm)
    if cache_key in _other_buses_cache:
        direct_routes = _other_buses_cache[cache_key]
    else:
        src_routes = _routes_by_stop.get(src_norm, [])
        dst_route_ids = {id(r) for r in _routes_by_stop.get(dst_norm, [])}
        
        direct_routes = []
        for r in src_routes:
            if id(r) not in dst_route_ids:
                continue
            base = r["base_route"]
            for si in _route_stop_positions(r, src_norm):
                later_dst = [di for di in _route_stop_positions(r, dst_norm) if si < di]
                if later_dst:
                    if base not in direct_routes:
                        direct_routes.append(base)
        _other_buses_cache[cache_key] = direct_routes
        
    routes = [r for r in direct_routes if r != current_route]
    # Sort by trips descending
    routes.sort(key=lambda b: (-_route_trips.get(b, 0), b))
    return routes


def _estimate_segment_fast(
    route_info: dict,
    start: str,
    end: str,
    start_time: datetime | None = None,
    trips_per_day: int = 0,
) -> dict | None:
    from features.fare import segment_fare_breakdown
    import hashlib

    start_positions = _route_stop_positions(route_info, start)
    end_positions   = _route_stop_positions(route_info, end)
    pairs = [(si, di) for si in start_positions for di in end_positions if si < di]
    if not pairs:
        return None
    start_idx, end_idx = min(pairs, key=lambda pair: pair[1] - pair[0])
    segment_distance   = route_info["cumulative_km"][end_idx] - route_info["cumulative_km"][start_idx]
    sub_norms          = route_info["norms"][start_idx:end_idx + 1]

    now_dt     = start_time or datetime.now()
    route_no   = route_info.get("route_no", "")
    base_route = route_info.get("base_route", route_no).replace("_REV", "")

    if not trips_per_day:
        trips_per_day = _route_trips.get(route_no, _route_trips.get(route_no.replace("_REV", ""), _route_trips.get(base_route, 0)))

    # ── 1. Try real GTFS schedule first ──────────────────────────────────────
    try:
        from core.gtfs import get_route_next_departure, _route_departures, _stop_ids_for_norm
        if base_route in _route_departures:
            src_ids = _stop_ids_for_norm(start)
            dst_ids = _stop_ids_for_norm(end)
            route_table = _route_departures[base_route]
            has_src = any(sid in route_table for sid in src_ids)
            has_dst = any(sid in route_table for sid in dst_ids)
            if has_src and has_dst:
                gtfs = get_route_next_departure(base_route, start, end, now_dt)
                if gtfs:
                    dep_str, arr_str, duration_min = gtfs
                    fare_info = segment_fare_breakdown(base_route, segment_distance, sub_norms)
                    
                    # Calculate waiting time relative to now_dt
                    h, m = map(int, dep_str.split(":"))
                    dep_dt = now_dt.replace(hour=h, minute=m, second=0, microsecond=0)
                    if dep_dt < now_dt:
                        dep_dt += timedelta(days=1)
                    waiting_time = max(0, int((dep_dt - now_dt).total_seconds() / 60))

                    return {
                        "duration":      duration_min,
                        "fare":          fare_info["total_fare"],
                        "base_fare":     fare_info["base_fare"],
                        "toll":          fare_info["toll"],
                        "has_toll":      fare_info["has_toll"],
                        "fare_category": fare_info["fare_category"],
                        "distance":      round(segment_distance, 2),
                        "departure":     dep_str,
                        "arrival":       arr_str,
                        "waiting_time":  waiting_time,
                    }
                else:
                    # No more departures today → fall through to frequency-based estimate below
                    pass
    except Exception as e:
        pass

    # ── 2. Frequency-based headway estimate (fallback) ────────────────────────
    OPERATIONAL_MINUTES = 18 * 60  # 05:00–23:00 (1080 mins)
    if trips_per_day and trips_per_day > 0:
        headway_minutes = OPERATIONAL_MINUTES / trips_per_day
        # Average waiting time for a route with headway H is H / 2.0
        wait_minutes = max(3.0, headway_minutes / 2.0)
    else:
        # Unknown or unindexed low-frequency route: default wait time > 30 mins so it gets filtered out
        wait_minutes = 45.0

    departure_dt = now_dt + timedelta(minutes=wait_minutes)
    waiting_time = max(0, int(wait_minutes))
    duration     = int((segment_distance / _bus_speed_kmh(departure_dt)) * 60)
    arrival_dt   = departure_dt + timedelta(minutes=duration)
    fare_info    = segment_fare_breakdown(base_route, segment_distance, sub_norms)
    return {
        "duration":      duration,
        "fare":          fare_info["total_fare"],
        "base_fare":     fare_info["base_fare"],
        "toll":          fare_info["toll"],
        "has_toll":      fare_info["has_toll"],
        "fare_category": fare_info["fare_category"],
        "distance":      round(segment_distance, 2),
        "departure":     departure_dt.strftime("%H:%M"),
        "arrival":       arrival_dt.strftime("%H:%M"),
        "waiting_time":  waiting_time,
    }


def _estimate_direct_segment(route_no: str, src_norm: str, dst_norm: str, norms: list[str], departure_dt: datetime | None = None) -> dict:
    from features.schedule import calculate_segment_times, normalize_search_start_time

    start_time = normalize_search_start_time(departure_dt)
    segment_norms = norms[norms.index(src_norm):norms.index(dst_norm) + 1]
    times = calculate_segment_times(
        [(route_no, src_norm, dst_norm, segment_norms)],
        start_time=start_time,
    )
    if not times:
        return {
            "duration": None,
            "fare": None,
            "base_fare": None,
            "toll": None,
            "has_toll": None,
            "fare_category": None,
            "distance": None,
            "departure": None,
            "arrival": None,
            "waiting_time": None,
        }
    seg = times[0]
    return {
        "duration": seg["duration"],
        "fare": seg["fare"],
        "base_fare": seg.get("base_fare", seg["fare"]),
        "toll": seg.get("toll", 0),
        "has_toll": seg.get("has_toll", False),
        "fare_category": seg.get("fare_category", "ordinary"),
        "distance": seg["distance"],
        "departure": seg["departure"],
        "arrival": seg["arrival"],
        "waiting_time": seg.get("waiting_time", int(WAITING_TIME)),
    }



_segment_estimate_cache: dict[tuple, dict] = {}


def _get_or_estimate_direct_segment(
    route_no: str,
    src_norm: str,
    dst_norm: str,
    norms: list[str],
    trips_per_day: int = 0,
    request_minute: int = 0,          # minute-precision key to bust stale cache
    departure_dt: datetime | None = None,
) -> dict:
    # Cache keyed by (route, src, dst, request_minute) so each new API request
    # gets fresh staggered times (not a stale time from a previous request).
    cache_key = (route_no, src_norm, dst_norm, request_minute)
    if cache_key in _segment_estimate_cache:
        return _segment_estimate_cache[cache_key]

    route_info = _direct_route_index_map.get(route_no)
    now_dt = _normalize_search_start_time(departure_dt)
    result = (
        _estimate_segment_fast(route_info, src_norm, dst_norm, now_dt, trips_per_day)
        if route_info
        else None
    )
    # If GTFS/fast-estimate returned nothing, always try the schedule-based fallback
    if result is None:
        result = _estimate_direct_segment(route_no, src_norm, dst_norm, norms, departure_dt)
    _segment_estimate_cache[cache_key] = result
    return result


def _route_priority(route_no: str, src_norm: str = "", dst_norm: str = "", preference: str = "cost") -> tuple:
    from features.fare import is_vajra_route, is_kia_route

    base = route_no.replace("_REV", "").upper()
    score = 0

    # KIA airport buses: always deprioritised for in-city queries (high ₹280+ fare)
    if is_kia_route(route_no):
        score += 2000
    elif is_vajra_route(base):
        if preference.lower() in ("convenience", "comfort", "vajra"):
            score -= 50  # Give priority boost for AC/Vajra when comfort/convenience/vajra is selected
        else:
            score += 2000  # Penalize Vajra under cost/time preference so ordinary buses are preferred
            
    if "NICE" in base:
        score += 20
    return (score, -_route_trips.get(route_no.replace("_REV", ""), 0), base)


def _route_stop_positions(route_info: dict, stop_norm: str) -> list[int]:
    return route_info["positions"].get(stop_norm, [])


def get_all_direct_buses(src_raw: str, dst_raw: str, departure_dt: datetime | None = None, preference: str = "cost") -> list[dict]:
    """
    Every route connecting src -> dst directly.

    Uses stop-to-route indexes instead of scanning all routes on every query.
    """
    src_norm = src_raw.strip().lower()
    dst_norm = dst_raw.strip().lower()
    results  = []
    seen_base: set = set()

    # Use a per-request minute key so the cache doesn't serve yesterday's times
    if departure_dt is None:
        departure_dt = datetime.now()
    _req_minute = departure_dt.hour * 60 + departure_dt.minute

    from core.graph import _nearby_stops

    # Include ALL proximity stops within walking distance to improve match rate,
    # especially for coordinate-based queries where the resolved stop may be on
    # a side road with few routes. Cap at 20 to avoid performance regressions.
    src_cluster = [src_norm]
    for n in _nearby_stops.get(src_norm, []):
        if n not in src_cluster:
            src_cluster.append(n)
    src_cluster = src_cluster[:20]

    dst_cluster = [dst_norm]
    for n in _nearby_stops.get(dst_norm, []):
        if n not in dst_cluster:
            dst_cluster.append(n)
    dst_cluster = dst_cluster[:20]

    src_routes_list = []
    seen_src_ids = set()
    for s_norm in src_cluster:
        for r_info in _routes_by_stop.get(s_norm, []):
            r_id = id(r_info)
            if r_id not in seen_src_ids:
                seen_src_ids.add(r_id)
                src_routes_list.append((s_norm, r_info))

    dst_stop_map = {}
    for d_norm in dst_cluster:
        for r_info in _routes_by_stop.get(d_norm, []):
            r_id = id(r_info)
            if r_id not in dst_stop_map:
                dst_stop_map[r_id] = d_norm

    for actual_src_norm, route_info in src_routes_list:
        r_id = id(route_info)
        if r_id not in dst_stop_map:
            continue
        actual_dst_norm = dst_stop_map[r_id]
        route_no = route_info["route_no"]
        norms    = route_info["norms"]
        for si in _route_stop_positions(route_info, actual_src_norm):
            later_dst = [di for di in _route_stop_positions(route_info, actual_dst_norm) if si < di]
            if not later_dst:
                continue
            di = min(later_dst)
            base = route_info["base_route"]
            seen_key = (base, si, di)
            if seen_key in seen_base:
                continue
            seen_base.add(seen_key)
            trips      = _route_trips.get(base, 0)
            schedule   = _get_or_estimate_direct_segment(
                route_no, actual_src_norm, actual_dst_norm, norms,
                trips_per_day=trips, request_minute=_req_minute,
                departure_dt=departure_dt,
            )
            if schedule is None or schedule.get("waiting_time", 0) > 30:
                continue
            stops = [canonical_stop_name(n) for n in norms[si:di + 1]]
            results.append({
                "route":        base,
                "trips":        trips,
                "stop_count":   di - si,
                "duration":     schedule["duration"],
                "total_time":   (schedule["duration"] or 0) + schedule.get("waiting_time", WAITING_TIME),
                "fare":         schedule["fare"],
                "base_fare":    schedule.get("base_fare", schedule["fare"]),
                "toll":         schedule.get("toll", 0),
                "has_toll":     schedule.get("has_toll", False),
                "fare_category": schedule.get("fare_category", "ordinary"),
                "distance":     schedule["distance"],
                "departure":    schedule["departure"],
                "arrival":      schedule["arrival"],
                "waiting_time": schedule.get("waiting_time", 0),
                "stops":        stops,
                "other_buses":  get_other_buses_fast(actual_src_norm, actual_dst_norm, base),
            })

    if preference.lower() == "cost":
        results.sort(key=lambda x: (
            x.get("fare", 9999),
            _route_priority(x["route"], src_norm, dst_norm, preference),
            x.get("waiting_time", 9999),
        ))
    elif preference.lower() == "time":
        results.sort(key=lambda x: (
            _route_priority(x["route"], src_norm, dst_norm, preference)[0],  # vajra penalty first
            x.get("total_time", 9999),
            x.get("waiting_time", 9999),
        ))
    else:
        results.sort(key=lambda x: (x.get("waiting_time", 9999), _route_priority(x["route"], src_norm, dst_norm, preference)))
    return results


@lru_cache(maxsize=16384)
def _best_join_indices_cached(first_route_no: str, second_route_no: str, src_norm: str, dst_norm: str) -> tuple | None:
    first = _direct_route_index_map.get(first_route_no)
    second = _direct_route_index_map.get(second_route_no)
    if not first or not second:
        return None

    first_src_positions = _route_stop_positions(first, src_norm)
    second_dst_positions = _route_stop_positions(second, dst_norm)
    if not first_src_positions or not second_dst_positions:
        return None

    min_src_idx = min(first_src_positions)
    max_dst_idx = max(second_dst_positions)
    
    # Prune stops: only consider transfer stops after boarding on the first route
    first_norms = first["norms"]
    valid_first_stops = set(first_norms[min_src_idx + 1:])
    
    # Prune stops: only consider transfer stops before alighting on the second route
    second_norms = second["norms"]
    valid_second_stops = set(second_norms[:max_dst_idx])

    best = None
    from core.graph import _nearby_stops
    for s1 in valid_first_stops:
        candidates = {s1}
        if s1 in _nearby_stops:
            candidates.update(_nearby_stops[s1])
        
        valid_joins = candidates & valid_second_stops
        if not valid_joins:
            continue
            
        first_join_positions = _route_stop_positions(first, s1)
        for join_norm in valid_joins:
            second_join_positions = _route_stop_positions(second, join_norm)
            for src_idx in first_src_positions:
                for first_join_idx in first_join_positions:
                    if first_join_idx - src_idx < 2:  # Must travel at least 2 stops on first bus
                        continue
                    for second_join_idx in second_join_positions:
                        for dst_idx in second_dst_positions:
                            if dst_idx - second_join_idx < 2:  # Must travel at least 2 stops on second bus
                                continue
                            lat1, lon1 = first["coords"][first_join_idx]
                            lat2, lon2 = second["coords"][second_join_idx]
                            xfer_dist = _haversine(lat1, lon1, lat2, lon2)
                            if xfer_dist > 0.75:
                                continue
                            travel_stops = (first_join_idx - src_idx) + (dst_idx - second_join_idx)
                            routes_at_join = len(_routes_by_stop.get(join_norm, []))
                            # Mild hub bonus (capped at 40 routes) so major hubs like Silk Board get a small tiebreaker,
                            # without overriding 40+ stops of detour to Majestic!
                            hub_bonus = min(routes_at_join, 40) * 0.05
                            score = travel_stops + (xfer_dist * 3.0) - hub_bonus
                            candidate = (score, travel_stops, src_idx, first_join_idx, second_join_idx, dst_idx, s1, join_norm)
                            if best is None or candidate < best:
                                best = candidate

    if best is None:
        return None
    return best[2], best[3], best[4], best[5], best[6], best[7]


def _best_join_indices(first: dict, second: dict, src_norm: str, dst_norm: str) -> tuple | None:
    return _best_join_indices_cached(first["route_no"], second["route_no"], src_norm, dst_norm)


@lru_cache(maxsize=512)
def _fast_transfer_options(src_norm: str, dst_norm: str, limit: int = 8, request_minute: int = 0, preference: str = "cost") -> tuple[dict, ...]:
    from core.graph import _nearby_stops

    # Build expanded source route list: include routes from nearby walkable stops
    # when the primary stop has few routes (helps coordinate-based queries).
    # Each entry is (route_info, actual_boarding_norm).
    src_route_pairs: list[tuple[dict, str]] = []
    seen_src_ids: set = set()
    for r in _routes_by_stop.get(src_norm, []):
        seen_src_ids.add(id(r))
        src_route_pairs.append((r, src_norm))
    if len(src_route_pairs) < 5:
        for nearby_norm in _nearby_stops.get(src_norm, []):
            for r in _routes_by_stop.get(nearby_norm, []):
                if id(r) not in seen_src_ids:
                    seen_src_ids.add(id(r))
                    src_route_pairs.append((r, nearby_norm))

    # Build expanded destination route list similarly.
    dst_route_pairs: list[tuple[dict, str]] = []
    seen_dst_ids: set = set()
    for r in _routes_by_stop.get(dst_norm, []):
        seen_dst_ids.add(id(r))
        dst_route_pairs.append((r, dst_norm))
    if len(dst_route_pairs) < 5:
        for nearby_norm in _nearby_stops.get(dst_norm, []):
            for r in _routes_by_stop.get(nearby_norm, []):
                if id(r) not in seen_dst_ids:
                    seen_dst_ids.add(id(r))
                    dst_route_pairs.append((r, nearby_norm))

    if not src_route_pairs or not dst_route_pairs:
        return tuple()

    # Sort source and destination route pairs by frequency (trips_per_day) descending
    # checking route_no, stripped _REV, and base_route so 600-F_REV gets full 133 trips priority
    def _get_trips(route_dict):
        rno = route_dict.get("route_no", "")
        base = route_dict.get("base_route", "")
        return _route_trips.get(rno, _route_trips.get(rno.replace("_REV", ""), _route_trips.get(base, 0)))

    src_route_pairs.sort(key=lambda pair: _get_trips(pair[0]), reverse=True)
    dst_route_pairs.sort(key=lambda pair: _get_trips(pair[0]), reverse=True)

    now = datetime.now()
    h = request_minute // 60
    m = request_minute % 60
    start_time = _normalize_search_start_time(now.replace(hour=h, minute=m, second=0, microsecond=0))
    candidates = []
    seen: set[tuple[str, str, str]] = set()

    for first, actual_src in src_route_pairs:
        for second, actual_dst in dst_route_pairs:
            if first["route_no"] == second["route_no"]:
                continue
            join = _best_join_indices(first, second, actual_src, actual_dst)
            if not join:
                continue

            src_idx, first_join_idx, second_join_idx, dst_idx, first_join, second_join = join
            base_first = first["base_route"]
            base_second = second["base_route"]
            seen_key = (base_first, base_second, first_join)
            if seen_key in seen:
                continue
            seen.add(seen_key)

            first_stops = first["norms"][src_idx:first_join_idx + 1]
            second_stops = second["norms"][second_join_idx:dst_idx + 1]
            if len(first_stops) < 3 or len(second_stops) < 3:
                continue

            segs = [
                (base_first, actual_src, first_join, first_stops),
                (base_second, second_join, actual_dst, second_stops),
            ]
            t1 = _estimate_segment_fast(first, actual_src, first_join, start_time)
            if not t1 or t1.get("distance", 0) < 0.8:
                continue
            t1_waiting = t1.get("waiting_time", WAITING_TIME)
            if t1_waiting > 30:
                continue

            # Compute actual arrival time at the transfer stop to chain the second segment correctly
            try:
                dep_h, dep_m = map(int, t1["departure"].split(":"))
                arr_h, arr_m = map(int, t1["arrival"].split(":"))
                dep_dt = start_time.replace(hour=dep_h, minute=dep_m, second=0, microsecond=0)
                arr_dt = start_time.replace(hour=arr_h, minute=arr_m, second=0, microsecond=0)
                if arr_dt < dep_dt:
                    arr_dt += timedelta(days=1)
            except Exception:
                arr_dt = start_time + timedelta(minutes=(t1.get("duration") or 0))

            t2_start_time = arr_dt + timedelta(minutes=TRANSFER_TIME)
            t2 = _estimate_segment_fast(second, second_join, actual_dst, t2_start_time)
            if not t2 or t2.get("distance", 0) < 0.8:
                continue
            t2_waiting = t2.get("waiting_time", WAITING_TIME)
            if t2_waiting > 30 or (t1_waiting + t2_waiting) > 30:
                continue

            times = [t1, t2]
            total_fare = sum(t["fare"] for t in times)
            t1_waiting = t1.get("waiting_time", WAITING_TIME)
            t2_waiting = t2.get("waiting_time", WAITING_TIME)
            total_time = sum(t["duration"] for t in times) + t1_waiting + TRANSFER_TIME + t2_waiting
            distance = sum(t["distance"] for t in times)
            buses = [base_first, base_second]
            p_lower = preference.lower()
            if p_lower in ("convenience", "comfort", "vajra"):
                score_val = (
                    _route_priority(base_first, actual_src, actual_dst, preference)[0] +
                    _route_priority(base_second, actual_src, actual_dst, preference)[0],
                    total_time,
                    total_fare,
                )
            elif p_lower == "cost":
                score_val = (
                    total_fare,
                    total_time,
                    _route_priority(base_first, actual_src, actual_dst, preference)[0] +
                    _route_priority(base_second, actual_src, actual_dst, preference)[0],
                )
            else:  # time / fastest (default)
                score_val = (
                    total_time,
                    total_fare,
                    _route_priority(base_first, actual_src, actual_dst, preference)[0] +
                    _route_priority(base_second, actual_src, actual_dst, preference)[0],
                )
            candidates.append({
                "transfers": 1,
                "distance": round(distance, 1),
                "total_time": int(total_time),
                "total_fare": total_fare,
                "waiting_time": t1_waiting,
                "buses": buses,
                "trips": [_route_trips.get(b, 0) for b in buses],
                "segments": segs,
                "segment_times": times,
                "_score": score_val,
            })

    candidates.sort(key=lambda opt: opt["_score"])
    for opt in candidates:
        opt.pop("_score", None)
    return tuple(candidates[:limit])


def _enrich_transfer_option(opt: dict) -> dict:
    segs = opt["segments"]
    times = opt["segment_times"]
    segment_details = []
    for (route, start_norm, end_norm, stop_norms), t_info in zip(segs, times):
        segment_details.append({
            "route": route,
            "from": canonical_stop_name(start_norm),
            "to": canonical_stop_name(end_norm),
            "stops": [canonical_stop_name(s) for s in stop_norms],
            "other_buses": get_other_buses_fast(start_norm, end_norm, route),
            "duration": t_info.get("duration"),
            "departure": t_info.get("departure"),
            "arrival": t_info.get("arrival"),
            "fare": t_info.get("fare"),
            "base_fare": t_info.get("base_fare", t_info.get("fare")),
            "toll": t_info.get("toll", 0),
            "has_toll": t_info.get("has_toll", False),
            "fare_category": t_info.get("fare_category", "ordinary"),
        })
    opt["segment_details"] = segment_details
    return opt


def get_all_buses_comprehensive(
    src_raw: str,
    dst_raw: str,
    max_transfer_options: int = 8,
    departure_dt: datetime | None = None,
    preference: str = "cost",
) -> tuple[list[dict], list[dict]]:
    """
    Returns (direct_buses, transfer_options).

    Transfer suggestions are built from route intersections first. That is much
    faster than a fresh whole-graph Dijkstra and gives corridor routes a chance
    to rank above long detours.
    """
    # Ensure GTFS data is loaded
    from core.gtfs import _get_gtfs
    _get_gtfs()

    src_norm = src_raw.strip().lower()
    dst_norm = dst_raw.strip().lower()

    if departure_dt is None:
        departure_dt = datetime.now()
    _req_minute = departure_dt.hour * 60 + departure_dt.minute

    direct = get_all_direct_buses(src_norm, dst_norm, departure_dt, preference)
    fast_xfer = list(_fast_transfer_options(src_norm, dst_norm, max_transfer_options * 2, _req_minute, preference))
    enriched_xfer = [_enrich_transfer_option(opt) for opt in fast_xfer]

    transfer_options = []
    if not FAST_QUERY_MODE:
        from core.graph import dijkstra_all_options, extract_segments
        opts = dijkstra_all_options(
            src_norm,
            dst_norm,
            max_transfers=2,
            max_options=min(max_transfer_options, 3),
        )

        from features.schedule import calculate_segment_times, normalize_search_start_time

        start_time = normalize_search_start_time(departure_dt)
        for path, (transfers, dist) in opts:
            if transfers == 0:
                continue
            segs = extract_segments(path)
            times = calculate_segment_times(segs, start_time=start_time)
            total_fare = sum(t["fare"] for t in times)
            t1_waiting = times[0].get("waiting_time", WAITING_TIME) if times else WAITING_TIME
            total_time = sum(t["duration"] for t in times) + sum(t.get("waiting_time", 0) for t in times)
            buses = [s[0] for s in segs]
            trips_list = [_route_trips.get(b, 0) for b in buses]
            transfer_options.append(_enrich_transfer_option({
                "transfers": transfers,
                "distance": round(dist, 1),
                "total_time": int(total_time),
                "total_fare": total_fare,
                "waiting_time": t1_waiting,
                "buses": buses,
                "trips": trips_list,
                "segments": segs,
                "segment_times": times,
            }))

    # Merge, filter out options exceeding 30 mins wait time, and deduplicate
    all_transfers = enriched_xfer + transfer_options
    seen_buses = set()
    unique_transfers = []
    for opt in all_transfers:
        bus_tuple = tuple(opt["buses"])
        w_time = opt.get("waiting_time", 0)
        seg_times = opt.get("segment_times", [])
        if w_time > 30 or any(st.get("waiting_time", 0) > 30 for st in seg_times):
            continue
        if bus_tuple not in seen_buses:
            seen_buses.add(bus_tuple)
            unique_transfers.append(opt)

    direct = [b for b in direct if b.get("waiting_time", 0) <= 30]

    if preference.lower() in ("convenience", "comfort"):
        unique_transfers.sort(key=lambda opt: (
            sum(_route_priority(b, src_norm, dst_norm, preference)[0] for b in opt["buses"]),
            opt["total_time"],
            opt["transfers"],
        ))
    elif preference.lower() == "cost":
        unique_transfers.sort(key=lambda opt: (
            opt["total_fare"],
            sum(_route_priority(b, src_norm, dst_norm, preference)[0] for b in opt["buses"]),
            opt["total_time"],
            opt["transfers"],
        ))
    else:  # time / fastest
        unique_transfers.sort(key=lambda opt: (
            sum(_route_priority(b, src_norm, dst_norm, preference)[0] for b in opt["buses"]),
            opt["total_time"],
            opt["transfers"],
        ))
    return direct, unique_transfers[:max_transfer_options]


def estimate_route_schedule(route_no: str, start_time: datetime | None = None) -> dict:
    """Estimate departure / arrival / duration / distance for a full route."""
    # Ensure GTFS data is loaded
    from core.gtfs import _get_gtfs
    _get_gtfs()

    from features.schedule import calculate_segment_times, normalize_search_start_time

    start_time = normalize_search_start_time(start_time)
    stop_norms = get_route_stop_list(route_no)
    if not stop_norms:
        return {}

    # Find the first and last stops that are matched in GTFS and have departures for this route
    from core.gtfs import _route_departures, _stop_ids_for_norm
    base_route = route_no.replace("_REV", "")
    route_table = _route_departures.get(base_route, {})
    gtfs_stops = [
        s for s in stop_norms 
        if any(sid in route_table for sid in _stop_ids_for_norm(s))
    ]
    
    if len(gtfs_stops) >= 2:
        src_gtfs = gtfs_stops[0]
        dst_gtfs = gtfs_stops[-1]
        si = stop_norms.index(src_gtfs)
        di = stop_norms.index(dst_gtfs)
        sub_norms = stop_norms[si:di + 1]
        segments = [(route_no, src_gtfs, dst_gtfs, sub_norms)]
    else:
        segments = [(route_no, stop_norms[0], stop_norms[-1], stop_norms)]

    seg_times = calculate_segment_times(segments, start_time)
    if not seg_times:
        return {}
    return {
        "departure": seg_times[0]["departure"],
        "arrival": seg_times[0]["arrival"],
        "duration": seg_times[0]["duration"],
        "distance": seg_times[0]["distance"],
    }


def generate_guide(segments: list[tuple]) -> list[str]:
    """Human-readable step-by-step boarding instructions."""
    instructions = []
    for i, (route, start, end, seg_stops) in enumerate(segments, 1):
        names = [canonical_stop_name(s) for s in seg_stops]
        instructions.append(f"Step {i}: Board Bus {route} at {names[0]}.")
        if len(names) > 2:
            instructions.append(f"Travel through: {' -> '.join(names[1:-1])}.")
        instructions.append(f"Get down at {names[-1]}.")
        instructions.append("")
    return instructions
