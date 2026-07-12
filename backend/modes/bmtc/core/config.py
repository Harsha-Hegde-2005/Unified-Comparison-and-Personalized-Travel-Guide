"""
core/config.py
==============
Centralised constants and configuration for BMTC Smart Planner.
All magic numbers live here — edit once, apply everywhere.
"""

import os as _os

# ── Data paths (absolute, relative to this file — works from any working dir) ─
_HERE         = _os.path.dirname(_os.path.abspath(__file__))   # .../bmtc_planner/core/
_ROOT         = _os.path.dirname(_HERE)                         # .../bmtc_planner/
WORKSPACE_ROOT = _os.path.abspath(_os.path.join(_HERE, "..", "..", "..", ".."))

DATA_DIR      = _os.path.join(WORKSPACE_ROOT, "database", "bmtc")
RAW_DIR       = _os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = _os.path.join(DATA_DIR, "processed")

STOP_LEVEL_CLEANED    = _os.path.join(PROCESSED_DIR, "bmtc_stop_level_cleaned.csv")
STOP_LEVEL_ORIGINAL   = _os.path.join(PROCESSED_DIR, "bmtc_stop_level.csv")
STOPS_CLEAN           = _os.path.join(PROCESSED_DIR, "stops_clean.csv")
REVERSE_SUPPLEMENT    = _os.path.join(PROCESSED_DIR, "reverse_routes_supplement.csv")
STOP_CLUSTERS         = _os.path.join(PROCESSED_DIR, "stop_clusters.csv")

GTFS_STOPS      = _os.path.join(RAW_DIR, "stops.txt")
GTFS_STOP_TIMES = _os.path.join(RAW_DIR, "stop_times.txt")
GTFS_TRIPS      = _os.path.join(RAW_DIR, "trips.txt")
GTFS_ROUTES     = _os.path.join(RAW_DIR, "routes.txt")

# ── Routing parameters ────────────────────────────────────────────────────────
WAITING_TIME   = 5    # minutes — boarding wait at first stop
TRANSFER_TIME  = 3    # minutes — per transfer penalty
MAX_TRANSFERS  = 2    # hard cap on transfers for Dijkstra
MAX_OPTIONS    = 5    # number of route alternatives to surface
FAST_QUERY_MODE = True

# ── Bus speed (km/h) by time-of-day — Bengaluru traffic profile ───────────────
SPEED_PEAK     = 10.0   # 07:00–10:00, 17:00–21:00
SPEED_DAY      = 20.0   # 10:00–17:00
SPEED_NIGHT    = 35.0   # 21:00–07:00

# ── Fare slabs ──────────────────────────────────────────────────────────────────
ORDINARY_FARE_SLABS = [
    (2,  6),  (4,  12), (6,  18), (8,  23), (10, 23),
    (12, 24), (14, 24), (16, 28), (18, 28), (20, 28),
    (22, 30), (24, 30), (26, 30), (28, 30), (30, 30),
]
ORDINARY_FARE_DEFAULT = 32   # anything beyond 30 km

# Vajra / AC fares are kept separate so premium services are not priced
# using ordinary-bus slabs. Values can be tuned here without touching logic.
VAJRA_FARE_SLABS = [
    (2,  12), (4,  15), (6,  20), (8,  25), (10, 30),
    (12, 35), (14, 40), (16, 45), (18, 50), (20, 55),
    (22, 60), (24, 65), (26, 70), (28, 75), (30, 80),
]
VAJRA_FARE_DEFAULT = 85

# KIA / Airport bus fares — premium airport express pricing
# BMTC airport buses charge Rs.150–310 depending on distance zone
KIA_FARE_SLABS = [
    (10,  150), (20, 200), (30, 250), (40, 280),
]
KIA_FARE_DEFAULT = 310  # full airport run (e.g. Kempegowda station → KIA ~40 km)

# ── Toll surcharges ───────────────────────────────────────────────────────────
TOLL_STOP_SURCHARGES: dict[str, int] = {
    "elc toll point": 7, "electronic city fly": 7,
    "electronic city flyover": 7, "elc nice road": 7,
    "konappana agrahara flyover": 7, "hosa road fly": 7,
    "singasandra fly": 7, "kudlu gate flyover": 7,
    "bommanahalli fly over": 7,
    "nice road": 5, "nice road 1st stone": 5,
    "nice road 2nd stone": 5, "nice road 3rd stone": 5,
    "nice road 15th stone": 5, "nice road 16th stone": 5,
    "nice road 17th stone": 5,
    "nice road bannerughatta road junction": 5,
    "nice road junction kengeri": 5,
    "nice road kanakapura road junction": 5,
}

# Premium-route markers used for Vajra / AC pricing.
VAJRA_ROUTE_PATTERNS = ["AC", "V-", "VAJRA", "VOLVO"]

# Airport-bus markers — KIA and AP routes are separate high-fare category
KIA_ROUTE_PATTERNS = ["KIA", "-AP ", "-AP_", "KBS-KIA", "PTH-KIA", "AIRPORT"]

# ── Routes to exclude from suggestions (airport premium only) ──────────────────
# Do NOT include "AC" here — Vajra AC buses are normal premium services, not airport-exclusive
EXCLUDED_ROUTE_PATTERNS = ["AP", "KIA", "AIRPORT"]

# ── Map defaults ──────────────────────────────────────────────────────────────
MAP_CENTER   = [12.97, 77.59]
MAP_ZOOM     = 12
MAP_TILE     = "CartoDB positron"
ROUTE_COLORS = ["#2d5be3", "#e85d26", "#0f9d58"]

# ── Google Maps API ───────────────────────────────────────────────────────────
# Auto-loads from .env file next to this package root (bmtc_planner/.env).
# Enables: embedded Google Map, live traffic ETA, Places autocomplete.
import os as _os

def _load_env_key() -> str:
    key = _os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if key:
        return key
    env_path = _os.path.join(WORKSPACE_ROOT, ".env")
    try:
        with open(env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line.startswith("GOOGLE_MAPS_API_KEY="):
                    return _line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return ""

GOOGLE_MAPS_API_KEY = _load_env_key()

# ── BMTC operational hours ─────────────────────────────────────────────────────
# Buses run 05:00 to 23:30. Outside these hours, searches are blocked.
BMTC_OPERATIONAL_START = "05:00"
BMTC_OPERATIONAL_END   = "23:30"

# ── UI ────────────────────────────────────────────────────────────────────────
PAGE_TITLE   = "BMTC Smart Planner"
PAGE_ICON    = "🚌"
TOP_N_BUSES  = 5
