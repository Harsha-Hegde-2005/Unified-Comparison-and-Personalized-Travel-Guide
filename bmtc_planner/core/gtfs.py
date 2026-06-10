"""
core/gtfs.py
============
Loads the four GTFS flat-files and exposes:
  - _stop_ids_for_norm(stop_norm) — exact stop_norm → [stop_id] look-up
  - suggest_top_buses()           — GTFS-backed top-N route suggestions

GTFS data is loaded inside @st.cache_resource so it is read from disk
ONCE per server session — button clicks never reload it.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from core.config import (
    GTFS_STOPS, GTFS_STOP_TIMES, GTFS_TRIPS, GTFS_ROUTES,
    EXCLUDED_ROUTE_PATTERNS, TOP_N_BUSES,
)


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _parse_gtfs_time(t: str) -> timedelta | None:
    if pd.isna(t):
        return None
    parts = str(t).split(":")
    if len(parts) != 3:
        return None
    h, m, s = map(int, parts)
    return timedelta(hours=h, minutes=m, seconds=s)


def format_gtfs_time(td: timedelta | None) -> str:
    if td is None:
        return "(none)"
    total = int(td.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def _is_excluded_route(route_label: str) -> bool:
    if not route_label:
        return False
    label_lower = str(route_label).lower()
    return any(pat.lower() in label_lower for pat in EXCLUDED_ROUTE_PATTERNS)


# ── Cached GTFS loader — runs once per server session ─────────────────────────

@st.cache_resource(show_spinner="Loading GTFS schedule…")
def _load_gtfs_cached() -> tuple[dict, dict]:
    """
    Returns (gtfs_data_dict, stopnorm_to_ids_dict).
    Cached — never re-runs on Streamlit reruns or button clicks.
    """
    from core.loader import stops_df
    try:
        gtfs_stops = pd.read_csv(GTFS_STOPS,      dtype={"stop_id": str, "stop_name": str})
        stop_times = pd.read_csv(GTFS_STOP_TIMES, dtype={"trip_id": str, "stop_id": str, "stop_sequence": int})
        trips      = pd.read_csv(GTFS_TRIPS,      dtype={"route_id": str, "trip_id": str, "route_short_name": str})
        routes     = pd.read_csv(GTFS_ROUTES,     dtype={"route_id": str, "route_short_name": str})

        data = {"stops": gtfs_stops, "stop_times": stop_times,
                "trips": trips,      "routes": routes}

        gtfs_stops["stop_norm"] = gtfs_stops["stop_name"].str.strip().str.lower()
        known_norms = set(stops_df["stop_norm"].unique())
        norm_to_ids: dict[str, list[str]] = {}
        for _, row in gtfs_stops.iterrows():
            n = row["stop_norm"]
            if n in known_norms:
                norm_to_ids.setdefault(n, []).append(str(row["stop_id"]))

        print(f"GTFS loaded. Matched {len(norm_to_ids)} stop norms to GTFS IDs.")
        return data, norm_to_ids

    except FileNotFoundError:
        print("GTFS files not found — schedule features disabled.")
        return {}, {}
    except Exception as e:
        print(f"GTFS load error: {e}")
        return {}, {}


def _get_gtfs() -> tuple[dict, dict]:
    """Return cached GTFS data and stop-norm index."""
    return _load_gtfs_cached()


def _stop_ids_for_norm(stop_norm: str) -> list[str]:
    """Return GTFS stop_id list for a normalised stop name (exact match)."""
    _, norm_to_ids = _get_gtfs()
    return norm_to_ids.get(stop_norm, [])


# ── Top-bus suggestions ───────────────────────────────────────────────────────

def suggest_top_buses(src_stop: str, dst_stop: str, top_n: int = 10) -> list[dict]:
    """
    Return top_n most frequent direct routes between src and dst,
    using GTFS schedule data. Excludes AC/airport routes.
    """
    gtfs_data, _ = _get_gtfs()
    if not gtfs_data:
        return []

    src_norm = src_stop.strip().lower()
    dst_norm = dst_stop.strip().lower()
    src_ids  = _stop_ids_for_norm(src_norm)
    dst_ids  = _stop_ids_for_norm(dst_norm)
    if not src_ids or not dst_ids:
        return []

    stop_times = gtfs_data["stop_times"]
    trips      = gtfs_data["trips"]
    routes     = gtfs_data["routes"]

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

    now_td = timedelta(hours=datetime.now().hour,
                       minutes=datetime.now().minute,
                       seconds=datetime.now().second)

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

    # Sort by next soonest arrival first (so all reachable routes show, not just highest-frequency).
    # Trip count is a secondary sort — helps with ties but doesn't hide low-frequency routes.
    result.sort(key=lambda x: (
        x["next_arrival"] or timedelta(hours=999),  # soonest first
        -x["trips_per_day"],                         # then most frequent
    ))
    return result[:top_n]

