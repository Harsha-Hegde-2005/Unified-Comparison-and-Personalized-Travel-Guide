"""
tools/route_finder.py
=====================
Find BMTC routes servicing a given stop with frequency and arrival times.

Usage:
    python -m tools.route_finder "Stop Name" [--top N]
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import pandas as pd

from core.config import GTFS_STOPS, GTFS_STOP_TIMES, GTFS_TRIPS, GTFS_ROUTES


def parse_time(t: str) -> timedelta | None:
    """Parse a GTFS time string (HH:MM:SS), allowing >24h values."""
    if pd.isna(t):
        return None
    parts = str(t).split(":")
    if len(parts) != 3:
        return None
    h, m, s = map(int, parts)
    return timedelta(hours=h, minutes=m, seconds=s)


def format_timedelta(td: timedelta) -> str:
    total = int(td.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def find_stop_ids(query: str, stops_df: pd.DataFrame) -> pd.DataFrame:
    mask = stops_df["stop_name"].astype(str).str.contains(query, case=False, na=False)
    return stops_df[mask][["stop_id", "stop_name"]].drop_duplicates()


def load_gtfs():
    stops      = pd.read_csv(GTFS_STOPS,      dtype={"stop_id": str, "stop_name": str})
    stop_times = pd.read_csv(GTFS_STOP_TIMES, dtype={"trip_id": str, "stop_id": str, "stop_sequence": int})
    trips      = pd.read_csv(GTFS_TRIPS,      dtype={"route_id": str, "trip_id": str, "route_short_name": str})
    routes     = pd.read_csv(GTFS_ROUTES,     dtype={"route_id": str, "route_short_name": str, "route_long_name": str})
    return stops, stop_times, trips, routes


def compute_route_stats(stop_ids, stop_times, trips, routes_df):
    st     = stop_times[stop_times["stop_id"].isin(stop_ids)]
    merged = st.merge(trips, on="trip_id", how="left").merge(routes_df, on="route_id", how="left")
    merged["route_label"] = merged["route_short_name"].fillna(merged["route_id"].astype(str))

    counts      = Counter(merged["route_label"])
    arrival_map = defaultdict(list)

    for _, row in merged.iterrows():
        t = parse_time(row.get("arrival_time"))
        if t is not None:
            arrival_map[row["route_label"]].append(t)

    for route in arrival_map:
        arrival_map[route].sort()

    return counts, arrival_map


def main():
    parser = argparse.ArgumentParser(description="Find BMTC routes serving a stop")
    parser.add_argument("stop",  help="Stop name (substring match)")
    parser.add_argument("--top", type=int, default=10, help="Top-N routes (default 10)")
    args = parser.parse_args()

    stops, stop_times, trips, routes = load_gtfs()
    matches = find_stop_ids(args.stop, stops)

    if matches.empty:
        print(f"No stops found matching '{args.stop}'.")
        return

    print(f"Found {len(matches)} matching stop(s):")
    for stop_id, stop_name in matches.values:
        print(f"  • {stop_id} — {stop_name}")

    stop_ids           = matches["stop_id"].unique().tolist()
    counts, arrival_map = compute_route_stats(stop_ids, stop_times, trips, routes)

    if not counts:
        print("No routes found stopping at this stop.")
        return

    print("\nAll routes serving this stop:")
    print("  " + ", ".join(sorted(counts.keys(), key=lambda r: (len(r), r))))

    now       = datetime.now()
    now_td    = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    top_routes = counts.most_common(args.top)

    print(f"\nTop {len(top_routes)} most frequent routes:")
    for route, freq in top_routes:
        future = [t for t in arrival_map.get(route, []) if t >= now_td][:3]
        next_str = ", ".join(format_timedelta(t) for t in future) if future else "(no more today)"
        print(f"  • {route}: {freq} trips/day  |  next: {next_str}")


if __name__ == "__main__":
    main()

