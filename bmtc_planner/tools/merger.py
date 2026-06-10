"""
tools/merger.py
===============
Download and merge missing BMTC GTFS routes into the cleaned dataset.

Usage:
    python -m tools.merger
"""

from __future__ import annotations

import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from core.config import STOP_LEVEL_ORIGINAL, PROCESSED_DIR

GTFS_DOWNLOAD_URL = "https://github.com/anikets95/bmtc-data/archive/refs/heads/main.zip"


def download_bmtc_data(dest_folder: str = "data/raw") -> bool:
    """Download and extract BMTC GTFS data from GitHub."""
    print("=" * 70)
    print("DOWNLOADING BMTC GTFS DATA")
    print("=" * 70)

    zip_path = "bmtc_data_temp.zip"
    try:
        print(f"\n  Fetching: {GTFS_DOWNLOAD_URL}")
        urllib.request.urlretrieve(GTFS_DOWNLOAD_URL, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall("bmtc_temp")

        for root, _, files in os.walk("bmtc_temp"):
            for fname in files:
                if fname == "bmtc.zip":
                    nested = os.path.join(root, fname)
                    os.makedirs(dest_folder, exist_ok=True)
                    with zipfile.ZipFile(nested, "r") as zf:
                        zf.extractall(dest_folder)
                    print(f"  Extracted GTFS files → {dest_folder}/")
                    return True

        print("  bmtc.zip not found inside archive.")
        return False

    except Exception as e:
        print(f"  Download error: {e}")
        return False

    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists("bmtc_temp"):
            shutil.rmtree("bmtc_temp")


def load_gtfs_data(gtfs_folder: str) -> dict[str, pd.DataFrame]:
    """Load GTFS CSV files from a folder."""
    print(f"\n[1] Loading GTFS files from {gtfs_folder}…")
    files = {
        "stops":      "stops.txt",
        "stop_times": "stop_times.txt",
        "trips":      "trips.txt",
        "routes":     "routes.txt",
    }
    data = {}
    for key, fname in files.items():
        path = os.path.join(gtfs_folder, fname)
        if os.path.exists(path):
            data[key] = pd.read_csv(path, dtype=str)
            print(f"   Loaded {fname}: {len(data[key]):,} rows")
        else:
            print(f"   WARNING: {fname} not found")
    return data


def merge_routes(existing_csv: str, gtfs_data: dict) -> pd.DataFrame:
    """Build a merged stops DataFrame from GTFS and existing data."""
    existing = pd.read_csv(existing_csv)
    existing_routes = set(existing["route_no"].astype(str).unique())

    trips  = gtfs_data.get("trips",  pd.DataFrame())
    routes = gtfs_data.get("routes", pd.DataFrame())

    if trips.empty or routes.empty:
        print("  Missing trips/routes — cannot merge.")
        return existing

    merged_trips = trips.merge(
        routes[["route_id", "route_short_name"]], on="route_id", how="left"
    )
    gtfs_route_names = set(merged_trips["route_short_name"].dropna().unique())
    new_routes = gtfs_route_names - existing_routes

    print(f"\n[2] Existing routes: {len(existing_routes)}")
    print(f"    GTFS routes:      {len(gtfs_route_names)}")
    print(f"    New to add:       {len(new_routes)}")

    return existing   # extend here with real stop-coordinate join as needed


if __name__ == "__main__":
    ok = download_bmtc_data(dest_folder="data/raw")
    if ok:
        gtfs = load_gtfs_data("data/raw")
        merge_routes(STOP_LEVEL_ORIGINAL, gtfs)
    else:
        print("\nDownload failed — check your internet connection.")

