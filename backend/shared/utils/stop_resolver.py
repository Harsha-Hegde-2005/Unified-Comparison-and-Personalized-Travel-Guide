"""Stop and station name resolver utility."""

from typing import List, Optional

# Prefix cleaning helper (strips CS- / CS prefixes)
def clean_input_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    name = name.strip()
    name_upper = name.upper()
    for prefix in ["CS-", "CS "]:
        if name_upper.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    return name

# Mapping of synonyms/variations to canonical keys
# Key is a standard lowercase slug. Value is a dict with canonical names for each mode.
HUB_MAPPINGS = {
    "majestic": {
        "metro": "Majestic",
        "bmtc": "Kempegowda Bus Station",
    },
    "kempegowda": {
        "metro": "Majestic",
        "bmtc": "Kempegowda Bus Station",
    },
    "kbs": {
        "metro": "Majestic",
        "bmtc": "Kempegowda Bus Station",
    },
    "nadaprabhu": {
        "metro": "Majestic",
        "bmtc": "Kempegowda Bus Station",
    },
    "city railway": {
        "metro": "City Railway Station",
        "bmtc": "City Railway Station",
    },
    "yeshwanthpur": {
        "metro": "Yeshwanthpur",
        "bmtc": "Yeshawanthapura Bus Station",
    },
    "yeshawanthapura": {
        "metro": "Yeshwanthpur",
        "bmtc": "Yeshawanthapura Bus Station",
    },
    "hosa road": {
        "metro": "Hosa Road",
        "bmtc": "Hosa Road",
    },
    "silk board": {
        "metro": "Central Silk Board",
        "bmtc": "Central Silk Board",
    },
    "central silk board": {
        "metro": "Central Silk Board",
        "bmtc": "Central Silk Board",
    },
    "kr puram": {
        "metro": "Krishnarajapura",
        "bmtc": "KR Puram",
    },
    "krishnarajapura": {
        "metro": "Krishnarajapura",
        "bmtc": "KR Puram",
    },
    "indiranagar": {
        "metro": "Indiranagar",
        "bmtc": "Indiranagara",
    },
    "indiranagara": {
        "metro": "Indiranagar",
        "bmtc": "Indiranagara",
    },
    "banashankari": {
        "metro": "Banashankari",
        "bmtc": "Banashankari",
    },
    "konanakunte": {
        "metro": "Konanakunte Cross",
        "bmtc": "Konanakunte Cross",
    },
    "konanakunte cross": {
        "metro": "Konanakunte Cross",
        "bmtc": "Konanakunte Cross",
    },
}

def resolve_stop_name(
    name: str,
    mode: str,
    bmtc_stops: Optional[List[str]] = None,
    metro_stations: Optional[List[str]] = None,
) -> str:
    """Resolve a user input stop or station name to its canonical representation for the mode."""
    cleaned = clean_input_name(name)
    if not cleaned:
        return ""
    
    cleaned_lower = cleaned.lower()
    
    # 1. Check direct hub substring matches (most specific/longest first)
    for key in sorted(HUB_MAPPINGS.keys(), key=len, reverse=True):
        if key in cleaned_lower:
            resolved = HUB_MAPPINGS[key].get(mode.lower())
            if resolved:
                return resolved

    # 2. Case-insensitive exact matching against lists
    if mode.lower() == "metro" and metro_stations:
        for ms in metro_stations:
            if ms.lower() == cleaned_lower:
                return ms
    elif mode.lower() == "bmtc" and bmtc_stops:
        for bs in bmtc_stops:
            if bs.lower() == cleaned_lower:
                return bs

    # 3. Fallback to cleaned title case or original name
    return cleaned
