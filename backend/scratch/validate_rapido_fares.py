import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Ensure backend path is in sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "modes", "cab"))

from engines.fare_engine import FareEngine

IST = ZoneInfo("Asia/Kolkata")

# Mapping from benchmark key to vehicle_key
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

def main():
    # Load resolved routes mapping
    with open("resolved_routes.json", "r", encoding="utf-8") as f:
        resolved_routes_list = json.load(f)
    resolved_routes = {r["id"]: r for r in resolved_routes_list}

    # Load cleaned benchmark
    with open("scratch/cleaned_benchmark.json", "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    # Load FareEngine
    config_path = os.path.join(_ROOT, "database", "cab", "fare_config.json")
    
    # We will dynamically inject rapido_auto_lite if not present to avoid runtime crashes
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    
    rapido_vehicles = config_data["providers"]["rapido"]["vehicles"]
    if "rapido_auto_lite" not in rapido_vehicles:
        print("Injected rapido_auto_lite template for analysis")
        # Template starting configuration for auto_lite
        rapido_vehicles["rapido_auto_lite"] = {
            "name": "Auto Lite",
            "base_fare": 50.0,
            "base_dist": 2.0,
            "per_km": 15.0,
            "per_min": 0.0,
            "min_fare": 50.0,
            "capacity": 3,
            "description": "Affordable auto request",
            "icon": "🛺",
            "vtype": "auto_lite",
            "waiting_charge_per_min": 0.0,
            "free_waiting_mins": 0.0,
            "booking_fee": 0.0,
            "night_charge": {
                "enabled": False,
                "start_hour": 23,
                "end_hour": 5,
                "multiplier": 1.0
            }
        }
        # Write modified config back temporarily for FareEngine initialization
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

    fare_engine = FareEngine(config_path)

    # We will accumulate errors per vehicle type
    errors = {k: [] for k in VEHICLE_MAP.keys()}

    for date_str, slots in benchmark.items():
        # Parse date
        dt_parts = [int(x) for x in date_str.split("-")]
        
        for slot_name, route_entries in slots.items():
            for entry in route_entries:
                route_id = int(entry["route"].replace("ROUTE ", ""))
                r_info = resolved_routes.get(route_id)
                if not r_info:
                    continue

                time_str = entry["time"]
                hour, minute = [int(x) for x in time_str.split(":")]
                
                # Combine date + time
                trip_time = datetime(dt_parts[0], dt_parts[1], dt_parts[2], hour, minute, tzinfo=IST)

                # Determine weather
                from weather_helper import get_realtime_weather
                weather = get_realtime_weather(trip_time)

                dist_km = r_info["distance_km"]
                dur_min = r_info["duration_min"]

                for bench_key, vehicle_key in VEHICLE_MAP.items():
                    if bench_key not in entry:
                        continue
                    actual = parse_actual_fare(entry[bench_key])
                    if actual is None:
                        continue

                    # Get simulated fare
                    try:
                        res = fare_engine.get_fare("rapido", vehicle_key, dist_km, dur_min, trip_time, weather)
                        estimated = float(res["fare_min"])
                        
                        ape = abs(actual - estimated) / actual
                        errors[bench_key].append((date_str, slot_name, route_id, actual, estimated, ape))
                    except Exception as e:
                        print(f"Error calculating fare for {bench_key} / {vehicle_key}: {e}")

    # Print report
    print("\n" + "="*80)
    print(f"{'VEHICLE TYPE':<25} | {'SIMULATIONS':<12} | {'MAPE (%)':<10} | {'ACCURACY (%)':<12}")
    print("="*80)
    
    global_total = 0
    global_ape_sum = 0.0

    for bench_key, sims in errors.items():
        if not sims:
            print(f"{bench_key:<25} | {'0':<12} | {'N/A':<10} | {'N/A':<12}")
            continue
        mape = (sum(x[5] for x in sims) / len(sims)) * 100
        accuracy = 100.0 - mape
        print(f"{bench_key:<25} | {len(sims):<12} | {mape:.2f}% | {accuracy:.2f}%")
        
        global_total += len(sims)
        global_ape_sum += sum(x[5] for x in sims)

    if global_total > 0:
        global_mape = (global_ape_sum / global_total) * 100
        global_accuracy = 100.0 - global_mape
        print("="*80)
        print(f"{'OVERALL RAPIDO':<25} | {global_total:<12} | {global_mape:.2f}% | {global_accuracy:.2f}%")
        print("="*80)
    else:
        print("No predictions were simulated.")

if __name__ == "__main__":
    main()
