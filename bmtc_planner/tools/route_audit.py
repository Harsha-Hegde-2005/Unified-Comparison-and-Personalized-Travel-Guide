"""
tools/route_audit.py
====================
CLI tool — audit current routes in the dataset and compare against
GTFS to identify defunct or missing routes.

Usage:
    python -m tools.route_audit
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.config import STOP_LEVEL_ORIGINAL, STOPS_CLEAN, GTFS_ROUTES


def audit_routes() -> set[str]:
    """Print a full audit report and return the set of current route numbers."""
    stops_df       = pd.read_csv(STOP_LEVEL_ORIGINAL)
    routes_current = set(stops_df["route_no"].unique())
    stops_in_data  = set(stops_df["stop_name"].unique())

    print("\n" + "=" * 70)
    print("BMTC ROUTE AUDIT REPORT")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n[DATASET STATISTICS]:")
    print(f"  Total Unique Routes:    {len(routes_current)}")
    print(f"  Total Route-Stop Rows:  {len(stops_df):,}")
    print(f"  Total Unique Stops:     {len(stops_in_data)}")
    print(f"  Avg Stops per Route:    {len(stops_df) / len(routes_current):.1f}")

    route_types = {
        "Express (EX)":      len([r for r in routes_current if str(r).startswith("EX")]),
        "Metro Feeder (MF)": len([r for r in routes_current if str(r).startswith("MF")]),
        "BIG 10 (G)":        len([r for r in routes_current if str(r).startswith("G")]),
        "BIG Circle (C/K)":  len([r for r in routes_current if str(r).startswith(("C", "K"))]),
        "Regular":           len([r for r in routes_current
                                  if not any(str(r).startswith(p) for p in ["EX", "MF", "G", "C", "K"])]),
    }
    print("\n[ROUTE TYPES]:")
    for rtype, count in sorted(route_types.items(), key=lambda x: -x[1]):
        print(f"  {rtype}: {count}")

    # Cross-check against GTFS
    try:
        gtfs_routes = set(pd.read_csv(GTFS_ROUTES)["route_short_name"].dropna().astype(str).unique())
        in_gtfs     = routes_current & gtfs_routes
        not_in_gtfs = routes_current - gtfs_routes
        print(f"\n[GTFS CROSS-CHECK]:")
        print(f"  Routes also in GTFS:    {len(in_gtfs)}")
        print(f"  Routes NOT in GTFS:     {len(not_in_gtfs)}  ← likely defunct")
    except FileNotFoundError:
        print("\n  GTFS routes.txt not found — skipping cross-check")

    routes_list = sorted(list(routes_current))
    out_path    = "current_routes_list.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"BMTC Routes in Current Dataset\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Routes: {len(routes_list)}\n\n")
        for i, r in enumerate(routes_list, 1):
            f.write(f"{i:4d}. {r}\n")
    print(f"\n  Saved route list → {out_path}")

    return routes_current


def compare_routes(old_routes: set, new_routes: set) -> tuple[set, set, set]:
    """Print a diff between two route sets."""
    removed  = old_routes - new_routes
    added    = new_routes - old_routes
    existing = old_routes & new_routes

    print("\n" + "=" * 70)
    print("ROUTE COMPARISON")
    print("=" * 70)
    print(f"  Existing:  {len(old_routes)}")
    print(f"  New:       {len(new_routes)}")
    print(f"  Removed:   {len(removed)}")
    print(f"  Added:     {len(added)}")
    print(f"  Unchanged: {len(existing)}")

    if removed:
        print(f"\n  REMOVED ({len(removed)}):")
        for r in sorted(removed)[:30]:
            print(f"    - {r}")
        if len(removed) > 30:
            print(f"    … and {len(removed) - 30} more")

    if added:
        print(f"\n  ADDED ({len(added)}):")
        for r in sorted(added)[:30]:
            print(f"    + {r}")
        if len(added) > 30:
            print(f"    … and {len(added) - 30} more")

    return removed, added, existing


if __name__ == "__main__":
    audit_routes()

