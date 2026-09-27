import os
import json
import requests
from typing import Dict, Any, List

def calculate_emissions(mode: str, distance: float) -> float:
    """Estimate CO2 emissions in grams based on mode and distance."""
    # Metro: ~10g/passenger-km
    # Bus/Multimodal: ~25g/passenger-km
    # Own Car: ~120g/km
    # Cab/Auto: ~150g/km
    factors = {
        "metro": 10.0,
        "bmtc": 25.0,
        "multimodal": 25.0,
        "car": 120.0,
        "cab": 150.0
    }
    return round(distance * factors.get(mode, 25.0), 1)

def get_comfort_score(mode: str, transfers: int, distance: float, is_vajra: bool = False) -> float:
    """Calculate comfort/convenience baseline score (0.1 to 1.0)."""
    baselines = {
        "cab": 1.0,
        "car": 0.95,
        "metro": 0.80,
        "bmtc": 0.60,
        "multimodal": 0.50
    }
    score = baselines.get(mode, 0.60)
    if is_vajra and mode in ("bmtc", "multimodal"):
        score = 0.85  # AC Vajra/Volvo buses are highly comfortable
    
    # Penalize transfers
    score -= (transfers * 0.15)
    
    # Bound to a sensible minimum
    return max(0.1, round(score, 2))

def get_weather_suitability(mode: str, weather: str) -> float:
    """Determine weather suitability score (0.1 to 1.0)."""
    weather = (weather or "clear").lower()
    
    if weather == "heavy rain":
        suitability = {
            "metro": 1.0,
            "car": 0.70,
            "cab": 0.60,
            "bmtc": 0.50,
            "multimodal": 0.45
        }
    elif weather == "light rain":
        suitability = {
            "metro": 1.0,
            "car": 0.90,
            "cab": 0.90,
            "bmtc": 0.80,
            "multimodal": 0.75
        }
    else: # clear / standard
        suitability = {
            "metro": 1.0,
            "car": 1.0,
            "cab": 1.0,
            "bmtc": 1.0,
            "multimodal": 1.0
        }
    return suitability.get(mode, 1.0)

def generate_fallback_explanations(options: List[Dict[str, Any]], weather: str, preference: str) -> Dict[str, str]:
    """Provide rule-based local explanations if LLM call is unavailable or fails."""
    explanations = {}
    weather = (weather or "clear").lower()
    preference = (preference or "cost").lower()
    
    for opt in options:
        mode = opt["mode"]
        cost = opt["cost"]
        time = opt["time"]
        transfers = opt["transfers"]
        
        if mode == "bmtc":
            if transfers == 0:
                explanations["bmtc"] = f"Direct BMTC bus service from nearest stop with 0 transfers, taking ~{time} mins at Rs. {cost}."
            elif weather == "heavy rain":
                explanations["bmtc"] = f"BMTC Bus is a very budget-friendly option (Rs. {cost}), but heavy rain could cause major road traffic delays and long wait times."
            elif preference == "cost":
                explanations["bmtc"] = f"BMTC Bus is the most economical choice at just Rs. {cost}, though it requires {transfers} transfer(s)."
            elif preference in ("fewest_transfers", "transfers"):
                explanations["bmtc"] = f"BMTC Bus with {transfers} transfer(s), total duration ~{time} mins."
            else:
                explanations["bmtc"] = f"BMTC Bus provides cheap transit at Rs. {cost}, with total travel time ~{time} mins."

        elif mode == "metro":
            if weather in ("light rain", "heavy rain"):
                explanations["metro"] = "Namma Metro is highly recommended as it completely bypasses road traffic congestion and waterlogging caused by the rain."
            elif preference in ("time", "fastest"):
                explanations["metro"] = f"Metro is an excellent choice for speed, taking {time} mins and bypassing gridlock on key transit corridors."
            else:
                explanations["metro"] = f"Metro offers a reliable and eco-friendly trip in {time} mins, avoiding peak traffic delays."
                
        elif mode == "multimodal":
            if weather == "heavy rain":
                explanations["multimodal"] = "Combined Bus + Metro route is budget-friendly, but transfer points and walking segments will be highly inconvenient in heavy rain."
            else:
                explanations["multimodal"] = f"Multimodal routing offers a balanced compromise: utilizing Metro speed for long distances, and buses/autos for first/last-mile connectivity."
                
        elif mode == "cab":
            if weather == "heavy rain":
                explanations["cab"] = "Cab/Auto offers door-to-door comfort keeping you dry, but heavy rain usually triggers surge pricing, low availability, and severe road delays."
            elif preference in ("convenience", "comfort"):
                explanations["cab"] = "Cab/Auto represents the peak convenience choice, providing direct door-to-door transit without any transfer hassle."
            else:
                explanations["cab"] = f"Cab/Auto offers direct door-to-door routing, but is expensive (Rs. {cost}) and vulnerable to city traffic."
                
        elif mode == "car":
            if weather == "heavy rain":
                explanations["car"] = "Driving your own vehicle is convenient and dry, but you must negotiate heavy traffic, potential waterlogging, and parking searches in the rain."
            elif preference in ("convenience", "comfort"):
                explanations["car"] = "Using your own vehicle gives you maximum schedule flexibility and door-to-door comfort without transfers."
            else:
                explanations["car"] = f"Private vehicle is quick and direct, but incurs fuel and parking costs (est. Rs. {cost}) plus driving stress."
                
    return explanations

def get_recommendations(results: Dict[str, Any], source: str, destination: str, preference: str = "cost", weather: str = "clear") -> List[Dict[str, Any]]:
    """
    Ranks available transit options and returns Top-K recommendations with XAI explanations.
    """
    available_options = []
    
    # 1. Filter out only available modes
    for mode, data in results.items():
        if not isinstance(data, dict) or not data.get("available"):
            continue
        
        cost = float(data.get("cost", 0.0))
        time = float(data.get("time", 0.0))
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
        weather_suit = get_weather_suitability(mode, weather)
        
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
            "time": time,
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
        
    # 2. Extract min/max values for scaling (guarding against division by zero)
    costs = [o["cost"] for o in available_options]
    times = [o["time"] for o in available_options]
    emissions_list = [o["emissions"] for o in available_options]
    
    min_cost, max_cost = min(costs), max(costs)
    min_time, max_time = min(times), max(times)
    min_emissions, max_emissions = min(emissions_list), max(emissions_list)
    
    # 3. Calculate normalized sub-scores (0.0 to 1.0) and composite recommendations
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
        # Cost score: lower cost = higher score
        if max_cost > min_cost:
            cost_score = 1.0 - ((opt["cost"] - min_cost) / (max_cost - min_cost))
        else:
            cost_score = 1.0
            
        # Time score: lower time = higher score
        if max_time > min_time:
            time_score = 1.0 - ((opt["time"] - min_time) / (max_time - min_time))
        else:
            time_score = 1.0
            
        # Eco score: lower emissions = higher score
        if max_emissions > min_emissions:
            eco_score = 1.0 - ((opt["emissions"] - min_emissions) / (max_emissions - min_emissions))
        else:
            eco_score = 1.0
            
        opt_comfort = opt["comfort"]
        opt_weather = opt["weather_suitability"]
        opt_traffic = opt["traffic_suitability"]
        
        # Calculate overall utility score (0 to 100)
        composite = (
            w["cost"] * cost_score +
            w["time"] * time_score +
            w["comfort"] * opt_comfort +
            w["eco"] * eco_score +
            w["weather"] * opt_weather +
            w["traffic"] * opt_traffic
        )
        opt["score"] = round(composite * 100, 1)
        
        # Save structured sub-scores (0-100 scale for UI progress bars)
        opt["details"] = {
            "cost_score": int(cost_score * 100),
            "time_score": int(time_score * 100),
            "comfort_score": int(opt_comfort * 100),
            "eco_score": int(eco_score * 100),
            "weather_score": int(opt_weather * 100),
            "traffic_score": int(opt_traffic * 100)
        }
        
    # Sort options by recommendation score descending
    available_options.sort(key=lambda x: x["score"], reverse=True)
    
    # 4. Generate Explainable AI explanations
    explanations = {}
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # Summary of options for the prompt
        summary_str = ""
        for idx, opt in enumerate(available_options):
            summary_str += f"- Option {idx+1}: {opt['mode'].upper()} (Cost: Rs.{opt['cost']}, Time: {opt['time']} mins, Transfers: {opt['transfers']}, CO2: {opt['emissions']}g, Score: {opt['score']}/100)\n"
            
        system_instruction = (
            "You are a local Bangalore transit recommendation analyzer. Given a journey, weather, and user preferences, "
            "explain the ranking and trade-offs of the transit modes in a highly concise manner.\n"
            "Format the response strictly as a JSON object mapping mode keys (bmtc, metro, cab, car, multimodal) "
            "to their respective explanation string. Do not include markdown wraps."
        )
        
        user_message = (
            f"Journey: {source} to {destination}\n"
            f"Weather: {weather}\n"
            f"Preference: {preference}\n\n"
            f"Transit Options Evaluated:\n{summary_str}\n"
            f"Provide a friendly, context-aware 2-sentence explanation for each mode key. Emphasize why it got its score."
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
            pass # Fallback below
            
    # Fallback to local rule-based descriptions for missing explanations
    fallback = generate_fallback_explanations(available_options, weather, preference)
    for opt in available_options:
        mode = opt["mode"]
        opt["explanation"] = explanations.get(mode) or fallback.get(mode, "Highly recommended option based on your preferences.")
        
    # Clean output dictionary for final response
    output_recommendations = []
    for idx, opt in enumerate(available_options):
        output_recommendations.append({
            "mode": opt["mode"],
            "score": opt["score"],
            "rank": idx + 1,
            "details": opt["details"],
            "explanation": opt["explanation"],
            "emissions": opt["emissions"]
        })
        
    return output_recommendations
