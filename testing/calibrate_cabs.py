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


def calculate_spec_fare(cfg, distance, duration, current_time, weather, is_auto):
    """Reference implementation of the updated tariff formula."""
    base_fare = cfg.get("base_fare", 0.0)
    base_dist = cfg.get("base_dist", 0.0)
    per_km_rate = cfg.get("per_km", 0.0)
    per_min_rate = cfg.get("per_min", 0.0)

    billable_km = max(0.0, distance - base_dist)
    distance_charge = round(billable_km * per_km_rate, 2)
    duration_charge = round(duration * per_min_rate, 2)

    waiting_charge = 0.0  # Default waiting time is 0.0 in calibration simulation

    pre_surge_subtotal = round(base_fare + distance_charge + duration_charge + waiting_charge, 2)

    # Surge Multiplier
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
    if "light rain" in weather_lower or "drizzle" in weather_lower:
        delta_weather = 0.15
    elif "heavy rain" in weather_lower or "thunderstorm" in weather_lower:
        delta_weather = 0.40
    elif "storm" in weather_lower or "flood" in weather_lower:
        delta_weather = 0.75

    surge_mult = 1.0 + delta_time + delta_weather
    surge_amount = round(pre_surge_subtotal * (surge_mult - 1.0), 2)

    # Night Surcharge
    night_cfg = cfg.get("night_charge")
    night_active = False
    night_mult = 1.0
    if night_cfg and night_cfg.get("enabled", False):
        start_hour = night_cfg.get("start_hour", 22)
        end_hour = night_cfg.get("end_hour", 5)
        hour = current_time.hour
        if start_hour == end_hour:
            night_active = False
        elif start_hour < end_hour:
            night_active = start_hour <= hour < end_hour
        else:
            night_active = hour >= start_hour or hour < end_hour

        if night_active:
            night_mult = night_cfg.get("multiplier", 1.0)

    night_amount = round((pre_surge_subtotal + surge_amount) * (night_mult - 1.0), 2)

    # Booking Fee
    booking_fee = cfg.get("booking_fee", 0.0)

    # Long Distance Surcharge
    long_distance_cfg = cfg.get("long_distance")
    long_distance_charge = 0.0
    if long_distance_cfg:
        threshold_km = long_distance_cfg.get("threshold_km", 0.0)
        if distance > threshold_km:
            long_distance_charge = long_distance_cfg.get("surcharge", 0.0)

    # Total estimate
    raw_total = round(pre_surge_subtotal + surge_amount + night_amount + booking_fee + long_distance_charge, 2)
    min_fare = cfg.get("min_fare", 0.0)
    estimate = max(raw_total, min_fare)
    return round(estimate)


def main():
    print("=" * 60)
    print("UTRS CAB FARE ENGINE CALIBRATION & MAPE VALIDATION (CALIBRATED)")
    print("=" * 60)

    # 1. Load engines
    config_path = os.path.abspath(os.path.join(_ROOT, "database", "cab", "fare_config.json"))
    fare_engine = FareEngine(config_path)
    distance_engine = DistanceEngine()

    print(f"Loaded providers: {list(fare_engine.providers.keys())}")

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

        for provider_key, provider_cfg in fare_engine.providers.items():
            for vehicle_key, vehicle_cfg in provider_cfg["vehicles"].items():
                is_auto = "auto" in vehicle_key or "bike" in vehicle_key

                # 1. Expected fare from spec formula
                expected = calculate_spec_fare(
                    vehicle_cfg,
                    dist_km,
                    dur_min,
                    trip_time,
                    weather,
                    is_auto
                )

                # 2. Estimate from FareEngine
                res = fare_engine.get_fare(provider_key, vehicle_key, dist_km, dur_min, trip_time, weather)
                estimated = res["fare_min"]

                # 3. Compute percentage error
                if expected == 0:
                    continue
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
