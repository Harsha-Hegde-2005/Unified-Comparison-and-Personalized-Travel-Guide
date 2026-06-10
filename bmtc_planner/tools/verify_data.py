"""
tools/verify_data.py
====================
Quick data-quality check — run after any dataset update.

Usage:
    python -m tools.verify_data
"""

import pandas as pd
from core.config import STOP_LEVEL_ORIGINAL, STOPS_CLEAN


def verify():
    print("DATASET VERIFICATION")
    print("=" * 70)

    df       = pd.read_csv(STOP_LEVEL_ORIGINAL)
    stops_df = pd.read_csv(STOPS_CLEAN)

    print(f"\n1. ROUTES DATA ({STOP_LEVEL_ORIGINAL})")
    print(f"   Total Records:   {len(df):,}")
    print(f"   Unique Routes:   {df['route_no'].nunique():,}")
    print(f"   Unique Stops:    {df['stop_name'].nunique():,}")

    print(f"\n2. STOPS DATA ({STOPS_CLEAN})")
    print(f"   Total Stops:     {len(stops_df):,}")

    print(f"\n3. DATA QUALITY")
    missing_coords = df[["latitude", "longitude"]].isna().any(axis=1).sum()
    print(f"   Missing coordinates:                 {missing_coords}")
    invalid_coords = (
        (df["latitude"] < 12.7) | (df["latitude"] > 13.5) |
        (df["longitude"] < 77.2) | (df["longitude"] > 77.9)
    ).sum()
    print(f"   Invalid coords (outside Bangalore):  {invalid_coords}")
    dup_pairs = len(df) - len(df.drop_duplicates(subset=["route_no", "stop_name"]))
    print(f"   Duplicate route-stop pairs:          {dup_pairs}")

    print(f"\n4. SAMPLE DATA (first 5 rows)")
    print(df.head(5).to_string())

    print(f"\n5. ROUTE TYPE DISTRIBUTION")
    routes = sorted(df["route_no"].unique())
    print(f"   Total: {len(routes)}")
    print(f"   Regular (digits only):  {len([r for r in routes if str(r).isdigit()])}")
    print(f"   Express (contains X):   {len([r for r in routes if 'X' in str(r)])}")
    print(f"   Metro Feeder (MF/FM):   {len([r for r in routes if any(p in str(r) for p in ['MF','FM'])])}")


if __name__ == "__main__":
    verify()

