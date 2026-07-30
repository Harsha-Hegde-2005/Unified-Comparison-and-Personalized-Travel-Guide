import sys
import os
import json
sys.path.insert(0, ".")
from modes.cab.engines.distance_engine import DistanceEngine

# Hardcoded coordinates for the 12 benchmark locations to avoid Nominatim rate limits/failures
locations = {
    "CHRIST University, Hosur Road": {"latitude": 12.93574, "longitude": 77.60595},
    "Nexus Koramangala": {"latitude": 12.93483, "longitude": 77.61134},
    "Manyata Tech Park": {"latitude": 13.04500, "longitude": 77.62000},
    "Aster CMI Hospital, Hebbal": {"latitude": 13.03600, "longitude": 77.58900},
    "Bagmane Tech Park": {"latitude": 12.97877, "longitude": 77.65886},
    "Indiranagar Metro Station": {"latitude": 12.97829, "longitude": 77.63865},
    "Bangalore University, Jnana Bharathi": {"latitude": 12.94600, "longitude": 77.50900},
    "RV College of Engineering": {"latitude": 12.92200, "longitude": 77.49800},
    "PES University": {"latitude": 12.93424, "longitude": 77.53432},
    "MG Road Metro Station": {"latitude": 12.97539, "longitude": 77.60650},
    "Yelahanka New Town": {"latitude": 13.09780, "longitude": 77.58119},
    "Orion Mall, Rajajinagar": {"latitude": 13.01100, "longitude": 77.55518},
    "KSR Bengaluru City Junction": {"latitude": 12.97230, "longitude": 77.56456},
    "Kempegowda International Airport": {"latitude": 13.19760, "longitude": 77.70749},
    "Electronic City": {"latitude": 12.84876, "longitude": 77.64825},
    "ITPB, Whitefield": {"latitude": 12.98300, "longitude": 77.73300},
    "Kengeri Railway Station": {"latitude": 12.90800, "longitude": 77.47800},
    "Infosys, Electronic City": {"latitude": 12.85025, "longitude": 77.66638}
}

routes = [
    ("CHRIST University, Hosur Road", "Nexus Koramangala"),  # ROUTE 1
    ("Manyata Tech Park", "Aster CMI Hospital, Hebbal"),     # ROUTE 2
    ("Bagmane Tech Park", "Indiranagar Metro Station"),       # ROUTE 3
    ("Bangalore University, Jnana Bharathi", "RV College of Engineering"), # ROUTE 4
    ("PES University", "MG Road Metro Station"),             # ROUTE 5
    ("Yelahanka New Town", "Orion Mall, Rajajinagar"),       # ROUTE 6
    ("Indiranagar Metro Station", "Nexus Koramangala"),       # ROUTE 7
    ("RV College of Engineering", "KSR Bengaluru City Junction"), # ROUTE 8
    ("Kempegowda International Airport", "Electronic City"), # ROUTE 9
    ("ITPB, Whitefield", "Kengeri Railway Station"),         # ROUTE 10
    ("Infosys, Electronic City", "Manyata Tech Park"),       # ROUTE 11
    ("Kengeri Railway Station", "ITPB, Whitefield")          # ROUTE 12
]

d_eng = DistanceEngine()

print("Resolving routes...")
resolved_routes = []
for i, (src_name, dst_name) in enumerate(routes, 1):
    try:
        src_coords = locations[src_name]
        dst_coords = locations[dst_name]
        route_info = d_eng.get_distance(src_coords, dst_coords)
        print(f"ROUTE {i}: {src_name} -> {dst_name}")
        print(f"  Distance: {route_info['distance_km']} km, Duration: {route_info['duration_min']} min")
        resolved_routes.append({
            "id": i,
            "src": src_name,
            "dst": dst_name,
            "src_coords": src_coords,
            "dst_coords": dst_coords,
            "distance_km": route_info["distance_km"],
            "duration_min": route_info["duration_min"]
        })
    except Exception as e:
        print(f"Error on ROUTE {i} ({src_name} -> {dst_name}): {e}")

with open("resolved_routes.json", "w") as f:
    json.dump(resolved_routes, f, indent=2)
print("Saved resolved_routes.json")
