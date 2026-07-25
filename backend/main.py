"""
unified_api.py
==============
Single FastAPI backend serving both BMTC and Metro routing.
Run from the bmtc_planner/ root:

    uvicorn unified_api:app --reload --port 8000

Then open the React UI — it calls:
    POST /api/metro/plan        → metro journey
    POST /api/bmtc/plan         → bmtc journey
    POST /api/compare           → all modes combined
    POST /api/cab/estimate      → ride-hailing estimates (all providers)
    GET  /api/cab/providers     → list available cab providers
    GET  /api/metro/stations    → all metro station names
    GET  /api/bmtc/stops        → all bmtc stop names
    GET  /api/vehicle/list      → all personal vehicle names
    POST /api/vehicle/search    → fuzzy search vehicles
    POST /api/vehicle/estimate  → fuel cost for personal vehicle

CORS is open for localhost:5173 (Vite) and localhost:3000 (CRA).
"""

from __future__ import annotations
import os, sys, json, math, re as _re
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Path setup & imports ──────────────────────────────────────────────────────
_HERE  = os.path.dirname(os.path.abspath(__file__))
_METRO = os.path.join(_HERE, "modes", "metro")
_BMTC  = os.path.join(_HERE, "modes", "bmtc")

sys.path.insert(0, _HERE)

# Metro imports
sys.path.insert(0, _METRO)
try:
    from planner.journey_planner import JourneyPlanner as MetroPlanner
finally:
    sys.path.remove(_METRO)

# BMTC imports
sys.path.insert(0, _BMTC)
try:
    from core.loader import ALL_STOPS, stops_df
    from features.routing import get_all_buses_comprehensive, _route_trips, estimate_route_schedule
    from core.graph import dijkstra, extract_segments
    from features.schedule import calculate_segment_times, normalize_search_start_time
    from core.stops import get_route_stop_names
finally:
    sys.path.remove(_BMTC)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Bengaluru Unified Transit API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000",
                   "http://localhost:5174", "*"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
async def _startup_preload_gtfs():
    """Kick off GTFS loading in a background thread and initialize database tables."""
    try:
        from db import init_db
        init_db()
        print("Database initialized successfully.")
    except Exception as dbe:
        print(f"Database init error: {dbe}")

    import threading, sys as _sys
    _bmtc_dir = os.path.join(_HERE, "modes", "bmtc")
    def _load():
        _sys.path.insert(0, _bmtc_dir)
        try:
            from core.gtfs import _load_gtfs
            _load_gtfs()
        except Exception as e:
            print(f"GTFS background load error: {e}")
        finally:
            if _bmtc_dir in _sys.path:
                _sys.path.remove(_bmtc_dir)
    threading.Thread(target=_load, daemon=True, name="gtfs-loader").start()


# ── Singletons ────────────────────────────────────────────────────────────────
_metro_planner   = MetroPlanner()
_metro_stations  = sorted(_metro_planner.routing_engine.stations.keys())

# ── Stop coordinates lookup (from File 2 — bug-free) ─────────────────────────
STOP_COORDS = (
    stops_df.groupby("stop_norm")
    .first()[["latitude", "longitude"]]
    .to_dict("index")
)

def get_stop_coords(stop_name: str) -> tuple[float, float] | None:
    # 1. Check if coordinate format directly
    coord_val = parse_coords(stop_name)
    if coord_val:
        return coord_val

    # 2. Check if it's explicitly a Metro station or user requested Metro
    from shared.utils import resolve_stop_name
    stop_name_lower = stop_name.strip().lower()
    is_metro_intent = "metro" in stop_name_lower or "station" in stop_name_lower
    
    # Load compiled metro station coordinates database
    metro_db = {}
    import json
    db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "database", "metro", "metro_coords.json")
    )
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                metro_db = json.load(f)
        except Exception:
            pass

    # Resolve names for both modes
    resolved_metro = None
    try:
        resolved_metro = resolve_stop_name(stop_name, "metro", metro_stations=_metro_stations)
    except Exception:
        pass

    resolved_bmtc = None
    try:
        resolved_bmtc = resolve_stop_name(stop_name, "bmtc", bmtc_stops=ALL_STOPS)
    except Exception:
        pass

    # Check if we should prefer Metro first:
    # 1. Explicit metro intent (e.g. contains "metro" or "station")
    # 2. Or is a valid metro station name but NOT a valid BMTC stop name
    is_metro_first = False
    if is_metro_intent:
        is_metro_first = True
    elif resolved_metro and resolved_metro.lower() in [s.lower() for s in _metro_stations]:
        has_bmtc_match = False
        if resolved_bmtc:
            has_bmtc_match = any(s.lower() == resolved_bmtc.lower() for s in ALL_STOPS)
        if not has_bmtc_match:
            is_metro_first = True

    # If this is a metro station, or is_metro_intent is true, try resolving as metro first
    if is_metro_first:
        # A. Check compiled metro DB
        if resolved_metro and resolved_metro in metro_db:
            return float(metro_db[resolved_metro]["lat"]), float(metro_db[resolved_metro]["lng"])
        
        # B. Check INTERCHANGE_POINTS
        try:
            from multimodal.config import INTERCHANGE_POINTS
            for station, pt in INTERCHANGE_POINTS.items():
                if resolved_metro and (station.lower() == resolved_metro.lower() or station.lower() in resolved_metro.lower()):
                    coords = pt["coords"]
                    return float(coords[0]), float(coords[1])
        except Exception:
            pass
            
        # C. Substring match on INTERCHANGE_POINTS
        try:
            from multimodal.config import INTERCHANGE_POINTS
            for station, pt in INTERCHANGE_POINTS.items():
                if station.lower() in stop_name_lower:
                    coords = pt["coords"]
                    return float(coords[0]), float(coords[1])
        except Exception:
            pass

    # 3. Try BMTC stops
    try:
        resolved = resolve_stop_name(stop_name, "bmtc", bmtc_stops=ALL_STOPS)
        norm = resolved.strip().lower()
        if norm in STOP_COORDS:
            return (
                float(STOP_COORDS[norm]["latitude"]),
                float(STOP_COORDS[norm]["longitude"]),
            )
    except Exception:
        pass

    # 4. Fallback to Metro if not resolved as BMTC and not already checked
    if not is_metro_first:
        if resolved_metro and resolved_metro in metro_db:
            return float(metro_db[resolved_metro]["lat"]), float(metro_db[resolved_metro]["lng"])
            
        try:
            from multimodal.config import INTERCHANGE_POINTS
            for station, pt in INTERCHANGE_POINTS.items():
                if resolved_metro and (station.lower() == resolved_metro.lower() or station.lower() in resolved_metro.lower()):
                    coords = pt["coords"]
                    return float(coords[0]), float(coords[1])
        except Exception:
            pass
            
        try:
            from multimodal.config import INTERCHANGE_POINTS
            for station, pt in INTERCHANGE_POINTS.items():
                if station.lower() in stop_name_lower:
                    coords = pt["coords"]
                    return float(coords[0]), float(coords[1])
        except Exception:
            pass

    return None


def is_coord_str(s: str) -> bool:
    return parse_coords(s) is not None


def parse_coords(s: str) -> tuple[float, float] | None:
    # 1. Try matching parenthesized coordinates anywhere in the string, e.g. "PES University (12.93496, 77.53488)"
    paren_match = _re.search(r"\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)", s)
    if paren_match:
        try:
            return float(paren_match.group(1)), float(paren_match.group(2))
        except ValueError:
            pass

    # 2. Try matching exact coordinate string
    match = _re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", s)
    if match:
        try:
            return float(match.group(1)), float(match.group(2))
        except ValueError:
            pass
    return None


def _google_walk_distance(src_lat, src_lng, dst_lat, dst_lng) -> tuple[float, float] | None:
    from modes.cab.engines.distance_engine import DistanceEngine
    if DistanceEngine.google_maps_disabled:
        return None
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not key:
        return None
    try:
        import requests as _req
        resp = _req.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={"origins":       f"{src_lat},{src_lng}",
                    "destinations":  f"{dst_lat},{dst_lng}",
                    "mode":          "walking",
                    "key":           key},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "REQUEST_DENIED":
            print("Google Maps Walk API failed: REQUEST_DENIED. Disabling Google Maps.")
            DistanceEngine.google_maps_disabled = True
            return None
        el = data["rows"][0]["elements"][0]
        if el["status"] != "OK":
            return None
        return (round(el["distance"]["value"] / 1000, 2),
                max(1, int(el["duration"]["value"] / 60)))
    except Exception:
        return None


def find_nearest_bmtc_stop(lat: float, lng: float) -> tuple[str, float]:
    from modes.bmtc.core.loader import canonical_stop_name
    try:
        from modes.bmtc.features.routing import _routes_by_stop
    except Exception:
        _routes_by_stop = {}

    best_stop = None
    best_score = -1.0
    best_dist = 0.0
    
    # Evaluate candidates within 1.0 km
    for norm, coords in STOP_COORDS.items():
        dist = _haversine_km(lat, lng, coords["latitude"], coords["longitude"])
        if dist > 1.0:
            continue
        
        norm_key = norm.strip().lower()
        route_count = len(_routes_by_stop.get(norm_key, []))
        
        # Scoring function: weight route count heavily while penalizing distance
        score = (route_count + 0.1) / (1.0 + dist * 2.0)
        
        if score > best_score:
            best_score = score
            best_stop = canonical_stop_name(norm)
            best_dist = dist
            
    if best_stop:
        return best_stop, best_dist

    # Fallback to absolute nearest stop
    min_dist = float('inf')
    best_stop = None
    for norm, coords in STOP_COORDS.items():
        dist = _haversine_km(lat, lng, coords["latitude"], coords["longitude"])
        if dist < min_dist:
            min_dist = dist
            best_stop = canonical_stop_name(norm)
    return best_stop, min_dist


_METRO_COORDS_CACHE = {}


def find_nearest_metro_station(lat: float, lng: float) -> tuple[str, float]:
    global _METRO_COORDS_CACHE
    if not _METRO_COORDS_CACHE:
        for station in _metro_stations:
            coords = get_stop_coords(station)
            if coords:
                _METRO_COORDS_CACHE[station] = coords
    
    best_station = None
    min_dist = float('inf')
    for station, coords in _METRO_COORDS_CACHE.items():
        dist = _haversine_km(lat, lng, coords[0], coords[1])
        if dist < min_dist:
            min_dist = dist
            best_station = station
    if not best_station and _metro_stations:
        best_station = _metro_stations[0]
        min_dist = 0.0
    return best_station, min_dist


def _shift_time_str(time_str: str, offset_mins: int) -> str:
    try:
        h, m = map(int, time_str.split(":"))
        dt = datetime.today().replace(hour=h, minute=m) + timedelta(minutes=offset_mins)
        return dt.strftime("%H:%M")
    except Exception:
        return time_str




# ══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════════

class JourneyRequest(BaseModel):
    source:      str
    destination: str
    time:        Optional[str] = None   # "HH:MM" or None → now
    preference:  Optional[str] = "cost" # cost | time | convenience

class AllBusesRequest(BaseModel):
    source:      str
    destination: str
    time:        Optional[str] = None

class CompareRequest(BaseModel):
    source:      str
    destination: str
    time:        Optional[str] = None
    preference:  Optional[str] = "cost"   # cost | time | convenience
    vehicle:     Optional[str] = None     # personal vehicle name

class CabRequest(BaseModel):
    src_lat:  float
    src_lng:  float
    dst_lat:  float
    dst_lng:  float
    time:     Optional[str] = None
    provider: Optional[str] = None        # None → all providers
    weather:  Optional[str] = "clear"

class VehicleRequest(BaseModel):
    vehicle:     str
    source_lat:  float
    source_lng:  float
    dest_lat:    float
    dest_lng:    float

class VehicleSearchRequest(BaseModel):
    query: str

class StopCoordsRequest(BaseModel):
    stops: list[str]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_time(t: str | None) -> datetime:
    if not t:
        return normalize_search_start_time(datetime.now())
    try:
        h, m = map(int, t.split(":"))
        dt = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        return normalize_search_start_time(dt)
    except Exception:
        return normalize_search_start_time(datetime.now())


def _fmt(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance (no road factor)."""
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _haversine_road_km(lat1, lon1, lat2, lon2) -> float:
    """Straight-line × 1.3 road factor."""
    return _haversine_km(lat1, lon1, lat2, lon2) * 1.3


def _google_road_distance(src_lat, src_lng, dst_lat, dst_lng) -> tuple[float, float] | None:
    """Returns (distance_km, duration_min) via Google Maps, or None."""
    from modes.cab.engines.distance_engine import DistanceEngine
    if DistanceEngine.google_maps_disabled:
        return None
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not key:
        return None
    try:
        import requests as _req
        resp = _req.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={"origins":       f"{src_lat},{src_lng}",
                    "destinations":  f"{dst_lat},{dst_lng}",
                    "mode":          "driving",
                    "key":           key},
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "REQUEST_DENIED":
            print("Google Maps Road API failed: REQUEST_DENIED. Disabling Google Maps.")
            DistanceEngine.google_maps_disabled = True
            return None
        el = data["rows"][0]["elements"][0]
        if el["status"] != "OK":
            return None
        return (round(el["distance"]["value"] / 1000, 2),
                round(el["duration"]["value"] / 60, 1))
    except Exception:
        return None


# ── Fallback cab/car estimates (no coordinates needed) ────────────────────────

def _cab_estimate(src: str, dst: str, dep_time: datetime) -> dict:
    """Rough cab estimate using distance heuristic."""
    est_km   = 18.0
    est_min  = 38
    est_fare = max(80, int(est_km * 12))
    arr      = dep_time + timedelta(minutes=est_min + 5)
    return {
        "available": True, "mode": "cab",
        "time": est_min, "cost": est_fare, "cost_max": est_fare + 30,
        "transfers": 0, "distance": est_km,
        "departure": _fmt(dep_time), "arrival": _fmt(arr),
        "segments": [{
            "route": "Direct", "type": "cab",
            "from": src, "to": dst,
            "departure": _fmt(dep_time), "arrival": _fmt(arr),
            "duration": est_min, "fare": est_fare, "distance": est_km,
            "stops": [src, dst],
        }],
        "guide": [
            {"step": 1, "icon": "cab",  "text": "Request Ola / Uber", "duration": "~5 min"},
            {"step": 2, "icon": "car",  "text": f"Direct ride to {dst}",
             "duration": f"{est_min} min", "detail": f"₹{est_fare} est. · Door-to-door"},
        ],
    }


def _car_estimate(src: str, dst: str, dep_time: datetime, src_coords=None, dst_coords=None) -> dict:
    """Self-drive estimate using actual coordinates / distance if available, otherwise heuristic."""
    distance_km = None
    if src_coords and dst_coords:
        if _NAMMA_OK and _ny_distance:
            try:
                road = _ny_distance.get_distance(
                    {"latitude": src_coords[0], "longitude": src_coords[1]},
                    {"latitude": dst_coords[0], "longitude": dst_coords[1]}
                )
                distance_km = road["distance_km"]
            except Exception:
                pass
        else:
            road = _google_road_distance(src_coords[0], src_coords[1], dst_coords[0], dst_coords[1])
            if road:
                distance_km = road[0]

        if not distance_km:
            distance_km = _haversine_km(src_coords[0], src_coords[1], dst_coords[0], dst_coords[1]) * 1.3

    if distance_km is None:
        distance_km = 17.0

    est_km = round(distance_km, 2)
    avg_speed_kmh = 25.0
    est_min = max(5, int((distance_km / avg_speed_kmh) * 60))

    # Standard Petrol Car parameters: mileage = 15.0 km/L, fuel price = 102.94 INR/L
    fuel_needed = distance_km / 15.0
    fuel = int(fuel_needed * 102.94)
    parking = 30
    est_fare = fuel + parking
    arr = dep_time + timedelta(minutes=est_min)

    return {
        "available": True, "mode": "car",
        "time": est_min, "cost": est_fare,
        "transfers": 0, "distance": est_km,
        "departure": _fmt(dep_time), "arrival": _fmt(arr),
        "segments": [{
            "route": "Via ORR / Main Roads", "type": "car",
            "from": src, "to": dst,
            "departure": _fmt(dep_time), "arrival": _fmt(arr),
            "duration": est_min, "fare": est_fare, "distance": est_km,
            "stops": [src, dst],
        }],
        "guide": [
            {"step": 1, "icon": "car",
             "text": f"Drive to {dst} via ORR / Main Roads",
             "duration": f"{est_min} min",
             "detail": f"₹{fuel} fuel + ₹{parking} parking est."},
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# METRO ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/metro/plan")
def metro_plan(req: JourneyRequest):
    from shared.utils import resolve_stop_name

    dep_time = _parse_time(req.time)

    # 1. Parse source coordinate / resolve station
    src_coord = parse_coords(req.source)
    if src_coord:
        start_lat, start_lng = src_coord
        source, start_walk_dist = find_nearest_metro_station(start_lat, start_lng)
        walk_metrics = _google_walk_distance(start_lat, start_lng, *get_stop_coords(source))
        if walk_metrics:
            start_walk_dist, start_walk_mins = walk_metrics
        else:
            start_walk_mins = max(1, int(start_walk_dist * 12.5))
    else:
        source = resolve_stop_name(req.source, "metro", metro_stations=_metro_stations)
        is_valid_source = any(s.lower() == source.lower() for s in _metro_stations)
        if not is_valid_source:
            coords = get_stop_coords(req.source)
            if coords:
                start_lat, start_lng = coords
                source, start_walk_dist = find_nearest_metro_station(start_lat, start_lng)
                walk_metrics = _google_walk_distance(start_lat, start_lng, *get_stop_coords(source))
                if walk_metrics:
                    start_walk_dist, start_walk_mins = walk_metrics
                else:
                    start_walk_mins = max(1, int(start_walk_dist * 12.5))
                src_coord = coords
            else:
                start_walk_dist = 0.0
                start_walk_mins = 0
        else:
            start_walk_dist = 0.0
            start_walk_mins = 0

    # 2. Parse destination coordinate / resolve station
    dst_coord = parse_coords(req.destination)
    if dst_coord:
        dest_lat, dest_lng = dst_coord
        destination, end_walk_dist = find_nearest_metro_station(dest_lat, dest_lng)
        walk_metrics = _google_walk_distance(*get_stop_coords(destination), dest_lat, dest_lng)
        if walk_metrics:
            end_walk_dist, end_walk_mins = walk_metrics
        else:
            end_walk_mins = max(1, int(end_walk_dist * 12.5))
    else:
        destination = resolve_stop_name(req.destination, "metro", metro_stations=_metro_stations)
        is_valid_dest = any(s.lower() == destination.lower() for s in _metro_stations)
        if not is_valid_dest:
            coords = get_stop_coords(req.destination)
            if coords:
                dest_lat, dest_lng = coords
                destination, end_walk_dist = find_nearest_metro_station(dest_lat, dest_lng)
                walk_metrics = _google_walk_distance(*get_stop_coords(destination), dest_lat, dest_lng)
                if walk_metrics:
                    end_walk_dist, end_walk_mins = walk_metrics
                else:
                    end_walk_mins = max(1, int(end_walk_dist * 12.5))
                dst_coord = coords
            else:
                end_walk_dist = 0.0
                end_walk_mins = 0
        else:
            end_walk_dist = 0.0
            end_walk_mins = 0

    try:
        result = _metro_planner.plan_journey(source, destination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Transit leg durations and timings
    current_time = dep_time + timedelta(minutes=start_walk_mins)
    
    segments = []
    
    # Prepend starting walk segment if coordinate input
    if src_coord:
        segments.append({
            "route": "Walk",
            "type": "walk",
            "from": req.source,
            "to": source + " Metro Station",
            "departure": _fmt(dep_time),
            "arrival": _fmt(current_time),
            "duration": start_walk_mins,
            "fare": 0,
            "distance": round(start_walk_dist, 2),
            "stops": [req.source, source + " Metro Station"]
        })

    for leg in result["route"]["legs"]:
        line_stations = _metro_planner.routing_engine.lines[leg["line"]]
        fi = line_stations.index(leg["from"])
        ti = line_stations.index(leg["to"])
        lo, hi    = min(fi, ti), max(fi, ti)
        leg_stops = line_stations[lo:hi + 1]
        if ti < fi:
            leg_stops = list(reversed(leg_stops))

        leg_dur  = leg.get("stations_crossed", len(leg_stops) - 1) * 2
        leg_fare = round(result["fare"]["token"] / len(result["route"]["legs"]), 0)
        
        leg_start = current_time
        leg_end = current_time + timedelta(minutes=leg_dur)
        
        segments.append({
            "route":     f"{leg['line']} Line",
            "type":      "metro",
            "from":      leg["from"] + " Metro Station" if not leg["from"].endswith(" Metro Station") else leg["from"],
            "to":        leg["to"] + " Metro Station" if not leg["to"].endswith(" Metro Station") else leg["to"],
            "departure": _fmt(leg_start),
            "arrival":   _fmt(leg_end),
            "duration":  leg_dur,
            "fare":      int(leg_fare),
            "distance":  round(leg.get("stations_crossed", 1) * 1.2, 1),
            "stops":     [s + " Metro Station" if not s.endswith(" Metro Station") else s for s in leg_stops],
        })
        current_time = leg_end

    # Append ending walk segment if coordinate input
    if dst_coord:
        end_walk_start = current_time
        end_walk_end = current_time + timedelta(minutes=end_walk_mins)
        segments.append({
            "route": "Walk",
            "type": "walk",
            "from": destination + " Metro Station",
            "to": req.destination,
            "departure": _fmt(end_walk_start),
            "arrival": _fmt(end_walk_end),
            "duration": end_walk_mins,
            "fare": 0,
            "distance": round(end_walk_dist, 2),
            "stops": [destination + " Metro Station", req.destination]
        })
        current_time = end_walk_end

    # Build the guide timeline
    guide = []
    step_num = 1
    
    # 1. Starting walk step
    if src_coord:
        station_coords = get_stop_coords(source + " Metro Station")
        nav_url = f"https://www.google.com/maps/dir/?api=1&origin={start_lat},{start_lng}&destination={station_coords[0]},{station_coords[1]}&travelmode=walking" if station_coords else None
        guide.append({
            "step": step_num,
            "icon": "walk",
            "text": f"Walk to {source} Metro Station",
            "duration": f"{start_walk_mins} min",
            "detail": f"{round(start_walk_dist, 2)} km",
            "nav_url": nav_url
        })
    else:
        station_coords = get_stop_coords(source + " Metro Station")
        nav_url = f"https://www.google.com/maps/dir/?api=1&destination={station_coords[0]},{station_coords[1]}&travelmode=walking" if station_coords else None
        guide.append({
            "step": step_num,
            "icon": "walk",
            "text": f"Walk to {source} Metro Station",
            "duration": "5–8 min",
            "nav_url": nav_url
        })
    step_num += 1

    # 2. Transit instructions
    for inst in result["instructions"]:
        icon = "metro" if "Board" in inst else "transfer" if "Change" in inst else "walk"
        # Format station names inside inst to append " Metro Station"
        formatted_inst = inst
        for station in _metro_stations:
            import re
            pattern = re.compile(rf"\b{re.escape(station)}\b(?! Metro Station)", re.IGNORECASE)
            formatted_inst = pattern.sub(f"{station} Metro Station", formatted_inst)
            
        guide.append({
            "step": step_num,
            "icon": icon,
            "text": formatted_inst,
            "duration": ""
        })
        step_num += 1

    # 3. Ending walk step
    if dst_coord:
        station_coords = get_stop_coords(destination + " Metro Station")
        nav_url = f"https://www.google.com/maps/dir/?api=1&origin={station_coords[0]},{station_coords[1]}&destination={dest_lat},{dest_lng}&travelmode=walking" if station_coords else None
        guide.append({
            "step": step_num,
            "icon": "walk",
            "text": f"Walk to destination",
            "duration": f"{end_walk_mins} min",
            "detail": f"{round(end_walk_dist, 2)} km",
            "nav_url": nav_url
        })
    else:
        station_coords = get_stop_coords(destination + " Metro Station")
        nav_url = f"https://www.google.com/maps/dir/?api=1&destination={station_coords[0]},{station_coords[1]}&travelmode=walking" if station_coords else None
        guide.append({
            "step": step_num,
            "icon": "walk",
            "text": f"Walk to {destination} Metro Station",
            "duration": "3–5 min",
            "nav_url": nav_url
        })

    total_mins = start_walk_mins + result["estimated_time"]["minutes"] + end_walk_mins
    total_dist = round(start_walk_dist + (result["stations_crossed"] * 1.2) + end_walk_dist, 1)

    return {
        "available":        True,
        "mode":             "metro",
        "time":             total_mins,
        "cost":             int(result["fare"]["token"]),
        "cost_smart":       int(result["fare"]["smart_card"]),
        "transfers":        len(result["route"]["interchanges"]),
        "distance":         total_dist,
        "departure":        _fmt(dep_time),
        "arrival":          _fmt(dep_time + timedelta(minutes=total_mins)),
        "stations_crossed": result["stations_crossed"],
        "interchanges":     result["route"]["interchanges"],
        "segments":         segments,
        "guide":            guide,
        "raw":              result,
    }


# ══════════════════════════════════════════════════════════════════════════════
# BMTC ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/bmtc/plan")
@app.post("/api/bmtc/plan")
def bmtc_plan(req: JourneyRequest, max_options: int = 8):
    from shared.utils import resolve_stop_name

    dep_time = _parse_time(req.time)

    # 1. Parse source coordinate / resolve stop
    src_coord = parse_coords(req.source)
    if src_coord:
        start_lat, start_lng = src_coord
        source, start_walk_dist = find_nearest_bmtc_stop(start_lat, start_lng)
        walk_metrics = _google_walk_distance(start_lat, start_lng, *get_stop_coords(source))
        if walk_metrics:
            start_walk_dist, start_walk_mins = walk_metrics
        else:
            start_walk_mins = max(1, int(start_walk_dist * 12.5))
    else:
        source = resolve_stop_name(req.source, "bmtc", bmtc_stops=ALL_STOPS)
        is_valid_source = any(s.lower() == source.lower() for s in ALL_STOPS)
        if not is_valid_source:
            coords = get_stop_coords(req.source)
            if coords:
                start_lat, start_lng = coords
                source, start_walk_dist = find_nearest_bmtc_stop(start_lat, start_lng)
                walk_metrics = _google_walk_distance(start_lat, start_lng, *get_stop_coords(source))
                if walk_metrics:
                    start_walk_dist, start_walk_mins = walk_metrics
                else:
                    start_walk_mins = max(1, int(start_walk_dist * 12.5))
                src_coord = coords
            else:
                start_walk_dist = 0.0
                start_walk_mins = 0
        else:
            start_walk_dist = 0.0
            start_walk_mins = 0

    src_norm = source.strip().lower()

    # 2. Parse destination coordinate / resolve stop
    dst_coord = parse_coords(req.destination)
    if dst_coord:
        dest_lat, dest_lng = dst_coord
        destination, end_walk_dist = find_nearest_bmtc_stop(dest_lat, dest_lng)
        walk_metrics = _google_walk_distance(*get_stop_coords(destination), dest_lat, dest_lng)
        if walk_metrics:
            end_walk_dist, end_walk_mins = walk_metrics
        else:
            end_walk_mins = max(1, int(end_walk_dist * 12.5))
    else:
        destination = resolve_stop_name(req.destination, "bmtc", bmtc_stops=ALL_STOPS)
        is_valid_dest = any(s.lower() == destination.lower() for s in ALL_STOPS)
        if not is_valid_dest:
            coords = get_stop_coords(req.destination)
            if coords:
                dest_lat, dest_lng = coords
                destination, end_walk_dist = find_nearest_bmtc_stop(dest_lat, dest_lng)
                walk_metrics = _google_walk_distance(*get_stop_coords(destination), dest_lat, dest_lng)
                if walk_metrics:
                    end_walk_dist, end_walk_mins = walk_metrics
                else:
                    end_walk_mins = max(1, int(end_walk_dist * 12.5))
                dst_coord = coords
            else:
                end_walk_dist = 0.0
                end_walk_mins = 0
        else:
            end_walk_dist = 0.0
            end_walk_mins = 0

    dst_norm = destination.strip().lower()

    try:
        direct, transfers = get_all_buses_comprehensive(
            src_norm, dst_norm,
            max_transfer_options=max_options,
            departure_dt=dep_time,
            preference=req.preference
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not direct and not transfers:
        raise HTTPException(status_code=404,
                             detail="No BMTC route found between these stops")

    # Choose whether to recommend a direct bus or transfer option based on preference:
    use_direct = True
    if not direct:
        use_direct = False
    elif not transfers:
        use_direct = True
    else:
        # Both are available, decide based on preference
        pref = req.preference or "cost"
        if pref == "time":
            # For time (fastest), choose the one with the minimum total time
            direct_time = direct[0].get("total_time", 9999)
            transfer_time = transfers[0].get("total_time", 9999)
            if transfer_time < direct_time:
                use_direct = False
        elif pref == "cost":
            # For cost (cheapest), choose the one with the minimum cost
            direct_cost = direct[0].get("fare", 9999)
            transfer_cost = transfers[0].get("total_fare", 9999)
            if transfer_cost < direct_cost:
                use_direct = False

    if use_direct:
        best = direct[0]
        transit_mins = best.get("duration") or 30
        waiting_time = best.get("waiting_time", 0)
        total_mins = start_walk_mins + transit_mins + end_walk_mins + waiting_time
        cost = best.get("fare") or 20
        dist = start_walk_dist + (best.get("distance") or 10.0) + end_walk_dist

        segments = []
        
        # 1. Start walk
        if src_coord:
            segments.append({
                "route": "Walk",
                "type": "walk",
                "from": req.source,
                "to": source,
                "departure": _fmt(dep_time),
                "arrival": _fmt(dep_time + timedelta(minutes=start_walk_mins)),
                "duration": start_walk_mins,
                "fare": 0,
                "distance": round(start_walk_dist, 2),
                "stops": [req.source, source]
            })

        # 2. Bus segment
        bus_start = dep_time + timedelta(minutes=start_walk_mins) + timedelta(minutes=waiting_time)
        bus_end = bus_start + timedelta(minutes=transit_mins)
        segments.append({
            "route":     best["route"],
            "type":      "bmtc",
            "from":      source,
            "to":        destination,
            "departure": _fmt(bus_start),
            "arrival":   _fmt(bus_end),
            "duration":  transit_mins,
            "fare":      int(cost),
            "distance":  round(best.get("distance") or 10.0, 1),
            "stops":     best.get("stops") or [source, destination],
        })

        # 3. End walk
        if dst_coord:
            segments.append({
                "route": "Walk",
                "type": "walk",
                "from": destination,
                "to": req.destination,
                "departure": _fmt(bus_end),
                "arrival": _fmt(bus_end + timedelta(minutes=end_walk_mins)),
                "duration": end_walk_mins,
                "fare": 0,
                "distance": round(end_walk_dist, 2),
                "stops": [destination, req.destination]
            })

        guide = []
        step_num = 1
        
        # Start walk guide
        if src_coord:
            stop_coords = get_stop_coords(source)
            nav_url = f"https://www.google.com/maps/dir/?api=1&origin={start_lat},{start_lng}&destination={stop_coords[0]},{stop_coords[1]}&travelmode=walking" if stop_coords else None
            guide.append({
                "step": step_num, "icon": "walk",
                "text": f"Walk to {source} bus stop",
                "duration": f"{start_walk_mins} min",
                "detail": f"{round(start_walk_dist, 2)} km",
                "nav_url": nav_url
            })
        else:
            stop_coords = get_stop_coords(source)
            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={stop_coords[0]},{stop_coords[1]}&travelmode=walking" if stop_coords else None
            guide.append({
                "step": step_num, "icon": "walk",
                "text": f"Walk to {source} bus stop", "duration": "3–5 min",
                "nav_url": nav_url
            })
        step_num += 1

        # Board bus guide
        guide.append({
            "step": step_num, "icon": "bus",
            "text": f"Board Bus {best['route']} (Direct)",
            "duration": f"{transit_mins} min",
            "detail": f"₹{int(cost)} · Direct"
        })
        step_num += 1

        # End walk guide
        if dst_coord:
            stop_coords = get_stop_coords(destination)
            nav_url = f"https://www.google.com/maps/dir/?api=1&origin={stop_coords[0]},{stop_coords[1]}&destination={dest_lat},{dest_lng}&travelmode=walking" if stop_coords else None
            guide.append({
                "step": step_num, "icon": "walk",
                "text": f"Walk to destination",
                "duration": f"{end_walk_mins} min",
                "detail": f"{round(end_walk_dist, 2)} km",
                "nav_url": nav_url
            })
        else:
            stop_coords = get_stop_coords(destination)
            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={stop_coords[0]},{stop_coords[1]}&travelmode=walking" if stop_coords else None
            guide.append({
                "step": step_num, "icon": "walk",
                "text": f"Arrive at {destination}", "duration": "~1 min",
                "nav_url": nav_url
            })

        return {
            "available":  True, "mode": "bmtc",
            "time":       total_mins,
            "cost":       int(cost),
            "transfers":  0, "distance": round(dist, 1),
            "departure":  _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_mins)),
            "waiting_time": best.get("waiting_time", 0),
            "all_direct": [b["route"] for b in direct[:8]],
            "segments": segments,
            "guide":     guide,
        }

    # Transfer option
    opt  = transfers[0]
    segs = opt.get("segment_times", [])
    
    transit_mins = opt.get("total_time", 45)
    total_mins = start_walk_mins + transit_mins + end_walk_mins
    total_dist = start_walk_dist + opt.get("distance", 12.0) + end_walk_dist

    ui_segs  = []
    
    # Prepend starting walk segment
    if src_coord:
        ui_segs.append({
            "route": "Walk",
            "type": "walk",
            "from": req.source,
            "to": source,
            "departure": _fmt(dep_time),
            "arrival": _fmt(dep_time + timedelta(minutes=start_walk_mins)),
            "duration": start_walk_mins,
            "fare": 0,
            "distance": round(start_walk_dist, 2),
            "stops": [req.source, source]
        })

    # Shift transit segments
    for i, (seg, st) in enumerate(zip(opt["segments"], segs)):
        st_duration = st.get("duration", 20)
        
        ui_segs.append({
            "route":     seg[0], "type": "bmtc",
            "from":      seg[1], "to": seg[2],
            "departure": st.get("departure"), "arrival": st.get("arrival"),
            "duration":  st_duration,
            "fare":      int(st.get("fare", 15)),
            "distance":  st.get("distance", 5.0),
            "stops":     list(seg[3]) if len(seg) > 3 else [seg[1], seg[2]],
        })

    final_transit_arrival = dep_time + timedelta(minutes=start_walk_mins + transit_mins)

    # Append ending walk segment
    if dst_coord:
        ui_segs.append({
            "route": "Walk",
            "type": "walk",
            "from": destination,
            "to": req.destination,
            "departure": _fmt(final_transit_arrival),
            "arrival": _fmt(final_transit_arrival + timedelta(minutes=end_walk_mins)),
            "duration": end_walk_mins,
            "fare": 0,
            "distance": round(end_walk_dist, 2),
            "stops": [destination, req.destination]
        })
        final_arrival = final_transit_arrival + timedelta(minutes=end_walk_mins)
    else:
        final_arrival = final_transit_arrival

    # Build transfer guide
    guide = []
    step_num = 1
    
    # 1. Starting walk
    if src_coord:
        stop_coords = get_stop_coords(source)
        nav_url = f"https://www.google.com/maps/dir/?api=1&origin={start_lat},{start_lng}&destination={stop_coords[0]},{stop_coords[1]}&travelmode=walking" if stop_coords else None
        guide.append({
            "step": step_num, "icon": "walk",
            "text": f"Walk to {source} bus stop",
            "duration": f"{start_walk_mins} min",
            "detail": f"{round(start_walk_dist, 2)} km",
            "nav_url": nav_url
        })
    else:
        stop_coords = get_stop_coords(source)
        nav_url = f"https://www.google.com/maps/dir/?api=1&destination={stop_coords[0]},{stop_coords[1]}&travelmode=walking" if stop_coords else None
        guide.append({
            "step": step_num, "icon": "walk",
            "text": f"Walk to {source} bus stop", "duration": "3–5 min",
            "nav_url": nav_url
        })
    step_num += 1

    # 2. Transit boardings & transfers
    for i, (seg, st) in enumerate(zip(opt["segments"], segs)):
        st_duration = st.get("duration", 20)
        guide.append({
            "step": step_num, "icon": "bus",
            "text": f"Board Bus {seg[0]}",
            "duration": f"{st_duration} min",
            "detail": f"₹{int(st.get('fare', 15))}"
        })
        step_num += 1
        if i < len(opt["segments"]) - 1:
            guide.append({
                "step": step_num, "icon": "transfer",
                "text": f"Transfer at {seg[2]}", "duration": "3–5 min"
            })
            step_num += 1

    # 3. Final walk
    if dst_coord:
        stop_coords = get_stop_coords(destination)
        nav_url = f"https://www.google.com/maps/dir/?api=1&origin={stop_coords[0]},{stop_coords[1]}&destination={dest_lat},{dest_lng}&travelmode=walking" if stop_coords else None
        guide.append({
            "step": step_num, "icon": "walk",
            "text": f"Walk to destination",
            "duration": f"{end_walk_mins} min",
            "detail": f"{round(end_walk_dist, 2)} km",
            "nav_url": nav_url
        })
    else:
        stop_coords = get_stop_coords(destination)
        nav_url = f"https://www.google.com/maps/dir/?api=1&destination={stop_coords[0]},{stop_coords[1]}&travelmode=walking" if stop_coords else None
        guide.append({
            "step": step_num, "icon": "walk",
            "text": f"Arrive at {destination}", "duration": "~1 min",
            "nav_url": nav_url
        })

    return {
        "available": True, "mode": "bmtc",
        "time":      total_mins,
        "cost":      int(opt.get("total_fare", 30)),
        "transfers": opt.get("transfers", 1),
        "distance":  round(total_dist, 1),
        "departure": _fmt(dep_time),
        "arrival":   _fmt(final_arrival),
        "waiting_time": opt.get("waiting_time", 0),
        "segments":  ui_segs,
        "guide":     guide,
    }


@app.post("/api/bmtc/all-buses")
def bmtc_all_buses(req: AllBusesRequest):
    from shared.utils import resolve_stop_name
    
    dep_time = _parse_time(req.time)

    # 1. Parse source coordinate / resolve stop
    src_coord = parse_coords(req.source)
    if src_coord:
        start_lat, start_lng = src_coord
        source, _ = find_nearest_bmtc_stop(start_lat, start_lng)
    else:
        source = resolve_stop_name(req.source, "bmtc", bmtc_stops=ALL_STOPS)

    src_norm = source.strip().lower()

    # 2. Parse destination coordinate / resolve stop
    dst_coord = parse_coords(req.destination)
    if dst_coord:
        dest_lat, dest_lng = dst_coord
        destination, _ = find_nearest_bmtc_stop(dest_lat, dest_lng)
    else:
        destination = resolve_stop_name(req.destination, "bmtc", bmtc_stops=ALL_STOPS)

    dst_norm = destination.strip().lower()

    try:
        direct, transfers = get_all_buses_comprehensive(src_norm, dst_norm, departure_dt=dep_time)
        return {
            "direct": direct,
            "transfer": transfers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bmtc/routes")
def bmtc_all_routes(q: str = ""):
    """Return all route numbers (optionally filtered by prefix/substring) for autocomplete."""
    all_routes = sorted(set(
        r.replace("_REV", "") for r in _route_trips.keys()
    ))
    if q.strip():
        q_upper = q.strip().upper()
        filtered = [r for r in all_routes if q_upper in r.upper()]
        return {"routes": filtered[:40]}
    return {"routes": all_routes[:200]}


@app.get("/api/bmtc/route-search")
def bmtc_route_search(route: str):
    route_clean = route.strip()
    stops = get_route_stop_names(route_clean)
    rev_stops = get_route_stop_names(route_clean + "_REV")
    
    if not stops and rev_stops:
        stops, rev_stops = rev_stops, []
        route_clean = route_clean + "_REV"
            
    if not stops:
        raise HTTPException(status_code=404, detail=f"Route '{route}' not found")
        
    base_route = route_clean.replace("_REV", "")
    trips = _route_trips.get(base_route, 0)
    
    sched = {}
    try:
        sched_est = estimate_route_schedule(route_clean)
        if sched_est:
            sched = {
                "departure": sched_est.get("departure"),
                "arrival": sched_est.get("arrival")
            }
    except Exception:
        pass
        
    return {
        "route": base_route,
        "stop_count": len(stops),
        "trips": trips,
        "schedule": sched,
        "stops": stops,
        "reverse_stops": rev_stops
    }


@app.get("/api/timetable/metro")
def metro_timetable(source: Optional[str] = None, time: Optional[str] = None):
    general_metro = [
        {
            "line": "Purple Line",
            "color": "#800080",
            "first_train": "05:00",
            "last_train": "23:00",
            "peak_frequency": "8 min",
            "non_peak_frequency": "10 min",
            "peak_hours": "07:30 - 10:30, 16:30 - 19:30"
        },
        {
            "line": "Green Line",
            "color": "#008000",
            "first_train": "05:00",
            "last_train": "23:00",
            "peak_frequency": "8 min",
            "non_peak_frequency": "10 min",
            "peak_hours": "07:30 - 10:30, 16:30 - 19:30"
        },
        {
            "line": "Yellow Line",
            "color": "#E6B800",
            "first_train": "05:00",
            "last_train": "23:00",
            "peak_frequency": "15 min",
            "non_peak_frequency": "20 min",
            "peak_hours": "07:30 - 10:30, 16:30 - 19:30"
        }
    ]
    
    if not source or not source.strip():
        return {"metro": general_metro}

    # 1. Resolve nearest metro station name
    from shared.utils import resolve_stop_name
    src_coord = parse_coords(source)
    if src_coord:
        start_lat, start_lng = src_coord
        station_base, _ = find_nearest_metro_station(start_lat, start_lng)
    else:
        station_base = resolve_stop_name(source, "metro", metro_stations=_metro_stations)
        is_valid = any(s.lower() == station_base.lower() for s in _metro_stations)
        if not is_valid:
            coords = get_stop_coords(source)
            if coords:
                start_lat, start_lng = coords
                station_base, _ = find_nearest_metro_station(start_lat, start_lng)
            else:
                return {"metro": general_metro, "resolved_station": None}

    # Format full station name (matching frontend display)
    station_full = station_base + " Metro Station" if not station_base.endswith(" Metro Station") else station_base
    
    # 2. Get line of this station
    stations_lookup = _metro_planner.routing_engine.stations
    lookup_name = station_full.replace(" Metro Station", "").strip()
    station_info = stations_lookup.get(lookup_name)
    if not station_info:
        # try case-insensitive lookup
        for k, v in stations_lookup.items():
            if k.lower() == lookup_name.lower():
                station_info = v
                break

    line_name = "Purple"
    line_color = "#800080"
    if station_info:
        line_name = station_info["line"]
        if line_name == "Green":
            line_color = "#008000"
        elif line_name == "Yellow":
            line_color = "#E6B800"

    # 3. Generate departures starting from time (or current time)
    dep_time = _parse_time(time)
    
    # Determine frequency based on peak / off-peak
    from modes.metro.engines.time_engine import TimeEngine
    te = TimeEngine()
    is_peak = te.is_peak(dep_time)
    freq = te.get_frequency(line_name, is_peak)
    
    # Generate next 8 departures
    departures = []
    import hashlib
    seed_val = int(hashlib.md5(lookup_name.encode()).hexdigest()[:4], 16)
    offset_mins = seed_val % freq
    
    start_dt = dep_time.replace(second=0, microsecond=0)
    start_day_mins = start_dt.hour * 60 + start_dt.minute
    aligned_min = ((start_day_mins - offset_mins + freq - 1) // freq) * freq + offset_mins
    
    # Operational window check (05:00 - 23:00)
    for i in range(8):
        dep_day_min = aligned_min + i * freq
        if 300 <= dep_day_min <= 1380:
            h = dep_day_min // 60
            m = dep_day_min % 60
            departures.append(f"{h:02d}:{m:02d}")
            
    return {
        "metro": general_metro,
        "resolved_station": station_full,
        "line": line_name + " Line",
        "color": line_color,
        "frequency": f"{freq} min",
        "departures": departures,
        "is_peak": is_peak
    }


@app.get("/api/bmtc/route-timetable")
def bmtc_route_timetable(route: str, stop: Optional[str] = None):
    sys.path.insert(0, _BMTC)
    try:
        from core.stops import get_route_stop_list
        from core.loader import canonical_stop_name, ALL_STOPS
        from core.gtfs import _get_gtfs, _route_departures, _stop_ids_for_norm
    finally:
        sys.path.remove(_BMTC)

    # Ensure GTFS data is loaded
    _get_gtfs()

    route_clean = route.strip()
    stop_norms = get_route_stop_list(route_clean)
    if not stop_norms:
        stop_norms = get_route_stop_list(route_clean + "_REV")
        if not stop_norms:
            raise HTTPException(status_code=404, detail=f"Route '{route}' not found")
        route_clean = route_clean + "_REV"

    base_route = route_clean.replace("_REV", "")
    route_table = _route_departures.get(base_route, {})
    
    # Filter stop norms by whether they actually have departures in the route_table
    gtfs_stops = [s for s in stop_norms if any(sid in route_table for sid in _stop_ids_for_norm(s))]
    
    departures = []
    board_stop = "Unknown"
    
    # If a stop is provided, try to match it first
    target_stop = None
    if stop:
        from shared.utils import resolve_stop_name
        resolved_stop = resolve_stop_name(stop, "bmtc", bmtc_stops=ALL_STOPS)
        if resolved_stop:
            resolved_norm = resolved_stop.strip().lower()
            if resolved_norm in stop_norms:
                target_stop = resolved_norm
            else:
                # Find closest stop norm in stop_norms to the resolved stop coordinates
                # or match name partially
                for s in stop_norms:
                    if resolved_norm in s or s in resolved_norm:
                        target_stop = s
                        break

    if target_stop and any(sid in route_table for sid in _stop_ids_for_norm(target_stop)):
        board_stop = canonical_stop_name(target_stop)
        src_ids = _stop_ids_for_norm(target_stop)
    elif gtfs_stops:
        board_stop = canonical_stop_name(gtfs_stops[0])
        src_ids = _stop_ids_for_norm(gtfs_stops[0])
    else:
        src_ids = []

    if src_ids:
        dep_times = set()
        for sid in src_ids:
            if sid in route_table:
                for dep_td, _, _ in route_table[sid]:
                    hours = int(dep_td.total_seconds() // 3600)
                    minutes = int((dep_td.total_seconds() % 3600) // 60)
                    hours = hours % 24
                    dep_times.add(f"{hours:02d}:{minutes:02d}")
        departures = sorted(list(dep_times))
        
    return {
        "route": base_route,
        "board_stop": board_stop,
        "departures": departures,
        "total_trips": len(departures)
    }


# ══════════════════════════════════════════════════════════════════════════════
# NAMMA YATRI ENGINE SETUP
# ══════════════════════════════════════════════════════════════════════════════

try:
    from modes.cab.engines.fare_engine import FareEngine as _FareEngine
    from modes.cab.engines.time_engine import TimeEngine as _TimeEngine
    from modes.cab.engines.distance_engine import DistanceEngine as _DistanceEngine
    _ny_fare   = _FareEngine(os.path.abspath(os.path.join(_HERE, "..", "database", "cab", "fare_config.json")))
    _ny_time   = _TimeEngine()
    _ny_distance = _DistanceEngine()
    print(f"Cab fare engine loaded: {list(_ny_fare.providers.keys())}")
    _NAMMA_OK  = True
except Exception as _e:
    import traceback
    traceback.print_exc()
    print(f"Cab fare engine not loaded ({_e}) — cab estimates will use fallback")
    _ny_fare  = None
    _ny_time  = None
    _ny_distance = None
    _NAMMA_OK = False


# ══════════════════════════════════════════════════════════════════════════════
# CAB / AUTO / BIKE PROVIDER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _generic_cab_estimates(provider_key: str, provider_name: str, src_lat, src_lng, dst_lat, dst_lng, dep_time, weather: str = "clear") -> list[dict]:
    if _NAMMA_OK:
        try:
            road = _ny_distance.get_distance(
                {"latitude": src_lat, "longitude": src_lng},
                {"latitude": dst_lat, "longitude": dst_lng}
            )
            dist_km  = road["distance_km"]
            osrm_min = road["duration_min"]
        except Exception as e:
            print(f"DistanceEngine failed: {e}, using haversine fallback")
            dist_km  = _haversine_road_km(src_lat, src_lng, dst_lat, dst_lng)
            osrm_min = dist_km / 30 * 60
    else:
        road = _google_road_distance(src_lat, src_lng, dst_lat, dst_lng)
        if road:
            dist_km, osrm_min = road
        else:
            dist_km  = _haversine_road_km(src_lat, src_lng, dst_lat, dst_lng)
            osrm_min = dist_km / 30 * 60

    results = []

    if _NAMMA_OK:
        time_est  = _ny_time.estimate_duration(osrm_min, dist_km, dep_time)
        travel_min = time_est["minutes"]
        all_fares = _ny_fare.get_all_fares_for_provider(provider_key, dist_km, travel_min, dep_time, weather)

        for fare in all_fares:
            vname = fare["vehicle"].lower()
            # Determine vehicle sub-type for frontend filtering
            if fare.get("parcel"):
                vtype = "parcel"
            elif fare.get("rental"):
                vtype = "rental"
            elif fare.get("pet"):
                vtype = "pet"
            elif fare.get("book_any"):
                vtype = "book_any"
            elif "auto" in vname:
                vtype = "auto"
            elif "scooty" in vname or "scooter" in vname:
                vtype = "scooty"
            elif fare.get("saver") or "saver" in vname:
                vtype = "saver"
            elif "bike" in vname or "moto" in vname:
                vtype = "bike"
            elif fare.get("black"):
                vtype = "black"
            elif "priority" in vname:
                vtype = "priority"
            else:
                vtype = "cab"

            key = fare["vehicle"].lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
            arr = dep_time + timedelta(minutes=5 + travel_min)
            results.append({
                "provider":      provider_name, "provider_key": provider_key,
                "vehicle_key":   key,
                "vehicle_name":  fare["vehicle"],
                "description":   fare["description"],
                "capacity":      fare["capacity"],
                "icon":          fare["icon"],
                "vtype":         vtype,
                "available":     fare.get("available", True), "mode": "cab",
                "is_vehicle_available": fare.get("available", True),
                "rental":        fare.get("rental", False),
                "parcel":        fare.get("parcel", False),
                "pet":           fare.get("pet", False),
                "saver":         fare.get("saver", False),
                "black":         fare.get("black", False),
                "book_any":      fare.get("book_any", False),
                "distance":      dist_km,
                "time":          5 + travel_min,
                "cost":          fare["fare_min"],
                "cost_max":      fare["fare_max"],
                "fare_display":  fare["fare_display"],
                "transfers":     0,
                "is_night":      fare["is_night"],
                "traffic_level": time_est["traffic_level"],
                "departure":     _fmt(dep_time),
                "arrival":       _fmt(arr),
                "segments": [{
                    "route":     f"{provider_name} {fare['vehicle']}", "type": "cab",
                    "from":      f"{src_lat:.4f},{src_lng:.4f}",
                    "to":        f"{dst_lat:.4f},{dst_lng:.4f}",
                    "departure": _fmt(dep_time), "arrival": _fmt(arr),
                    "duration":  travel_min, "fare": fare["fare_min"],
                    "distance":  dist_km, "stops": [],
                }],
                "guide": [
                    {"step": 1, "icon": "cab",
                     "text": f"Book {fare['vehicle']} on {provider_name}",
                     "duration": "~2–5 min pickup"},
                    {"step": 2, "icon": "car", "text": "Ride to destination",
                     "duration": f"~{travel_min} min",
                     "detail": f"{fare['fare_display']} · {dist_km} km · {time_est['traffic_level']} traffic"},
                ],
            })
    else:
        # Fallback when engines not loaded
        travel_min = int(dist_km / 25 * 60)
        arr        = dep_time + timedelta(minutes=5 + travel_min)
        results.append({
            "provider": provider_name, "provider_key": provider_key,
            "vehicle_key": "auto", "vehicle_name": "Auto",
            "description": "Easy Commute", "capacity": 3, "icon": "🛺",
            "vtype": "auto", "available": True, "mode": "cab",
            "distance": dist_km, "time": 5 + travel_min,
            "cost": int(30 + dist_km * 16), "cost_max": int(40 + dist_km * 16),
            "fare_display": f"Rs. {int(30 + dist_km * 16)} - Rs. {int(40 + dist_km * 16)}",
            "transfers": 0, "is_night": False, "traffic_level": "moderate",
            "departure": _fmt(dep_time), "arrival": _fmt(arr),
            "segments": [], "guide": [],
        })

    return results


def _namma_yatri_estimates(src_lat, src_lng, dst_lat, dst_lng, dep_time, weather: str = "clear") -> list[dict]:
    return _generic_cab_estimates("namma_yatri", "Namma Yatri", src_lat, src_lng, dst_lat, dst_lng, dep_time, weather)


def _ola_estimates(src_lat, src_lng, dst_lat, dst_lng, dep_time, weather: str = "clear") -> list[dict]:
    return _generic_cab_estimates("ola", "Ola", src_lat, src_lng, dst_lat, dst_lng, dep_time, weather)


def _rapido_estimates(src_lat, src_lng, dst_lat, dst_lng, dep_time, weather: str = "clear") -> list[dict]:
    return _generic_cab_estimates("rapido", "Rapido", src_lat, src_lng, dst_lat, dst_lng, dep_time, weather)


def _uber_estimates(src_lat, src_lng, dst_lat, dst_lng, dep_time, weather: str = "clear") -> list[dict]:
    return _generic_cab_estimates("uber", "Uber", src_lat, src_lng, dst_lat, dst_lng, dep_time, weather)


# ── Provider registry ─────────────────────────────────────────────────────────

RIDE_PROVIDERS = {
    "namma_yatri": {"fn": _namma_yatri_estimates, "label": "Namma Yatri", "live": True},
    "ola":         {"fn": _ola_estimates,          "label": "Ola",         "live": False},
    "uber":        {"fn": _uber_estimates,          "label": "Uber",        "live": False},
    "rapido":      {"fn": _rapido_estimates,        "label": "Rapido",      "live": False},
}


# ══════════════════════════════════════════════════════════════════════════════
# CAB ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/cab/providers")
def cab_providers():
    return {
        "providers": [
            {"key": k, "label": v["label"], "live": v["live"]}
            for k, v in RIDE_PROVIDERS.items()
        ]
    }


@app.post("/api/cab/estimate")
def cab_estimate(req: CabRequest):
    """
    Returns fare estimates from all providers (or one if provider= specified).
    Groups results by provider, sorted by cost within each group.
    """
    dep_time  = _parse_time(req.time)
    providers = [req.provider] if req.provider else list(RIDE_PROVIDERS.keys())
    results   = {}

    for p in providers:
        if p not in RIDE_PROVIDERS:
            continue
        try:
            estimates = RIDE_PROVIDERS[p]["fn"](
                req.src_lat, req.src_lng, req.dst_lat, req.dst_lng, dep_time, req.weather
            )
            estimates.sort(key=lambda x: x["cost"])
            results[p] = {
                "provider":  RIDE_PROVIDERS[p]["label"],
                "live":      RIDE_PROVIDERS[p]["live"],
                "estimates": estimates,
                "cheapest":  estimates[0] if estimates else None,
            }
        except Exception as e:
            results[p] = {
                "provider":  RIDE_PROVIDERS[p]["label"],
                "error":     str(e),
                "estimates": [],
            }

    return {"results": results, "provider_count": len(results)}


# ══════════════════════════════════════════════════════════════════════════════
# PERSONAL VEHICLE COST ESTIMATION  (bug-free version from File 2)
# ══════════════════════════════════════════════════════════════════════════════

_VEHICLE_DIR = os.path.abspath(os.path.join(_HERE, "..", "database", "personal_vehicle"))
_BIKES_CSV   = os.path.join(_VEHICLE_DIR, "india_500_bike_models_master_dataset.csv")
_CARS_CSV    = os.path.join(_VEHICLE_DIR, "Car details v3.csv")

_FUEL_PRICES = {"petrol": 102.94, "diesel": 88.99, "electric": 7.00, "ev": 7.00, "cng": 75.0}

try:
    import pandas as _pd

    _bikes_df = _pd.read_csv(_BIKES_CSV)
    _bikes_df.columns = _bikes_df.columns.str.strip().str.lower()
    _bikes_df["full_name"] = _bikes_df["brand"] + " " + _bikes_df["model"]

    _cars_df = _pd.read_csv(_CARS_CSV)
    _cars_df.columns = _cars_df.columns.str.strip().str.lower()

    _all_vehicles = sorted(set(
        _bikes_df["full_name"].dropna().tolist() +
        _cars_df["name"].dropna().tolist()
    ))
    print(f"Vehicle datasets loaded: {len(_all_vehicles)} vehicles")
except Exception as _ve:
    print(f"Vehicle datasets not found ({_ve}) — /api/vehicle endpoints will return 404")
    _bikes_df     = None
    _cars_df      = None
    _all_vehicles = []


def _lookup_vehicle(name: str) -> dict | None:
    """Return {mileage, fuel, vtype, engine} or None."""
    if name.startswith("custom:"):
        try:
            parts = name.split(":", 1)[1].split("|")
            vname = parts[0].strip()
            fuel = parts[1].strip().lower()
            if fuel == "ev":
                fuel = "electric"
            efficiency = float(parts[2].strip())
            return {
                "mileage": efficiency,
                "fuel":    fuel,
                "vtype":   "EV" if fuel == "electric" else "Car",
                "engine":  "Electric" if fuel == "electric" else "ICE",
            }
        except Exception as e:
            print(f"Error parsing custom vehicle: {e}")
            return None

    if _bikes_df is not None:
        bike = _bikes_df[_bikes_df["full_name"].str.lower() == name.lower()]
        if not bike.empty:
            row = bike.iloc[0]
            return {
                "mileage": float(row.get("arai mileage (kmpl) (approx)", 40)),
                "fuel":    "petrol",
                "vtype":   "Bike",
                "engine":  str(row.get("engine segment", "")),
            }

    if _cars_df is not None:
        car = _cars_df[_cars_df["name"].str.lower() == name.lower()]
        if not car.empty:
            row   = car.iloc[0]
            raw   = str(row.get("mileage", "15 kmpl"))
            match = _re.search(r"\d+\.?\d*", raw)
            fuel  = str(row.get("fuel", "Petrol")).lower()
            return {
                "mileage": float(match.group()) if match else 15.0,
                "fuel":    fuel,
                "vtype":   "Car",
                "engine":  str(row.get("engine", "")),
            }
    return None


@app.get("/api/vehicle/list")
def vehicle_list():
    return {"vehicles": _all_vehicles, "count": len(_all_vehicles)}


@app.post("/api/vehicle/search")
def vehicle_search(req: VehicleSearchRequest):
    q       = req.query.lower()
    matches = [v for v in _all_vehicles if q in v.lower()][:20]
    return {"matches": matches}


@app.post("/api/vehicle/estimate")
def vehicle_estimate(req: VehicleRequest):
    """
    Fuel-cost estimate for a personal vehicle trip.
    Uses real mileage from datasets + haversine distance (× 1.3 road factor).
    Upgrades to real road distance if GOOGLE_MAPS_API_KEY is set.
    """
    vehicle_info = _lookup_vehicle(req.vehicle)
    if not vehicle_info:
        raise HTTPException(status_code=404,
                            detail=f"Vehicle '{req.vehicle}' not found in dataset")

    # Try DistanceEngine first, fall back to Google/Haversine
    distance_km = None
    if _NAMMA_OK and _ny_distance:
        try:
            road = _ny_distance.get_distance(
                {"latitude": req.source_lat, "longitude": req.source_lng},
                {"latitude": req.dest_lat, "longitude": req.dest_lng}
            )
            distance_km = road["distance_km"]
        except Exception:
            pass
    else:
        road = _google_road_distance(req.source_lat, req.source_lng, req.dest_lat, req.dest_lng)
        if road:
            distance_km = road[0]

    if not distance_km:
        distance_km = _haversine_km(
            req.source_lat, req.source_lng, req.dest_lat, req.dest_lng
        ) * 1.3   # road-factor correction for Bengaluru

    mileage     = vehicle_info["mileage"]
    fuel        = vehicle_info["fuel"]
    fuel_price  = _FUEL_PRICES.get(fuel, 102.94)
    fuel_needed = round(distance_km / mileage, 3)
    total_cost  = round(fuel_needed * fuel_price, 2)
    cost_per_km = round(total_cost / distance_km, 2) if distance_km else 0

    avg_speed_kmh = 25.0
    est_minutes   = int((distance_km / avg_speed_kmh) * 60)

    dep_time = _parse_time(None)
    arr_time = dep_time + timedelta(minutes=est_minutes)

    return {
        "available":   True,
        "mode":        "car",
        "vehicle":     req.vehicle,
        "vtype":       vehicle_info["vtype"],
        "fuel":        fuel.capitalize(),
        "engine":      vehicle_info.get("engine", ""),
        "distance":    round(distance_km, 2),
        "mileage":     mileage,
        "fuel_needed": fuel_needed,
        "fuel_price":  fuel_price,
        "cost":        total_cost,
        "cost_per_km": cost_per_km,
        "time":        est_minutes,
        "departure":   _fmt(dep_time),
        "arrival":     _fmt(arr_time),
        "transfers":   0,
        "segments": [{
            "route":     f"Via road ({fuel.capitalize()})", "type": "car",
            "from":      f"{req.source_lat:.4f},{req.source_lng:.4f}",
            "to":        f"{req.dest_lat:.4f},{req.dest_lng:.4f}",
            "departure": _fmt(dep_time), "arrival": _fmt(arr_time),
            "duration":  est_minutes, "fare": total_cost,
            "distance":  round(distance_km, 2), "stops": [],
        }],
        "guide": [
            {"step": 1, "icon": "car",
             "text": f"Drive {req.vehicle} ({vehicle_info['vtype']}) to destination",
             "duration": f"~{est_minutes} min",
             "detail": f"{round(distance_km, 1)} km · {fuel_needed}L {fuel} · ₹{total_cost}"},
            {"step": 2, "icon": "mappin",
             "text": "Arrive at destination", "duration": ""},
        ],
        "fuel_breakdown": {
            "fuel_type":   fuel.capitalize(),
            "price_per_l": fuel_price,
            "litres":      fuel_needed,
            "total":       total_cost,
            "per_km":      cost_per_km,
        },
    }


def multimodal_plan(source: str, destination: str, dep_time: datetime, preference: str = "cost", weather: str = "clear") -> dict:
    from multimodal.config import INTERCHANGE_POINTS
    from shared.utils import resolve_stop_name

    src_coords = get_stop_coords(source)
    dst_coords = get_stop_coords(destination)
    if not src_coords or not dst_coords:
        return {"available": False, "mode": "multimodal", "error": "Could not resolve source or destination coordinates"}

    # Check if source/dest are already valid stops
    resolved_bmtc_src = resolve_stop_name(source, "bmtc", bmtc_stops=ALL_STOPS)
    is_src_bmtc = any(s.lower() == resolved_bmtc_src.lower() for s in ALL_STOPS)
    if is_src_bmtc:
        nearest_bmtc_src = resolved_bmtc_src
        dist_bmtc_src = 0.0
    else:
        nearest_bmtc_src, dist_bmtc_src = find_nearest_bmtc_stop(src_coords[0], src_coords[1])

    resolved_bmtc_dst = resolve_stop_name(destination, "bmtc", bmtc_stops=ALL_STOPS)
    is_dst_bmtc = any(s.lower() == resolved_bmtc_dst.lower() for s in ALL_STOPS)
    if is_dst_bmtc:
        nearest_bmtc_dst = resolved_bmtc_dst
        dist_bmtc_dst = 0.0
    else:
        nearest_bmtc_dst, dist_bmtc_dst = find_nearest_bmtc_stop(dst_coords[0], dst_coords[1])

    resolved_metro_src = resolve_stop_name(source, "metro", metro_stations=_metro_stations)
    is_src_metro = any(s.lower() == resolved_metro_src.lower() for s in _metro_stations)
    if is_src_metro:
        nearest_metro_src = resolved_metro_src
        dist_metro_src = 0.0
    else:
        nearest_metro_src, dist_metro_src = find_nearest_metro_station(src_coords[0], src_coords[1])

    resolved_metro_dst = resolve_stop_name(destination, "metro", metro_stations=_metro_stations)
    is_dst_metro = any(s.lower() == resolved_metro_dst.lower() for s in _metro_stations)
    if is_dst_metro:
        nearest_metro_dst = resolved_metro_dst
        dist_metro_dst = 0.0
    else:
        nearest_metro_dst, dist_metro_dst = find_nearest_metro_station(dst_coords[0], dst_coords[1])

    def get_walk_leg(from_name: str, to_name: str, start_time: datetime) -> dict:
        fc = get_stop_coords(from_name)
        tc = get_stop_coords(to_name)
        if not fc or not tc:
            return None
        walk_metrics = _google_walk_distance(fc[0], fc[1], tc[0], tc[1])
        if walk_metrics:
            dist_km, duration_mins = walk_metrics
        else:
            dist_km = _haversine_km(fc[0], fc[1], tc[0], tc[1])
            duration_mins = max(1, int(dist_km * 12.5))
            
        # Limit walking segments to a maximum of 1.5 km in multimodal routes
        if dist_km > 1.5:
            return None
            
        arrival_time = start_time + timedelta(minutes=duration_mins)
        return {
            "route": "Walk", "type": "walk",
            "from": from_name, "to": to_name,
            "departure": _fmt(start_time), "arrival": _fmt(arrival_time),
            "duration": duration_mins, "fare": 0, "distance": round(dist_km, 2),
            "stops": [from_name, to_name]
        }

    def get_cab_leg(from_name: str, to_name: str, start_time: datetime) -> dict:
        fc = get_stop_coords(from_name)
        tc = get_stop_coords(to_name)
        if not fc or not tc:
            return None
        dist_km = _haversine_road_km(fc[0], fc[1], tc[0], tc[1])
        
        # 1. Traffic-adjusted travel duration via TimeEngine if available
        osrm_min = dist_km / 30 * 60
        travel_min = max(3, int(dist_km / 25 * 60))
        if _ny_time:
            try:
                time_est = _ny_time.estimate_duration(osrm_min, dist_km, start_time)
                travel_min = time_est["minutes"]
            except Exception:
                pass
        
        # 2. Query all engines to select the cheapest feeder ride
        cheapest_fare = float('inf')
        best_vehicle = "Auto"
        best_provider = "Namma Yatri"
        best_icon = "🛺"
        
        if _ny_fare:
            for provider in ["namma_yatri", "uber", "ola", "rapido"]:
                try:
                    provider_fares = _ny_fare.get_all_fares_for_provider(provider, dist_km, travel_min, start_time, weather)
                    for f in provider_fares:
                        vname = f["vehicle"].lower()
                        # Feeder transit options only (Auto, Bike, Scooty, Saver; no logistics/parcels)
                        is_feeder_vehicle = any(k in vname for k in ["auto", "bike", "moto", "scooty", "saver"]) and "parcel" not in vname
                        if f.get("available", True) and is_feeder_vehicle:
                            if f["fare_min"] < cheapest_fare:
                                cheapest_fare = f["fare_min"]
                                best_vehicle = f["vehicle"]
                                best_provider = _ny_fare.providers[provider]["name"]
                                best_icon = f.get("icon", "🛺")
                except Exception:
                    pass
        
        if cheapest_fare == float('inf'):
            cheapest_fare = max(30, int(30 + dist_km * 16))
            best_vehicle = "Auto"
            best_provider = "Auto/Cab"
            best_icon = "🛺"

        arrival_time = start_time + timedelta(minutes=travel_min)
        return {
            "route": f"{best_provider} {best_vehicle}", "type": "cab",
            "from": from_name, "to": to_name,
            "departure": _fmt(start_time), "arrival": _fmt(arrival_time),
            "duration": travel_min, "fare": cheapest_fare, "distance": round(dist_km, 2),
            "stops": [from_name, to_name]
        }

    def combine_and_time_segments(segments: list[dict], start_time: datetime) -> tuple[list[dict], list[dict], int, int, float]:
        current_time = start_time
        final_segments = []
        total_cost = 0
        total_dist = 0.0
        
        for i, seg in enumerate(segments):
            seg_duration = seg["duration"]
            seg_departure = current_time
            seg_arrival = current_time + timedelta(minutes=seg_duration)
            
            new_seg = {
                "route": seg["route"],
                "type": seg["type"],
                "from": seg["from"],
                "to": seg["to"],
                "departure": _fmt(seg_departure),
                "arrival": _fmt(seg_arrival),
                "duration": seg_duration,
                "fare": seg["fare"],
                "distance": seg["distance"],
                "stops": seg["stops"]
            }
            final_segments.append(new_seg)
            total_cost += seg["fare"]
            total_dist += seg["distance"]
            
            current_time = seg_arrival
            if i < len(segments) - 1:
                current_time += timedelta(minutes=5)
                
        total_time = int((current_time - start_time).total_seconds() / 60)
        
        guide = []
        step_num = 1
        for i, seg in enumerate(final_segments):
            if seg["type"] == "walk":
                fc = get_stop_coords(seg["from"])
                tc = get_stop_coords(seg["to"])
                nav_url = f"https://www.google.com/maps/dir/?api=1&origin={fc[0]},{fc[1]}&destination={tc[0]},{tc[1]}&travelmode=walking" if fc and tc else None
                guide.append({
                    "step": step_num, "icon": "walk",
                    "text": f"Walk to {seg['to']}", "duration": f"{seg['duration']} min",
                    "detail": f"{seg['distance']} km", "nav_url": nav_url
                })
            elif seg["type"] == "cab":
                guide.append({
                    "step": step_num, "icon": "cab",
                    "text": f"Take {seg['route']} to {seg['to']}", "duration": f"{seg['duration']} min",
                    "detail": f"₹{seg['fare']} est. · {seg['distance']} km"
                })
            elif seg["type"] == "bmtc":
                guide.append({
                    "step": step_num, "icon": "bus",
                    "text": f"Board Bus {seg['route']} from {seg['from']} to {seg['to']}", "duration": f"{seg['duration']} min",
                    "detail": f"₹{seg['fare']} · {len(seg['stops'])} stops"
                })
            elif seg["type"] == "metro":
                guide.append({
                    "step": step_num, "icon": "metro",
                    "text": f"Board Metro {seg['route']} from {seg['from']} to {seg['to']}", "duration": f"{seg['duration']} min",
                    "detail": f"₹{seg['fare']} · {len(seg['stops'])} stations"
                })
            step_num += 1
            
            if i < len(final_segments) - 1:
                next_seg = final_segments[i + 1]
                guide.append({
                    "step": step_num, "icon": "transfer",
                    "text": f"Transfer to {next_seg['route']} at {seg['to']}", "duration": "5 min buffer"
                })
                step_num += 1
                
        return final_segments, guide, total_time, total_cost, round(total_dist, 2)

    options_results = []

    # 1. Walk + Bus + Walk
    walk1 = get_walk_leg(source, nearest_bmtc_src, dep_time)
    if walk1:
        current_time = dep_time + timedelta(minutes=walk1["duration"])
        try:
            bus_res = bmtc_plan(JourneyRequest(source=nearest_bmtc_src, destination=nearest_bmtc_dst, time=_fmt(current_time)))
            if bus_res.get("available"):
                bus_segs = [s for s in bus_res["segments"] if s["type"] != "walk"]
                if bus_segs:
                    bus_arr = _parse_time(bus_segs[-1]["arrival"])
                    walk2 = get_walk_leg(nearest_bmtc_dst, destination, bus_arr)
                    if walk2:
                        segs = [walk1] + bus_segs + [walk2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "walk_bus_walk",
                            "combination_label": "Walk + Bus + Walk",
                            "route_summary": f"Walk to {nearest_bmtc_src} · Bus to {nearest_bmtc_dst} · Walk to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(bus_segs) - 1, "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # 2. Walk + Metro + Walk
    walk1 = get_walk_leg(source, nearest_metro_src, dep_time)
    if walk1:
        current_time = dep_time + timedelta(minutes=walk1["duration"])
        try:
            metro_res = metro_plan(JourneyRequest(source=nearest_metro_src, destination=nearest_metro_dst, time=_fmt(current_time)))
            if metro_res.get("available"):
                metro_segs = [s for s in metro_res["segments"] if s["type"] != "walk"]
                if metro_segs:
                    metro_arr = _parse_time(metro_segs[-1]["arrival"])
                    walk2 = get_walk_leg(nearest_metro_dst, destination, metro_arr)
                    if walk2:
                        segs = [walk1] + metro_segs + [walk2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "walk_metro_walk",
                            "combination_label": "Walk + Metro + Walk",
                            "route_summary": f"Walk to {nearest_metro_src} · Metro to {nearest_metro_dst} · Walk to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(metro_segs) - 1, "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # Sort and filter interchange points to the top 3 closest to the trip path to avoid massive detours and speed up calculations
    sorted_interchanges = []
    for I_name, I_info in INTERCHANGE_POINTS.items():
        I_coords = I_info["coords"]
        d_src = _haversine_km(src_coords[0], src_coords[1], I_coords[0], I_coords[1])
        d_dst = _haversine_km(dst_coords[0], dst_coords[1], I_coords[0], I_coords[1])
        sorted_interchanges.append((I_name, I_info, d_src + d_dst))
    sorted_interchanges.sort(key=lambda x: x[2])
    best_interchanges = sorted_interchanges[:3]

    # 3. Walk + Bus + Metro + Walk
    best_opt_bm = None
    best_time_bm = float("inf")
    for I_name, I_info, _ in best_interchanges:
        I_bmtc = I_info["nearby_bmtc_stops"][0]
        I_metro = I_info["metro_station"]
        walk1 = get_walk_leg(source, nearest_bmtc_src, dep_time)
        if not walk1:
            continue
        current_time = dep_time + timedelta(minutes=walk1["duration"])
        try:
            bus_res = bmtc_plan(JourneyRequest(source=nearest_bmtc_src, destination=I_bmtc, time=_fmt(current_time)), max_options=1)
            if bus_res.get("available"):
                bus_segs = [s for s in bus_res["segments"] if s["type"] != "walk"]
                if bus_segs:
                    bus_arr = _parse_time(bus_segs[-1]["arrival"])
                    metro_start = bus_arr + timedelta(minutes=5)
                    metro_res = metro_plan(JourneyRequest(source=I_metro, destination=nearest_metro_dst, time=_fmt(metro_start)))
                    if metro_res.get("available"):
                        metro_segs = [s for s in metro_res["segments"] if s["type"] != "walk"]
                        if metro_segs:
                            metro_arr = _parse_time(metro_segs[-1]["arrival"])
                            walk2 = get_walk_leg(nearest_metro_dst, destination, metro_arr)
                            if walk2:
                                segs = [walk1] + bus_segs + metro_segs + [walk2]
                                final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                                if total_time < best_time_bm:
                                    best_time_bm = total_time
                                    best_opt_bm = {
                                        "combination_type": "walk_bus_metro_walk",
                                        "combination_label": "Walk + Bus + Metro + Walk",
                                        "route_summary": f"Walk to {nearest_bmtc_src} · Bus via {I_name} · Metro to {nearest_metro_dst}",
                                        "available": True, "mode": "multimodal",
                                        "time": total_time, "cost": total_cost, "transfers": len(bus_segs) + len(metro_segs), "distance": total_dist,
                                        "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                                        "segments": final_segs, "guide": final_guide
                                    }
        except Exception:
            pass
    if best_opt_bm:
        options_results.append(best_opt_bm)

    # 4. Walk + Metro + Bus + Walk
    best_opt_mb = None
    best_time_mb = float("inf")
    for I_name, I_info, _ in best_interchanges:
        I_bmtc = I_info["nearby_bmtc_stops"][0]
        I_metro = I_info["metro_station"]
        walk1 = get_walk_leg(source, nearest_metro_src, dep_time)
        if not walk1:
            continue
        current_time = dep_time + timedelta(minutes=walk1["duration"])
        try:
            metro_res = metro_plan(JourneyRequest(source=nearest_metro_src, destination=I_metro, time=_fmt(current_time)))
            if metro_res.get("available"):
                metro_segs = [s for s in metro_res["segments"] if s["type"] != "walk"]
                if metro_segs:
                    metro_arr = _parse_time(metro_segs[-1]["arrival"])
                    bus_start = metro_arr + timedelta(minutes=5)
                    bus_res = bmtc_plan(JourneyRequest(source=I_bmtc, destination=nearest_bmtc_dst, time=_fmt(bus_start)), max_options=1)
                    if bus_res.get("available"):
                        bus_segs = [s for s in bus_res["segments"] if s["type"] != "walk"]
                        if bus_segs:
                            bus_arr = _parse_time(bus_segs[-1]["arrival"])
                            walk2 = get_walk_leg(nearest_bmtc_dst, destination, bus_arr)
                            if walk2:
                                segs = [walk1] + metro_segs + bus_segs + [walk2]
                                final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                                if total_time < best_time_mb:
                                    best_time_mb = total_time
                                    best_opt_mb = {
                                        "combination_type": "walk_metro_bus_walk",
                                        "combination_label": "Walk + Metro + Bus + Walk",
                                        "route_summary": f"Walk to {nearest_metro_src} · Metro via {I_name} · Bus to {nearest_bmtc_dst}",
                                        "available": True, "mode": "multimodal",
                                        "time": total_time, "cost": total_cost, "transfers": len(metro_segs) + len(bus_segs), "distance": total_dist,
                                        "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                                        "segments": final_segs, "guide": final_guide
                                    }
        except Exception:
            pass
    if best_opt_mb:
        options_results.append(best_opt_mb)

    # 5. Auto/Cab + Bus + Auto/Cab
    cab1 = get_cab_leg(source, nearest_bmtc_src, dep_time)
    if cab1:
        current_time = dep_time + timedelta(minutes=cab1["duration"])
        try:
            bus_res = bmtc_plan(JourneyRequest(source=nearest_bmtc_src, destination=nearest_bmtc_dst, time=_fmt(current_time)), max_options=1)
            if bus_res.get("available"):
                bus_segs = [s for s in bus_res["segments"] if s["type"] != "walk"]
                if bus_segs:
                    bus_arr = _parse_time(bus_segs[-1]["arrival"])
                    cab2 = get_cab_leg(nearest_bmtc_dst, destination, bus_arr)
                    if cab2:
                        segs = [cab1] + bus_segs + [cab2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "cab_bus_cab",
                            "combination_label": "Auto/Cab + Bus + Auto/Cab",
                            "route_summary": f"Auto to {nearest_bmtc_src} · Bus to {nearest_bmtc_dst} · Auto to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(bus_segs), "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # 6. Auto/Cab + Bus + Walk
    cab1 = get_cab_leg(source, nearest_bmtc_src, dep_time)
    if cab1:
        current_time = dep_time + timedelta(minutes=cab1["duration"])
        try:
            bus_res = bmtc_plan(JourneyRequest(source=nearest_bmtc_src, destination=nearest_bmtc_dst, time=_fmt(current_time)), max_options=1)
            if bus_res.get("available"):
                bus_segs = [s for s in bus_res["segments"] if s["type"] != "walk"]
                if bus_segs:
                    bus_arr = _parse_time(bus_segs[-1]["arrival"])
                    walk2 = get_walk_leg(nearest_bmtc_dst, destination, bus_arr)
                    if walk2:
                        segs = [cab1] + bus_segs + [walk2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "cab_bus_walk",
                            "combination_label": "Auto/Cab + Bus + Walk",
                            "route_summary": f"Auto to {nearest_bmtc_src} · Bus to {nearest_bmtc_dst} · Walk to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(bus_segs), "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # 7. Walk + Bus + Auto/Cab
    walk1 = get_walk_leg(source, nearest_bmtc_src, dep_time)
    if walk1:
        current_time = dep_time + timedelta(minutes=walk1["duration"])
        try:
            bus_res = bmtc_plan(JourneyRequest(source=nearest_bmtc_src, destination=nearest_bmtc_dst, time=_fmt(current_time)), max_options=1)
            if bus_res.get("available"):
                bus_segs = [s for s in bus_res["segments"] if s["type"] != "walk"]
                if bus_segs:
                    bus_arr = _parse_time(bus_segs[-1]["arrival"])
                    cab2 = get_cab_leg(nearest_bmtc_dst, destination, bus_arr)
                    if cab2:
                        segs = [walk1] + bus_segs + [cab2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "walk_bus_cab",
                            "combination_label": "Walk + Bus + Auto/Cab",
                            "route_summary": f"Walk to {nearest_bmtc_src} · Bus to {nearest_bmtc_dst} · Auto to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(bus_segs), "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # 8. Auto/Cab + Metro + Auto/Cab
    cab1 = get_cab_leg(source, nearest_metro_src, dep_time)
    if cab1:
        current_time = dep_time + timedelta(minutes=cab1["duration"])
        try:
            metro_res = metro_plan(JourneyRequest(source=nearest_metro_src, destination=nearest_metro_dst, time=_fmt(current_time)))
            if metro_res.get("available"):
                metro_segs = [s for s in metro_res["segments"] if s["type"] != "walk"]
                if metro_segs:
                    metro_arr = _parse_time(metro_segs[-1]["arrival"])
                    cab2 = get_cab_leg(nearest_metro_dst, destination, metro_arr)
                    if cab2:
                        segs = [cab1] + metro_segs + [cab2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "cab_metro_cab",
                            "combination_label": "Auto/Cab + Metro + Auto/Cab",
                            "route_summary": f"Auto to {nearest_metro_src} · Metro to {nearest_metro_dst} · Auto to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(metro_segs), "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # 9. Auto/Cab + Metro + Walk
    cab1 = get_cab_leg(source, nearest_metro_src, dep_time)
    if cab1:
        current_time = dep_time + timedelta(minutes=cab1["duration"])
        try:
            metro_res = metro_plan(JourneyRequest(source=nearest_metro_src, destination=nearest_metro_dst, time=_fmt(current_time)))
            if metro_res.get("available"):
                metro_segs = [s for s in metro_res["segments"] if s["type"] != "walk"]
                if metro_segs:
                    metro_arr = _parse_time(metro_segs[-1]["arrival"])
                    walk2 = get_walk_leg(nearest_metro_dst, destination, metro_arr)
                    if walk2:
                        segs = [cab1] + metro_segs + [walk2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "cab_metro_walk",
                            "combination_label": "Auto/Cab + Metro + Walk",
                            "route_summary": f"Auto to {nearest_metro_src} · Metro to {nearest_metro_dst} · Walk to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(metro_segs), "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    # 10. Walk + Metro + Auto/Cab
    walk1 = get_walk_leg(source, nearest_metro_src, dep_time)
    if walk1:
        current_time = dep_time + timedelta(minutes=walk1["duration"])
        try:
            metro_res = metro_plan(JourneyRequest(source=nearest_metro_src, destination=nearest_metro_dst, time=_fmt(current_time)))
            if metro_res.get("available"):
                metro_segs = [s for s in metro_res["segments"] if s["type"] != "walk"]
                if metro_segs:
                    metro_arr = _parse_time(metro_segs[-1]["arrival"])
                    cab2 = get_cab_leg(nearest_metro_dst, destination, metro_arr)
                    if cab2:
                        segs = [walk1] + metro_segs + [cab2]
                        final_segs, final_guide, total_time, total_cost, total_dist = combine_and_time_segments(segs, dep_time)
                        options_results.append({
                            "combination_type": "walk_metro_cab",
                            "combination_label": "Walk + Metro + Auto/Cab",
                            "route_summary": f"Walk to {nearest_metro_src} · Metro to {nearest_metro_dst} · Auto to dest",
                            "available": True, "mode": "multimodal",
                            "time": total_time, "cost": total_cost, "transfers": len(metro_segs), "distance": total_dist,
                            "departure": _fmt(dep_time), "arrival": _fmt(dep_time + timedelta(minutes=total_time)),
                            "segments": final_segs, "guide": final_guide
                        })
        except Exception:
            pass

    if not options_results:
        return {"available": False, "mode": "multimodal", "error": "No viable multimodal route found"}

    # Sort based on preference
    if preference == "cost":
        options_results.sort(key=lambda x: x["cost"])
    else:
        options_results.sort(key=lambda x: x["time"])

    best_option = options_results[0]
    return {
        "available": True,
        "mode": "multimodal",
        "time": best_option["time"],
        "cost": best_option["cost"],
        "transfers": best_option["transfers"],
        "distance": best_option["distance"],
        "departure": best_option["departure"],
        "arrival": best_option["arrival"],
        "segments": best_option["segments"],
        "guide": best_option["guide"],
        "all_options": options_results
    }


# ══════════════════════════════════════════════════════════════════════════════
# COMPARE ENDPOINT  (all modes — uses coordinate-aware vehicle estimate)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/compare")
def compare(req: CompareRequest):
    import concurrent.futures

    dep_time = _parse_time(req.time)
    results  = {}

    from weather_helper import get_realtime_weather
    weather_cond = get_realtime_weather(dep_time)

    # Resolve coordinates first
    src_coords = get_stop_coords(req.source)
    dst_coords = get_stop_coords(req.destination)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Submit tasks for bmtc, metro, cab, car
        future_bmtc = executor.submit(
            bmtc_plan, JourneyRequest(source=req.source, destination=req.destination, time=req.time, preference=req.preference)
        )
        future_metro = executor.submit(
            metro_plan, JourneyRequest(source=req.source, destination=req.destination, time=req.time)
        )

        def run_cab():
            if src_coords and dst_coords:
                try:
                    all_estimates = []
                    for p_key, p_info in RIDE_PROVIDERS.items():
                        try:
                            estimates = p_info["fn"](
                                src_coords[0], src_coords[1], dst_coords[0], dst_coords[1], dep_time, weather_cond
                            )
                            all_estimates.extend(estimates)
                        except Exception as ex:
                            print(f"Error fetching estimates for {p_key}: {ex}")
                    
                    if all_estimates:
                        all_estimates.sort(key=lambda x: x["cost"])
                        default_est = all_estimates[0]
                        return {
                            "available": True,
                            "mode": "cab",
                            "time": default_est["time"],
                            "cost": default_est["cost"],
                            "cost_max": default_est["cost_max"],
                            "transfers": 0,
                            "distance": default_est["distance"],
                            "departure": default_est["departure"],
                            "arrival": default_est["arrival"],
                            "segments": default_est["segments"],
                            "guide": default_est["guide"],
                            "all_estimates": all_estimates,
                        }
                except Exception as e:
                    print(f"Real cab estimation error: {e}")
            return _cab_estimate(req.source, req.destination, dep_time)

        future_cab = executor.submit(run_cab)

        def run_car():
            if req.vehicle and src_coords and dst_coords:
                try:
                    return vehicle_estimate(VehicleRequest(
                        vehicle=req.vehicle,
                        source_lat=src_coords[0], source_lng=src_coords[1],
                        dest_lat=dst_coords[0],   dest_lng=dst_coords[1],
                    ))
                except Exception as e:
                    print(f"Vehicle estimate error: {e}")
            return _car_estimate(req.source, req.destination, dep_time, src_coords, dst_coords)

        future_car = executor.submit(run_car)

        # Retrieve results
        try:
            results["bmtc"] = future_bmtc.result()
        except Exception as e:
            results["bmtc"] = {"available": False, "mode": "bmtc", "error": str(e)}

        try:
            results["metro"] = future_metro.result()
        except Exception as e:
            results["metro"] = {"available": False, "mode": "metro", "error": str(e)}

        try:
            results["cab"] = future_cab.result()
        except Exception as e:
            results["cab"] = {"available": False, "mode": "cab", "error": str(e)}

        try:
            results["car"] = future_car.result()
        except Exception as e:
            results["car"] = {"available": False, "mode": "car", "error": str(e)}

    # Multimodal
    direct_bus_available = results.get("bmtc", {}).get("available") and results.get("bmtc", {}).get("transfers", 999) == 0
    direct_metro_available = results.get("metro", {}).get("available") and results.get("metro", {}).get("transfers", 999) == 0

    if direct_bus_available or direct_metro_available:
        results["multimodal"] = {"available": False, "mode": "multimodal", "error": "Direct transit option is available"}
    else:
        try:
            results["multimodal"] = multimodal_plan(
                req.source, req.destination, dep_time, preference=req.preference or "cost", weather=weather_cond
            )
        except Exception as e:
            results["multimodal"] = {"available": False, "mode": "multimodal", "error": str(e)}

    # Tag the recommended option
    pref      = req.preference or "cost"
    available = {k: v for k, v in results.items() if v.get("available")}
    if available:
        if pref == "cost":
            best = min(available, key=lambda k: available[k].get("cost", 9999))
        elif pref == "time":
            best = min(available, key=lambda k: available[k].get("time", 9999))
        else:   # convenience
            best = min(available, key=lambda k: available[k].get("transfers", 9999))
        results[best]["recommended"] = True
        tag_map = {"cost": "Cheapest", "time": "Fastest", "convenience": "Fewest Transfers"}
        results[best]["tag"] = tag_map.get(pref, "Recommended")

    # Call AI Recommender for Top-K ranking and Explainable AI
    from recommender import get_recommendations
    recs = get_recommendations(results, req.source, req.destination, pref, weather_cond)

    return {
        "results": results,
        "recommendations": recs,
        "searched_at": datetime.now().isoformat()
    }


@app.post("/api/stops/coords")
def get_stops_coordinates(req: StopCoordsRequest):
    coords = {}
    for stop in req.stops:
        res = get_stop_coords(stop)
        if res:
            coords[stop] = {
                "lat": res[0],
                "lng": res[1],
                "resolved": stop
            }
    return {"coordinates": coords}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/metro/stations")
def metro_stations():
    return {"stations": _metro_stations, "count": len(_metro_stations)}


@app.get("/api/bmtc/stops")
def bmtc_stops():
    return {"stops": ALL_STOPS, "count": len(ALL_STOPS)}


@app.get("/api/health")
def health():
    return {
        "status":          "ok",
        "bmtc_stops":      len(ALL_STOPS),
        "metro_stations":  len(_metro_stations),
        "namma_yatri_ok":  _NAMMA_OK,
        "vehicles_loaded": len(_all_vehicles),
        "time":            datetime.now().isoformat(),
    }


# ── Chatbot Endpoint ────────────────────────────────────────────────────────
from chatbot_engine import ChatbotEngine

class ChatbotRequest(BaseModel):
    message: str
    time: Optional[str] = None
    weather: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

def _geocode_location(place: str):
    """Geocode any Bangalore place name to (lat, lon). Returns None on failure."""
    if not place:
        return None
    p_lower = place.strip().lower()
    if p_lower in ("my current location", "current location", "me", "here", "current"):
        # Default to a central location in Bangalore (Majestic)
        return (12.9779, 77.5724)
    try:
        from modes.cab.engines.geocoding_engine import GeocodingEngine
        geo = GeocodingEngine()
        result = geo.geocode(place)
        return (result["latitude"], result["longitude"])
    except Exception:
        return None


def _osrm_distance(src_lat, src_lon, dst_lat, dst_lon):
    """Get driving distance and duration via OSRM. Returns dict or None."""
    try:
        from modes.cab.engines.distance_engine import DistanceEngine
        de = DistanceEngine()
        return de.get_distance(
            {"latitude": src_lat, "longitude": src_lon},
            {"latitude": dst_lat, "longitude": dst_lon}
        )
    except Exception:
        return None


def _get_all_ride_fares(distance_km: float, duration_min: float, dep_time, weather: str = "clear"):
    """Return per-provider fare estimates for all 4 providers."""
    try:
        from modes.cab.engines.fare_engine import FareEngine
        fe = FareEngine()
        providers = {}
        for pkey in ["ola", "uber", "namma_yatri", "rapido"]:
            try:
                fares = fe.get_all_fares_for_provider(pkey, distance_km, duration_min, dep_time, weather)
                providers[pkey] = fares
            except Exception:
                pass
        return providers
    except Exception:
        return {}


def _get_fuel_cost(src_lat, src_lon, dst_lat, dst_lon, vehicle_type: str = "car"):
    """Calculate fuel consumption and cost for a private vehicle trip."""
    try:
        from modes.cab.engines.distance_engine import DistanceEngine
        de = DistanceEngine()
        route = de.get_distance(
            {"latitude": src_lat, "longitude": src_lon},
            {"latitude": dst_lat, "longitude": dst_lon}
        )
        distance_km = route.get("distance_km", 0)
        duration_min = route.get("duration_min", 0)

        # Default efficiencies and fuel types
        if vehicle_type == "bike":
            efficiency_kmpl = 45.0  # typical two-wheeler
            fuel_type = "petrol"
            fuel_price_per_litre = 103.0
            co2_per_litre = 2.31
        else:
            efficiency_kmpl = 15.0  # typical car (petrol)
            fuel_type = "petrol"
            fuel_price_per_litre = 103.0
            co2_per_litre = 2.31

        # Try to get real vehicle data
        if vehicle_type == "bike" and _bikes_df is not None and not _bikes_df.empty:
            try:
                mileage_col = [c for c in _bikes_df.columns if "mileage" in c.lower() or "efficiency" in c.lower()]
                if mileage_col:
                    val = _bikes_df[mileage_col[0]].iloc[0]
                    if val and float(val) > 0:
                        efficiency_kmpl = float(val)
            except Exception:
                pass
        elif vehicle_type == "car" and _cars_df is not None and not _cars_df.empty:
            try:
                mileage_col = [c for c in _cars_df.columns if "mileage" in c.lower() or "efficiency" in c.lower()]
                if mileage_col:
                    val = _cars_df[mileage_col[0]].iloc[0]
                    if val and float(val) > 0:
                        efficiency_kmpl = float(val)
            except Exception:
                pass

        fuel_litres = distance_km / efficiency_kmpl
        fuel_cost = fuel_litres * fuel_price_per_litre
        co2_kg = fuel_litres * co2_per_litre

        return {
            "distance_km": round(distance_km, 2),
            "duration_min": round(duration_min),
            "efficiency_kmpl": efficiency_kmpl,
            "fuel_type": fuel_type,
            "fuel_litres": round(fuel_litres, 3),
            "fuel_cost": round(fuel_cost, 1),
            "co2_kg": round(co2_kg, 3),
        }
    except Exception as e:
        return {}

def _get_traffic_level(drive_time_min: float, distance_km: float):
    """Classify congestion level based on average speed."""
    if distance_km <= 0:
        return "moderate"
    avg_speed = distance_km / (drive_time_min / 60) if drive_time_min > 0 else 30
    if avg_speed >= 30:
        return "clear"
    elif avg_speed >= 15:
        return "moderate"
    return "heavy"

@app.post("/api/chatbot/query")
def chatbot_query(req: ChatbotRequest):
    engine = ChatbotEngine(bmtc_stops=ALL_STOPS, metro_stations=_metro_stations, all_vehicles=_all_vehicles)

    # Extract stops
    matched_stops = engine.extract_stops(req.message)

    intent = None
    params = {"message": req.message}

    llm_res = None
    try:
        llm_res = engine.query_llm(req.message, req.history)
    except Exception:
        pass

    if llm_res and isinstance(llm_res, dict):
        intent = llm_res.get("intent")
        llm_params = llm_res.get("parameters") or {}
        for k, v in llm_params.items():
            if v is not None:
                params[k] = v

        # Sanitize parameters
        if "time" in params and isinstance(params["time"], str) and params["time"]:
            try:
                params["time"] = engine.extract_time(params["time"])
            except Exception:
                pass
        if "budget" in params and params["budget"] is not None:
            try:
                params["budget"] = int(params["budget"])
            except Exception:
                pass
        if "vehicle_type" in params:
            params["vtype"] = params.get("vehicle_type")

        llm_answer = llm_res.get("answer")
        if llm_answer and intent in ("general", "clarification"):
            serialized_params = {}
            for k, v in params.items():
                if isinstance(v, datetime):
                    serialized_params[k] = v.isoformat()
                else:
                    serialized_params[k] = v
            return {
                "text": llm_answer,
                "intent": intent,
                "parameters": serialized_params,
                "embedded_data": None
            }
    else:
        resolved_context = engine.resolve_context_from_history(req.message, req.history)
        if resolved_context:
            intent, params = resolved_context
        else:
            intent, params = engine.classify_intent(req.message, matched_stops)

    dep_time = None
    if req.time:
        try:
            dep_time = _parse_time(req.time)
        except Exception:
            pass
    if not dep_time:
        dep_time = params.get("time")
    if not dep_time:
        dep_time = datetime.now()

    data = {}
    embedded_data = None

    # ── ride_cost: Geocode + DistanceEngine + FareEngine all providers ─────────
    if intent == "ride_cost":
        source = params.get("source") or ""
        destination = params.get("destination") or ""
        weather = req.weather or engine.get_simulated_weather(dep_time)

        src_coords = get_stop_coords(source) or _geocode_location(source)
        dst_coords = get_stop_coords(destination) or _geocode_location(destination)

        if src_coords and dst_coords:
            route = _osrm_distance(src_coords[0], src_coords[1], dst_coords[0], dst_coords[1])
            if route:
                distance_km = route.get("distance_km", 10)
                duration_min = route.get("duration_min", 25)
                providers = _get_all_ride_fares(distance_km, duration_min, dep_time, weather)
                data["providers"] = providers
                data["distance_km"] = distance_km
                data["duration_min"] = duration_min
                # Build embedded_data as a cab-mode summary for the card
                if providers:
                    # Find cheapest overall
                    all_fares = [(v["fare_min"], v) for pv in providers.values() for v in pv]
                    if all_fares:
                        cheapest_fare = min(all_fares, key=lambda x: x[0])[1]
                        embedded_data = {
                            "mode": "cab",
                            "available": True,
                            "cost": cheapest_fare.get("fare_min"),
                            "cost_max": cheapest_fare.get("fare_max"),
                            "time": int(duration_min),
                            "distance": distance_km,
                            "distance_km": distance_km,
                            "duration_min": duration_min,
                            "source": source,
                            "destination": destination,
                            "providers": providers,
                        }


    # ── fuel_cost: Geocode + DistanceEngine + fuel math ──────────────────────
    elif intent == "fuel_cost":
        source = params.get("source") or ""
        destination = params.get("destination") or ""
        vehicle_type = params.get("vehicle_type") or params.get("vtype") or "car"

        src_coords = get_stop_coords(source) or _geocode_location(source)
        dst_coords = get_stop_coords(destination) or _geocode_location(destination)

        if src_coords and dst_coords:
            fuel_data = _get_fuel_cost(src_coords[0], src_coords[1], dst_coords[0], dst_coords[1], vehicle_type)
            data.update(fuel_data)
            data["vehicle_type"] = vehicle_type
            if fuel_data:
                embedded_data = {
                    "mode": "car",
                    "available": True,
                    "cost": int(fuel_data.get("fuel_cost", 0)),
                    "fuel_litres": fuel_data.get("fuel_litres", 0),
                    "distance_km": fuel_data.get("distance_km", 0),
                    "time": fuel_data.get("duration_min", 0),
                    "distance": fuel_data.get("distance_km", 0),
                    "source": source,
                    "destination": destination,
                }


    # ── traffic_query: OSRM drive time → congestion level ────────────────────
    elif intent == "traffic_query":
        source = params.get("source") or ""
        destination = params.get("destination") or ""

        if source and destination:
            src_coords = get_stop_coords(source) or _geocode_location(source)
            dst_coords = get_stop_coords(destination) or _geocode_location(destination)
            if src_coords and dst_coords:
                route = _osrm_distance(src_coords[0], src_coords[1], dst_coords[0], dst_coords[1])
                if route:
                    drive_time = route.get("duration_min", 0)
                    dist_km = route.get("distance_km", 0)
                    level = _get_traffic_level(drive_time, dist_km)
                    data["congestion_level"] = level
                    data["drive_time_min"] = int(drive_time)
                    data["distance_km"] = round(dist_km, 1)
                    # Try to get transit time for comparison
                    try:
                        b_res = bmtc_plan(JourneyRequest(source=source, destination=destination, time=_fmt(dep_time)))
                        if b_res.get("available"):
                            data["transit_time"] = b_res.get("time")
                    except Exception:
                        pass
                    embedded_data = {
                        "congestion_level": level,
                        "drive_time_min": int(drive_time),
                        "transit_time": data.get("transit_time"),
                    }
        else:
            # General traffic query without specific locations
            weather = req.weather or engine.get_simulated_weather(dep_time)
            hour = dep_time.hour if isinstance(dep_time, datetime) else datetime.now().hour
            if (8 <= hour <= 10) or (17 <= hour <= 20):
                data["congestion_level"] = "heavy"
            elif (7 <= hour <= 11) or (16 <= hour <= 21):
                data["congestion_level"] = "moderate"
            else:
                data["congestion_level"] = "clear"

    elif intent == "nearest_stops":
        loc = params.get("location")
        nearest = None
        if loc:
            # Clean up noise prefixes added by regex or LLM
            import re as _re
            noise_patterns = [
                r"^(nearest|closest|nearby|closest\s+)?bus\s+stop\s+(to|near|near\s+the|at)?\s*",
                r"^(nearest|closest|nearby)?\s+metro\s+(station\s+)?(to|near|near\s+the|at)?\s*",
                r"^(nearest|closest|nearby)\s+(stop|station|transit)\s+(to|near|near\s+the|at)?\s*",
                r"^(stops?|stations?)\s+(near|to|at)\s*",
                r"\s*(bus\s+stop|metro\s+station|metro\s+stop|transit\s+stop)$",
            ]
            cleaned_loc = loc.strip()
            for pat in noise_patterns:
                cleaned_loc = _re.sub(pat, "", cleaned_loc, flags=_re.IGNORECASE).strip()
            # If cleaning made it empty, fall back to original
            if cleaned_loc:
                loc = cleaned_loc

            # First try our known stop coords
            coords = get_stop_coords(loc)
            # If not a known stop, geocode it (landmark, area, address)
            if not coords:
                coords = _geocode_location(loc)

            # Also try multimodal interchange points
            if not coords:
                from multimodal.config import INTERCHANGE_POINTS
                for station, pt in INTERCHANGE_POINTS.items():
                    if station.lower() in loc.lower() or loc.lower() in station.lower():
                        coords = pt["coords"]
                        break

            if coords:
                from shared.utils import resolve_stop_name
                bmtc_dists = []
                for norm, info in STOP_COORDS.items():
                    lat = float(info["latitude"])
                    lng = float(info["longitude"])
                    d = _haversine_km(coords[0], coords[1], lat, lng)
                    if d > 0.03:
                        c_name = resolve_stop_name(norm, "bmtc", bmtc_stops=ALL_STOPS)
                        bmtc_dists.append((c_name, d))

                metro_dists = []
                from multimodal.config import INTERCHANGE_POINTS
                for station, pt in INTERCHANGE_POINTS.items():
                    m_coords = pt["coords"]
                    d = _haversine_km(coords[0], coords[1], m_coords[0], m_coords[1])
                    metro_dists.append((station, d))

                bmtc_dists.sort(key=lambda x: x[1])
                metro_dists.sort(key=lambda x: x[1])

                seen_names = set()
                uniq_bmtc = []
                for name, dist in bmtc_dists:
                    if name not in seen_names:
                        seen_names.add(name)
                        uniq_bmtc.append((name, dist))
                        if len(uniq_bmtc) >= 3:
                            break

                nearest = {
                    "bmtc": uniq_bmtc,
                    "metro": metro_dists[:3]
                }
        data["nearest"] = nearest
        if nearest:
            embedded_data = {
                "nearest": nearest,
                "location": loc,
            }

    # ── multimodal_journey ────────────────────────────────────────────────────
    elif intent == "multimodal_journey":
        source = params.get("source")
        destination = params.get("destination")
        multimodal_options = []

        if source and destination:
            try:
                from multimodal.router import MultimodalRouter
                router = MultimodalRouter()
                results = router.plan_multimodal(source, destination)
                for r in results[:3]:
                    opt = {
                        "total_time": getattr(r, "total_time", None),
                        "total_fare": getattr(r, "total_fare", None),
                        "legs": []
                    }
                    for leg in getattr(r, "legs", []):
                        opt["legs"].append({
                            "mode": getattr(leg, "mode", "transit").lower(),
                            "from": getattr(leg, "source", ""),
                            "to": getattr(leg, "destination", ""),
                        })
                    multimodal_options.append(opt)
            except Exception:
                pass

            # Fallback: if no multimodal, try BMTC direct
            if not multimodal_options:
                try:
                    b_res = bmtc_plan(JourneyRequest(source=source, destination=destination, time=_fmt(dep_time)))
                    if b_res.get("available"):
                        embedded_data = b_res
                except Exception:
                    pass

        data["options"] = multimodal_options

    # ── journey_time / journey_cost / budget_constrained / possible_ways ──────
    elif intent in ("journey_time", "journey_cost", "budget_constrained", "possible_ways"):
        source = params.get("source")
        destination = params.get("destination")

        if source and destination:
            compare_results = {}

            # BMTC
            try:
                compare_results["bmtc"] = bmtc_plan(
                    JourneyRequest(source=source, destination=destination, time=_fmt(dep_time))
                )
            except Exception:
                compare_results["bmtc"] = {"available": False, "mode": "bmtc"}

            # Metro
            try:
                compare_results["metro"] = metro_plan(
                    JourneyRequest(source=source, destination=destination, time=_fmt(dep_time))
                )
            except Exception:
                compare_results["metro"] = {"available": False, "mode": "metro"}

            # Cab
            src_coords = get_stop_coords(source) or _geocode_location(source)
            dst_coords = get_stop_coords(destination) or _geocode_location(destination)
            if src_coords and dst_coords:
                try:
                    all_estimates = []
                    for p_key, p_info in RIDE_PROVIDERS.items():
                        try:
                            estimates = p_info["fn"](
                                src_coords[0], src_coords[1], dst_coords[0], dst_coords[1], dep_time, "clear"
                            )
                            all_estimates.extend(estimates)
                        except Exception:
                            pass
                    if all_estimates:
                        all_estimates.sort(key=lambda x: x["cost"])
                        default_est = all_estimates[0]
                        compare_results["cab"] = {
                            "available": True,
                            "mode": "cab",
                            "time": default_est["time"],
                            "cost": default_est["cost"],
                            "cost_max": default_est["cost_max"],
                            "transfers": 0,
                            "distance": default_est["distance"],
                            "departure": default_est["departure"],
                            "arrival": default_est["arrival"],
                            "segments": default_est["segments"],
                            "guide": default_est["guide"],
                        }
                    else:
                        compare_results["cab"] = _cab_estimate(source, destination, dep_time)
                except Exception:
                    compare_results["cab"] = _cab_estimate(source, destination, dep_time)
            else:
                compare_results["cab"] = _cab_estimate(source, destination, dep_time)

            # Car/vehicle
            compare_results["car"] = _car_estimate(source, destination, dep_time)

            # Build modes list
            modes_data = []
            for mode, mdata in compare_results.items():
                if mdata.get("available"):
                    modes_data.append({
                        "mode": mode,
                        "time": mdata.get("time", 999),
                        "cost": mdata.get("cost", 999),
                        "details": mdata
                    })

            # Check for transit mode preference in query keywords (metro vs bus)
            msg_lower = req.message.lower()
            prefer_metro = any(k in msg_lower for k in ["metro", "train", "purple", "green line"])
            prefer_bus = any(k in msg_lower for k in ["bus", "bmtc", "volvo", "vajra"])

            if prefer_metro:
                filtered_modes = [x for x in modes_data if x["mode"] == "metro"]
                if filtered_modes:
                    modes_data = filtered_modes
            elif prefer_bus:
                filtered_modes = [x for x in modes_data if x["mode"] == "bmtc"]
                if filtered_modes:
                    modes_data = filtered_modes

            if modes_data:
                if intent == "journey_time":
                    best_option = min(modes_data, key=lambda x: x["time"])
                    data["best_option"] = best_option
                    embedded_data = best_option["details"]
                elif intent == "journey_cost":
                    best_option = min(modes_data, key=lambda x: x["cost"])
                    data["best_option"] = best_option
                    embedded_data = best_option["details"]
                elif intent == "budget_constrained":
                    budget = params.get("budget", 0)
                    options = [x for x in modes_data if x["cost"] <= budget]
                    options.sort(key=lambda x: x["cost"])
                    data["options"] = options
                    if options:
                        embedded_data = options[0]["details"]
                    else:
                        cheapest = min(modes_data, key=lambda x: x["cost"])
                        data["cheapest_available"] = cheapest
                        embedded_data = cheapest["details"]
                elif intent == "possible_ways":
                    data["options"] = modes_data
                    if modes_data:
                        cheapest = min(modes_data, key=lambda x: x["cost"])
                        embedded_data = cheapest["details"]
            else:
                data["best_option"] = None
                data["options"] = []
                data["cheapest_available"] = None
        else:
            data["best_option"] = None
            data["options"] = []
            data["cheapest_available"] = None

    # ── vehicle_vs_transit ─────────────────────────────────────────────────────
    elif intent == "vehicle_vs_transit":
        vtype = params.get("vtype", "bike")
        destination = params.get("destination")

        source = "Majestic"
        if matched_stops:
            src_parsed, dst_parsed = engine.determine_source_dest(matched_stops, req.message)
            if src_parsed:
                source = src_parsed
            if dst_parsed:
                destination = dst_parsed

        src_coords = get_stop_coords(source) or _geocode_location(source)
        dst_coords = get_stop_coords(destination or "Indiranagar") or _geocode_location(destination or "Indiranagar")

        vehicle_name = None
        if vtype == "bike":
            if _bikes_df is not None and not _bikes_df.empty:
                vehicle_name = _bikes_df["full_name"].iloc[0]
            else:
                vehicle_name = "Honda Activa"
        else:
            if _cars_df is not None and not _cars_df.empty:
                vehicle_name = _cars_df["name"].iloc[0]
            else:
                vehicle_name = "Maruti Swift"

        v_cost, v_time = 0, 0
        if src_coords and dst_coords and vehicle_name:
            try:
                v_res = vehicle_estimate(VehicleRequest(
                    vehicle=vehicle_name,
                    source_lat=src_coords[0], source_lng=src_coords[1],
                    dest_lat=dst_coords[0], dest_lng=dst_coords[1]
                ))
                v_cost = v_res.get("cost", 0)
                v_time = v_res.get("time", 0)
            except Exception:
                v_res = _car_estimate(source, destination or "Indiranagar", dep_time)
                v_cost = v_res.get("cost", 0)
                v_time = v_res.get("time", 0)
        else:
            v_res = _car_estimate(source, destination or "Indiranagar", dep_time)
            v_cost = v_res.get("cost", 0)
            v_time = v_res.get("time", 0)

        t_cost, t_time = 999, 999
        transit_option = None
        try:
            b_res = bmtc_plan(JourneyRequest(source=source, destination=destination or "Indiranagar", time=_fmt(dep_time)))
            if b_res.get("available") and b_res.get("cost", 999) < t_cost:
                t_cost = b_res.get("cost", 999)
                t_time = b_res.get("time", 999)
                transit_option = b_res
        except Exception:
            pass
        try:
            m_res = metro_plan(JourneyRequest(source=source, destination=destination or "Indiranagar", time=_fmt(dep_time)))
            if m_res.get("available") and m_res.get("cost", 999) < t_cost:
                t_cost = m_res.get("cost", 999)
                t_time = m_res.get("time", 999)
                transit_option = m_res
        except Exception:
            pass

        if t_cost == 999:
            t_cost = 25
            t_time = 45

        weather = req.weather or engine.get_simulated_weather(dep_time)
        data["vehicle_cost"] = v_cost
        data["vehicle_time"] = v_time
        data["transit_cost"] = t_cost
        data["transit_time"] = t_time
        data["weather"] = weather

        if transit_option:
            embedded_data = transit_option

    # ── ac_bus_available ──────────────────────────────────────────────────────
    elif intent == "ac_bus_available":
        source = params.get("source")
        destination = params.get("destination")
        has_ac = False
        ac_buses = []

        if source and destination:
            try:
                b_res = bmtc_plan(JourneyRequest(source=source, destination=destination, time=_fmt(dep_time)))
                if b_res.get("available"):
                    from modes.bmtc.features.routing import get_all_direct_buses
                    from shared.utils import resolve_stop_name
                    src_norm = resolve_stop_name(source, "bmtc", bmtc_stops=ALL_STOPS).strip().lower()
                    dst_norm = resolve_stop_name(destination, "bmtc", bmtc_stops=ALL_STOPS).strip().lower()
                    direct = get_all_direct_buses(src_norm, dst_norm, dep_time)
                    for b in direct:
                        route_no = b["route"]
                        category = b.get("fare_category", "ordinary").lower()
                        if category in ("vajra", "ac", "premium") or route_no.lower().startswith("v") or "vajra" in route_no.lower():
                            has_ac = True
                            ac_buses.append(route_no)
                    if has_ac:
                        embedded_data = b_res
            except Exception:
                pass

        data["has_ac"] = has_ac
        data["ac_buses"] = ac_buses

    # ── weather_query ─────────────────────────────────────────────────────────
    elif intent == "weather_query":
        weather = req.weather or engine.get_simulated_weather(dep_time)
        data["weather"] = weather

    text_response = engine.format_response(intent, params, data)

    serialized_params = {}
    for k, v in params.items():
        if isinstance(v, datetime):
            serialized_params[k] = v.isoformat()
        else:
            serialized_params[k] = v

    return {
        "text": text_response,
        "intent": intent,
        "parameters": serialized_params,
        "embedded_data": embedded_data
    }


# ── User Auth, Garage, and Document Library Endpoints ──────────────────────
import shutil
from fastapi.staticfiles import StaticFiles
from db import get_db, User, Journey, Vehicle, Document
from auth import hash_password, verify_password, create_access_token, get_current_user
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile, File, Form

# Mount uploads static folder
uploads_path = os.path.join(_HERE, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

class UserAuthRequest(BaseModel):
    username: str
    password: str


class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class JourneySaveRequest(BaseModel):
    from_stop: str
    to_stop: str
    mode: str
    cost: int
    duration: int
    distance: float
    date: str
    is_saved: Optional[bool] = True
    custom_name: Optional[str] = None

class VehicleAddRequest(BaseModel):
    name: str
    fuel_type: str
    efficiency: float

@app.post("/api/auth/signup", response_model=UserAuthResponse)
def auth_signup(req: UserAuthRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = hash_password(req.password)
    user = User(username=req.username, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

@app.post("/api/auth/login", response_model=UserAuthResponse)
def auth_login(req: UserAuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

@app.post("/api/user/journey")
def save_user_journey(req: JourneySaveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    journey = Journey(
        user_id=current_user.id,
        from_stop=req.from_stop,
        to_stop=req.to_stop,
        mode=req.mode,
        cost=req.cost,
        duration=req.duration,
        distance=req.distance,
        date=req.date,
        is_saved=req.is_saved if req.is_saved is not None else True,
        custom_name=req.custom_name
    )
    db.add(journey)
    db.commit()
    return {"status": "success", "journey_id": journey.id}

@app.delete("/api/user/journey/{journey_id}")
def delete_user_journey(journey_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    db.delete(journey)
    db.commit()
    return {"status": "success"}

@app.get("/api/user/dashboard")
def get_user_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    journeys = db.query(Journey).filter(Journey.user_id == current_user.id).order_by(Journey.id.desc()).all()
    
    # Separate search history (is_saved = False) and saved routes (is_saved = True)
    recent_searches = [j for j in journeys if not j.is_saved]
    saved_routes = [j for j in journeys if j.is_saved]
    
    total_saved_routes = len(saved_routes)
    total_cost = sum(j.cost for j in saved_routes)
    avg_cost = int(total_cost / total_saved_routes) if total_saved_routes > 0 else 0
    
    # Savings calculation based on saved routes
    money_saved = sum(150 if j.mode in ("bmtc", "metro") else 0 for j in saved_routes)
    time_saved_hr = round(sum(0.5 if j.mode == "metro" else 0.2 if j.mode == "bmtc" else 0 for j in saved_routes), 1)
    
    recent_list = []
    for j in recent_searches[:6]:
        recent_list.append({
            "id": j.id,
            "from": j.from_stop,
            "to": j.to_stop,
            "date": j.date
        })
        
    saved_list = []
    for j in saved_routes[:6]:
        saved_list.append({
            "id": j.id,
            "from": j.from_stop,
            "to": j.to_stop,
            "mode": j.mode,
            "cost": j.cost,
            "date": j.date,
            "custom_name": j.custom_name
        })
        
    stats = [
        {"label": "Journeys", "val": str(total_saved_routes), "icon": "mappin", "color": "#f97316"},
        {"label": "Saved", "val": f"₹{money_saved}", "icon": "trend", "color": "#8b5cf6"},
        {"label": "Time saved", "val": f"{time_saved_hr} hr" if time_saved_hr > 0 else "0 hr", "icon": "clock", "color": "#f59e0b"},
        {"label": "Avg cost", "val": f"₹{avg_cost}", "icon": "now", "color": "#10b981"}
    ]
    
    return {
        "stats": stats,
        "recent": recent_list,
        "saved": saved_list
    }

@app.get("/api/user/vehicles")
def get_user_vehicles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()
    return [{"id": v.id, "name": v.name, "fuel_type": v.fuel_type, "efficiency": v.efficiency} for v in vehicles]

@app.post("/api/user/vehicles")
def add_user_vehicle(req: VehicleAddRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicle = Vehicle(
        user_id=current_user.id,
        name=req.name,
        fuel_type=req.fuel_type,
        efficiency=req.efficiency
    )
    db.add(vehicle)
    db.commit()
    return {"status": "success", "vehicle_id": vehicle.id}

@app.delete("/api/user/vehicles/{vehicle_id}")
def delete_user_vehicle(vehicle_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.user_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
    return {"status": "success"}

@app.get("/api/user/documents")
def get_user_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return [
        {
            "id": d.id,
            "doc_type": d.doc_type,
            "doc_number": d.doc_number,
            "expiry_date": d.expiry_date,
            "file_path": d.file_path
        }
        for d in documents
    ]

@app.post("/api/user/documents")
async def add_user_document(
    doc_type: str = Form(...),
    doc_number: str = Form(...),
    expiry_date: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    uploads_dir = os.path.join(_HERE, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1]
    safe_filename = f"user_{current_user.id}_{doc_type.lower()}{file_ext}"
    file_dest = os.path.join(uploads_dir, safe_filename)
    
    with open(file_dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    existing = db.query(Document).filter(Document.user_id == current_user.id, Document.doc_type == doc_type).first()
    if existing:
        existing.doc_number = doc_number
        existing.expiry_date = expiry_date
        existing.file_path = f"/uploads/{safe_filename}"
        db.commit()
        return {"status": "success", "document_id": existing.id}
    else:
        doc = Document(
            user_id=current_user.id,
            doc_type=doc_type,
            doc_number=doc_number,
            expiry_date=expiry_date,
            file_path=f"/uploads/{safe_filename}"
        )
        db.add(doc)
        db.commit()
        return {"status": "success", "document_id": doc.id}

@app.delete("/api/user/documents/{doc_id}")
def delete_user_document(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        filename = doc.file_path.split("/")[-1]
        file_path = os.path.join(_HERE, "uploads", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error removing file: {e}")
        
    db.delete(doc)
    db.commit()
    return {"status": "success"} # trigger reload cabs, update reverse supplement config and reload uvicorn
