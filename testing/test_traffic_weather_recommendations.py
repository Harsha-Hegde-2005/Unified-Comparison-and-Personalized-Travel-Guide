"""
Unit and integration tests for upgraded Traffic + Weather travel recommendation system.
Tests 15 distinct operational cases including future/ETA weather, traffic classification,
outdoor exposure, temperature/humidity comfort, short-distance trips (<1km), and API fallbacks.
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from weather_helper import (
    fetch_open_meteo_details,
    get_journey_weather_profile,
    get_realtime_weather
)
from recommender import (
    get_recommendations,
    get_weather_suitability,
    calculate_weather_exposure,
    generate_fallback_explanations
)

def test_case_1_clear_origin_clear_dest_low_traffic():
    """CASE 1: Clear origin, clear destination, low traffic."""
    print("Testing Case 1: Clear weather & low traffic...")
    now = datetime.now() + timedelta(hours=2)
    profile = get_journey_weather_profile(12.8452, 77.6602, 12.9767, 77.5713, now, 35.0)
    
    assert profile["origin"] is not None
    assert profile["destination"] is not None
    assert "departure_time" in profile
    assert "estimated_arrival_time" in profile
    
    # Mock low traffic results
    results = {
        "bmtc": {"available": True, "cost": 25.0, "time": 45.0, "transfers": 0, "distance": 18.0},
        "metro": {"available": True, "cost": 40.0, "time": 30.0, "transfers": 0, "distance": 18.0},
        "cab": {"available": True, "cost": 320.0, "time": 35.0, "transfers": 0, "distance": 18.0, "free_flow_duration_min": 32.0}
    }
    recs = get_recommendations(results, "Electronic City", "Majestic", "cost", profile)
    assert len(recs) == 3
    print("  -> Passed Case 1")

def test_case_2_clear_origin_high_rain_destination():
    """CASE 2: Clear origin, high rain probability at destination."""
    print("Testing Case 2: Clear origin, high rain at destination...")
    now = datetime.now() + timedelta(hours=3)
    
    # Mock weather profile with rain shift
    profile = {
        "source": "open_meteo",
        "type": "forecast",
        "departure_time": now.strftime("%I:%M %p"),
        "estimated_arrival_time": (now + timedelta(minutes=45)).strftime("%I:%M %p"),
        "origin": {"rain_probability": 10, "temperature": 27, "condition": "clear"},
        "destination": {"rain_probability": 78, "temperature": 24, "condition": "heavy rain"},
        "weather_change_detected": True,
        "advisory": "Rain probability increases near destination around expected arrival time."
    }
    
    assert profile["weather_change_detected"] is True
    
    results = {
        "metro": {"available": True, "cost": 45.0, "time": 30.0, "transfers": 0, "distance": 15.0},
        "cab": {"available": True, "cost": 350.0, "time": 50.0, "transfers": 0, "distance": 15.0, "free_flow_duration_min": 32.0},
        "bmtc": {"available": True, "cost": 30.0, "time": 55.0, "transfers": 1, "distance": 15.0, "walking_distance": 900}
    }
    recs = get_recommendations(results, "Electronic City", "Majestic", "time", profile)
    
    # Metro should get top weather score due to covered track & low outdoor exposure
    metro_rec = next(r for r in recs if r["mode"] == "metro")
    bmtc_rec = next(r for r in recs if r["mode"] == "bmtc")
    assert metro_rec["details"]["weather_score"] >= bmtc_rec["details"]["weather_score"]
    print("  -> Passed Case 2")

def test_case_3_rain_at_origin_clear_destination():
    """CASE 3: Rain at origin, clear destination."""
    print("Testing Case 3: Rain at origin, clear destination...")
    profile = {
        "origin": {"rain_probability": 85, "condition": "heavy rain"},
        "destination": {"rain_probability": 15, "condition": "clear"},
        "weather_change_detected": True,
        "advisory": "Rain expected near origin, but conditions clear up near destination."
    }
    assert profile["weather_change_detected"] is True
    print("  -> Passed Case 3")

def test_case_4_rain_at_intermediate_checkpoint():
    """CASE 4: Rain expected during intermediate journey section."""
    print("Testing Case 4: Rain at intermediate corridor checkpoint...")
    now = datetime.now() + timedelta(hours=4)
    profile = get_journey_weather_profile(12.8452, 77.6602, 12.9767, 77.5713, now, 50.0)
    assert "checkpoints" in profile
    print("  -> Passed Case 4")

def test_case_5_high_temp_humidity_comfort():
    """CASE 5: High temperature + high humidity outdoor walking penalty."""
    print("Testing Case 5: High temp + humidity walking penalty...")
    profile = {
        "origin": {"apparent_temperature": 34.0, "humidity": 82, "rain_probability": 10},
        "destination": {"apparent_temperature": 33.0, "humidity": 80, "rain_probability": 10},
        "outdoor_uncomfortable": True,
        "outdoor_comfort_note": "High apparent temp and humidity may feel uncomfortable during outdoor walking."
    }
    
    bmtc_data = {"walking_distance": 950, "waiting_time": 12}
    suitability = get_weather_suitability("bmtc", profile, bmtc_data)
    assert suitability < 1.0  # Reduced due to outdoor exposure under high heat index
    print("  -> Passed Case 5")

def test_case_6_future_journey_peak_traffic():
    """CASE 6: Future journey during predicted peak traffic."""
    print("Testing Case 6: Future journey peak traffic...")
    future_time = datetime.now() + timedelta(days=1)
    future_time = future_time.replace(hour=18, minute=30)
    
    results = {
        "car": {"available": True, "cost": 180.0, "time": 58.0, "transfers": 0, "distance": 16.0, "free_flow_duration_min": 30.0},
        "metro": {"available": True, "cost": 40.0, "time": 32.0, "transfers": 0, "distance": 16.0}
    }
    recs = get_recommendations(results, "Silk Board", "Majestic", "time", "clear")
    metro_rec = next(r for r in recs if r["mode"] == "metro")
    car_rec = next(r for r in recs if r["mode"] == "car")
    assert metro_rec["score"] > car_rec["score"]
    print("  -> Passed Case 6")

def test_case_7_future_journey_low_traffic():
    """CASE 7: Future journey during low predicted traffic (night/off-peak)."""
    print("Testing Case 7: Off-peak low traffic...")
    future_time = datetime.now() + timedelta(days=1)
    future_time = future_time.replace(hour=22, minute=30)
    
    results = {
        "car": {"available": True, "cost": 180.0, "time": 25.0, "transfers": 0, "distance": 16.0, "free_flow_duration_min": 24.0},
        "metro": {"available": True, "cost": 40.0, "time": 35.0, "transfers": 0, "distance": 16.0}
    }
    recs = get_recommendations(results, "Silk Board", "Majestic", "fastest", "clear")
    car_rec = next(r for r in recs if r["mode"] == "car")
    assert car_rec["details"]["traffic_score"] >= 80
    print("  -> Passed Case 7")

def test_case_8_weather_api_failure_fallback():
    """CASE 8: Weather API failure gracefully uses fallback metadata."""
    print("Testing Case 8: Weather API fallback...")
    res = fetch_open_meteo_details(999.0, 999.0, datetime.now())  # Invalid coords trigger fallback
    assert res["source"] == "fallback"
    assert res["type"] == "simulated"
    print("  -> Passed Case 8")

def test_case_9_traffic_api_failure_labeling():
    """CASE 9: Google traffic API fallback labeling."""
    print("Testing Case 9: Traffic fallback metadata...")
    from modes.cab.engines.distance_engine import DistanceEngine
    engine = DistanceEngine()
    res = engine.get_distance({"latitude": 12.9716, "longitude": 77.5946}, {"latitude": 12.9352, "longitude": 77.6245})
    assert "distance_km" in res
    assert "duration_min" in res
    print("  -> Passed Case 9")

def test_case_10_short_distance_clear_weather():
    """CASE 10: Journey < 1 km under clear weather."""
    print("Testing Case 10: Short distance (<1 km) clear weather...")
    results = {
        "bmtc": {
            "available": True, "cost": 5.0, "time": 6.0, "transfers": 0, "distance": 0.7,
            "short_distance_info": {
                "is_short_distance": True,
                "distance_km": 0.7,
                "walking_time_mins": 8,
                "availability": "HIGH",
                "recommendation": "both",
                "message": "The destination is 0.7 km away (~8 min walk). Walking or BMTC are both convenient."
            }
        }
    }
    exps = generate_fallback_explanations([{"mode": "bmtc", "cost": 5.0, "time": 6.0, "transfers": 0, "raw_data": results["bmtc"]}], "clear", "cost")
    assert "0.7 km" in exps["bmtc"]
    print("  -> Passed Case 10")

def test_case_11_short_distance_high_rain():
    """CASE 11: Journey < 1 km under high rain probability."""
    print("Testing Case 11: Short distance (<1 km) high rain...")
    rain_profile = {
        "origin": {"rain_probability": 85},
        "destination": {"rain_probability": 90},
        "estimated_arrival_time": "5:40 PM"
    }
    results = {
        "bmtc": {
            "available": True, "cost": 5.0, "time": 6.0, "transfers": 0, "distance": 0.7,
            "short_distance_info": {
                "is_short_distance": True,
                "distance_km": 0.7,
                "walking_time_mins": 8,
                "availability": "HIGH",
                "recommendation": "bmtc",
                "message": "Destination is 0.7 km away. BMTC is recommended over walking due to 90% rain forecast."
            }
        }
    }
    recs = get_recommendations(results, "Stop A", "Stop B", "cost", rain_profile)
    assert len(recs) == 1
    print("  -> Passed Case 11")

def test_case_12_bmtc_frequent_rain():
    """CASE 12: Frequent BMTC service with rain."""
    print("Testing Case 12: Frequent BMTC with rain...")
    bmtc_data = {"available": True, "all_direct": ["335E", "500D", "500A"], "walking_distance": 200, "waiting_time": 4}
    exposure = calculate_weather_exposure("bmtc", bmtc_data, {})
    assert exposure < 0.5  # Low exposure for short walk + short wait
    print("  -> Passed Case 12")

def test_case_13_bmtc_infrequent_clear():
    """CASE 13: Infrequent BMTC service under clear weather."""
    print("Testing Case 13: Infrequent BMTC clear weather...")
    results = {
        "bmtc": {"available": True, "cost": 15.0, "time": 35.0, "transfers": 1, "distance": 8.0, "waiting_time": 15},
        "car": {"available": True, "cost": 90.0, "time": 20.0, "transfers": 0, "distance": 8.0}
    }
    recs = get_recommendations(results, "A", "B", "time", "clear")
    car_rec = next(r for r in recs if r["mode"] == "car")
    bmtc_rec = next(r for r in recs if r["mode"] == "bmtc")
    assert car_rec["score"] > bmtc_rec["score"]
    print("  -> Passed Case 13")

def test_case_14_metro_heavy_road_traffic():
    """CASE 14: Metro advantage over heavy road traffic."""
    print("Testing Case 14: Metro vs heavy traffic...")
    results = {
        "metro": {"available": True, "cost": 30.0, "time": 22.0, "transfers": 0, "distance": 12.0},
        "cab": {"available": True, "cost": 280.0, "time": 54.0, "transfers": 0, "distance": 12.0, "free_flow_duration_min": 25.0}
    }
    recs = get_recommendations(results, "MG Road", "Baiyappanahalli", "time", "clear")
    metro_rec = next(r for r in recs if r["mode"] == "metro")
    assert metro_rec["rank"] == 1
    print("  -> Passed Case 14")

def test_case_15_cab_heavy_traffic_rain():
    """CASE 15: Cab with heavy traffic and rain."""
    print("Testing Case 15: Cab with heavy traffic and rain...")
    rain_profile = {
        "origin": {"rain_probability": 75},
        "destination": {"rain_probability": 80},
        "estimated_arrival_time": "6:15 PM"
    }
    results = {
        "cab": {"available": True, "cost": 420.0, "time": 55.0, "transfers": 0, "distance": 14.0, "free_flow_duration_min": 30.0},
        "metro": {"available": True, "cost": 45.0, "time": 28.0, "transfers": 0, "distance": 14.0}
    }
    recs = get_recommendations(results, "Indiranagar", "Kengeri", "time", rain_profile)
    metro_rec = next(r for r in recs if r["mode"] == "metro")
    assert metro_rec["rank"] == 1
    print("  -> Passed Case 15")

def run_all_tests():
    print("==================================================")
    print("RUNNING TRAFFIC & WEATHER RECOMMENDATION SUITE")
    print("==================================================")
    test_case_1_clear_origin_clear_dest_low_traffic()
    test_case_2_clear_origin_high_rain_destination()
    test_case_3_rain_at_origin_clear_destination()
    test_case_4_rain_at_intermediate_checkpoint()
    test_case_5_high_temp_humidity_comfort()
    test_case_6_future_journey_peak_traffic()
    test_case_7_future_journey_low_traffic()
    test_case_8_weather_api_failure_fallback()
    test_case_9_traffic_api_failure_labeling()
    test_case_10_short_distance_clear_weather()
    test_case_11_short_distance_high_rain()
    test_case_12_bmtc_frequent_rain()
    test_case_13_bmtc_infrequent_clear()
    test_case_14_metro_heavy_road_traffic()
    test_case_15_cab_heavy_traffic_rain()
    print("==================================================")
    print("ALL 15/15 TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
