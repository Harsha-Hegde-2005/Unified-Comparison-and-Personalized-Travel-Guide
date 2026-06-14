"""
core/loader.py
==============
Loads and normalises the primary BMTC stop-level dataset and the
reverse-routes supplement.

All heavy I/O is wrapped in @st.cache_resource so it runs ONCE per
Streamlit server session — button clicks and reruns never reload data.

Public API (import these, never the cached functions directly):
    stops_df         — primary DataFrame
    _rev_df          — reverse-routes supplement DataFrame
    _canonical_name  — stop_norm → display name dict
    ALL_STOPS        — sorted list of all display names
    canonical_stop_name(stop_norm) → str
"""

from __future__ import annotations

import os as _os
import pandas as pd
import streamlit as st

from core.config import (
    STOP_LEVEL_CLEANED,
    STOP_LEVEL_ORIGINAL,
    REVERSE_SUPPLEMENT,
    GTFS_ROUTES,
)


# ── Helpers (pure, no I/O) ────────────────────────────────────────────────────

def _build_canonical_map(df: pd.DataFrame) -> dict[str, str]:
    return (
        df.groupby("stop_norm")["stop_name"]
        .agg(lambda s: s.value_counts().index[0])
        .to_dict()
    )


def _clean_against_gtfs(df: pd.DataFrame) -> pd.DataFrame:
    """Drop routes not present in GTFS (likely defunct). Save cleaned CSV."""
    try:
        gtfs_routes    = set(pd.read_csv(GTFS_ROUTES)["route_short_name"].dropna().astype(str).unique())
        dataset_routes = set(df["route_no"].astype(str).unique())
        valid_routes   = dataset_routes & gtfs_routes
        removed        = dataset_routes - gtfs_routes
        print(f"Cleaning: {len(dataset_routes)} → {len(valid_routes)} routes "
              f"({len(removed)} defunct removed)")
        df = df[df["route_no"].astype(str).isin(valid_routes)].copy()
        df.to_csv(STOP_LEVEL_CLEANED, index=False)
    except FileNotFoundError:
        print("GTFS routes.txt not found — skipping dataset cleaning")
    return df


# ── Cached loader — runs exactly once per server session ─────────────────────

@st.cache_resource(show_spinner="Loading BMTC dataset…")
def _load_all() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str], list[str]]:
    """
    Load stops_df, _rev_df, canonical name map, and ALL_STOPS.
    @st.cache_resource means this runs once; reruns and button clicks
    hit the cache and return instantly.
    """
    # 1. Primary dataset
    # Try cleaned first, then fall back to original, with a clear error if neither exists.
    if _os.path.exists(STOP_LEVEL_CLEANED):
        df = pd.read_csv(STOP_LEVEL_CLEANED)
        print("Loaded cleaned dataset:", STOP_LEVEL_CLEANED)
    elif _os.path.exists(STOP_LEVEL_ORIGINAL):
        df = pd.read_csv(STOP_LEVEL_ORIGINAL)
        print("Loaded original dataset — cleaning against GTFS…")
        df = _clean_against_gtfs(df)
    else:
        raise FileNotFoundError(
            f"Neither cleaned nor original dataset found.\n"
            f"Expected one of:\n"
            f"  {STOP_LEVEL_CLEANED}\n"
            f"  {STOP_LEVEL_ORIGINAL}\n"
            f"Please ensure the data/ folder from the original project is present."
        )

    df["stop_norm"] = df["stop_name"].str.strip().str.lower()

    # 2. Canonical name map
    canonical: dict[str, str] = _build_canonical_map(df)

    # 3. Reverse-routes supplement
    try:
        rev = pd.read_csv(REVERSE_SUPPLEMENT)
        rev["stop_norm"] = rev["stop_name"].str.strip().str.lower()
        for norm, name in zip(rev["stop_norm"], rev["stop_name"]):
            if norm not in canonical:
                canonical[norm] = name
        print(f"Reverse supplement: {rev['route_no'].nunique()} reverse routes")
    except FileNotFoundError:
        print("reverse_routes_supplement.csv not found — skipping")
        rev = pd.DataFrame(columns=["route_no", "stop_sequence", "stop_name",
                                     "latitude", "longitude", "stop_norm"])

    all_stops = sorted(canonical.values())
    return df, rev, canonical, all_stops


# ── Module-level names — cheap attribute lookups after first load ─────────────

stops_df, _rev_df, _canonical_name, ALL_STOPS = _load_all()


# ── Public helper ─────────────────────────────────────────────────────────────

def canonical_stop_name(stop_norm: str) -> str:
    """Return the canonical display name for a normalised stop key."""
    return _canonical_name.get(stop_norm, stop_norm.title())

