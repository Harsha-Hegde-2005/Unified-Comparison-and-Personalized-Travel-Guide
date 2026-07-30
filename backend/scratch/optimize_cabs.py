import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "modes", "cab"))

IST = ZoneInfo("Asia/Kolkata")

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

def get_surge_mult(current_time, is_auto):
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
    return 1.0 + delta_time

def main():
    # Load resolved routes
    with open("resolved_routes.json", "r", encoding="utf-8") as f:
        resolved_routes_list = json.load(f)
    resolved_routes = {r["id"]: r for r in resolved_routes_list}

    # Load benchmark
    with open("scratch/cleaned_benchmark.json", "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    # Compile dataset for each vehicle
    data_by_vehicle = {k: [] for k in VEHICLE_MAP.keys()}

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
                trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)

                is_auto = "AUTO" in entry or "BIKE" in entry or "SCOOTY" in entry
                # Let's verify is_auto based on vehicle name
                
                dist_km = r_info["distance_km"]
                dur_min = r_info["duration_min"]

                for bench_key in VEHICLE_MAP.keys():
                    if bench_key not in entry:
                        continue
                    actual = parse_actual_fare(entry[bench_key])
                    if actual is None:
                        continue
                    
                    is_vehicle_auto = "AUTO" in bench_key or "BIKE" in bench_key or "SCOOTY" in bench_key
                    surge = get_surge_mult(trip_time, is_vehicle_auto)
                    
                    data_by_vehicle[bench_key].append({
                        "dist": dist_km,
                        "dur": dur_min,
                        "time": trip_time,
                        "surge": surge,
                        "actual": actual
                    })

    # For each vehicle, let's optimize base_fare, base_dist, per_km, and min_fare
    # Formula: Fare = max(min_fare, (base_fare + max(0, dist - base_dist) * per_km) * surge)
    # Let's perform a grid search/optimization to minimize MAPE!
    
    from scipy.optimize import minimize

    print("Optimizing parameters for each vehicle type...")
    optimized_config = {}

    for bench_key, samples in data_by_vehicle.items():
        if not samples:
            continue
        
        # We want to minimize the MAPE over the samples
        # Define objective function
        def objective(params):
            base_fare, base_dist, per_km, min_fare = params
            if base_fare < 0 or base_dist < 0 or per_km < 0 or min_fare < 0:
                return 1e6
            
            ape_sum = 0.0
            for s in samples:
                pre_surge = base_fare + max(0.0, s["dist"] - base_dist) * per_km
                raw_total = pre_surge * s["surge"]
                estimate = round(max(raw_total, min_fare))
                
                ape_sum += abs(s["actual"] - estimate) / s["actual"]
            return (ape_sum / len(samples)) * 100

        # Initial guess based on existing config or heuristics
        # Let's make a reasonable initial guess
        initial_guess = [50.0, 3.0, 15.0, 50.0]
        
        # Set bounds
        bounds = [
            (10.0, 200.0), # base_fare
            (0.0, 10.0),   # base_dist
            (5.0, 50.0),   # per_km
            (10.0, 200.0)  # min_fare
        ]
        
        res = minimize(objective, initial_guess, bounds=bounds, method="Powell")
        opt_base_fare, opt_base_dist, opt_per_km, opt_min_fare = res.x
        
        # Round the values nicely
        opt_base_fare = round(opt_base_fare, 1)
        opt_base_dist = round(opt_base_dist, 1)
        opt_per_km = round(opt_per_km, 2)
        opt_min_fare = round(opt_min_fare, 1)
        
        final_mape = objective([opt_base_fare, opt_base_dist, opt_per_km, opt_min_fare])
        
        print(f"{bench_key}:")
        print(f"  base_fare: {opt_base_fare}")
        print(f"  base_dist: {opt_base_dist}")
        print(f"  per_km: {opt_per_km}")
        print(f"  min_fare: {opt_min_fare}")
        print(f"  MAPE: {final_mape:.2f}% (Accuracy: {100.0 - final_mape:.2f}%)")
        
        optimized_config[VEHICLE_MAP[bench_key]] = {
            "base_fare": opt_base_fare,
            "base_dist": opt_base_dist,
            "per_km": opt_per_km,
            "min_fare": opt_min_fare,
            "mape": final_mape
        }

    with open("scratch/optimized_rapido_params.json", "w") as f:
        json.dump(optimized_config, f, indent=2)
    print("Saved optimized parameters to scratch/optimized_rapido_params.json")

if __name__ == "__main__":
    main()
