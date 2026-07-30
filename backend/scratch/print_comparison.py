import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "modes", "cab"))

from engines.fare_engine import FareEngine
from engines.time_engine import TimeEngine
from weather_helper import get_realtime_weather
IST = ZoneInfo("Asia/Kolkata")

# Load resolved routes
with open("resolved_routes.json", "r", encoding="utf-8") as f:
    resolved_routes = {r["id"]: r for r in json.load(f)}

# Load benchmark
with open("scratch/cleaned_benchmark.json", "r", encoding="utf-8") as f:
    benchmark = json.load(f)

# Load FareEngine
config_path = os.path.join(_ROOT, "database", "cab", "fare_config.json")
fare_engine = FareEngine(config_path)
time_eng = TimeEngine()

def parse_actual_fare(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        if "-" in val:
            parts = val.split("-")
            return (float(parts[0]) + float(parts[1])) / 2.0
        try:
            return float(val)
        except ValueError:
            return None
    return None

VEHICLE_MAP = {
    "BIKE DIRECT": "rapido_bike",
    "SCOOTY DIRECT": "rapido_scooty",
    "BIKE RATED BY WOMEN": "rapido_bike_women",
    "AUTO LITE": "rapido_auto_lite",
    "AUTO": "rapido_auto",
    "AUTO PRIORITY": "rapido_auto_priority",
    "CAB NON AC": "rapido_cab",
    "CAB AC": "rapido_cab_ac",
    "CAB AC PRIORITY": "rapido_cab_ac_priority",
    "AUTO PET": "rapido_auto_pet",
    "CAB PREMIUM": "rapido_cab_premium",
    "CAB XL": "rapido_cab_xl"
}

# Print comparison for BIKE DIRECT and AUTO
for date_str, slots in list(benchmark.items())[:1]:
    dt_parts = [int(x) for x in date_str.split("-")]
    for slot_name, route_entries in list(slots.items())[:2]:
        print(f"\n=== {date_str} {slot_name} ===")
        for entry in route_entries[:3]:
            route_id = int(entry["route"].replace("ROUTE ", ""))
            r_info = resolved_routes[route_id]
            
            time_str = entry["time"]
            hour, minute = [int(x) for x in time_str.split(":")]
            trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)
            
            dist = r_info["distance_km"]
            osrm_dur = r_info["duration_min"]
            time_est = time_eng.estimate_duration(osrm_dur, dist, trip_time)
            travel_min = time_est["minutes"]
            weather = get_realtime_weather(trip_time)
            
            print(f"ROUTE {route_id} (dist={dist}km, osrm_dur={osrm_dur}min, travel_min={travel_min}min, weather={weather}):")
            for bench_key in ["BIKE DIRECT", "AUTO", "CAB NON AC"]:
                actual = parse_actual_fare(entry[bench_key])
                vehicle_key = VEHICLE_MAP[bench_key]
                try:
                    res = fare_engine.get_fare("rapido", vehicle_key, dist, travel_min, trip_time, weather)
                    est = res["fare_min"]
                    print(f"  {bench_key:<15} | Actual: {actual:<5} | Est: {est:<5} | Diff: {actual - est:<5} | Surge: {res.get('surge_mult', 1.0)}")
                except Exception as e:
                    print(f"  {bench_key:<15} | Error: {e}")
