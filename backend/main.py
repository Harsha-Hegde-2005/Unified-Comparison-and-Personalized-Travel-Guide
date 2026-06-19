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
from typing import Optional

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
    from shared.utils import resolve_stop_name
    resolved = resolve_stop_name(stop_name, "bmtc", bmtc_stops=ALL_STOPS)
    norm = resolved.strip().lower()
    if norm not in STOP_COORDS:
        return None
    return (
        float(STOP_COORDS[norm]["latitude"]),
        float(STOP_COORDS[norm]["longitude"]),
    )


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════════

class JourneyRequest(BaseModel):
    source:      str
    destination: str
    time:        Optional[str] = None   # "HH:MM" or None → now

class AllBusesRequest(BaseModel):
    source:      str
    destination: str

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
        ).json()
        el = resp["rows"][0]["elements"][0]
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


def _car_estimate(src: str, dst: str, dep_time: datetime) -> dict:
    """Rough self-drive estimate using distance heuristic."""
    est_km   = 17.0
    est_min  = 35
    fuel     = int(est_km * 5.5)
    parking  = 30
    est_fare = fuel + parking
    arr      = dep_time + timedelta(minutes=est_min)
    return {
        "available": True, "mode": "car",
        "time": est_min, "cost": est_fare,
        "transfers": 0, "distance": est_km,
        "departure": _fmt(dep_time), "arrival": _fmt(arr),
        "segments": [{
            "route": "Via Hosur Rd", "type": "car",
            "from": src, "to": dst,
            "departure": _fmt(dep_time), "arrival": _fmt(arr),
            "duration": est_min, "fare": est_fare, "distance": est_km,
            "stops": [src, dst],
        }],
        "guide": [
            {"step": 1, "icon": "car",
             "text": f"Drive to {dst} via Hosur Road / ORR",
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
    source = resolve_stop_name(req.source, "metro", metro_stations=_metro_stations)
    destination = resolve_stop_name(req.destination, "metro", metro_stations=_metro_stations)
    try:
        result = _metro_planner.plan_journey(source, destination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    dep_time = _parse_time(req.time)
    mins     = result["estimated_time"]["minutes"]
    arr_time = dep_time + timedelta(minutes=mins)

    segments = []
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
        segments.append({
            "route":     f"{leg['line']} Line",
            "type":      "metro",
            "from":      leg["from"],
            "to":        leg["to"],
            "departure": _fmt(dep_time),
            "arrival":   _fmt(dep_time + timedelta(minutes=leg_dur)),
            "duration":  leg_dur,
            "fare":      int(leg_fare),
            "distance":  round(leg.get("stations_crossed", 1) * 1.2, 1),
            "stops":     leg_stops,
        })

    guide = [{"step": 1, "icon": "walk",
              "text": f"Walk to {source} Metro Station", "duration": "5–8 min"}]
    for i, inst in enumerate(result["instructions"]):
        icon = "metro" if "Board" in inst else "transfer" if "Change" in inst else "walk"
        guide.append({"step": i + 2, "icon": icon, "text": inst, "duration": ""})
    guide.append({"step": len(guide) + 1, "icon": "walk",
                  "text": f"Walk to {destination}", "duration": "3–5 min"})

    return {
        "available":        True, "mode": "metro",
        "time":             mins,
        "cost":             int(result["fare"]["token"]),
        "cost_smart":       int(result["fare"]["smart_card"]),
        "transfers":        len(result["route"]["interchanges"]),
        "distance":         round(result["stations_crossed"] * 1.2, 1),
        "departure":        _fmt(dep_time),
        "arrival":          _fmt(arr_time),
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
def bmtc_plan(req: JourneyRequest):
    from shared.utils import resolve_stop_name
    source = resolve_stop_name(req.source, "bmtc", bmtc_stops=ALL_STOPS)
    destination = resolve_stop_name(req.destination, "bmtc", bmtc_stops=ALL_STOPS)
    src_norm = source.strip().lower()
    dst_norm = destination.strip().lower()
    dep_time = _parse_time(req.time)

    try:
        direct, transfers = get_all_buses_comprehensive(src_norm, dst_norm, departure_dt=dep_time)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not direct and not transfers:
        raise HTTPException(status_code=404,
                             detail="No BMTC route found between these stops")

    if direct:
        best = direct[0]
        dep  = dep_time
        arr  = dep + timedelta(minutes=best.get("duration") or 30)
        cost = best.get("fare") or 20
        dist = best.get("distance") or 10.0
        return {
            "available":  True, "mode": "bmtc",
            "time":       best.get("duration") or 30,
            "cost":       int(cost),
            "transfers":  0, "distance": round(dist, 1),
            "departure":  _fmt(dep), "arrival": _fmt(arr),
            "all_direct": [b["route"] for b in direct[:8]],
            "segments": [{
                "route":     best["route"], "type": "bmtc",
                "from":      source, "to": destination,
                "departure": _fmt(dep), "arrival": _fmt(arr),
                "duration":  best.get("duration") or 30,
                "fare":      int(cost), "distance": round(dist, 1),
                "stops":     best.get("stops") or [source, destination],
            }],
            "guide": [
                {"step": 1, "icon": "walk",
                 "text": f"Walk to {source} bus stop", "duration": "3–5 min"},
                {"step": 2, "icon": "bus",
                 "text": f"Board Bus {best['route']} (Direct)",
                 "duration": f"{best.get('duration') or 30} min",
                 "detail": f"₹{int(cost)} · Direct"},
                {"step": 3, "icon": "walk",
                 "text": f"Arrive at {destination}", "duration": "~1 min"},
            ],
        }

    # Transfer option
    opt  = transfers[0]
    segs = opt.get("segment_times", [])
    guide    = [{"step": 1, "icon": "walk",
                 "text": f"Walk to {source} bus stop", "duration": "3–5 min"}]
    ui_segs  = []
    for i, (seg, st) in enumerate(zip(opt["segments"], segs)):
        dep_s = st.get("departure", _fmt(dep_time))
        arr_s = st.get("arrival",   _fmt(dep_time + timedelta(minutes=st.get("duration", 20))))
        ui_segs.append({
            "route":     seg[0], "type": "bmtc",
            "from":      seg[1], "to": seg[2],
            "departure": dep_s, "arrival": arr_s,
            "duration":  st.get("duration", 20),
            "fare":      int(st.get("fare", 15)),
            "distance":  st.get("distance", 5.0),
            "stops":     list(seg[3]) if len(seg) > 3 else [seg[1], seg[2]],
        })
        guide.append({"step": i + 2, "icon": "bus",
                      "text": f"Board Bus {seg[0]}",
                      "duration": f"{st.get('duration', 20)} min",
                      "detail": f"₹{int(st.get('fare', 15))}"})
        if i < len(opt["segments"]) - 1:
            guide.append({"step": i + 3, "icon": "transfer",
                          "text": f"Transfer at {seg[2]}", "duration": "3–5 min"})
    guide.append({"step": len(guide) + 1, "icon": "walk",
                  "text": f"Arrive at {destination}", "duration": "~1 min"})

    return {
        "available": True, "mode": "bmtc",
        "time":      opt.get("total_time", 45),
        "cost":      int(opt.get("total_fare", 30)),
        "transfers": opt.get("transfers", 1),
        "distance":  opt.get("distance", 12.0),
        "departure": ui_segs[0]["departure"] if ui_segs else _fmt(dep_time),
        "arrival":   ui_segs[-1]["arrival"]  if ui_segs else "",
        "segments":  ui_segs,
        "guide":     guide,
    }


@app.post("/api/bmtc/all-buses")
def bmtc_all_buses(req: AllBusesRequest):
    from shared.utils import resolve_stop_name
    source = resolve_stop_name(req.source, "bmtc", bmtc_stops=ALL_STOPS)
    destination = resolve_stop_name(req.destination, "bmtc", bmtc_stops=ALL_STOPS)
    src_norm = source.strip().lower()
    dst_norm = destination.strip().lower()
    try:
        direct, transfers = get_all_buses_comprehensive(src_norm, dst_norm)
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
            if "auto" in vname:
                vtype = "auto"
            elif "bike" in vname:
                vtype = "bike"
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
                "available":     True, "mode": "cab",
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

    # Try Google Maps first, fall back to haversine × road-factor
    distance_km = None
    google_key  = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if google_key:
        try:
            import requests as _req
            resp = _req.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params={
                    "origins":      f"{req.source_lat},{req.source_lng}",
                    "destinations": f"{req.dest_lat},{req.dest_lng}",
                    "key":          google_key,
                },
                timeout=5,
            ).json()
            val = resp["rows"][0]["elements"][0]["distance"]["value"]
            distance_km = val / 1000.0
        except Exception:
            pass

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


# ══════════════════════════════════════════════════════════════════════════════
# COMPARE ENDPOINT  (all modes — uses coordinate-aware vehicle estimate)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/compare")
def compare(req: CompareRequest):
    dep_time = _parse_time(req.time)
    results  = {}

    # BMTC
    try:
        results["bmtc"] = bmtc_plan(
            JourneyRequest(source=req.source, destination=req.destination, time=req.time)
        )
    except Exception as e:
        results["bmtc"] = {"available": False, "mode": "bmtc", "error": str(e)}

    # Metro
    try:
        results["metro"] = metro_plan(
            JourneyRequest(source=req.source, destination=req.destination, time=req.time)
        )
    except Exception as e:
        results["metro"] = {"available": False, "mode": "metro", "error": str(e)}

    # Personal vehicle — use real coordinates + dataset if vehicle supplied
    src_coords = get_stop_coords(req.source)
    dst_coords = get_stop_coords(req.destination)

    # Cab estimates - try using real coordinates, fallback to heuristic
    if src_coords and dst_coords:
        try:
            all_estimates = []
            for p_key, p_info in RIDE_PROVIDERS.items():
                try:
                    estimates = p_info["fn"](
                        src_coords[0], src_coords[1], dst_coords[0], dst_coords[1], dep_time, "clear"
                    )
                    all_estimates.extend(estimates)
                except Exception as ex:
                    print(f"Error fetching estimates for {p_key}: {ex}")
            
            if all_estimates:
                all_estimates.sort(key=lambda x: x["cost"])
                default_est = all_estimates[0]
                results["cab"] = {
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
            else:
                results["cab"] = _cab_estimate(req.source, req.destination, dep_time)
        except Exception as e:
            print(f"Real cab estimation error: {e}")
            results["cab"] = _cab_estimate(req.source, req.destination, dep_time)
    else:
        results["cab"] = _cab_estimate(req.source, req.destination, dep_time)

    if req.vehicle and src_coords and dst_coords:
        try:
            results["car"] = vehicle_estimate(VehicleRequest(
                vehicle=req.vehicle,
                source_lat=src_coords[0], source_lng=src_coords[1],
                dest_lat=dst_coords[0],   dest_lng=dst_coords[1],
            ))
        except Exception as e:
            print(f"Vehicle estimate error: {e}")
            results["car"] = _car_estimate(req.source, req.destination, dep_time)
    else:
        results["car"] = _car_estimate(req.source, req.destination, dep_time)

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

    return {"results": results, "searched_at": datetime.now().isoformat()}


@app.post("/api/stops/coords")
def get_stops_coordinates(req: StopCoordsRequest):
    from shared.utils import resolve_stop_name
    from multimodal.config import INTERCHANGE_POINTS
    coords = {}
    for stop in req.stops:
        # Resolve as BMTC first
        resolved = resolve_stop_name(stop, "bmtc", bmtc_stops=ALL_STOPS)
        norm = resolved.strip().lower()
        if norm in STOP_COORDS:
            coords[stop] = {
                "lat": float(STOP_COORDS[norm]["latitude"]),
                "lng": float(STOP_COORDS[norm]["longitude"]),
                "resolved": resolved
            }
            continue
        
        # If not found in BMTC, resolve as Metro
        resolved = resolve_stop_name(stop, "metro", metro_stations=_metro_stations)
        matched_metro = None
        for station, pt in INTERCHANGE_POINTS.items():
            if station.lower() == resolved.lower() or station.lower() in resolved.lower():
                matched_metro = pt["coords"]
                break
        if matched_metro:
            coords[stop] = {
                "lat": float(matched_metro[0]),
                "lng": float(matched_metro[1]),
                "resolved": resolved
            }
            continue
            
        # Try a substring match on INTERCHANGE_POINTS directly
        norm_stop = stop.strip().lower()
        matched_metro = None
        for station, pt in INTERCHANGE_POINTS.items():
            if station.lower() in norm_stop:
                matched_metro = pt["coords"]
                resolved = station
                break
        if matched_metro:
            coords[stop] = {
                "lat": float(matched_metro[0]),
                "lng": float(matched_metro[1]),
                "resolved": resolved
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

@app.post("/api/chatbot/query")
def chatbot_query(req: ChatbotRequest):
    engine = ChatbotEngine(bmtc_stops=ALL_STOPS, metro_stations=_metro_stations, all_vehicles=_all_vehicles)
    
    # Extract stops
    matched_stops = engine.extract_stops(req.message)
    
    # Classify intent
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
    
    if intent in ("journey_time", "journey_cost", "budget_constrained", "possible_ways"):
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
            src_coords = get_stop_coords(source)
            dst_coords = get_stop_coords(destination)
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
                
            # Car
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
                
        src_coords = get_stop_coords(source)
        dst_coords = get_stop_coords(destination or "Indiranagar")
        
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
        # BMTC
        try:
            b_res = bmtc_plan(JourneyRequest(source=source, destination=destination or "Indiranagar", time=_fmt(dep_time)))
            if b_res.get("available") and b_res.get("cost", 999) < t_cost:
                t_cost = b_res.get("cost", 999)
                t_time = b_res.get("time", 999)
                transit_option = b_res
        except Exception:
            pass
        # Metro
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

    elif intent == "nearest_stops":
        loc = params.get("location")
        nearest = None
        if loc:
            coords = get_stop_coords(loc)
            if not coords:
                from shared.utils import resolve_stop_name
                from multimodal.config import INTERCHANGE_POINTS
                resolved = resolve_stop_name(loc, "metro", metro_stations=_metro_stations)
                for station, pt in INTERCHANGE_POINTS.items():
                    if station.lower() == resolved.lower() or station.lower() in resolved.lower():
                        coords = pt["coords"]
                        break
                        
            if coords:
                from shared.utils import resolve_stop_name
                bmtc_dists = []
                for norm, info in STOP_COORDS.items():
                    lat = float(info["latitude"])
                    lng = float(info["longitude"])
                    d = _haversine_km(coords[0], coords[1], lat, lng)
                    if d > 0.05:
                        c_name = resolve_stop_name(norm, "bmtc", bmtc_stops=ALL_STOPS)
                        bmtc_dists.append((c_name, d))
                        
                metro_dists = []
                from multimodal.config import INTERCHANGE_POINTS
                for station, pt in INTERCHANGE_POINTS.items():
                    m_coords = pt["coords"]
                    d = _haversine_km(coords[0], coords[1], m_coords[0], m_coords[1])
                    if d > 0.05:
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
    return {"status": "success"} # forced reload update