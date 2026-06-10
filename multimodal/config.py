"""Multimodal interchange point configuration."""

# Metro stations with nearby BMTC stop names and coordinates
# Coordinates are approximate (latitude, longitude)
INTERCHANGE_POINTS = {
    # Green Line interchanges
    "Majestic": {
        "metro_station": "Majestic",
        "line": "Green",
        "coords": (12.9667, 77.5667),
        "nearby_bmtc_stops": ["Majestic", "Kempegowda Metro", "City Railway Station"],
    },
    "Yeshwanthpur": {
        "metro_station": "Yeshwanthpur",
        "line": "Green",
        "coords": (13.0011, 77.5920),
        "nearby_bmtc_stops": ["Yeshwanthpur", "Yeshwanthpur Metro"],
    },
    "Rajajinagar": {
        "metro_station": "Rajajinagar",
        "line": "Green",
        "coords": (13.0018, 77.5751),
        "nearby_bmtc_stops": ["Rajajinagar", "Rajajinagar Junction"],
    },
    # Purple Line interchanges
    "Trinity": {
        "metro_station": "Trinity",
        "line": "Purple",
        "coords": (12.9761, 77.6120),
        "nearby_bmtc_stops": ["Trinity", "Trinity Circle"],
    },
    "MG Road": {
        "metro_station": "MG Road",
        "line": "Purple",
        "coords": (12.9667, 77.5915),
        "nearby_bmtc_stops": ["MG Road", "Raheja Arcade"],
    },
    "Cubbon Park": {
        "metro_station": "Cubbon Park",
        "line": "Purple",
        "coords": (12.9710, 77.5912),
        "nearby_bmtc_stops": ["Cubbon Park", "Vidhana Soudha"],
    },
    "Indiranagar": {
        "metro_station": "Indiranagar",
        "line": "Purple",
        "coords": (12.9716, 77.6413),
        "nearby_bmtc_stops": ["Indiranagar", "100 Feet Road"],
    },
    # Yellow Line interchanges
    "Rashtriya Vidyalaya Road": {
        "metro_station": "Rashtriya Vidyalaya Road",
        "line": "Yellow",
        "coords": (12.9667, 77.5667),
        "nearby_bmtc_stops": ["Rashtriya Vidyalaya Road", "BMTC Stop"],
    },
    "Electronic City": {
        "metro_station": "Electronic City",
        "line": "Yellow",
        "coords": (12.8441, 77.6763),
        "nearby_bmtc_stops": ["Electronic City", "ELCITA"],
    },
    "Hosa Road": {
        "metro_station": "Hosa Road",
        "line": "Yellow",
        "coords": (12.8747, 77.6497),
        "nearby_bmtc_stops": ["Hosa Road", "HSR Layout"],
    },
    # Additional key interchanges
    "Whitefield": {
        "metro_station": "Whitefield",
        "line": "Purple",
        "coords": (12.9696, 77.7499),
        "nearby_bmtc_stops": ["Whitefield", "Whitefield Main"],
    },
    "Baiyappanahalli": {
        "metro_station": "Baiyappanahalli",
        "line": "Purple",
        "coords": (12.9533, 77.6267),
        "nearby_bmtc_stops": ["Baiyappanahalli", "Malleswaram"],
    },
}

# Settings
WALKING_RADIUS_M = 500  # Maximum walking distance between metro and BMTC
TRANSFER_BUFFER_MINUTES = 10  # Buffer time for changing transport
MAX_MULTIMODAL_OPTIONS = 5  # Show top 5 multimodal alternatives
