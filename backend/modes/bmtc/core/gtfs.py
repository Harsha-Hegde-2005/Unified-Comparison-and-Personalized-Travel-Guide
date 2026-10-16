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
import os
import sqlite3

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
_GTFS_DB = os.path.join(_REPO_ROOT, "database", "gtfs_index.db")

_gtfs_lock     = threading.Lock()
_gtfs_loaded   = False
_gtfs_data: dict      = {}          # {"stops": df, "routes": df}
_norm_to_ids:  dict   = {}          # stop_norm → [stop_id, ...]


class RouteDeparturesDict(dict):
    """
    High-performance on-demand route departures lookup backed by SQLite.
    Replaces the 1GB in-memory nested dictionary with zero-overhead cached queries.
    """
    def __init__(self, db_path: str = _GTFS_DB):
        super().__init__()
        self.db_path = db_path
        self._cache: dict = {}

    def _query(self, route_key: str):
        if not route_key or not os.path.exists(self.db_path):
            return None
        raw = str(route_key).strip().upper().replace("_REV", "")
        clean = raw.split()[0] if raw else raw
        candidates = list(dict.fromkeys([raw, clean, clean.replace("-", ""), str(route_key).strip()]))
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in candidates)
            cur.execute(
                f"SELECT stop_id, departure_time, arrival_time, trip_id "
                f"FROM route_stop_times WHERE route_short_name IN ({placeholders})",
                candidates
            )
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return None
            table: dict[str, list] = {}
            for r in rows:
                dep = _parse_gtfs_time(r["departure_time"])
                arr = _parse_gtfs_time(r["arrival_time"])
                if dep:
                    table.setdefault(str(r["stop_id"]), []).append(
                        (dep, arr or dep, str(r["trip_id"]))
                    )
            for sid in table:
                table[sid].sort(key=lambda x: x[0])
            return table
        except Exception as e:
            print(f"GTFS Route query error for {route_key}: {e}")
            return None

    def __contains__(self, key):
        return self[key] is not None

    def get(self, key, default=None):
        val = self[key]
        return val if val is not None else default

    def __getitem__(self, key):
        if not key:
            return None
        k = str(key).strip().upper()
        if k in self._cache:
            return self._cache[k]
        res = self._query(key)
        self._cache[k] = res
        return res


_route_departures = RouteDeparturesDict()

BMTC_START = timedelta(hours=5)
BMTC_END   = timedelta(hours=23, minutes=30)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _parse_gtfs_time(t) -> Optional[timedelta]:
    """Parse a GTFS HH:MM:SS time string (may exceed 24h) into a timedelta."""
    if pd.isna(t) or not t:
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
# Singleton loader (called on demand, instant execution)
# ---------------------------------------------------------------------------

def _load_gtfs() -> None:
    global _gtfs_loaded, _gtfs_data, _norm_to_ids, _route_departures

    with _gtfs_lock:
        if _gtfs_loaded:
            return

        try:
            if not os.path.exists(_GTFS_DB):
                try:
                    import subprocess
                    script = os.path.join(_REPO_ROOT, "backend", "build_gtfs_db.py")
                    if os.path.exists(script):
                        print("GTFS: auto-generating database/gtfs_index.db...")
                        subprocess.run([sys.executable, script], check=True)
                except Exception as ex:
                    print(f"GTFS auto-build failed: {ex}")

            if os.path.exists(_GTFS_DB):
                conn = sqlite3.connect(_GTFS_DB, timeout=5)
                cur = conn.cursor()
                cur.execute("SELECT stop_norm, stop_id FROM stops")
                for norm, sid in cur.fetchall():
                    _norm_to_ids.setdefault(norm, []).append(str(sid))
                conn.close()
                print(f"GTFS: matched {len(_norm_to_ids)} stop norms from indexed SQLite.")
            else:
                from core.loader import stops_df
                gtfs_stops = pd.read_csv(GTFS_STOPS, dtype={"stop_id": str, "stop_name": str})
                gtfs_stops["clean_name"] = gtfs_stops["stop_name"].apply(
                    lambda name: name[3:].strip() if isinstance(name, str) and (name.upper().startswith("CS-") or name.upper().startswith("CS ")) else name
                )
                gtfs_stops["stop_norm"] = gtfs_stops["clean_name"].str.strip().str.lower()
                known_norms = set(stops_df["stop_norm"].unique())
                for _, row in gtfs_stops.iterrows():
                    n = row["stop_norm"]
                    if n in known_norms:
                        _norm_to_ids.setdefault(n, []).append(str(row["stop_id"]))
                print(f"GTFS: matched {len(_norm_to_ids)} stop norms from CSV.")

            # Load lightweight routes DataFrame if file exists
            if os.path.exists(GTFS_ROUTES):
                routes = pd.read_csv(GTFS_ROUTES, dtype={"route_id": str, "route_short_name": str})
                _gtfs_data["routes"] = routes

            _route_departures = RouteDeparturesDict(_GTFS_DB)
            print("GTFS: departure query engine initialized (<10MB RAM).")

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
    if not _gtfs_loaded:
        _load_gtfs()

    if not _gtfs_data or not _route_departures:
        return None

    base_route = route_no.replace("_REV", "").strip()
    clean_base = base_route.split()[0] if base_route else base_route
    route_table = (
        _route_departures.get(base_route) or
        _route_departures.get(clean_base) or
        _route_departures.get(clean_base.replace("-", "")) or
        _route_departures.get(route_no)
    )
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


def get_route_stops(route_no: str) -> list:
    """Return an ordered list of stop names along a given route number."""
    if not route_no:
        return []

    # 1. Try fast indexed SQLite query
    if os.path.exists(_GTFS_DB):
        try:
            raw = str(route_no).strip().upper().replace("_REV", "")
            clean = raw.split()[0] if raw else raw
            candidates = list(dict.fromkeys([raw, clean, clean.replace("-", ""), str(route_no).strip()]))
            conn = sqlite3.connect(_GTFS_DB, timeout=5)
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in candidates)
            cur.execute(
                f"SELECT clean_name FROM route_stop_times "
                f"WHERE route_short_name IN ({placeholders}) "
                f"GROUP BY clean_name ORDER BY min(stop_sequence)",
                candidates
            )
            rows = cur.fetchall()
            conn.close()
            if rows:
                return [r[0] for r in rows if r[0]]
        except Exception:
            pass

    # 2. Fast fallback to cleaned stop-level dataset
    try:
        from core.stops import get_route_stop_names
        stops = get_route_stop_names(route_no)
        if stops:
            return stops
    except Exception:
        pass

    return []

