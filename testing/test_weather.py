import pytest
from datetime import datetime, timedelta
from weather_helper import map_wmo_code, get_realtime_weather

def test_weather_helper_mapping():
    # Clear codes
    assert map_wmo_code(0) == "clear"
    assert map_wmo_code(3) == "clear"
    # Drizzle / Light rain codes
    assert map_wmo_code(51) == "light rain"
    assert map_wmo_code(61) == "light rain"
    # Heavy rain codes
    assert map_wmo_code(63) == "heavy rain"
    assert map_wmo_code(80) == "heavy rain"
    assert map_wmo_code(95) == "heavy rain"
    # Out of range defaults to clear
    assert map_wmo_code(999) == "clear"

def test_weather_helper_api_resolution():
    # Fetch live weather (or mock fallback if offline)
    cond = get_realtime_weather()
    assert cond in ("clear", "light rain", "heavy rain")

def test_weather_helper_out_of_range_fallback():
    # 10 days in the future (out of forecast bounds) -> triggers fallback
    future_time = datetime.now() + timedelta(days=10)
    cond = get_realtime_weather(future_time)
    assert cond in ("clear", "light rain", "heavy rain")
