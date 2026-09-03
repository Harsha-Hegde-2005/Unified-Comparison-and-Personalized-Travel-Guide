"""
tests/conftest.py
=================
Shared pytest fixtures — lightweight in-memory data so tests
never need the real 24MB GTFS files or the cleaned CSVs.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_BACKEND = os.path.join(_ROOT, "backend")

# Setup sys.path for testing imports
for p in [
    _BACKEND,
    os.path.join(_BACKEND, "modes", "bmtc"),
    os.path.join(_BACKEND, "modes", "metro"),
    os.path.join(_BACKEND, "modes", "cab"),
    os.path.join(_BACKEND, "modes", "personal_vehicle"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd
import pytest


@pytest.fixture
def sample_stops_df():
    """Minimal stops DataFrame covering two routes and six stops."""
    return pd.DataFrame([
        {"route_no": "500C", "stop_sequence": 1, "stop_name": "Majestic",          "latitude": 12.977, "longitude": 77.572, "stop_norm": "majestic"},
        {"route_no": "500C", "stop_sequence": 2, "stop_name": "Shivajinagar",      "latitude": 12.984, "longitude": 77.600, "stop_norm": "shivajinagar"},
        {"route_no": "500C", "stop_sequence": 3, "stop_name": "Indiranagar",       "latitude": 12.978, "longitude": 77.638, "stop_norm": "indiranagar"},
        {"route_no": "356D", "stop_sequence": 1, "stop_name": "Shivajinagar",      "latitude": 12.984, "longitude": 77.600, "stop_norm": "shivajinagar"},
        {"route_no": "356D", "stop_sequence": 2, "stop_name": "Marathahalli",      "latitude": 12.956, "longitude": 77.701, "stop_norm": "marathahalli"},
        {"route_no": "356D", "stop_sequence": 3, "stop_name": "Whitefield",        "latitude": 12.970, "longitude": 77.750, "stop_norm": "whitefield"},
    ])


@pytest.fixture
def sample_rev_df():
    """Minimal reverse-routes DataFrame."""
    return pd.DataFrame(columns=[
        "route_no", "stop_sequence", "stop_name", "latitude", "longitude", "stop_norm"
    ])


@pytest.fixture
def sample_route_trips():
    """Mocked trip-frequency dict."""
    return {"500C": 85, "356D": 40}

