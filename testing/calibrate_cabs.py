"""
testing/calibrate_cabs.py
==========================
UTRS Cab Fare Calibration Script.
Generates 200 random coordinate pairs in Bengaluru, queries DistanceEngine/OSRM
for road distance + time, computes simulated fares, and validates them against
the official specification tariff matrices.
"""

import sys
import os
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Ensure backend path is in sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_BACKEND = os.path.join(_ROOT, "backend")

sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "modes", "cab"))

from engines.distance_engine import DistanceEngine
from engines.fare_engine import FareEngine

IST = ZoneInfo("Asia/Kolkata")

# Bengaluru bounding box from spec
LAT_MIN, LAT_MAX = 12.8500, 13.0800
LNG_MIN, LNG_MAX = 77.4500, 77.7500


def get_random_coord():
    return {
        "latitude": random.uniform(LAT_MIN, LAT_MAX),
        "longitude": random.uniform(LNG_MIN, LNG_MAX)
    }


def calculate_spec_fare(base_fare, base_dist, per_km, per_min, min_fare,
                        distance, duration, surge_multiplier):
    """Reference implementation of the tariff formula in the spec."""
    dist_charge = max(0.0, distance - base_dist) * per_km
    dur_charge = duration * per_min
    subtotal = base_fare + dist_charge + dur_charge
    fare = max(subtotal, min_fare) * surge_multiplier
    return round(fare)


def main():
    print("=" * 60)
    print("UTRS CAB FARE ENGINE CALIBRATION & MAPE VALIDATION")
    print("=" * 60)

    # 1. Load engines
    config_path = os.path.abspath(os.path.join(_ROOT, "database", "cab", "fare_config.json"))
    fare_engine = FareEngine(config_path)
    distance_engine = DistanceEngine()

    print(f"Loaded providers: {list(fare_engine.providers.keys())}")

    # Official spec parameter matrix
    spec_tariffs = {
        "namma_yatri": {
            "auto": {"base_fare": 30.0, "base_dist": 2.0, "per_km": 15.0, "per_min": 0.0, "min_fare": 30.0},
            "non_ac_cab": {"base_fare": 80.0, "base_dist": 4.0, "per_km": 18.0, "per_min": 1.0, "min_fare": 80.0},
            "ac_cab": {"base_fare": 100.0, "base_dist": 4.0, "per_km": 21.0, "per_min": 1.2, "min_fare": 100.0}
        },
        "uber": {
            "uber_auto": {"base_fare": 35.0, "base_dist": 1.5, "per_km": 16.5, "per_min": 0.0, "min_fare": 35.0},
            "uber_go": {"base_fare": 85.0, "base_dist": 3.0, "per_km": 19.5, "per_min": 1.5, "min_fare": 85.0},
            "uber_premier": {"base_fare": 110.0, "base_dist": 3.0, "per_km": 24.0, "per_min": 2.0, "min_fare": 110.0},
            "uber_xl": {"base_fare": 150.0, "base_dist": 3.0, "per_km": 30.0, "per_min": 2.5, "min_fare": 150.0}
        },
        "ola": {
            "ola_auto": {"base_fare": 35.0, "base_dist": 1.5, "per_km": 16.0, "per_min": 0.0, "min_fare": 35.0},
            "ola_mini": {"base_fare": 90.0, "base_dist": 3.0, "per_km": 19.0, "per_min": 1.6, "min_fare": 90.0},
            "ola_prime": {"base_fare": 115.0, "base_dist": 3.0, "per_km": 23.0, "per_min": 2.1, "min_fare": 115.0}
        },
        "rapido": {
            "rapido_bike": {"base_fare": 20.0, "base_dist": 1.0, "per_km": 11.0, "per_min": 0.0, "min_fare": 20.0},
            "rapido_auto": {"base_fare": 30.0, "base_dist": 1.5, "per_km": 15.5, "per_min": 0.0, "min_fare": 30.0},
            "rapido_cab": {"base_fare": 80.0, "base_dist": 3.0, "per_km": 18.0, "per_min": 1.4, "min_fare": 80.0}
        }
    }

    # Weather levels and time categories to randomize over
    weathers = ["clear", "light rain", "heavy rain", "storm"]
    
    # We will generate a base time in IST and vary hours
    base_dt = datetime.now(IST)

    total_predictions = 0
    total_absolute_pct_error = 0.0

    print("\nGenerating 200 random coordinate trips...")
    
    # Run 200 iterations
    for i in range(1, 201):
        src = get_random_coord()
        dst = get_random_coord()
        
        # Get road distance + time (OSRM or Haversine fallback)
        try:
            route = distance_engine.get_distance(src, dst)
        except Exception as e:
            print(f"Skipping route {i} due to routing error: {e}")
            continue

        dist_km = route["distance_km"]
        dur_min = route["duration_min"]

        # Randomize weather & time
        weather = random.choice(weathers)
        hour = random.choice([9, 14, 19, 23, 2])  # Covers morning/evening peak, offpeak, late night
        minute = random.randint(0, 59)
        trip_time = base_dt.replace(hour=hour, minute=minute)

        for provider, vehicles in spec_tariffs.items():
            for vehicle_key, spec_params in vehicles.items():
                is_auto = "auto" in vehicle_key or "bike" in vehicle_key
                surge = fare_engine.get_surge_multiplier(trip_time, weather, is_auto)

                # 1. Expected fare from spec formula
                expected = calculate_spec_fare(
                    spec_params["base_fare"],
                    spec_params["base_dist"],
                    spec_params["per_km"],
                    spec_params["per_min"],
                    spec_params["min_fare"],
                    dist_km,
                    dur_min,
                    surge
                )

                # 2. Estimate from FareEngine
                res = fare_engine.get_fare(provider, vehicle_key, dist_km, dur_min, trip_time, weather)
                estimated = res["fare_min"]

                # 3. Compute percentage error
                absolute_pct_error = abs(expected - estimated) / expected
                total_absolute_pct_error += absolute_pct_error
                total_predictions += 1

    # Calculate MAPE
    if total_predictions == 0:
        print("Error: No predictions generated.")
        sys.exit(1)

    mape = (total_absolute_pct_error / total_predictions) * 100
    accuracy = 100.0 - mape

    print("-" * 60)
    print(f"Validation completed over {total_predictions} fare simulations.")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.4f}%")
    print(f"Overall Fare Calibration Accuracy: {accuracy:.4f}% (Goal: >= 90%)")
    print("-" * 60)

    if mape <= 10.0:
        print("PASS: Cab pricing matches the spec model with MAPE <= 10% (Accuracy >= 90%).")
        sys.exit(0)
    else:
        print("FAIL: Cab pricing MAPE exceeds 10%. Please inspect tariff configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
