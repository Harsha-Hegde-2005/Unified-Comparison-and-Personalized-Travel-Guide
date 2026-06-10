"""
tools/validator.py
==================
Validate data quality for individual routes and audit the full dataset.

Usage:
    python -m tools.validator [--route ROUTE_NO]
"""

from __future__ import annotations

import argparse

import pandas as pd

from core.config import STOP_LEVEL_ORIGINAL, STOPS_CLEAN, GTFS_ROUTES


def audit_routes() -> set[str]:
    stops_df       = pd.read_csv(STOP_LEVEL_ORIGINAL)
    stops_clean_df = pd.read_csv(STOPS_CLEAN)
    routes_current = set(stops_df["route_no"].unique())

    print("\n" + "=" * 70)
    print("BMTC ROUTE VALIDATOR")
    print("=" * 70)
    print(f"\n  Route-stop records: {len(stops_df):,}")
    print(f"  Unique routes:      {len(routes_current)}")
    print(f"  Unique stops:       {stops_df['stop_name'].nunique()}")
    print(f"  Reference stops:    {len(stops_clean_df)}")

    route_types = {
        "Express":      len([r for r in routes_current if str(r).startswith("EX")]),
        "Metro Feeder": len([r for r in routes_current if str(r).startswith("MF")]),
        "BIG 10":       len([r for r in routes_current if str(r).startswith("G")]),
        "BIG Circle":   len([r for r in routes_current if str(r).startswith(("C", "K"))]),
        "Regular":      len([r for r in routes_current
                             if not any(str(r).startswith(p) for p in ["EX", "MF", "G", "C", "K"])]),
    }
    print("\n  Route types:")
    for k, v in sorted(route_types.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    return routes_current


def validate_route(route_no: str) -> dict:
    """Return a quality report for a single route."""
    stops_df  = pd.read_csv(STOP_LEVEL_ORIGINAL)
    route_data = stops_df[stops_df["route_no"] == route_no]

    if route_data.empty:
        return {"error": f"Route {route_no} not found"}

    stops            = len(route_data)
    coords_missing   = route_data[["latitude", "longitude"]].isnull().sum().sum()
    invalid_lat      = ((route_data["latitude"] < 12.7) | (route_data["latitude"] > 13.5)).sum()
    invalid_lon      = ((route_data["longitude"] < 77.2) | (route_data["longitude"] > 77.9)).sum()

    return {
        "route":               route_no,
        "total_stops":         stops,
        "missing_coordinates": int(coords_missing),
        "invalid_lat":         int(invalid_lat),
        "invalid_lon":         int(invalid_lon),
        "data_quality":        "Good" if coords_missing == 0 and invalid_lat == 0 else "Issues",
    }


def compare_routes(old_routes: set, new_routes: set) -> tuple[set, set, set]:
    removed  = old_routes - new_routes
    added    = new_routes - old_routes
    existing = old_routes & new_routes
    print(f"\n  Removed: {len(removed)}, Added: {len(added)}, Unchanged: {len(existing)}")
    return removed, added, existing


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate BMTC route data")
    parser.add_argument("--route", help="Validate a specific route number")
    args = parser.parse_args()

    if args.route:
        report = validate_route(args.route)
        for k, v in report.items():
            print(f"  {k}: {v}")
    else:
        audit_routes()

