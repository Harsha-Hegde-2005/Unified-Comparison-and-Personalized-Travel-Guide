"""
poi_data.py
===========
Loads the curated Bengaluru points-of-interest dataset (colleges, hospitals,
tech parks, malls, tourist attractions, hotels, railway stations, airport,
landmarks) from database/poi/pois.json.

This gives the chatbot city-wide location coverage beyond the raw BMTC stop /
Metro station lists -- extract_stops() in chatbot_engine.py treats POI names
exactly like any other stop name (substring + alias + fuzzy matching), and
main.py uses the lat/lng here to find the nearest *routable* BMTC stop or
Metro station via the existing haversine helper, so all fares/times are still
computed by the real routing engines -- POIs only supply a name + coordinate,
never a fare or duration.
"""

import json
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
