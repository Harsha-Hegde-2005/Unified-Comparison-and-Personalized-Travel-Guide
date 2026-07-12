"""
core/gtfs.py
============
GTFS schedule loader — FastAPI-compatible singleton (NO Streamlit dependency).

Loads the four GTFS flat-files ONCE at import time using a threading lock so
uvicorn worker threads share a single copy.

Public API
----------
  _parse_gtfs_time(t)                  → timedelta | None
  _get_gtfs()                          → (gtfs_data_dict, norm_to_ids_dict)
  _stop_ids_for_norm(stop_norm)        → list[str]
  get_route_next_departure(route_no, src_norm, dst_norm, after_dt)
                                       → (dep_str, arr_str, duration_min) | None
  suggest_top_buses(src, dst, top_n)   → list[dict]
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from core.config import (
    GTFS_STOPS, GTFS_STOP_TIMES, GTFS_TRIPS, GTFS_ROUTES,
    EXCLUDED_ROUTE_PATTERNS, TOP_N_BUSES,
)

# ---------------------------------------------------------------------------
# Module-level singleton (loaded once, shared across all requests)
# ---------------------------------------------------------------------------
_gtfs_lock     = threading.Lock()
_gtfs_loaded   = False
_gtfs_data: dict      = {}          # {"stops": df, "stop_times": df, "trips": df, "routes": df}
_norm_to_ids:  dict   = {}          # stop_norm → [stop_id, ...]

# Fast departure index:
#   _route_departures[route_short_name][src_norm][dst_norm]
#     = sorted list of (dep_timedelta, arr_timedelta)
_route_departures: dict = {}

BMTC_START = timedelta(hours=5)
BMTC_END   = timedelta(hours=23, minutes=30)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _parse_gtfs_time(t) -> Optional[timedelta]:
    """Parse a GTFS HH:MM:SS time string (may exceed 24h) into a timedelta."""
    if pd.isna(t):
        return None
    parts = str(t).split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = map(int, parts)
        return timedelta(hours=h, minutes=m, seconds=s)
    except ValueError:
        return None


def format_gtfs_time(td: Optional[timedelta]) -> str:
    if td is None:
        return "(none)"
    total = int(td.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def _is_excluded_route(route_label: str) -> bool:
    if not route_label:
        return False
    label_lower = str(route_label).lower()
    return any(pat.lower() in label_lower for pat in EXCLUDED_ROUTE_PATTERNS)


# ---------------------------------------------------------------------------
# Singleton loader (called at import time, once)
# ---------------------------------------------------------------------------

def _load_gtfs() -> None:
    global _gtfs_loaded, _gtfs_data, _norm_to_ids, _route_departures

    with _gtfs_lock:
        if _gtfs_loaded:
            return

        try:
            from core.loader import stops_df

            print("GTFS: loading files…")
            gtfs_stops = pd.read_csv(GTFS_STOPS,      dtype={"stop_id": str, "stop_name": str})
            stop_times = pd.read_csv(GTFS_STOP_TIMES, dtype={"trip_id": str, "stop_id": str,
                                                               "stop_sequence": int})
            trips      = pd.read_csv(GTFS_TRIPS,      dtype={"route_id": str, "trip_id": str})
            routes     = pd.read_csv(GTFS_ROUTES,     dtype={"route_id": str,
                                                               "route_short_name": str})

            _gtfs_data = {
                "stops":      gtfs_stops,
                "stop_times": stop_times,
                "trips":      trips,
                "routes":     routes,
            }

            # Build stop_norm → [stop_id] mapping
            def clean_stop_name(name: str) -> str:
                if not isinstance(name, str):
                    return name
                name_upper = name.upper()
                for prefix in ["CS-", "CS "]:
                    if name_upper.startswith(prefix):
                        return name[len(prefix):].strip()
                return name

            gtfs_stops["stop_name"] = gtfs_stops["stop_name"].apply(clean_stop_name)
            gtfs_stops["stop_norm"] = gtfs_stops["stop_name"].str.strip().str.lower()
            from core.loader import _rev_df
            import math

            # Group all_stops_combined by stop_norm to get average coordinates
            all_stops_combined = pd.concat([stops_df, _rev_df], ignore_index=True) if not _rev_df.empty else stops_df
            coords_by_norm = all_stops_combined.groupby("stop_norm")[["latitude", "longitude"]].mean()

            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
                return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            # Grid parameters (150m tolerance)
            TOLERANCE_KM = 0.15
            KM_PER_DEG_LAT = 111.0
            KM_PER_DEG_LNG = 111.0 * math.cos(math.radians(13.0)) # ≈ 108.1
            CELL_DEG_LAT = TOLERANCE_KM / KM_PER_DEG_LAT * 1.05
            CELL_DEG_LNG = TOLERANCE_KM / KM_PER_DEG_LNG * 1.05

            grid = {}
            for norm, row in coords_by_norm.iterrows():
                lat, lng = row["latitude"], row["longitude"]
                cell = (int(lat / CELL_DEG_LAT), int(lng / CELL_DEG_LNG))
                grid.setdefault(cell, []).append((str(norm), lat, lng))

            # Match GTFS stops to known norms using exact and proximity matching
            for _, row in gtfs_stops.iterrows():
                n = row["stop_norm"]
                stop_id = str(row["stop_id"])
                gtfs_lat, gtfs_lng = row["stop_lat"], row["stop_lon"]
                
                # 1. Exact match
                if n in coords_by_norm.index:
                    _norm_to_ids.setdefault(n, []).append(stop_id)
                
                # 2. Proximity match (find any known stop within 150m)
                cx = int(gtfs_lat / CELL_DEG_LAT)
                cy = int(gtfs_lng / CELL_DEG_LNG)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for norm_cand, clat, clng in grid.get((cx + dx, cy + dy), []):
                            if norm_cand == n:
                                continue # already handled by exact match
                            d = haversine(gtfs_lat, gtfs_lng, clat, clng)
                            if d <= TOLERANCE_KM:
                                _norm_to_ids.setdefault(norm_cand, []).append(stop_id)

            print(f"GTFS: matched {len(_norm_to_ids)} stop norms to GTFS IDs (with proximity fallback).")

            # ── Build fast route-departure index ──────────────────────────────
            # Merge stop_times with trips → routes to get route_short_name per trip
            # We build: _route_departures[route_short_name][stop_id]
            #             = sorted list of (dep_timedelta, arr_timedelta, trip_id)
            print("GTFS: building departure index (vectorized)…")

            # Merge stop_times with trips → route_short_name in one vectorized pass
            merged_trips = trips.merge(
                routes[["route_id", "route_short_name"]], on="route_id", how="left"
            )
            st = stop_times.merge(
                merged_trips[["trip_id", "route_short_name"]], on="trip_id", how="left"
            )
            st = st.dropna(subset=["route_short_name", "departure_time"])

            # Parse times vectorized — map only unique time strings for speed
            all_dep_times = st["departure_time"].unique()
            all_arr_times = st["arrival_time"].dropna().unique()
            dep_map = {t: _parse_gtfs_time(t) for t in all_dep_times}
            arr_map = {t: _parse_gtfs_time(t) for t in all_arr_times}

            st["dep_td"] = st["departure_time"].map(dep_map)
            st["arr_td"] = st["arrival_time"].map(arr_map)
            st = st.dropna(subset=["dep_td"])

            # Group by route and stop_id — build sorted departure lists
            _route_stop_departures: dict[str, dict[str, list]] = {}
            for (rname, sid), grp in st.groupby(["route_short_name", "stop_id"]):
                entries = list(zip(grp["dep_td"], grp["arr_td"].fillna(grp["dep_td"]), grp["trip_id"]))
                entries.sort(key=lambda x: x[0])
                _route_stop_departures.setdefault(str(rname), {})[str(sid)] = entries

            _route_departures = _route_stop_departures
            print(f"GTFS: departure index built for {len(_route_departures)} routes.")

        except FileNotFoundError:
            print("GTFS: files not found — schedule features disabled.")
        except Exception as e:
            print(f"GTFS: load error: {e}")

        _gtfs_loaded = True


def _get_gtfs() -> tuple[dict, dict]:
    """Return (gtfs_data_dict, norm_to_ids_dict). Loads GTFS data on first call."""
    if not _gtfs_loaded:
        _load_gtfs()
    return _gtfs_data, _norm_to_ids


def _stop_ids_for_norm(stop_norm: str) -> list[str]:
    """Return GTFS stop_id list for a normalised stop name."""
    return _norm_to_ids.get(stop_norm, [])


def get_route_next_departure(
    route_no: str,
    src_norm: str,
    dst_norm: str,
    after_dt: datetime,
) -> Optional[tuple[str, str, int]]:
    """
    Return (departure_str "HH:MM", arrival_str "HH:MM", duration_min) for the
    next real GTFS trip of `route_no` departing `src_norm` after `after_dt`.

    Returns None if no match found or GTFS not loaded.
    """
    if not _gtfs_data or not _route_departures:
        return None

    base_route = route_no.replace("_REV", "")
    route_table = _route_departures.get(base_route)
    if not route_table:
        return None

    src_ids = _stop_ids_for_norm(src_norm)
    dst_ids = _stop_ids_for_norm(dst_norm)
    if not src_ids or not dst_ids:
        return None

    after_td = timedelta(
        hours=after_dt.hour,
        minutes=after_dt.minute,
        seconds=after_dt.second,
    )

    # Collect all source departures from any matching stop_id
    src_candidates: list[tuple[timedelta, timedelta, str]] = []
    for sid in src_ids:
        if sid in route_table:
            src_candidates.extend(route_table[sid])

    if not src_candidates:
        return None

    # Sort by departure time and find the first one after `after_td`
    src_candidates.sort(key=lambda x: x[0])

    # Try to find a matching trip where src departs AFTER after_td and dst comes after src
    dst_ids_set = set(dst_ids)

    # Build trip_id → dst_arrival map for this route
    # (scan all dst stop_ids)
    trip_dst_arrivals: dict[str, timedelta] = {}
    for sid in dst_ids:
        if sid in route_table:
            for dep_td, arr_td, trip_id in route_table[sid]:
                # Keep the earliest arrival for each trip (in case of multi-stop matches)
                if trip_id not in trip_dst_arrivals or arr_td < trip_dst_arrivals[trip_id]:
                    trip_dst_arrivals[trip_id] = arr_td

    best: Optional[tuple[timedelta, timedelta]] = None

    for dep_td, arr_td, trip_id in src_candidates:
        # Must depart after current time
        if dep_td < after_td:
            continue
        # Must be within BMTC operating hours
        if not (BMTC_START <= dep_td <= BMTC_END):
            continue
        # Find matching dst arrival for same trip
        dst_arr = trip_dst_arrivals.get(trip_id)
        if dst_arr is None:
            continue
        # dst must come AFTER src on this trip
        if dst_arr <= dep_td:
            continue
        best = (dep_td, dst_arr)
        break

    if best is None:
        return None

    dep_td, arr_td = best
    base = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dep_dt = base + dep_td
    arr_dt = base + arr_td
    duration_min = max(1, int((arr_dt - dep_dt).total_seconds() / 60))

    return (
        dep_dt.strftime("%H:%M"),
        arr_dt.strftime("%H:%M"),
        duration_min,
    )


# ---------------------------------------------------------------------------
# Top-bus suggestions (unchanged logic, now uses singleton)
# ---------------------------------------------------------------------------

def suggest_top_buses(src_stop: str, dst_stop: str, top_n: int = TOP_N_BUSES) -> list[dict]:
    """
    Return top_n most frequent direct routes between src and dst,
    using GTFS schedule data. Excludes AC/airport routes.
    """
    if not _gtfs_data:
        return []

    src_norm = src_stop.strip().lower()
    dst_norm = dst_stop.strip().lower()
    src_ids  = _stop_ids_for_norm(src_norm)
    dst_ids  = _stop_ids_for_norm(dst_norm)
    if not src_ids or not dst_ids:
        return []

    stop_times = _gtfs_data["stop_times"]
    trips      = _gtfs_data["trips"]
    routes     = _gtfs_data["routes"]

    src_times = (
        stop_times[stop_times["stop_id"].isin(src_ids)]
        [["trip_id", "stop_sequence", "departure_time", "arrival_time"]]
        .rename(columns={"stop_sequence": "src_seq",
                         "departure_time": "src_departure",
                         "arrival_time":   "src_arrival"})
    )
    dst_times = (
        stop_times[stop_times["stop_id"].isin(dst_ids)]
        [["trip_id", "stop_sequence", "departure_time", "arrival_time"]]
        .rename(columns={"stop_sequence": "dst_seq",
                         "departure_time": "dst_departure",
                         "arrival_time":   "dst_arrival"})
    )

    merged = src_times.merge(dst_times, on="trip_id", how="inner")
    merged = merged[merged["src_seq"] < merged["dst_seq"]]
    if merged.empty:
        return []

    merged = merged.merge(trips,  on="trip_id",  how="left")
    merged = merged.merge(routes, on="route_id", how="left")

    now_td = timedelta(
        hours=datetime.now().hour,
        minutes=datetime.now().minute,
        seconds=datetime.now().second,
    )

    route_info: dict[str, dict] = {}
    for _, row in merged.iterrows():
        label = str(row.get("route_short_name") or row.get("route_id") or "")
        if _is_excluded_route(label):
            continue
        info = route_info.setdefault(label, {"count": 0, "all_departures": [], "all_arrivals": []})
        info["count"] += 1
        dep = _parse_gtfs_time(row.get("src_departure"))
        arr = _parse_gtfs_time(row.get("dst_arrival"))
        if dep:
            info["all_departures"].append(dep)
        if arr:
            info["all_arrivals"].append(arr)

    result = []
    for route, info in route_info.items():
        future_deps = sorted(t for t in info["all_departures"] if t >= now_td)
        future_arrs = sorted(t for t in info["all_arrivals"]   if t >= now_td)
        result.append({
            "route":          route,
            "trips_per_day":  info["count"],
            "next_departure": future_deps[0] if future_deps else None,
            "next_arrival":   future_arrs[0] if future_arrs else None,
        })

    result.sort(key=lambda x: (
        x["next_arrival"] or timedelta(hours=999),
        -x["trips_per_day"],
    ))
    return result[:top_n]
