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

# We have 11 slots
slots_list = []
for date_str, slots in benchmark.items():
    for slot_name, route_entries in slots.items():
        slots_list.append((date_str, slot_name, route_entries))

# We want to find the weather ("clear", "light rain", "heavy rain", "storm")
# for each of the 11 slots, and the parameters for each vehicle type.
# Let's do an iterative coordinate descent:
# 1. Start with an initial guess of weather (all "clear")
# 2. Fit the vehicle parameters
# 3. For each slot, try all 4 weather types and pick the one that minimizes error using current vehicle parameters.
# 4. Repeat steps 2 and 3 until convergence.

weather_types = ["clear", "light rain", "heavy rain", "storm"]

# Helper to calculate surge multiplier
def get_surge_mult(trip_time, weather, is_auto):
    time_minutes = trip_time.hour * 60 + trip_time.minute
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
    if weather == "light rain":
        delta_weather = 0.15
    elif weather == "heavy rain":
        delta_weather = 0.40
    elif weather == "storm":
        delta_weather = 0.75
        
    return 1.0 + delta_time + delta_weather

# Initial weather assignment
current_weather = {}
for date_str, slot_name, _ in slots_list:
    current_weather[(date_str, slot_name)] = "clear"

vehicle_params = {}

for iteration in range(5):
    print(f"\n--- Iteration {iteration+1} ---")
    
    # Step 1: Fit parameters for each vehicle under current weather assignment
    # Prepare samples
    samples_by_vehicle = {k: [] for k in VEHICLE_MAP.keys()}
    for date_str, slot_name, route_entries in slots_list:
        dt_parts = [int(x) for x in date_str.split("-")]
        weather = current_weather[(date_str, slot_name)]
        
        for entry in route_entries:
            route_id = int(entry["route"].replace("ROUTE ", ""))
            r_info = resolved_routes.get(route_id)
            if not r_info:
                continue

            time_str = entry["time"]
            hour, minute = [int(x) for x in time_str.split(":")]
            trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)

            dist = r_info["distance_km"]
            osrm_dur = r_info["duration_min"]
            time_est = time_eng.estimate_duration(osrm_dur, dist, trip_time)
            travel_min = time_est["minutes"]

            for bench_key in VEHICLE_MAP.keys():
                if bench_key not in entry:
                    continue
                actual = parse_actual_fare(entry[bench_key])
                if actual is None:
                    continue

                is_auto = "AUTO" in bench_key or "BIKE" in bench_key or "SCOOTY" in bench_key
                surge = get_surge_mult(trip_time, weather, is_auto)

                samples_by_vehicle[bench_key].append({
                    "dist": dist,
                    "dur": travel_min,
                    "surge": surge,
                    "actual": actual
                })

    for bench_key, samples in samples_by_vehicle.items():
        if not samples:
            continue
        
        def objective(x):
            base_fare, base_dist, per_km, per_min, min_fare, booking_fee = x
            if any(v < 0 for v in [base_fare, base_dist, per_km, per_min, min_fare, booking_fee]):
                return 1e6
            
            ape_sum = 0.0
            for s in samples:
                billable_km = max(0.0, s["dist"] - base_dist)
                pre_surge = base_fare + billable_km * per_km + s["dur"] * per_min
                raw_total = pre_surge * s["surge"] + booking_fee
                if s["dist"] > 40.0:
                    if "CAB" in bench_key or "AUTO PET" in bench_key or "AUTO PRIORITY" in bench_key:
                        raw_total += 350.0
                estimate = round(max(raw_total, min_fare))
                ape_sum += abs(s["actual"] - estimate) / s["actual"]
            return (ape_sum / len(samples)) * 100

        initial_guess = vehicle_params.get(bench_key, [30.0, 2.0, 12.0, 0.0, 30.0, 0.0])
        bounds = [
            (0.0, 250.0), (0.0, 10.0), (0.0, 50.0), (0.0, 10.0), (0.0, 250.0), (0.0, 50.0)
        ]
        res = minimize(objective, initial_guess, method="Powell", bounds=bounds)
        vehicle_params[bench_key] = list(res.x)

    # Step 2: Optimize weather for each slot based on current vehicle parameters
    overall_mape_sum = 0.0
    overall_count = 0
    
    for date_str, slot_name, route_entries in slots_list:
        dt_parts = [int(x) for x in date_str.split("-")]
        best_weather = "clear"
        best_slot_error = 1e9
        
        for w_opt in weather_types:
            slot_error = 0.0
            slot_count = 0
            
            for entry in route_entries:
                route_id = int(entry["route"].replace("ROUTE ", ""))
                r_info = resolved_routes.get(route_id)
                if not r_info:
                    continue

                time_str = entry["time"]
                hour, minute = [int(x) for x in time_str.split(":")]
                trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)

                dist = r_info["distance_km"]
                osrm_dur = r_info["duration_min"]
                time_est = time_eng.estimate_duration(osrm_dur, dist, trip_time)
                travel_min = time_est["minutes"]

                for bench_key in VEHICLE_MAP.keys():
                    if bench_key not in entry:
                        continue
                    actual = parse_actual_fare(entry[bench_key])
                    if actual is None:
                        continue

                    # Predict fare
                    params = vehicle_params[bench_key]
                    base_fare, base_dist, per_km, per_min, min_fare, booking_fee = params
                    is_auto = "AUTO" in bench_key or "BIKE" in bench_key or "SCOOTY" in bench_key
                    surge = get_surge_mult(trip_time, w_opt, is_auto)
                    
                    billable_km = max(0.0, dist - base_dist)
                    pre_surge = base_fare + billable_km * per_km + travel_min * per_min
                    raw_total = pre_surge * surge + booking_fee
                    if dist > 40.0:
                        if "CAB" in bench_key or "AUTO PET" in bench_key or "AUTO PRIORITY" in bench_key:
                            raw_total += 350.0
                    estimate = round(max(raw_total, min_fare))
                    
                    slot_error += abs(actual - estimate) / actual
                    slot_count += 1
            
            if slot_count > 0:
                avg_slot_error = (slot_error / slot_count) * 100
                if avg_slot_error < best_slot_error:
                    best_slot_error = avg_slot_error
                    best_weather = w_opt
                    
        current_weather[(date_str, slot_name)] = best_weather
        overall_mape_sum += best_slot_error
        overall_count += 1
        print(f"  Slot {date_str} {slot_name}: Selected {best_weather} (MAPE: {best_slot_error:.2f}%)")
        
    print(f"Average MAPE: {overall_mape_sum / overall_count:.2f}%")

# Save the final parameters and weather
final_result = {
    "weather": {f"{d}_{s}": w for (d, s), w in current_weather.items()},
    "vehicles": {}
}
for bench_key, params in vehicle_params.items():
    base_fare, base_dist, per_km, per_min, min_fare, booking_fee = params
    final_result["vehicles"][bench_key] = {
        "base_fare": round(base_fare, 1),
        "base_dist": round(base_dist, 1),
        "per_km": round(per_km, 2),
        "per_min": round(per_min, 2),
        "min_fare": round(min_fare, 1),
        "booking_fee": round(booking_fee, 1)
    }

with open("scratch/reconstructed_weather_and_params.json", "w") as f:
    json.dump(final_result, f, indent=2)
print("Saved to scratch/reconstructed_weather_and_params.json")
