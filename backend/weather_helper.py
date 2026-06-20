import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Bengaluru Coordinates
BENGALURU_LAT = 12.9716
BENGALURU_LNG = 77.5946

def get_simulated_weather_fallback(time: datetime) -> str:
    """Mock simulated weather timeline fallback."""
    h = time.hour
    if 8 <= h <= 10:
        return "light rain"
    elif 15 <= h <= 18:
        return "heavy rain"
    else:
        return "clear"

def map_wmo_code(code: int) -> str:
    """
    Map WMO weather codes to standard chatbot/fare engine categories:
    'clear', 'light rain', 'heavy rain'.
    """
    # 0: Clear sky
    # 1, 2, 3: Mainly clear, partly cloudy, and overcast
    if 0 <= code <= 3:
        return "clear"
    
    # 51, 53, 55: Drizzle (light, moderate, dense)
    # 56, 57: Freezing Drizzle
    # 61: Slight rain
    elif code in (51, 53, 55, 56, 57, 61):
        return "light rain"
    
    # 63, 65: Moderate and heavy rain
    # 66, 67: Freezing rain
    # 80, 81, 82: Rain showers (slight, moderate, violent)
    # 95, 96, 99: Thunderstorm
    elif code in (63, 65, 66, 67, 80, 81, 82, 95, 96, 99):
        return "heavy rain"
        
    return "clear"

def get_realtime_weather(target_time: Optional[datetime] = None) -> str:
    """
    Fetch real-time weather from Open-Meteo for Bengaluru coordinates.
    If target_time is provided, look up the hourly forecast matching that time.
    Otherwise, fetch current weather conditions.
    
    Falls back to mock simulated timeline if the API call fails or returns an error.
    """
    if target_time is None:
        target_time = datetime.now()
        
    # Check if target_time is within 7 days from now (Open-Meteo standard forecast window)
    now = datetime.now()
    if abs((target_time - now).days) > 6:
        # Out of forecast range, default directly to mock fallback
        return get_simulated_weather_fallback(target_time)

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": BENGALURU_LAT,
            "longitude": BENGALURU_LNG,
            "current": "weather_code,rain,showers",
            "hourly": "weather_code,rain,showers",
            "timezone": "Asia/Kolkata"
        }
        
        # Timeout 4s to ensure fast chatbot response even on network lag
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code != 200:
            return get_simulated_weather_fallback(target_time)
            
        data = resp.json()
        
        # If target_time is close to current time (within 30 mins), use current weather
        if abs((target_time - now).total_seconds()) <= 1800:
            current_code = data.get("current", {}).get("weather_code")
            if current_code is not None:
                return map_wmo_code(current_code)
                
        # Hourly forecast lookup
        # Round target_time to closest hour boundary
        rounded_time = target_time + timedelta(minutes=30)
        target_iso_hour = rounded_time.strftime("%Y-%m-%dT%H:00")
        
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        codes = hourly.get("weather_code", [])
        
        if target_iso_hour in times:
            idx = times.index(target_iso_hour)
            if idx < len(codes):
                return map_wmo_code(codes[idx])
                
        # Fallback if specific hour index wasn't found in times list
        current_code = data.get("current", {}).get("weather_code")
        if current_code is not None:
            return map_wmo_code(current_code)
            
        return get_simulated_weather_fallback(target_time)

    except Exception:
        # Fallback on connection errors, timeout, DNS failures, etc.
        return get_simulated_weather_fallback(target_time)
