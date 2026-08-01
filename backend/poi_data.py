"""
poi_data.py
===========
Loads the curated Bengaluru points-of-interest dataset (colleges, hospitals,
tech parks, malls, tourist attractions, hotels, railway stations, airport,
landmarks, and restaurants) from database/poi/pois.json.

This gives the chatbot city-wide location coverage beyond the raw BMTC stop /
Metro station lists -- extract_stops() in chatbot_engine.py treats POI names
exactly like any other stop name (substring + alias + fuzzy matching), and
main.py uses the lat/lng here to find the nearest *routable* BMTC stop or
Metro station via the existing haversine helper, so all fares/times are still
computed by the real routing engines -- POIs only supply a name + coordinate,
never a fare or duration.
"""

import json
import math
import os
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_POI_PATH = os.path.join(_HERE, "..", "database", "poi", "pois.json")

_pois: List[Dict[str, Any]] = []
_by_name_lower: Dict[str, Dict[str, Any]] = {}
_alias_to_name: Dict[str, str] = {}


def _load() -> None:
    global _pois, _by_name_lower, _alias_to_name
    try:
        with open(_POI_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _pois = raw.get("pois", [])
    except Exception as e:
        print(f"POI dataset not loaded ({e}) -- city-wide POI recognition will be unavailable")
        _pois = []

    _by_name_lower = {p["name"].lower(): p for p in _pois}
    _alias_to_name = {}
    for p in _pois:
        for alias in p.get("aliases", []):
            _alias_to_name[alias.lower()] = p["name"]


_load()


def all_poi_names() -> List[str]:
    """Every canonical POI name, for the chatbot's location-extraction list."""
    return [p["name"] for p in _pois]


def all_poi_aliases() -> Dict[str, str]:
    """alias (lowercase) -> canonical POI name, for normalize_query_text()."""
    return dict(_alias_to_name)


def get_poi(name: str) -> Optional[Dict[str, Any]]:
    """Look up a POI by canonical name or known alias (case-insensitive)."""
    key = name.lower().strip()
    if key in _by_name_lower:
        return _by_name_lower[key]
    if key in _alias_to_name:
        return _by_name_lower.get(_alias_to_name[key].lower())
    return None


def get_pois_by_category(category: str) -> List[Dict[str, Any]]:
    return [p for p in _pois if p.get("category") == category]


def get_attractions() -> List[Dict[str, Any]]:
    return get_pois_by_category("attraction")


def get_restaurants() -> List[Dict[str, Any]]:
    """All restaurant-category POIs."""
    return get_pois_by_category("restaurant")


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in km between two lat/lng points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_restaurants_near(lat: float, lng: float, radius_km: float = 2.0, max_results: int = 4) -> List[Dict[str, Any]]:
    """Return up to `max_results` restaurants within `radius_km` of the given coordinates,
    sorted by distance ascending. Each result includes a 'distance_km' field."""
    results = []
    for r in get_restaurants():
        d = _haversine_km(lat, lng, r["lat"], r["lng"])
        if d <= radius_km:
            entry = dict(r)
            entry["distance_km"] = round(d, 2)
            results.append(entry)
    results.sort(key=lambda x: x["distance_km"])
    return results[:max_results]


def get_nearby_pois(lat: float, lng: float, radius_km: float = 2.0, categories: Optional[List[str]] = None, max_results: int = 5) -> List[Dict[str, Any]]:
    """Return POIs within `radius_km`, optionally filtered by category list."""
    results = []
    for p in _pois:
        if categories and p.get("category") not in categories:
            continue
        d = _haversine_km(lat, lng, p["lat"], p["lng"])
        if d <= radius_km:
            entry = dict(p)
            entry["distance_km"] = round(d, 2)
            results.append(entry)
    results.sort(key=lambda x: x["distance_km"])
    return results[:max_results]

