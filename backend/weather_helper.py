import requests
import time as _time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Bengaluru Coordinates (Fallback default if lat/lng not supplied)
BENGALURU_LAT = 12.9716
BENGALURU_LNG = 77.5946

# Cache for Open-Meteo responses: (lat_round, lng_round, date_str) -> (timestamp, data)
_WEATHER_CACHE: Dict[tuple, tuple] = {}
_CACHE_TTL = 600  # 10 minutes TTL

def get_simulated_weather_fallback(time_val: datetime) -> str:
    """Mock simulated weather timeline fallback."""
    h = time_val.hour
    if 8 <= h <= 10:
        return "light rain"
    elif 15 <= h <= 18:
        return "heavy rain"
    else:
        return "clear"

def map_wmo_code(code: int) -> str:
    """
    Map WMO weather codes to standard categories:
    'clear', 'light rain', 'heavy rain'.
    """
    if 0 <= code <= 3:
        return "clear"
    elif code in (51, 53, 55, 56, 57, 61):
        return "light rain"
    elif code in (63, 65, 66, 67, 80, 81, 82, 95, 96, 99):
        return "heavy rain"
    return "clear"

def fetch_open_meteo_details(lat: float, lng: float, target_time: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Fetch comprehensive hourly forecast variables from Open-Meteo for given coordinates and target_time.
    Supports current vs future forecast classification, API efficiency caching, and fallback metrics.
    """
    if target_time is None:
        target_time = datetime.now()
        
    tz = target_time.tzinfo
    now = datetime.now(tz) if tz else datetime.now()
    is_now = abs((target_time - now).total_seconds()) <= 1800
    is_future = target_time > (now + timedelta(minutes=30))
    
    formatted_time = target_time.strftime("%I:%M %p").lstrip("0")
    
    # Check cache
    lat_r = round(float(lat), 2)
    lng_r = round(float(lng), 2)
    date_str = target_time.strftime("%Y-%m-%d")
    cache_key = (lat_r, lng_r, date_str)
    
    now_ts = _time.time()
    cached_entry = _WEATHER_CACHE.get(cache_key)
    data = None
    if cached_entry and (now_ts - cached_entry[0]) < _CACHE_TTL:
        data = cached_entry[1]
        
    if data is None and abs((target_time - now).days) <= 6:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat_r,
                "longitude": lng_r,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m",
                "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,rain,weather_code,wind_speed_10m",
                "timezone": "Asia/Kolkata"
            }
            resp = requests.get(url, params=params, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                _WEATHER_CACHE[cache_key] = (now_ts, data)
        except Exception:
            data = None
            
    if data:
        # Extract matching hourly or current slot
        current_block = data.get("current", {})
        hourly_block = data.get("hourly", {})
        
        rounded_time = target_time + timedelta(minutes=30)
        target_iso_hour = rounded_time.strftime("%Y-%m-%dT%H:00")
        
        times = hourly_block.get("time", [])
        idx = -1
        if target_iso_hour in times:
            idx = times.index(target_iso_hour)
            
        if is_now and current_block:
            w_code = current_block.get("weather_code", 0)
            temp = current_block.get("temperature_2m", 26.0)
            app_temp = current_block.get("apparent_temperature", temp)
            humidity = current_block.get("relative_humidity_2m", 60.0)
            precip = current_block.get("precipitation", 0.0)
            wind = current_block.get("wind_speed_10m", 10.0)
            
            # Default rain prob from precip if hourly index available
            rain_prob = 0
            if idx != -1 and idx < len(hourly_block.get("precipitation_probability", [])):
                rain_prob = hourly_block["precipitation_probability"][idx] or (80 if precip > 0.5 else 10)
            else:
                rain_prob = 80 if precip > 1.0 else (40 if precip > 0.1 else 10)
                
            cond = map_wmo_code(w_code)
            return {
                "source": "open_meteo",
                "type": "current",
                "latitude": lat_r,
                "longitude": lng_r,
                "time_iso": target_time.isoformat(),
                "formatted_time": formatted_time,
                "temperature": round(float(temp), 1),
                "apparent_temperature": round(float(app_temp), 1),
                "humidity": int(humidity),
                "rain_probability": int(rain_prob),
                "precipitation": round(float(precip), 1),
                "weather_code": int(w_code),
                "condition": cond,
                "wind_speed": round(float(wind), 1)
            }
        elif idx != -1:
            w_code = hourly_block.get("weather_code", [])[idx] if idx < len(hourly_block.get("weather_code", [])) else 0
            temp = hourly_block.get("temperature_2m", [])[idx] if idx < len(hourly_block.get("temperature_2m", [])) else 25.0
            app_temp = hourly_block.get("apparent_temperature", [])[idx] if idx < len(hourly_block.get("apparent_temperature", [])) else temp
            humidity = hourly_block.get("relative_humidity_2m", [])[idx] if idx < len(hourly_block.get("relative_humidity_2m", [])) else 60.0
            rain_prob = hourly_block.get("precipitation_probability", [])[idx] if idx < len(hourly_block.get("precipitation_probability", [])) else 10
            precip = hourly_block.get("precipitation", [])[idx] if idx < len(hourly_block.get("precipitation", [])) else 0.0
            wind = hourly_block.get("wind_speed_10m", [])[idx] if idx < len(hourly_block.get("wind_speed_10m", [])) else 10.0
            
            cond = map_wmo_code(w_code or 0)
            return {
                "source": "open_meteo",
                "type": "forecast" if is_future else "historical",
                "latitude": lat_r,
                "longitude": lng_r,
                "time_iso": target_time.isoformat(),
                "formatted_time": formatted_time,
                "temperature": round(float(temp or 25.0), 1),
                "apparent_temperature": round(float(app_temp or temp or 25.0), 1),
                "humidity": int(humidity or 60),
                "rain_probability": int(rain_prob or 0),
                "precipitation": round(float(precip or 0.0), 1),
                "weather_code": int(w_code or 0),
                "condition": cond,
                "wind_speed": round(float(wind or 10.0), 1)
            }

    # Fallback to simulated mock data
    sim_cond = get_simulated_weather_fallback(target_time)
    rain_prob = 80 if sim_cond == "heavy rain" else (45 if sim_cond == "light rain" else 10)
    precip = 6.0 if sim_cond == "heavy rain" else (1.2 if sim_cond == "light rain" else 0.0)
    w_code = 65 if sim_cond == "heavy rain" else (61 if sim_cond == "light rain" else 0)
    
    return {
        "source": "fallback",
        "type": "simulated",
        "latitude": lat_r,
        "longitude": lng_r,
        "time_iso": target_time.isoformat(),
        "formatted_time": formatted_time,
        "temperature": 26.0,
        "apparent_temperature": 27.0,
        "humidity": 65,
        "rain_probability": rain_prob,
        "precipitation": precip,
        "weather_code": w_code,
        "condition": sim_cond,
        "wind_speed": 12.0
    }

def get_realtime_weather(target_time: Optional[datetime] = None) -> str:
    """
    Backwards-compatible string weather getter for legacy endpoints.
    Fetches real-time or hourly weather condition for Bengaluru.
    """
    details = fetch_open_meteo_details(BENGALURU_LAT, BENGALURU_LNG, target_time)
    return details.get("condition", "clear")

def get_journey_weather_profile(
    src_lat: float,
    src_lng: float,
    dst_lat: float,
    dst_lng: float,
    dep_time: datetime,
    est_duration_min: float = 40.0
) -> Dict[str, Any]:
    """
    Calculates ETA-aware, multi-checkpoint weather profile along the journey path.
    Evaluates weather at departure location at departure time, and destination location at arrival time.
    Samples intermediate checkpoints for longer trips.
    """
    est_duration_min = max(5.0, float(est_duration_min))
    arr_time = dep_time + timedelta(minutes=est_duration_min)
    
    # 1. Fetch Origin Weather (Departure time)
    origin_weather = fetch_open_meteo_details(src_lat, src_lng, dep_time)
    
    # 2. Fetch Destination Weather (Arrival ETA time)
    dest_weather = fetch_open_meteo_details(dst_lat, dst_lng, arr_time)
    
    # 3. Intermediate Checkpoints (if distance > 8 km or duration > 20 mins)
    checkpoints = []
    # Calculate approximate distance
    from math import radians, cos, sin, asin, sqrt
    def _dist(l1, g1, l2, g2):
        r = 6371.0
        dlat, dgng = radians(l2 - l1), radians(g2 - g1)
        a = sin(dlat/2)**2 + cos(radians(l1))*cos(radians(l2))*sin(dgng/2)**2
        return r * 2 * asin(sqrt(a))
        
    total_dist_km = _dist(src_lat, src_lng, dst_lat, dst_lng)
    
    if total_dist_km >= 8.0:
        # Sample 1 midpoint checkpoint
        mid_lat = (src_lat + dst_lat) / 2.0
        mid_lng = (src_lng + dst_lng) / 2.0
        mid_time = dep_time + timedelta(minutes=est_duration_min / 2.0)
        mid_weather = fetch_open_meteo_details(mid_lat, mid_lng, mid_time)
        checkpoints.append({
            "name": "Midpoint Corridor",
            "lat": round(mid_lat, 4),
            "lng": round(mid_lng, 4),
            "eta": mid_time.strftime("%I:%M %p").lstrip("0"),
            "weather": mid_weather
        })

    # Weather change detection logic
    orig_prob = origin_weather.get("rain_probability", 0)
    dest_prob = dest_weather.get("rain_probability", 0)
    prob_diff = dest_prob - orig_prob
    
    weather_change_detected = False
    advisory = None
    
    if prob_diff >= 25:
        weather_change_detected = True
        advisory = (
            f"🌧️ Weather change expected: Conditions are expected to remain clearer near your starting point "
            f"({orig_prob}% rain probability), but the probability of rain increases to {dest_prob}% near your "
            f"destination around your expected arrival time (~{dest_weather['formatted_time']})."
        )
    elif prob_diff <= -25:
        weather_change_detected = True
        advisory = (
            f"🌦️ Rain expected near origin ({orig_prob}%), but conditions are forecast to clear up near your "
            f"destination by your arrival time (~{dest_weather['formatted_time']}, {dest_prob}% rain probability)."
        )
    elif max(orig_prob, dest_prob) >= 60:
        weather_change_detected = True
        advisory = (
            f"🌧️ Rain expected along the journey corridor (~{max(orig_prob, dest_prob)}% rain probability around "
            f"your travel window)."
        )
    else:
        advisory = f"☀️ Favorable weather conditions expected along your route (~{dest_weather['temperature']}°C)."

    # Outdoor comfort assessment (heat index / humidity for walking/bike)
    max_temp = max(origin_weather.get("apparent_temperature", 25), dest_weather.get("apparent_temperature", 25))
    max_hum = max(origin_weather.get("humidity", 50), dest_weather.get("humidity", 50))
    
    outdoor_uncomfortable = (max_temp >= 31.0 and max_hum >= 70) or (max_temp >= 34.0)
    outdoor_comfort_note = None
    if outdoor_uncomfortable:
        outdoor_comfort_note = (
            f"🌡️ High apparent temperature ({max_temp}°C) and humidity ({max_hum}%) may feel uncomfortable "
            f"during outdoor walking or waiting segments."
        )

    return {
        "source": dest_weather.get("source", "open_meteo"),
        "type": dest_weather.get("type", "forecast"),
        "departure_time": dep_time.strftime("%I:%M %p").lstrip("0"),
        "estimated_arrival_time": arr_time.strftime("%I:%M %p").lstrip("0"),
        "estimated_duration_min": round(est_duration_min, 1),
        "origin": origin_weather,
        "destination": dest_weather,
        "checkpoints": checkpoints,
        "weather_change_detected": weather_change_detected,
        "advisory": advisory,
        "outdoor_uncomfortable": outdoor_uncomfortable,
        "outdoor_comfort_note": outdoor_comfort_note
    }

