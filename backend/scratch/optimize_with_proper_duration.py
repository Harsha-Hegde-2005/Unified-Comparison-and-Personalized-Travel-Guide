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
            trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)

            dist = r_info["distance_km"]
            osrm_dur = r_info["duration_min"]
            
            # Get traffic-adjusted duration
            time_est = time_eng.estimate_duration(osrm_dur, dist, trip_time)
            travel_min = time_est["minutes"]

            for bench_key in VEHICLE_MAP.keys():
                if bench_key not in entry:
                    continue
                actual = parse_actual_fare(entry[bench_key])
                if actual is None:
                    continue

                samples_by_vehicle[bench_key].append({
                    "dist": dist,
                    "dur": travel_min, # use traffic-adjusted duration!
                    "slot": slot_name,
                    "time": trip_time,
                    "actual": actual
                })

# Run optimization for each vehicle type
optimized_params = {}

for bench_key, samples in samples_by_vehicle.items():
    if not samples:
        continue

    # Let's fit:
    # 0: base_fare, 1: base_dist, 2: per_km, 3: per_min, 4: min_fare
    # 5: s_morn, 6: s_aft, 7: s_eve, 8: s_ngt
    # 9: booking_fee
    
    def objective(x):
        base_fare, base_dist, per_km, per_min, min_fare, s_morn, s_aft, s_eve, s_ngt, booking_fee = x
        
        # Penalties for invalid values
        if any(v < 0 for v in [base_fare, base_dist, per_km, per_min, min_fare, booking_fee]):
            return 1e6
        if any(s < 0.5 or s > 3.0 for s in [s_morn, s_aft, s_eve, s_ngt]):
            return 1e6

        ape_sum = 0.0
        for s in samples:
            billable_km = max(0.0, s["dist"] - base_dist)
            pre_surge = base_fare + billable_km * per_km + s["dur"] * per_min
            
            if s["slot"] == "morning":
                mult = s_morn
            elif s["slot"] == "afternoon":
                mult = s_aft
            elif s["slot"] == "evening":
                mult = s_eve
            else:
                mult = s_ngt
                
            raw_total = pre_surge * mult + booking_fee
            
            # Add long-distance surcharge for > 40km for cabs/pet
            if s["dist"] > 40.0:
                if "CAB" in bench_key or "AUTO PET" in bench_key or "AUTO PRIORITY" in bench_key:
                    raw_total += 350.0

            estimate = round(max(raw_total, min_fare))
            ape_sum += abs(s["actual"] - estimate) / s["actual"]

        return (ape_sum / len(samples)) * 100

    # Initial guess
    initial_guess = [30.0, 2.0, 12.0, 0.0, 30.0, 1.25, 1.0, 1.30, 1.50, 0.0]
    
    bounds = [
        (0.0, 250.0),  # base_fare
        (0.0, 10.0),   # base_dist
        (0.0, 50.0),   # per_km
        (0.0, 10.0),   # per_min
        (0.0, 250.0),  # min_fare
        (0.8, 2.5),    # s_morn
        (0.8, 2.5),    # s_aft
        (0.8, 2.5),    # s_eve
        (0.8, 2.5),    # s_ngt
        (0.0, 50.0)    # booking_fee
    ]

    res = minimize(objective, initial_guess, method="Powell", bounds=bounds)
    opt = res.x
    
    base_fare, base_dist, per_km, per_min, min_fare, s_morn, s_aft, s_eve, s_ngt, booking_fee = opt
    
    # Round nicely
    base_fare = round(base_fare, 1)
    base_dist = round(base_dist, 1)
    per_km = round(per_km, 2)
    per_min = round(per_min, 2)
    min_fare = round(min_fare, 1)
    s_morn = round(s_morn, 2)
    s_aft = round(s_aft, 2)
    s_eve = round(s_eve, 2)
    s_ngt = round(s_ngt, 2)
    booking_fee = round(booking_fee, 1)
    
    final_mape = objective([base_fare, base_dist, per_km, per_min, min_fare, s_morn, s_aft, s_eve, s_ngt, booking_fee])
    print(f"Vehicle: {bench_key}")
    print(f"  base_fare: {base_fare}, base_dist: {base_dist}, per_km: {per_km}, per_min: {per_min}, min_fare: {min_fare}")
    print(f"  Surges: morning={s_morn}, afternoon={s_aft}, evening={s_eve}, night={s_ngt}")
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
        "surges": {
            "morning": s_morn,
            "afternoon": s_aft,
            "evening": s_eve,
            "night": s_ngt
        },
        "accuracy": 100.0 - final_mape
    }

with open("scratch/perfect_rapido_params_traffic_duration.json", "w") as f:
    json.dump(optimized_params, f, indent=2)
print("Saved parameters to scratch/perfect_rapido_params_traffic_duration.json")
