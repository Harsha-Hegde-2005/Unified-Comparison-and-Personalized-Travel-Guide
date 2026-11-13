import os
import json
import requests
from typing import Dict, Any, List, Union

def calculate_emissions(mode: str, distance: float) -> float:
    """Estimate CO2 emissions in grams based on mode and distance."""
    factors = {
        "metro": 10.0,
        "bmtc": 25.0,
        "multimodal": 25.0,
        "car": 120.0,
        "cab": 150.0,
        "bike": 35.0,
        "walk": 0.0
    }
    return round(distance * factors.get(mode, 25.0), 1)

def get_comfort_score(mode: str, transfers: int, distance: float, is_vajra: bool = False) -> float:
    """Calculate comfort/convenience baseline score (0.1 to 1.0)."""
    baselines = {
        "cab": 1.0,
        "car": 0.95,
        "metro": 0.80,
        "bmtc": 0.60,
        "multimodal": 0.50,
        "bike": 0.65,
        "walk": 0.85 if distance < 1.0 else 0.40
    }
    score = baselines.get(mode, 0.60)
    if is_vajra and mode in ("bmtc", "multimodal"):
        score = 0.85  # AC Vajra/Volvo buses are highly comfortable
    
    # Penalize transfers
    score -= (transfers * 0.15)
    
    # Bound to a sensible minimum
    return max(0.1, round(score, 2))

def calculate_weather_exposure(mode: str, data: Dict[str, Any], weather_info: Any) -> float:
    """
    Calculate outdoor exposure score (0.0 = completely sheltered, 1.0 = fully exposed to outdoors).
    """
    if mode in ("walk", "walking"):
        return 1.0
    elif mode in ("bike", "scooty"):
        return 0.95
    elif mode == "bmtc":
        # Bus itself is covered, but walking to stop + waiting is outdoor exposure
        walk_m = data.get("walking_distance", 500) or 500
        wait_m = data.get("waiting_time", 8) or 8
        if walk_m < 300 and wait_m < 5:
            return 0.35
        elif walk_m > 800 or wait_m > 12:
            return 0.75
        return 0.55
    elif mode == "metro":
        # Metro is covered, walking to station is outdoor exposure
        walk_m = data.get("walking_distance", 400) or 400
        return 0.25 if walk_m < 500 else 0.45
    elif mode in ("cab", "car"):
        return 0.10  # Door-to-door
    elif mode == "multimodal":
        return 0.50
    return 0.50

def get_weather_suitability(mode: str, weather_info: Any, data: Dict[str, Any] = None) -> float:
    """Determine weather suitability score (0.1 to 1.0) based on outdoor exposure and forecast rain/heat."""
    data = data or {}
    
    # Handle string weather representation (legacy fallback)
    if isinstance(weather_info, str):
        w_str = weather_info.lower()
        if w_str == "heavy rain":
            suitability = {"metro": 1.0, "car": 0.70, "cab": 0.60, "bmtc": 0.50, "multimodal": 0.45, "bike": 0.15, "walk": 0.10}
        elif w_str == "light rain":
            suitability = {"metro": 1.0, "car": 0.90, "cab": 0.90, "bmtc": 0.80, "multimodal": 0.75, "bike": 0.40, "walk": 0.30}
        else:
            suitability = {"metro": 1.0, "car": 1.0, "cab": 1.0, "bmtc": 1.0, "multimodal": 1.0, "bike": 0.95, "walk": 0.95}
        return suitability.get(mode, 1.0)

    # Handle rich dict weather representation
    if isinstance(weather_info, dict):
        dest_weather = weather_info.get("destination", {})
        orig_weather = weather_info.get("origin", {})
        
        orig_rain = orig_weather.get("rain_probability", 0)
        dest_rain = dest_weather.get("rain_probability", 0)
        max_rain = max(orig_rain, dest_rain)
        
        exposure = calculate_weather_exposure(mode, data, weather_info)
        
        # Base suitability starts at 1.0 and is penalized by (rain_prob * exposure)
        penalty = (max_rain / 100.0) * exposure * 0.85
        
        # Heat/humidity penalty for high exposure modes
        if weather_info.get("outdoor_uncomfortable") and exposure > 0.6:
            penalty += 0.20
            
        return max(0.1, round(1.0 - penalty, 2))
        
    return 1.0

def generate_fallback_explanations(
    options: List[Dict[str, Any]],
    weather_info: Any,
    preference: str,
    source: str = "",
    destination: str = ""
) -> Dict[str, str]:
    """Provide dynamic, numerical, data-driven XAI explanations detailing weather at ETA, traffic delay, and comfort trade-offs."""
    explanations = {}
    preference = (preference or "cost").lower()
    
    # Extract weather summary & numbers
    if isinstance(weather_info, dict):
        orig_w = weather_info.get("origin", {})
        dest_w = weather_info.get("destination", {})
        dest_eta = weather_info.get("estimated_arrival_time", "ETA")
        orig_prob = orig_w.get("rain_probability", 0)
        dest_prob = dest_w.get("rain_probability", 0)
        orig_temp = orig_w.get("temperature", 27)
        dest_temp = dest_w.get("temperature", 27)
        dest_hum = dest_w.get("humidity", 65)
        max_rain = max(orig_prob, dest_prob)
        weather_desc = f"Rain probability is {orig_prob}% at departure and {dest_prob}% near destination at ETA (~{dest_eta})."
    elif isinstance(weather_info, str):
        max_rain = 80 if "rain" in weather_info.lower() else 10
        orig_prob, dest_prob = max_rain, max_rain
        dest_eta = "ETA"
        orig_temp, dest_temp, dest_hum = 27, 27, 65
        weather_desc = f"Expected weather condition: {weather_info}."
    else:
        max_rain, orig_prob, dest_prob = 10, 10, 10
        dest_eta = "ETA"
        orig_temp, dest_temp, dest_hum = 27, 27, 65
        weather_desc = "Clear weather expected along the route."

    for opt in options:
        mode = opt["mode"]
        cost = opt["cost"]
        cost_max = opt.get("cost_max", cost)
        time = opt["time"]
        transfers = opt["transfers"]
        distance = opt.get("distance", 0.0)
        raw = opt.get("raw_data", {})
        
        # Traffic delay extraction
        free_flow = raw.get("free_flow_duration_min")
        delay_min = round(time - free_flow, 1) if free_flow and free_flow > 0 and time > free_flow else 0.0
        traffic_level = "HEAVY" if delay_min >= 12 else ("MODERATE" if delay_min >= 4 else "LOW")
        
        # Format cost string
        if mode == "cab" or (cost_max and cost_max > cost):
            cost_str = f"₹{int(cost)}–₹{int(cost_max)}"
        else:
            cost_str = f"₹{int(cost)}"
            
        if mode == "bmtc":
            short_info = raw.get("short_distance_info")
            if short_info and short_info.get("is_short_distance"):
                explanations["bmtc"] = (
                    f"🚶 Short-distance trip ({distance:.1f} km): Walking takes ~{short_info.get('walking_time_mins', 9)} mins at 5 km/h. "
                    f"BMTC Bus ({cost_str}) is available, but waiting at the stop may exceed the 9-min walking time."
                )
            elif max_rain >= 50:
                explanations["bmtc"] = (
                    f"🚌 BMTC Bus is economical ({cost_str} for {distance:.1f} km), but {max_rain}% rain forecast at ETA (~{dest_eta}) "
                    f"may increase outdoor exposure (~500 m walk & wait) under {dest_temp}°C temperature."
                )
            elif delay_min >= 8:
                explanations["bmtc"] = (
                    f"🚌 BMTC Bus costs {cost_str} for {distance:.1f} km (est. {time} mins), facing predicted arterial road traffic delay (+{delay_min} mins)."
                )
            else:
                explanations["bmtc"] = (
                    f"🚌 Direct BMTC Bus service takes ~{time} mins over {distance:.1f} km for {cost_str}, offering low emissions ({opt.get('emissions', 0)}g CO2)."
                )

        elif mode == "metro":
            if delay_min >= 8 or max_rain >= 50:
                explanations["metro"] = (
                    f"🚇 Namma Metro is highly recommended for this {distance:.1f} km journey: taking ~{time} mins at {cost_str}, "
                    f"it completely bypasses predicted road traffic (+{delay_min} min delay on roads) and keeps outdoor walking under ~400 m during {max_rain}% rain forecast."
                )
            else:
                explanations["metro"] = (
                    f"🚇 Namma Metro provides a reliable, traffic-free trip in {time} mins for {cost_str} across {distance:.1f} km with minimal outdoor exposure."
                )
                
        elif mode == "multimodal":
            if max_rain >= 50:
                explanations["multimodal"] = (
                    f"🚌+🚇 Multimodal route balances cost ({cost_str} over {distance:.1f} km in {time} mins), but {transfers} transfer(s) "
                    f"increase outdoor exposure during forecast {dest_prob}% rain."
                )
            else:
                explanations["multimodal"] = (
                    f"🚌+🚇 Multimodal option combines rapid Metro transit with last-mile bus/auto coverage ({distance:.1f} km in {time} mins for {cost_str})."
                )
                
        elif mode == "cab":
            if max_rain >= 50 and delay_min >= 8:
                explanations["cab"] = (
                    f"🚕 Cab/Auto provides direct door-to-door comfort keeping you dry during {max_rain}% rain forecast, "
                    f"though heavy traffic adds +{delay_min} min delay (total ~{time} mins). Note: The displayed {cost_str} fare is an approximate estimate and actual pricing may vary."
                )
            elif delay_min >= 8:
                explanations["cab"] = (
                    f"🚕 Cab/Auto provides peak convenience for {distance:.1f} km in ~{time} mins (+{delay_min} min traffic delay). "
                    f"The displayed {cost_str} fare is an estimate based on available pricing models; actual pricing may vary."
                )
            else:
                explanations["cab"] = (
                    f"🚕 Cab/Auto provides direct door-to-door transit for {distance:.1f} km in ~{time} mins. "
                    f"The estimated fare is {cost_str}; actual fare may vary based on demand and surge."
                )
                
        elif mode == "car":
            if delay_min >= 8:
                explanations["car"] = (
                    f"🚗 Private vehicle offers direct route flexibility for {distance:.1f} km (~{time} mins), "
                    f"facing +{delay_min} min predicted traffic delay and estimated fuel cost of {cost_str}."
                )
            else:
                explanations["car"] = (
                    f"🚗 Private vehicle provides maximum scheduling freedom for {distance:.1f} km in ~{time} mins under {dest_temp}°C weather at est. fuel cost of {cost_str}."
                )
                
    return explanations


def get_recommendations(
    results: Dict[str, Any],
    source: str,
    destination: str,
    preference: str = "cost",
    weather: Union[str, Dict[str, Any]] = "clear"
) -> List[Dict[str, Any]]:
    """
    Ranks available transit options and returns Top-K recommendations with dynamic XAI explanations.
    Supports location-aware, ETA-aware weather profiles, traffic delay classification, and data source transparency.
    """
    available_options = []
    
    # 1. Filter out only available modes
    for mode, data in results.items():
        if not isinstance(data, dict) or not data.get("available"):
            continue
        
        cost = float(data.get("cost", 0.0))
        cost_max = float(data.get("cost_max", cost))
        time_val = float(data.get("time", 0.0))
        transfers = int(data.get("transfers", 0))
        distance = float(data.get("distance", 0.0))
        
        # Check if this route contains an AC/Vajra bus
        is_vajra = False
        if mode in ("bmtc", "multimodal"):
            segments = data.get("segments", [])
            for seg in segments:
                if seg.get("type") == "bmtc" or (seg.get("route") and seg.get("route") != "Walk"):
                    route_name = seg.get("route", "")
                    if any(p in route_name.upper() for p in ["AC", "V-", "VAJRA", "VOLVO"]):
                        is_vajra = True
                        break
        
        # Calculate carbon emissions and baseline comfort/weather suitability
        emissions = calculate_emissions(mode, distance)
        comfort = get_comfort_score(mode, transfers, distance, is_vajra=is_vajra)
        weather_suit = get_weather_suitability(mode, weather, data)
        
        # Calculate dynamic traffic score
        traffic_score = 1.0
        if mode == "metro":
            traffic_score = 1.0
        elif mode in ("car", "cab", "bmtc", "multimodal"):
            free_flow = data.get("free_flow_duration_min")
            actual_time = data.get("time")
            if free_flow and actual_time and free_flow > 0:
                delay_factor = max(1.0, actual_time / free_flow)
                traffic_score = max(0.1, min(1.0, 1.0 / delay_factor))
            else:
                import datetime
                h = datetime.datetime.now().hour
                if 8 <= h <= 10 or 17 <= h <= 20:
                    traffic_score = 0.4
                elif 12 <= h <= 15 or 21 <= h <= 23:
                    traffic_score = 0.7
                else:
                    traffic_score = 0.95

        available_options.append({
            "mode": mode,
            "cost": cost,
            "cost_max": cost_max,
            "time": time_val,
            "transfers": transfers,
            "distance": distance,
            "emissions": emissions,
            "comfort": comfort,
            "weather_suitability": weather_suit,
            "traffic_suitability": traffic_score,
            "raw_data": data
        })
        
    if not available_options:
        return []
        
    # 2. Extract min/max values for scaling
    costs = [o["cost"] for o in available_options]
    times = [o["time"] for o in available_options]
    emissions_list = [o["emissions"] for o in available_options]
    
    min_cost, max_cost = min(costs), max(costs)
    min_time, max_time = min(times), max(times)
    min_emissions, max_emissions = min(emissions_list), max(emissions_list)
    
    # 3. Weight sets by preference
    weight_sets = {
        "cost": {"cost": 0.55, "time": 0.15, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.10},
        "cheapest": {"cost": 0.55, "time": 0.15, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.10},
        "time": {"cost": 0.10, "time": 0.50, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.20},
        "fastest": {"cost": 0.10, "time": 0.50, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.20},
        "convenience": {"cost": 0.10, "time": 0.15, "comfort": 0.45, "eco": 0.05, "weather": 0.15, "traffic": 0.10},
        "least_walking": {"cost": 0.15, "time": 0.20, "comfort": 0.40, "eco": 0.05, "weather": 0.10, "traffic": 0.10},
        "fewest_transfers": {"cost": 0.20, "time": 0.25, "comfort": 0.35, "eco": 0.05, "weather": 0.05, "traffic": 0.10},
        "default": {"cost": 0.25, "time": 0.25, "comfort": 0.20, "eco": 0.10, "weather": 0.10, "traffic": 0.10}
    }
    
    w = weight_sets.get(preference.lower(), weight_sets["default"])
    
    for opt in available_options:
        cost_score = 1.0 - ((opt["cost"] - min_cost) / (max_cost - min_cost)) if max_cost > min_cost else 1.0
        time_score = 1.0 - ((opt["time"] - min_time) / (max_time - min_time)) if max_time > min_time else 1.0
        eco_score = 1.0 - ((opt["emissions"] - min_emissions) / (max_emissions - min_emissions)) if max_emissions > min_emissions else 1.0
            
        opt_comfort = opt["comfort"]
        opt_weather = opt["weather_suitability"]
        opt_traffic = opt["traffic_suitability"]
        
        composite = (
            w["cost"] * cost_score +
            w["time"] * time_score +
            w["comfort"] * opt_comfort +
            w["eco"] * eco_score +
            w["weather"] * opt_weather +
            w["traffic"] * opt_traffic
        )
        opt["score"] = round(composite * 100, 1)
        
        opt["details"] = {
            "cost_score": int(cost_score * 100),
            "time_score": int(time_score * 100),
            "comfort_score": int(opt_comfort * 100),
            "eco_score": int(eco_score * 100),
            "weather_score": int(opt_weather * 100),
            "traffic_score": int(opt_traffic * 100)
        }
        
    available_options.sort(key=lambda x: x["score"], reverse=True)
    
    # 4. Generate AI or rule-based explanations
    explanations = {}
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        summary_str = ""
        for idx, opt in enumerate(available_options):
            summary_str += f"- Option {idx+1}: {opt['mode'].upper()} (Distance: {opt['distance']} km, Cost: Rs.{opt['cost']}, Time: {opt['time']} mins, Transfers: {opt['transfers']}, CO2: {opt['emissions']}g, Score: {opt['score']}/100)\n"
            
        w_summary = weather if isinstance(weather, str) else (weather.get("advisory") or "clear weather")
        system_instruction = (
            "You are a local Bangalore transit recommendation analyzer. Given a journey, weather forecast at ETA, and user preferences, "
            "explain the ranking and trade-offs of the transit modes in a highly concise, numerical, data-driven manner.\n"
            "Include specific numbers (distance in km, duration in min, cost range in Rs) in every explanation sentence.\n"
            "For cab, explicitly state that displayed fare is an estimate based on available models.\n"
            "Format the response strictly as a JSON object mapping mode keys (bmtc, metro, cab, car, multimodal) "
            "to their respective explanation string. Do not include markdown wraps."
        )
        
        user_message = (
            f"Journey: {source} to {destination}\n"
            f"Weather Forecast at ETA: {w_summary}\n"
            f"Preference: {preference}\n\n"
            f"Transit Options Evaluated:\n{summary_str}\n"
            f"Provide a friendly, context-aware 2-sentence explanation for each mode key. Emphasize why it got its score with exact numbers."
        )
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=3.0)
            if resp.status_code == 200:
                text_content = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                explanations = json.loads(text_content)
        except Exception:
            pass
            
    fallback = generate_fallback_explanations(available_options, weather, preference, source, destination)
    for opt in available_options:
        mode = opt["mode"]
        opt["explanation"] = explanations.get(mode) or fallback.get(mode, f"Recommended choice for {opt['distance']} km in {opt['time']} mins.")
        
    output_recommendations = []
    for idx, opt in enumerate(available_options):
        # Attach data source transparency metadata
        data_sources = {
            "traffic": "Google Maps Routes API / Calibrated Model",
            "weather": "Open-Meteo Weather API",
            "bmtc": "BMTC GTFS Dataset",
            "fare": "Calibrated Cab Estimation Model (Approximate)" if opt["mode"] == "cab" else "Official Tariff Dataset",
            "route": "Google Maps / OSRM Geometry"
        }
        output_recommendations.append({
            "mode": opt["mode"],
            "score": opt["score"],
            "rank": idx + 1,
            "details": opt["details"],
            "explanation": opt["explanation"],
            "emissions": opt["emissions"],
            "data_sources": data_sources
        })
        
    return output_recommendations


