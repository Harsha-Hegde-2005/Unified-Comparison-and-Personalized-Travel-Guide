"""Multimodal interchange point configuration."""

# Metro stations with nearby BMTC stop names and coordinates
# Coordinates are precise station coordinates matching database/metro/metro_coords.json
INTERCHANGE_POINTS = {
    # Green Line interchanges
    "Majestic": {
        "metro_station": "Majestic",
        "line": "Green",
        "coords": (12.975635, 77.572832),
        "nearby_bmtc_stops": ["Kempegowda Bus Station", "Majestic", "City Railway Station"],
    },
    "Yeshwanthpur": {
        "metro_station": "Yeshwanthpur",
        "line": "Green",
        "coords": (13.023249, 77.550131),
        "nearby_bmtc_stops": ["Yeshawanthapura Bus Station", "Yeshwanthpur", "Yeshwanthpur TTMC"],
    },
    "Rajajinagar": {
        "metro_station": "Rajajinagar",
        "line": "Green",
        "coords": (12.998492, 77.555709),
        "nearby_bmtc_stops": ["Rajajinagar", "Rajajinagar Entrance"],
    },
    "Banashankari": {
        "metro_station": "Banashankari",
        "line": "Green",
        "coords": (12.91655, 77.57349),
        "nearby_bmtc_stops": ["Banashankari Bus Station", "Banashankari TTMC", "Banashankari"],
    },
    "Goraguntepalya": {
        "metro_station": "Goraguntepalya",
        "line": "Green",
        "coords": (13.028543, 77.540821),
        "nearby_bmtc_stops": ["Goraguntepalya", "Goraguntepalya Bus Stop"],
    },
    # Purple Line interchanges
    "Trinity": {
        "metro_station": "Trinity",
        "line": "Purple",
        "coords": (12.972863, 77.617141),
        "nearby_bmtc_stops": ["Trinity", "Trinity Circle"],
    },
    "MG Road": {
        "metro_station": "MG Road",
        "line": "Purple",
        "coords": (12.975548, 77.606543),
        "nearby_bmtc_stops": ["MG Road", "Mayo Hall"],
    },
    "Cubbon Park": {
        "metro_station": "Cubbon Park",
        "line": "Purple",
        "coords": (12.980741, 77.598412),
        "nearby_bmtc_stops": ["Cubbon Park", "Vidhana Soudha"],
    },
    "Indiranagar": {
        "metro_station": "Indiranagar",
        "line": "Purple",
        "coords": (12.978294, 77.638652),
        "nearby_bmtc_stops": ["Indiranagara", "Indiranagar 100ft Road", "CMH Hospital"],
    },
    "Baiyappanahalli": {
        "metro_station": "Baiyappanahalli",
        "line": "Purple",
        "coords": (12.991937, 77.6516),
        "nearby_bmtc_stops": ["Baiyappanahalli Metro", "Baiyappanahalli Railway Station"],
    },
    "Krishnarajapura": {
        "metro_station": "Krishnarajapura",
        "line": "Purple",
        "coords": (12.998436, 77.678144),
        "nearby_bmtc_stops": ["KR Puram", "KR Puram Railway Station"],
    },
    "Whitefield": {
        "metro_station": "Whitefield",
        "line": "Purple",
        "coords": (12.9865, 77.75),
        "nearby_bmtc_stops": ["Whitefield", "Whitefield Bus Stand"],
    },
    "Kengeri Bus Terminal": {
        "metro_station": "Kengeri Bus Terminal",
        "line": "Purple",
        "coords": (12.908422, 77.476413),
        "nearby_bmtc_stops": ["Kengeri TTMC", "Kengeri Bus Stand"],
    },
    # Yellow Line interchanges
    "Rashtriya Vidyalaya Road": {
        "metro_station": "Rashtriya Vidyalaya Road",
        "line": "Yellow",
        "coords": (12.921503, 77.580124),
        "nearby_bmtc_stops": ["Rashtriya Vidyalaya Road", "RV Road"],
    },
    "Central Silk Board": {
        "metro_station": "Central Silk Board",
        "line": "Yellow",
        "coords": (12.917285, 77.623287),
        "nearby_bmtc_stops": ["Central Silk Board", "Silk Board"],
    },
    "Jayadeva Hospital": {
        "metro_station": "Jayadeva Hospital",
        "line": "Yellow",
        "coords": (12.918119, 77.598112),
        "nearby_bmtc_stops": ["Jayadeva Hospital", "Jayadeva"],
    },
    "Electronic City": {
        "metro_station": "Electronic City",
        "line": "Yellow",
        "coords": (12.844111, 77.676343),
        "nearby_bmtc_stops": ["Electronic City", "ELCITA"],
    },
    "Hosa Road": {
        "metro_station": "Hosa Road",
        "line": "Yellow",
        "coords": (12.874721, 77.649721),
        "nearby_bmtc_stops": ["Hosa Road", "Hosa Road Junction"],
    },
}

# Settings
WALKING_RADIUS_M = 500  # Maximum walking distance between metro and BMTC
TRANSFER_BUFFER_MINUTES = 10  # Buffer time for changing transport
MAX_MULTIMODAL_OPTIONS = 5  # Show top 5 multimodal alternatives
