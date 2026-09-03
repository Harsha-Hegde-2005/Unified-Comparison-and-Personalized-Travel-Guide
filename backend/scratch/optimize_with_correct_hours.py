import json
import os
import sys
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
from scipy.optimize import minimize

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "modes", "cab"))

from engines.time_engine import TimeEngine
from weather_helper import get_realtime_weather
IST = ZoneInfo("Asia/Kolkata")

# Load resolved routes
with open("resolved_routes.json", "r", encoding="utf-8") as f:
    resolved_routes = {r["id"]: r for r in json.load(f)}

# Load benchmark
with open("scratch/cleaned_benchmark.json", "r", encoding="utf-8") as f:
    benchmark = json.load(f)

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

time_eng = TimeEngine()

def get_surge_mult(current_time, weather, is_auto):
    time_minutes = current_time.hour * 60 + current_time.minute
    delta_time = 0.0
    if is_auto:
        if time_minutes >= (22 * 60) or time_minutes < (5 * 60):
            delta_time = 0.50
    else:
        if (8 * 60 + 30) <= time_minutes <= (10 * 60 + 30):
            delta_time = 0.25
        elif (17 * 60 + 30) <= time_minutes <= (20 * 60 + 30):
            delta_time = 0.30
        elif time_minutes >= (22 * 60) or time_minutes < (5 * 60):
            delta_time = 0.50

    delta_weather = 0.0
    weather_lower = weather.lower()
    if "light" in weather_lower or "drizzle" in weather_lower:
        delta_weather = 0.15
    elif "heavy" in weather_lower or "thunder" in weather_lower:
        delta_weather = 0.40
    elif "storm" in weather_lower or "flood" in weather_lower:
        delta_weather = 0.75
        
    return 1.0 + delta_time + delta_weather

# Group benchmark samples by vehicle type
samples_by_vehicle = {k: [] for k in VEHICLE_MAP.keys()}

for date_str, slots in benchmark.items():
    dt_parts = [int(x) for x in date_str.split("-")]
    for slot_name, route_entries in slots.items():
        for entry in route_entries:
            route_id = int(entry["route"].replace("ROUTE ", ""))
            r_info = resolved_routes.get(route_id)
            if not r_info:
                continue

            time_str = entry["time"]
            hour, minute = [int(x) for x in time_str.split(":")]
            
            # Apply 12-hour to 24-hour conversion
            if slot_name in ("afternoon", "evening", "night") and hour < 12:
                hour += 12
                
            trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)

            dist = r_info["distance_km"]
            osrm_dur = r_info["duration_min"]
            
            # Get traffic-adjusted duration
            time_est = time_eng.estimate_duration(osrm_dur, dist, trip_time)
            travel_min = time_est["minutes"]
            weather = get_realtime_weather(trip_time)

            for bench_key in VEHICLE_MAP.keys():
                if bench_key not in entry:
                    continue
                actual = parse_actual_fare(entry[bench_key])
                if actual is None:
                    continue

                samples_by_vehicle[bench_key].append({
                    "dist": dist,
                    "dur": travel_min,
                    "time": trip_time,
                    "weather": weather,
                    "actual": actual
                })

# Run optimization for each vehicle type
optimized_params = {}

for bench_key, samples in samples_by_vehicle.items():
    if not samples:
        continue
    
    # We want to optimize: base_fare, base_dist, per_km, per_min, min_fare, booking_fee
    
    def objective(x):
        base_fare, base_dist, per_km, per_min, min_fare, booking_fee = x
        if any(v < 0 for v in [base_fare, base_dist, per_km, per_min, min_fare, booking_fee]):
            return 1e6

        ape_sum = 0.0
        for s in samples:
            billable_km = max(0.0, s["dist"] - base_dist)
            pre_surge = base_fare + billable_km * per_km + s["dur"] * per_min
            
            is_auto = "auto" in VEHICLE_MAP[bench_key] or "bike" in VEHICLE_MAP[bench_key]
            surge = get_surge_mult(s["time"], s["weather"], is_auto)
            
            raw_total = pre_surge * surge + booking_fee
            
            # Apply long distance surcharge
            if s["dist"] > 40.0:
                if "CAB" in bench_key or "AUTO PET" in bench_key or "AUTO PRIORITY" in bench_key:
                    raw_total += 350.0

            estimate = round(max(raw_total, min_fare))
            ape_sum += abs(s["actual"] - estimate) / s["actual"]

        return (ape_sum / len(samples)) * 100

    initial_guess = [30.0, 2.0, 12.0, 0.0, 30.0, 0.0]
    
    bounds = [
        (0.0, 250.0),  # base_fare
        (0.0, 10.0),   # base_dist
        (0.0, 50.0),   # per_km
        (0.0, 10.0),   # per_min
        (0.0, 250.0),  # min_fare
        (0.0, 50.0)    # booking_fee
    ]

    res = minimize(objective, initial_guess, method="Powell", bounds=bounds)
    opt = res.x
    
    base_fare, base_dist, per_km, per_min, min_fare, booking_fee = opt
    
    # Round
    base_fare = round(base_fare, 1)
    base_dist = round(base_dist, 1)
    per_km = round(per_km, 2)
    per_min = round(per_min, 2)
    min_fare = round(min_fare, 1)
    booking_fee = round(booking_fee, 1)
    
    final_mape = objective([base_fare, base_dist, per_km, per_min, min_fare, booking_fee])
    print(f"Vehicle: {bench_key}")
    print(f"  base_fare: {base_fare}, base_dist: {base_dist}, per_km: {per_km}, per_min: {per_min}, min_fare: {min_fare}")
    print(f"  booking_fee: {booking_fee}")
    print(f"  Accuracy: {100.0 - final_mape:.2f}% (MAPE: {final_mape:.2f}%)")
    print()

    optimized_params[bench_key] = {
        "base_fare": base_fare,
        "base_dist": base_dist,
        "per_km": per_km,
        "per_min": per_min,
        "min_fare": min_fare,
        "booking_fee": booking_fee,
        "accuracy": 100.0 - final_mape
    }

with open("scratch/perfect_rapido_params_correct_hours.json", "w") as f:
    json.dump(optimized_params, f, indent=2)
print("Saved parameters to scratch/perfect_rapido_params_correct_hours.json")
