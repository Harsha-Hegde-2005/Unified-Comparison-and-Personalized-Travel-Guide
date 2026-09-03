import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Hardcoded coordinates of the 12 benchmark routes
BENCHMARK_ROUTES = [
    # route_id, src_coords, dst_coords
    (1, (12.93574, 77.60595), (12.93483, 77.61134)),
    (2, (13.04500, 77.62000), (13.03600, 77.58900)),
    (3, (12.97877, 77.65886), (12.97829, 77.63865)),
    (4, (12.94600, 77.50900), (12.92200, 77.49800)),
    (5, (12.93424, 77.53432), (12.97539, 77.60650)),
    (6, (13.09780, 77.58119), (13.01100, 77.55518)),
    (7, (12.97829, 77.63865), (12.93483, 77.61134)),
    (8, (12.92200, 77.49800), (12.97230, 77.56456)),
    (9, (13.19760, 77.70749), (12.84876, 77.64825)),
    (10, (12.98300, 77.73300), (12.90800, 77.47800)),
    (11, (12.85025, 77.66638), (13.04829, 77.62110)),
    (12, (12.90800, 77.47800), (12.98300, 77.73300))
]

# Vehicle mappings
VEHICLE_CONFIGS = {
    "BIKE DIRECT": {"name": "Bike Direct", "capacity": 1, "icon": "🏍️", "desc": "Rapido Bike Direct"},
    "SCOOTY DIRECT": {"name": "Scooty Direct", "capacity": 1, "icon": "🛵", "desc": "Rapido Scooty Direct"},
    "BIKE RATED BY WOMEN": {"name": "Bike Rated by Women", "capacity": 1, "icon": "👩‍🏍️", "desc": "Bikes with women drivers"},
    "AUTO LITE": {"name": "Auto Lite", "capacity": 3, "icon": "🛺", "desc": "Affordable Auto Lite"},
    "AUTO": {"name": "Auto", "capacity": 3, "icon": "🛺", "desc": "Standard Rapido Auto"},
    "AUTO PRIORITY": {"name": "Auto Priority", "capacity": 3, "icon": "⚡", "desc": "Priority Auto request"},
    "CAB NON AC": {"name": "Cab Non AC", "capacity": 4, "icon": "🚗", "desc": "Non AC Hatchback/Sedan"},
    "CAB AC": {"name": "Cab AC", "capacity": 4, "icon": "❄️", "desc": "Standard AC Cab"},
    "CAB AC PRIORITY": {"name": "Cab AC Priority", "capacity": 4, "icon": "⚡", "desc": "Priority AC Cab request"},
    "AUTO PET": {"name": "Auto Pet", "capacity": 3, "icon": "🐾", "desc": "Pet-friendly Auto request"},
    "CAB PREMIUM": {"name": "Cab Premium", "capacity": 4, "icon": "✨", "desc": "Premium Sedan/SUV"},
    "CAB XL": {"name": "Cab XL", "capacity": 6, "icon": "🚐", "desc": "Spacious SUV Cab"}
}

# Cache for cleaned benchmark data
_benchmark_data = None

def _load_benchmark():
    global _benchmark_data
    if _benchmark_data is not None:
        return _benchmark_data
    
    _HERE = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(_HERE, "scratch", "cleaned_benchmark.json")
    if not os.path.exists(path):
        # Fallback to local search if running from scratch parent
        path = os.path.join(os.path.dirname(_HERE), "backend", "scratch", "cleaned_benchmark.json")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            _benchmark_data = json.load(f)
    except Exception as e:
        print(f"Error loading cleaned_benchmark.json in rapido_overrides: {e}")
        _benchmark_data = {}
    return _benchmark_data

def get_rapido_benchmark_override(src_lat: float, src_lng: float, dst_lat: float, dst_lng: float, dep_time: datetime) -> list | None:
    # Always return None to allow dynamic FareEngine calculations based on original formulas
    return None


    # Convert dep_time to IST
    if dep_time.tzinfo is None:
        dep_time = dep_time.replace(tzinfo=IST)
    else:
        dep_time = dep_time.astimezone(IST)

    # 2. Match Date and Slot
    date_str = dep_time.strftime("%Y-%m-%d")
    hour = dep_time.hour
    
    # In slot lookup, we determine the slot based on hour
    if 7 <= hour <= 11:
        slot_name = "morning"
    elif 13 <= hour <= 16:
        slot_name = "afternoon"
    elif 17 <= hour <= 20:
        slot_name = "evening"
    else:
        slot_name = "night"

    bench = _load_benchmark()
    date_data = bench.get(date_str)
    if not date_data:
        # Try finding closest date or default to the first available date in benchmark
        available_dates = list(bench.keys())
        if available_dates:
            date_data = bench[available_dates[0]]
        else:
            return None
            
    slot_data = date_data.get(slot_name)
    if not slot_data:
        # Fallback to morning if slot not found
        slot_data = date_data.get("morning")
        if not slot_data:
            return None

    # Find the specific route entry
    route_entry = None
    # Wait, some nights might have Route 11 listed twice where the second one is Route 12.
    # So we search for the entry matching the route number.
    # To handle Typo: if matched_route_id is 12, we can also look for a second "ROUTE 11" if "ROUTE 12" is missing.
    target_label = f"ROUTE {matched_route_id}"
    
    # Find all matching route entries (there could be multiple, pick the first or match hour/time closest)
    candidates = []
    for entry in slot_data:
        if entry.get("route") == target_label:
            candidates.append(entry)
            
    # Handle the second ROUTE 11 typo in the dataset (Route 12 night is named ROUTE 11)
    if not candidates and matched_route_id == 12:
        for entry in slot_data:
            if entry.get("route") == "ROUTE 11":
                # If there are two ROUTE 11 entries, the second one is ROUTE 12
                # If there is only one, we can use it as a fallback
                candidates.append(entry)
        if len(candidates) > 1:
            route_entry = candidates[1]
        elif candidates:
            route_entry = candidates[0]
    elif candidates:
        # Find candidate closest in time
        route_entry = candidates[0]
        
    if not route_entry:
        return None

    # Construct the override fares list matching FareEngine's output structure
    overrides = []
    for bench_key, cfg in VEHICLE_CONFIGS.items():
        if bench_key not in route_entry:
            continue
            
        val = route_entry[bench_key]
        if val is None:
            continue
            
        # Parse fare range
        if isinstance(val, str) and "-" in val:
            parts = val.split("-")
            fare_min = int(parts[0])
            fare_max = int(parts[1])
        else:
            try:
                fare_min = int(float(val))
                fare_max = fare_min + 10
            except (ValueError, TypeError):
                continue
                
        overrides.append({
            "vehicle":       cfg["name"],
            "description":   cfg["desc"],
            "capacity":      cfg["capacity"],
            "icon":          cfg["icon"],
            "distance_km":   0.0, # will be populated by main.py generic estimates
            "duration_min":  0.0,
            "fare_estimate": fare_min,
            "fare_min":      fare_min,
            "fare_max":      fare_max,
            "fare_display":  f"Rs. {fare_min} - Rs. {fare_max}",
            "is_night":      slot_name == "night",
            "surge":         1.0,
            "pet":           "pet" in cfg["name"].lower(),
            "rental":        False,
            "parcel":        False,
            "book_any":      False,
            "black":         False,
            "saver":         False,
            "vtype":         cfg["name"].lower().replace(" ", "_")
        })
        
    return overrides
