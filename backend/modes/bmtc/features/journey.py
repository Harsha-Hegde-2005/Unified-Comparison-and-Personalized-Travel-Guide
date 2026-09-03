"""
features/journey.py
===================
Public journey-planning API consumed by the Streamlit UI.

plan_journey_ui()                  — best single route
plan_journey_with_time_preference()— up to N options ranked by preferred arrival
get_route_arrival_time()           — convenience ETA wrapper
"""

from __future__ import annotations

from datetime import datetime, timedelta

from core.config import WAITING_TIME, TRANSFER_TIME, MAX_OPTIONS, FAST_QUERY_MODE
from core.loader import stops_df
from features.schedule import (
    calculate_segment_times,
    format_time,
    normalize_search_start_time,
    time_difference_minutes,
)
from features.routing import generate_guide


def _validate_stop(raw: str, label: str) -> str:
    norm = raw.strip().lower()
    if norm not in stops_df.stop_norm.values:
        raise ValueError(f"{label} stop '{raw}' not found in dataset.")
    return norm


def plan_journey_ui(src_raw: str, dst_raw: str) -> dict:
    """Return the single best route between src and dst."""
    src = _validate_stop(src_raw, "Source")
    dst = _validate_stop(dst_raw, "Destination")

    from core.graph import dijkstra, extract_segments

    result = dijkstra(src, dst)
    if not result:
        raise RuntimeError("No route found between these stops.")

    path, (transfers, distance) = result
    segments = extract_segments(path)
    now = datetime.now()
    search_start = normalize_search_start_time(now)
    segment_times = calculate_segment_times(segments, start_time=search_start)
    total_fare    = sum(st["fare"] for st in segment_times)
    total_time    = (sum(st["duration"] for st in segment_times)
                     + WAITING_TIME + transfers * TRANSFER_TIME)
    final_eta = search_start + timedelta(minutes=total_time)

    return {
        "segments":       segments,
        "segment_times":  segment_times,
        "distance":       distance,
        "transfers":      transfers,
        "fare":           total_fare,
        "segment_fares":  [st["fare"] for st in segment_times],
        "guide":          generate_guide(segments),
        "possible_buses": sorted({seg[0] for seg in segments}),
        "total_time":     int(total_time),
        "current_time":   format_time(search_start),
        "eta":            format_time(final_eta),
    }


def plan_journey_with_time_preference(
    src_raw: str,
    dst_raw: str,
    preferred_arrival_time: datetime | None = None,
    max_options: int = MAX_OPTIONS,
) -> list[dict]:
    """
    Return up to max_options route alternatives.
    The option whose ETA is closest to preferred_arrival_time is flagged.
    """
    src = _validate_stop(src_raw, "Source")
    dst = _validate_stop(dst_raw, "Destination")

    if FAST_QUERY_MODE:
        from core.graph import dijkstra, extract_segments

        best = dijkstra(src, dst)
        all_options = [best] if best else []
    else:
        from core.graph import dijkstra_all_options, extract_segments

        all_options = dijkstra_all_options(src, dst, max_options=max_options)
    if not all_options:
        raise RuntimeError("No route found between these stops.")

    now    = datetime.now()
    search_start = normalize_search_start_time(now)
    routes = []

    for path, (transfers, distance) in all_options:
        segments      = extract_segments(path)
        segment_times = calculate_segment_times(segments, start_time=search_start)
        total_fare    = sum(st["fare"] for st in segment_times)
        total_time    = (sum(st["duration"] for st in segment_times)
                         + WAITING_TIME + transfers * TRANSFER_TIME)
        final_eta     = search_start + timedelta(minutes=total_time)
        time_diff     = (
            time_difference_minutes(final_eta, preferred_arrival_time)
            if preferred_arrival_time else None
        )

        routes.append({
            "segments":                   segments,
            "segment_times":              segment_times,
            "distance":                   distance,
            "transfers":                  transfers,
            "fare":                       total_fare,
            "segment_fares":              [st["fare"] for st in segment_times],
            "possible_buses":             sorted({seg[0] for seg in segments}),
            "total_time":                 int(total_time),
            "departure_time":             format_time(search_start),
            "arrival_time":               format_time(final_eta),
            "time_diff_from_preference":  time_diff,
            "is_closest_to_preference":   False,
        })

    if preferred_arrival_time and routes:
        best = min(range(len(routes)),
                   key=lambda i: routes[i]["time_diff_from_preference"] or float("inf"))
        routes[best]["is_closest_to_preference"] = True

    return routes


def get_route_arrival_time(
    segments: list[tuple],
    start_time: datetime | None = None,
) -> datetime:
    """Convenience wrapper — returns final ETA for a list of segments."""
    seg_times = calculate_segment_times(segments, start_time)
    t = start_time or datetime.now()
    for st in seg_times:
        t += timedelta(minutes=st["duration"])
    return t
