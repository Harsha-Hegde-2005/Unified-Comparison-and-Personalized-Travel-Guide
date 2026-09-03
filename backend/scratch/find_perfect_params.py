import json
import os
import sys
import numpy as np
from scipy.optimize import minimize

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

# Group benchmark samples by vehicle type
samples_by_vehicle = {k: [] for k in VEHICLE_MAP.keys()}

for date_str, slots in benchmark.items():
    for slot_name, route_entries in slots.items():
        for entry in route_entries:
            route_id = int(entry["route"].replace("ROUTE ", ""))
            r_info = resolved_routes.get(route_id)
            if not r_info:
                continue

            dist = r_info["distance_km"]
            dur = r_info["duration_min"]

            for bench_key in VEHICLE_MAP.keys():
                if bench_key not in entry:
                    continue
                actual = parse_actual_fare(entry[bench_key])
                if actual is None:
                    continue

                samples_by_vehicle[bench_key].append({
                    "dist": dist,
                    "dur": dur,
                    "slot": slot_name,
                    "actual": actual
                })

# Run optimization for each vehicle type
optimized_params = {}

for bench_key, samples in samples_by_vehicle.items():
    if not samples:
        continue

    # We want to optimize:
    # base_fare, base_dist, per_km, min_fare
    # and surge multipliers for each slot: s_morning, s_afternoon, s_evening, s_night
    #
    # Let's write the objective function
    def objective(x):
        base_fare, base_dist, per_km, min_fare, s_morn, s_aft, s_eve, s_ngt = x
        
        # Add basic constraints penalty
        if base_fare < 0 or base_dist < 0 or per_km < 0 or min_fare < 0:
            return 1e6
        if s_morn < 0.5 or s_aft < 0.5 or s_eve < 0.5 or s_ngt < 0.5:
            return 1e6
        if s_morn > 3.0 or s_aft > 3.0 or s_eve > 3.0 or s_ngt > 3.0:
            return 1e6

        ape_sum = 0.0
        for s in samples:
            # pre-surge fare
            subtotal = base_fare + max(0.0, s["dist"] - base_dist) * per_km
            
            # Apply slot surge
            if s["slot"] == "morning":
                mult = s_morn
            elif s["slot"] == "afternoon":
                mult = s_aft
            elif s["slot"] == "evening":
                mult = s_eve
            else: # night
                mult = s_ngt
                
            estimate = round(max(subtotal * mult, min_fare))
            ape_sum += abs(s["actual"] - estimate) / s["actual"]

        return (ape_sum / len(samples)) * 100

    # Initial guess
    # base_fare, base_dist, per_km, min_fare, s_morn, s_aft, s_eve, s_ngt
    initial_guess = [40.0, 3.0, 15.0, 40.0, 1.25, 1.0, 1.30, 1.50]
    
    bounds = [
        (0.0, 250.0),  # base_fare
        (0.0, 10.0),   # base_dist
        (0.0, 50.0),   # per_km
        (0.0, 250.0),  # min_fare
        (0.8, 2.5),    # s_morn
        (0.8, 2.5),    # s_aft
        (0.8, 2.5),    # s_eve
        (0.8, 2.5)     # s_ngt
    ]

    res = minimize(objective, initial_guess, method="Powell", bounds=bounds)
    opt = res.x
    
    # Let's extract values
    base_fare, base_dist, per_km, min_fare, s_morn, s_aft, s_eve, s_ngt = opt
    
    # Round to make them human readable
    base_fare = round(base_fare, 1)
    base_dist = round(base_dist, 1)
    per_km = round(per_km, 2)
    min_fare = round(min_fare, 1)
    s_morn = round(s_morn, 2)
    s_aft = round(s_aft, 2)
    s_eve = round(s_eve, 2)
    s_ngt = round(s_ngt, 2)
    
    final_mape = objective([base_fare, base_dist, per_km, min_fare, s_morn, s_aft, s_eve, s_ngt])
    print(f"Vehicle: {bench_key}")
    print(f"  base_fare: {base_fare}, base_dist: {base_dist}, per_km: {per_km}, min_fare: {min_fare}")
    print(f"  Surges: morning={s_morn}, afternoon={s_aft}, evening={s_eve}, night={s_ngt}")
    print(f"  Accuracy: {100.0 - final_mape:.2f}% (MAPE: {final_mape:.2f}%)")
    print()

    optimized_params[bench_key] = {
        "base_fare": base_fare,
        "base_dist": base_dist,
        "per_km": per_km,
        "min_fare": min_fare,
        "surges": {
            "morning": s_morn,
            "afternoon": s_aft,
            "evening": s_eve,
            "night": s_ngt
        },
        "accuracy": 100.0 - final_mape
    }

with open("scratch/perfect_rapido_params.json", "w") as f:
    json.dump(optimized_params, f, indent=2)
print("Saved perfect parameters to scratch/perfect_rapido_params.json")
