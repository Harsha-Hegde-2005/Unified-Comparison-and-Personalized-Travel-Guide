"""Stop and station name resolver utility."""

import difflib
import re
from typing import List, Optional

def clean_input_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    # Remove parenthetical coordinates e.g. "Hebbal (12.8712, 77.6562)" -> "Hebbal"
    name = re.sub(r"\s*\(\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*\s*\)", "", name)
    name = name.strip()
    name_upper = name.upper()
    for prefix in ["CS-", "CS "]:
        if name_upper.startswith(prefix):
            name = name[len(prefix):].strip()
            name_upper = name.upper()
            break
            
    # Preserve City Railway Station
    if name_upper in ("CITY RAILWAY STATION", "CITY RAILWAY"):
        return "City Railway Station"

    # Strip common metro/station suffixes
    for suffix in [
        " METRO STATION",
        " METRO",
        " RAILWAY STATION",
    ]:
        if name_upper.endswith(suffix):
            name = name[:-len(suffix)].strip()
            name_upper = name.upper()
            break

    # Strip trailing " STATION" only if not City Railway Station
    if name_upper.endswith(" STATION") and not name_upper.startswith("CITY RAILWAY"):
        name = name[:-len(" STATION")].strip()

    return name


# Comprehensive Namma Metro canonical aliases (covering all 83 stations & popular names)
METRO_ALIASES = {
    # Purple Line
    "city": "City Railway Station",
    "whitefield": "Whitefield",
    "whitefield kadugodi": "Whitefield",
    "whitefield metro": "Whitefield",
    "kadugodi": "Kadugodi Tree Park",
    "kadugodi metro": "Kadugodi Tree Park",
    "tree park": "Kadugodi Tree Park",
    "kadugodi tree park": "Kadugodi Tree Park",
    "hopefarm": "Hopefarm Channasandra",
    "hope farm": "Hopefarm Channasandra",
    "channasandra": "Hopefarm Channasandra",
    "hopefarm channasandra": "Hopefarm Channasandra",
    "pattandur agrahara": "Pattandur Agrahara",
    "itpl": "Pattandur Agrahara",
    "itpl metro": "Pattandur Agrahara",
    "sri sathya sai hospital": "Sri Sathya Sai Hospital",
    "sathya sai hospital": "Sri Sathya Sai Hospital",
    "satya sai hospital": "Sri Sathya Sai Hospital",
    "satya sai": "Sri Sathya Sai Hospital",
    "sathya sai": "Sri Sathya Sai Hospital",
    "sai hospital": "Sri Sathya Sai Hospital",
    "nallurhalli": "Nallurhalli",
    "nallurahalli": "Nallurhalli",
    "kundalahalli": "Kundalahalli",
    "kundanahalli": "Kundalahalli",
    "seetharampalya": "Seetharampalya",
    "seetharam palya": "Seetharampalya",
    "hoodi": "Hoodi",
    "hoodi halt": "Hoodi",
    "garudacharapalya": "Garudacharapalya",
    "garudacharpalya": "Garudacharapalya",
    "singayyanapalya": "Singayyanapalya",
    "mahadevapura": "Singayyanapalya",
    "krishnarajapura": "Krishnarajapura",
    "kr puram": "Krishnarajapura",
    "k.r. puram": "Krishnarajapura",
    "krishnarajapuram": "Krishnarajapura",
    "benniganahalli": "Benniganahalli",
    "tin factory": "Benniganahalli",
    "tin factory metro": "Benniganahalli",
    "baiyappanahalli": "Baiyappanahalli",
    "byappanahalli": "Baiyappanahalli",
    "bayappanahalli": "Baiyappanahalli",
    "swami vivekananda road": "Swami Vivekananda Road",
    "sv road": "Swami Vivekananda Road",
    "s.v. road": "Swami Vivekananda Road",
    "indiranagar": "Indiranagar",
    "indiranagara": "Indiranagar",
    "cmh road": "Indiranagar",
    "halasuru": "Halasuru",
    "ulsoor": "Halasuru",
    "ulsoor metro": "Halasuru",
    "trinity": "Trinity",
    "trinity circle": "Trinity",
    "mg road": "MG Road",
    "m.g. road": "MG Road",
    "mahatma gandhi road": "MG Road",
    "cubbon park": "Cubbon Park",
    "vidhana soudha": "Vidhana Soudha",
    "central college": "Central College",
    "sir m visvesvaraya": "Central College",
    "sir m. visvesvaraya": "Central College",
    "visvesvaraya": "Central College",
    "visveswaraya": "Central College",
    "uvce": "Central College",
    "majestic": "Majestic",
    "kempegowda": "Majestic",
    "kbs": "Majestic",
    "nadaprabhu": "Majestic",
    "city railway station": "City Railway Station",
    "city railway": "City Railway Station",
    "ksr": "City Railway Station",
    "ksr bengaluru": "City Railway Station",
    "krantivira sangolli rayanna": "City Railway Station",
    "bangalore city": "City Railway Station",
    "bangalore city railway station": "City Railway Station",
    "sbc": "City Railway Station",
    "magadi road": "Magadi Road",
    "hosahalli": "Hosahalli",
    "vijayanagara": "Vijayanagara",
    "vijayanagar": "Vijayanagara",
    "attiguppe": "Attiguppe",
    "deepanjali nagar": "Deepanjali Nagar",
    "deepanjalinagar": "Deepanjali Nagar",
    "mysuru road": "Mysuru Road",
    "mysore road": "Mysuru Road",
    "nayandahalli": "Nayandahalli",
    "rajarajeshwari nagar": "Rajarajeshwari Nagar",
    "rr nagar": "Rajarajeshwari Nagar",
    "r.r. nagar": "Rajarajeshwari Nagar",
    "jnanabharathi": "Jnanabharathi",
    "jnana bharathi": "Jnanabharathi",
    "bangalore university": "Jnanabharathi",
    "pattanagere": "Pattanagere",
    "rvce": "Pattanagere",
    "kengeri bus terminal": "Kengeri Bus Terminal",
    "kengeri ttmc": "Kengeri Bus Terminal",
    "kengeri bus stand": "Kengeri Bus Terminal",
    "kengeri": "Kengeri",
    "challaghatta": "Challaghatta",

    # Green Line
    "madavara": "Madavara",
    "biec": "Madavara",
    "bangalore exhibition centre": "Madavara",
    "chikkabidarakallu": "Chikkabidarakallu",
    "jindal": "Chikkabidarakallu",
    "manjunatha nagara": "Manjunatha Nagara",
    "manjunatha nagar": "Manjunatha Nagara",
    "nagasandra": "Nagasandra",
    "dasarahalli": "Dasarahalli",
    "jalahalli": "Jalahalli",
    "jalahalli cross": "Jalahalli",
    "peenya industry": "Peenya Industry",
    "peenya 1st stage": "Peenya Industry",
    "peenya industrial area": "Peenya Industry",
    "peenya": "Peenya",
    "goraguntepalya": "Goraguntepalya",
    "goragunte palya": "Goraguntepalya",
    "yeshwanthpur": "Yeshwanthpur",
    "yeshwantpur": "Yeshwanthpur",
    "yeshawanthapura": "Yeshwanthpur",
    "yesvantpur": "Yeshwanthpur",
    "sandal soap factory": "Sandal Soap Factory",
    "sandal soap": "Sandal Soap Factory",
    "mahalakshmi": "Mahalakshmi",
    "mahalakshmi layout": "Mahalakshmi",
    "rajajinagar": "Rajajinagar",
    "kuvempu road": "Kuvempu Road",
    "srirampura": "Srirampura",
    "srirampuram": "Srirampura",
    "sampige road": "Sampige Road",
    "mantri square": "Sampige Road",
    "mantri square sampige road": "Sampige Road",
    "mantri mall": "Sampige Road",
    "malleswaram metro": "Sampige Road",
    "swastik": "Sampige Road",
    "chickpete": "Chickpete",
    "chickpet": "Chickpete",
    "chikpet": "Chickpete",
    "chikpete": "Chickpete",
    "krishna rajendra market": "Krishna Rajendra Market",
    "kr market": "Krishna Rajendra Market",
    "k.r. market": "Krishna Rajendra Market",
    "city market": "Krishna Rajendra Market",
    "market metro": "Krishna Rajendra Market",
    "national college": "National College",
    "basavanagudi": "National College",
    "lalbagh botanical garden": "Lalbagh Botanical Garden",
    "lalbagh": "Lalbagh Botanical Garden",
    "lal bagh": "Lalbagh Botanical Garden",
    "south end circle": "South End Circle",
    "south end": "South End Circle",
    "jayanagara": "Jayanagara",
    "jayanagar": "Jayanagara",
    "4th block jayanagar": "Jayanagara",
    "rashtriya vidyalaya road": "Rashtriya Vidyalaya Road",
    "rv road": "Rashtriya Vidyalaya Road",
    "r.v. road": "Rashtriya Vidyalaya Road",
    "banashankari": "Banashankari",
    "bsk": "Banashankari",
    "jaya prakash nagara": "Jaya Prakash Nagara",
    "jp nagar": "Jaya Prakash Nagara",
    "j.p. nagar": "Jaya Prakash Nagara",
    "jayaprakash nagar": "Jaya Prakash Nagara",
    "jayaprakash nagara": "Jaya Prakash Nagara",
    "yelachenahalli": "Yelachenahalli",
    "puttenahalli": "Yelachenahalli",
    "konanakunte cross": "Konanakunte Cross",
    "konanakunte": "Konanakunte Cross",
    "forum south bangalore": "Konanakunte Cross",
    "doddakallasandra": "Doddakallasandra",
    "vajrahalli": "Vajrahalli",
    "thalaghattapura": "Thalaghattapura",
    "talaghattapura": "Thalaghattapura",
    "silk institute": "Silk Institute",

    # Yellow Line
    "ragigudda": "Ragigudda",
    "jayadeva hospital": "Jayadeva Hospital",
    "jayadeva": "Jayadeva Hospital",
    "jayadeva metro": "Jayadeva Hospital",
    "btm layout": "BTM Layout",
    "btm": "BTM Layout",
    "btm metro": "BTM Layout",
    "central silk board": "Central Silk Board",
    "silk board": "Central Silk Board",
    "csb": "Central Silk Board",
    "bommanahalli": "Bommanahalli",
    "hongasandra": "Hongasandra",
    "kudlu gate": "Kudlu Gate",
    "kudlu": "Kudlu Gate",
    "singasandra": "Singasandra",
    "hosa road": "Hosa Road",
    "beretena agrahara": "Beretena Agrahara",
    "beratena agrahara": "Beretena Agrahara",
    "electronic city": "Electronic City",
    "electronics city": "Electronic City",
    "e-city": "Electronic City",
    "ecity": "Electronic City",
    "electronic city 1": "Electronic City",
    "infosys foundation konappana agrahara": "Infosys Foundation Konappana Agrahara",
    "konappana agrahara": "Infosys Foundation Konappana Agrahara",
    "infosys": "Infosys Foundation Konappana Agrahara",
    "infosys metro": "Infosys Foundation Konappana Agrahara",
    "electronic city 2": "Infosys Foundation Konappana Agrahara",
    "huskur road": "Huskur Road",
    "huskur": "Huskur Road",
    "biocon hebbagodi": "Biocon Hebbagodi",
    "hebbagodi": "Biocon Hebbagodi",
    "biocon": "Biocon Hebbagodi",
    "delta electronics bommasandra": "Delta Electronics Bommasandra",
    "bommasandra": "Delta Electronics Bommasandra",
}

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
    "manyata": {
        "bmtc": "Manyatha Tech Park",
    },
    "manyatha": {
        "bmtc": "Manyatha Tech Park",
    },
    "manyata tech park": {
        "bmtc": "Manyatha Tech Park",
    },
    "manyatha teck park": {
        "bmtc": "Manyatha Tech Park",
    },
    "hosakerehalli": {
        "bmtc": "Hosakerehalli  Junction",
    },
    "hoskerehalli": {
        "bmtc": "Hosakerehalli  Junction",
    },
    "hosakerehalli cross": {
        "bmtc": "Hosakerehalli Cross",
    },
    "hoskerehalli cross": {
        "bmtc": "Hosakerehalli Cross",
    },
    "hosakerehalli junction": {
        "bmtc": "Hosakerehalli  Junction",
    },
    "hoskerehalli junction": {
        "bmtc": "Hosakerehalli  Junction",
    },
    "hosakerehalli petrol bunk": {
        "bmtc": "Hosakerehalli Petrol Bunk",
    },
    "hoskerehalli petrol bunk": {
        "bmtc": "Hosakerehalli Petrol Bunk",
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
    
    # ── METRO MODE RESOLUTION ────────────────────────────────────────────────
    if mode.lower() == "metro":
        # 1. Direct match in comprehensive METRO_ALIASES
        if cleaned_lower in METRO_ALIASES:
            return METRO_ALIASES[cleaned_lower]

        # 2. Check HUB_MAPPINGS
        for key in sorted(HUB_MAPPINGS.keys(), key=len, reverse=True):
            if key == cleaned_lower or key in cleaned_lower:
                resolved = HUB_MAPPINGS[key].get("metro")
                if resolved:
                    return resolved

        # 3. Exact case-insensitive match against official station list
        if metro_stations:
            for ms in metro_stations:
                if ms.lower() == cleaned_lower:
                    return ms

            # 4. Transliteration variants: Kannada 'a' ending differences
            # e.g., "Jayanagar" <-> "Jayanagara", "Vijayanagar" <-> "Vijayanagara"
            cand_variants = [
                cleaned_lower + "a",
                cleaned_lower[:-1] if cleaned_lower.endswith("a") else cleaned_lower,
                cleaned_lower + "e",
                cleaned_lower[:-1] if cleaned_lower.endswith("e") else cleaned_lower,
            ]
            for var in cand_variants:
                if var in METRO_ALIASES:
                    return METRO_ALIASES[var]
                for ms in metro_stations:
                    if ms.lower() == var:
                        return ms

            # 5. Substring match in METRO_ALIASES (longest key first)
            for key in sorted(METRO_ALIASES.keys(), key=len, reverse=True):
                if len(key) >= 4 and key in cleaned_lower:
                    return METRO_ALIASES[key]

            # 6. Fuzzy match fallback against metro_stations (strict 0.86 cutoff to prevent false positives like hosakerehalli -> hosahalli)
            ms_map = {ms.lower(): ms for ms in metro_stations}
            matches = difflib.get_close_matches(cleaned_lower, list(ms_map.keys()), n=1, cutoff=0.86)
            if matches:
                cand = matches[0]
                if "kere" in cleaned_lower and "kere" not in cand:
                    pass
                else:
                    return ms_map[cand]

        return cleaned

    # ── BMTC MODE RESOLUTION ─────────────────────────────────────────────────
    # 1. Check direct hub substring matches (most specific/longest first)
    for key in sorted(HUB_MAPPINGS.keys(), key=len, reverse=True):
        if key in cleaned_lower:
            resolved = HUB_MAPPINGS[key].get(mode.lower())
            if resolved:
                return resolved

    # 2. Case-insensitive exact matching against bmtc_stops
    if bmtc_stops:
        for bs in bmtc_stops:
            if bs.lower() == cleaned_lower:
                return bs

    # 3. Fallback to cleaned title case or original name
    return cleaned
