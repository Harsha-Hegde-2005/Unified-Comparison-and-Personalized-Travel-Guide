import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

class ChatbotEngine:
    def __init__(self, bmtc_stops: List[str], metro_stations: List[str], all_vehicles: Optional[List[Dict[str, Any]]] = None):
        self.bmtc_stops = bmtc_stops
        self.metro_stations = metro_stations
        # Combine and deduplicate stop names
        self.all_stops = list(set(list(bmtc_stops) + list(metro_stations)))
        self.all_vehicles = all_vehicles or []

    def get_simulated_weather(self, time: datetime) -> str:
        """Simulated weather timeline matching spec examples."""
        h = time.hour
        if 8 <= h <= 10:
            return "light rain"
        elif 15 <= h <= 18:
            return "heavy rain"
        else:
            return "clear"

    def extract_stops(self, text: str) -> List[str]:
        """Fuzzy/exact substring stop name extraction."""
        text_lower = text.lower()
        matched = []
        
        # Sort stop names by length descending to match longest phrases first
        sorted_stops = sorted(self.all_stops, key=len, reverse=True)
        used_indices: List[Tuple[int, int]] = []
        
        for stop in sorted_stops:
            stop_lower = stop.lower()
            if len(stop_lower) < 3:  # Skip extremely short stop names
                continue
                
            start_idx = 0
            while True:
                idx = text_lower.find(stop_lower, start_idx)
                if idx == -1:
                    break
                
                # Check for overlap with already matched stop names
                overlap = False
                for s, e in used_indices:
                    if not (idx + len(stop_lower) <= s or idx >= e):
                        overlap = True
                        break
                        
                if not overlap:
                    # For short words, enforce word boundaries
                    is_word = True
                    if len(stop_lower) <= 5:
                        before_char = text_lower[idx - 1] if idx > 0 else ' '
                        after_char = text_lower[idx + len(stop_lower)] if idx + len(stop_lower) < len(text_lower) else ' '
                        if before_char.isalnum() or after_char.isalnum():
                            is_word = False
                            
                    if is_word:
                        matched.append((idx, stop))
                        used_indices.append((idx, idx + len(stop_lower)))
                        
                start_idx = idx + 1
                
        # Sort matched stops by their position in the text
        matched.sort(key=lambda x: x[0])
        return [name for _, name in matched]

    def determine_source_dest(self, matched_stops: List[str], text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse source and destination from matching stops based on prepositions."""
        if not matched_stops:
            return None, None
            
        if len(matched_stops) == 1:
            stop = matched_stops[0]
            stop_idx = text.lower().find(stop.lower())
            before_text = text[:stop_idx].lower()
            if any(k in before_text for k in ["to ", "reach ", "go to ", "dest ", "destination "]):
                return None, stop
            return stop, None
            
        stop1, stop2 = matched_stops[0], matched_stops[1]
        idx1 = text.lower().find(stop1.lower())
        idx2 = text.lower().find(stop2.lower())
        
        before1 = text[max(0, idx1 - 10):idx1].lower()
        before2 = text[max(0, idx2 - 10):idx2].lower()
        
        if "from" in before2:
            # "... to stop1 from stop2"
            return stop2, stop1
        elif "from" in before1:
            # "from stop1 to stop2"
            return stop1, stop2
        elif any(k in before2 for k in ["to", "reach", "destination", "dest"]):
            # "stop1 to stop2"
            return stop1, stop2
        else:
            return stop1, stop2

    def extract_budget(self, text: str) -> Optional[int]:
        """Regex budget amount extractor (e.g. ₹50, rs. 60, under 100)."""
        text_lower = text.lower()
        
        # 1. hh:mm pm/am boundary checks to avoid matching times as budgets
        # e.g., "4 pm" or "16:00" shouldn't be parsed as ₹4 or ₹1600.
        
        # Look for patterns like "50 rupees", "50 rs", "50 bucks"
        m1 = re.search(r'\b(\d+)\s*(?:rupees|rs\.?|bucks|inr)\b', text_lower)
        if m1:
            return int(m1.group(1))
            
        # Look for rs/₹ followed by a number
        m2 = re.search(r'(?:rs\.?|₹|inr)\s*(\d+)\b', text_lower)
        if m2:
            return int(m2.group(1))
            
        # Look for "under/below/max/budget" followed by number
        m3 = re.search(r'\b(?:under|below|max|budget|within|only|less than)\s*(?:rs\.?|₹)?\s*(\d+)\b', text_lower)
        if m3:
            return int(m3.group(1))
            
        # Fallback: if there is a number in the text and currency keywords are present
        if any(k in text_lower for k in ["budget", "rupee", "₹", "rs", "cost", "cheap", "max", "price"]):
            nums = re.findall(r'\b(\d+)\b', text_lower)
            for n_str in nums:
                n = int(n_str)
                # Ignore values likely to be times or stop numbers
                if 15 <= n <= 2000:
                    return n
        return None

    def extract_time(self, text: str) -> datetime:
        """Scan text for time indicators (e.g. "4 pm", "16:30"). Defaults to current time."""
        text_lower = text.lower()
        now = datetime.now()
        
        # 1. hh:mm pm/am or hh:mm
        m1 = re.search(r'\b(\d{1,2}):(\d{2})\s*(pm|am)?\b', text_lower)
        if m1:
            h, m = int(m1.group(1)), int(m1.group(2))
            is_pm = m1.group(3) == "pm"
            is_am = m1.group(3) == "am"
            if is_pm and h < 12:
                h += 12
            elif is_am and h == 12:
                h = 0
            return now.replace(hour=h, minute=m, second=0, microsecond=0)
            
        # 2. hh pm/am
        m2 = re.search(r'\b(\d{1,2})\s*(pm|am)\b', text_lower)
        if m2:
            h = int(m2.group(1))
            is_pm = m2.group(2) == "pm"
            if is_pm and h < 12:
                h += 12
            elif m2.group(2) == "am" and h == 12:
                h = 0
            return now.replace(hour=h, minute=0, second=0, microsecond=0)
            
        # 3. "at 4" or "today at 4"
        m3 = re.search(r'\b(?:at|today at|around)\s*(\d{1,2})\b', text_lower)
        if m3:
            h = int(m3.group(1))
            if h <= 12:
                # If current hour is past h, assume PM (e.g. searching at 10 AM for "at 4" refers to 4 PM)
                if h < 7 or (h >= 7 and now.hour > h):
                    h += 12
            if 0 <= h < 24:
                return now.replace(hour=h, minute=0, second=0, microsecond=0)
                
        return now

    def extract_vehicle_type(self, text: str) -> Optional[str]:
        """Extract personal vehicle type (bike vs car)."""
        text_lower = text.lower()
        if any(k in text_lower for k in ["bike", "motorcycle", "scooter", "two wheeler", "activa", "bullet"]):
            return "bike"
        if any(k in text_lower for k in ["car", "sedan", "suv", "vehicle", "four wheeler", "swift"]):
            return "car"
        return None

    def classify_intent(self, text: str, matched_stops: List[str]) -> Tuple[str, Dict[str, Any]]:
        """Classify conversational intent and compile parameters."""
        text_lower = text.lower()
        params: Dict[str, Any] = {}
        
        # Keep original message for general replies
        params["message"] = text
        
        # 1. AC Bus Check
        if any(k in text_lower for k in ["ac bus", "ac buses", "vajra", "volvo", "ac available"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "ac_bus_available", params

        # 2. Possible Ways Check
        if any(k in text_lower for k in ["possible ways", "all ways", "different ways", "all options", "routes to"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "possible_ways", params

        # 3. Nearest Stop Check
        if any(k in text_lower for k in ["nearest", "closest", "nearby", "close to"]):
            if matched_stops:
                params["location"] = matched_stops[0]
                return "nearest_stops", params
        
        # 4. Budget Constraint
        budget = self.extract_budget(text)
        if budget is not None:
            src, dst = self.determine_source_dest(matched_stops, text)
            params["budget"] = budget
            params["source"] = src
            params["destination"] = dst
            return "budget_constrained", params
            
        # 5. Vehicle vs Transit
        vtype = self.extract_vehicle_type(text)
        if vtype is not None:
            _, dst = self.determine_source_dest(matched_stops, text)
            params["vtype"] = vtype
            params["destination"] = dst or (matched_stops[0] if matched_stops else None)
            return "vehicle_vs_transit", params
            
        # 6. Weather Forecast
        if any(k in text_lower for k in ["weather", "rain", "shower", "storm", "flood", "precipitation", "drizzle", "clear"]):
            params["time"] = self.extract_time(text)
            return "weather_query", params
            
        # 7. Journey Time vs Cost
        if len(matched_stops) >= 2:
            src, dst = self.determine_source_dest(matched_stops, text)
            params["source"] = src
            params["destination"] = dst
            
            if any(k in text_lower for k in ["cost", "price", "fare", "cheap", "expensive", "rupee", "charge", "much"]):
                return "journey_cost", params
            else:
                return "journey_time", params
                
        # 8. General conversational fallback
        return "general", params

    def format_response(self, intent: str, params: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Construct conversational replies based on solver output data."""
        if intent == "weather_query":
            weather = data.get("weather", "clear")
            time_str = params.get("time", datetime.now()).strftime("%I:%M %p")
            
            if "heavy rain" in weather or "storm" in weather:
                return (
                    f"Yes, heavy rain is forecast at {time_str} today. Road speeds will drop by 35%. "
                    "I recommend taking the Metro rather than a cab or bus to avoid traffic gridlock."
                )
            elif "light rain" in weather or "drizzle" in weather:
                return (
                    f"Light rain is forecast at {time_str}. Road speeds might be slightly slower. "
                    "A direct Metro or AC Vajra Bus would be comfortable options."
                )
            else:
                return f"The weather is forecast to be clear at {time_str}. All modes are operating normally."
                
        elif intent == "journey_time":
            src, dst = params.get("source"), params.get("destination")
            best_opt = data.get("best_option")
            if not best_opt:
                return f"Sorry, I couldn't find a route from {src} to {dst}."
                
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab / Auto", "car": "Personal Vehicle"}
            m_label = mode_labels.get(best_opt.get("mode"), "Transit")
            
            return (
                f"Traveling from {src} to {dst} via {m_label} is the fastest option. "
                f"It takes about {best_opt.get('time')} minutes and costs ₹{best_opt.get('cost')}."
            )
            
        elif intent == "journey_cost":
            src, dst = params.get("source"), params.get("destination")
            cheapest = data.get("best_option")
            if not cheapest:
                return f"Sorry, I couldn't find a route from {src} to {dst}."
                
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab / Auto", "car": "Personal Vehicle"}
            m_label = mode_labels.get(cheapest.get("mode"), "Transit")
            
            return (
                f"The cheapest way to reach {dst} from {src} is by {m_label}. "
                f"The estimated cost is ₹{cheapest.get('cost')}, and it takes about {cheapest.get('time')} minutes."
            )
            
        elif intent == "budget_constrained":
            src, dst = params.get("source"), params.get("destination")
            budget = params.get("budget", 0)
            options = data.get("options", [])
            
            if options:
                # Recommend best option under budget
                best = options[0]
                mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab / Auto", "car": "Personal Vehicle"}
                m_label = mode_labels.get(best.get("mode"), "Transit")
                
                return (
                    f"Under your ₹{budget} budget, I found {len(options)} options. The recommended choice is "
                    f"the {m_label} which costs ₹{best.get('cost')} and takes {best.get('time')} minutes."
                )
            else:
                # Suggest cheapest available option and specify difference
                cheapest = data.get("cheapest_available")
                if not cheapest:
                    return f"Sorry, I couldn't find any travel options from {src} to {dst}."
                    
                diff = cheapest.get("cost", 0) - budget
                mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab / Auto", "car": "Personal Vehicle"}
                m_label = mode_labels.get(cheapest.get("mode"), "Transit")
                
                return (
                    f"Your budget of ₹{budget} is too low for a direct trip. The cheapest option is the "
                    f"{m_label} at ₹{cheapest.get('cost')}, which is ₹{diff} over your budget."
                )
                
        elif intent == "vehicle_vs_transit":
            dst = params.get("destination")
            vtype = params.get("vtype", "bike")
            v_cost = data.get("vehicle_cost", 0)
            v_time = data.get("vehicle_time", 0)
            t_cost = data.get("transit_cost", 0)
            t_time = data.get("transit_time", 0)
            weather = data.get("weather", "clear")
            
            if "heavy rain" in weather or "storm" in weather:
                if vtype == "bike":
                    return (
                        f"I recommend public transit today. Driving your bike to {dst} will cost ₹{v_cost:.0f} "
                        f"and take {v_time:.0f} mins in heavy rain. The Metro/Bus costs ₹{t_cost}, "
                        f"is sheltered, and takes about {t_time} mins."
                    )
                else:
                    return (
                        f"Roads are highly congested due to heavy rain. Driving your car to {dst} will cost ₹{v_cost:.0f} "
                        f"and take {v_time:.0f} mins. Public transit costs ₹{t_cost} and takes {t_time} mins. "
                        "I recommend taking Namma Metro to avoid gridlock."
                    )
            else:
                if v_cost < t_cost:
                    return (
                        f"Driving your {vtype} to {dst} is highly cost-effective today. It costs ₹{v_cost:.0f} "
                        f"and takes {v_time:.0f} mins, compared to transit which costs ₹{t_cost} and takes {t_time} mins."
                    )
                else:
                    return (
                        f"I recommend public transit to {dst}. Driving your {vtype} costs ₹{v_cost:.0f} "
                        f"and takes {v_time:.0f} mins, whereas public transit is ₹{t_cost} and takes about {t_time} mins."
                    )
                    
        elif intent == "possible_ways":
            src, dst = params.get("source"), params.get("destination")
            options = data.get("options", [])
            if not options:
                return f"Sorry, I couldn't find any transit options from {src} to {dst}."
            
            reply = f"Here are the possible ways to travel from {src} to {dst}:\n"
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab / Auto", "car": "Personal Vehicle"}
            for opt in options:
                m_label = mode_labels.get(opt.get("mode"), "Transit")
                reply += f"- **{m_label}**: Takes about {opt.get('time')} mins, costs ₹{opt.get('cost')}\n"
            return reply

        elif intent == "ac_bus_available":
            src, dst = params.get("source"), params.get("destination")
            has_ac = data.get("has_ac", False)
            ac_buses = data.get("ac_buses", [])
            if has_ac and ac_buses:
                buses_str = ", ".join(ac_buses[:4])
                return f"Yes, AC Vajra bus service is available between {src} and {dst}. You can take: {buses_str}."
            else:
                return f"No direct AC Vajra bus was found between {src} and {dst}. You can check regular BMTC ordinary buses or Namma Metro."

        elif intent == "nearest_stops":
            loc = params.get("location")
            nearest = data.get("nearest")
            if not nearest:
                return f"Sorry, I couldn't resolve nearest stops for location '{loc}'."
            
            reply = f"Here are the nearest transit stops to {loc}:\n"
            if nearest.get("bmtc"):
                reply += "\n**BMTC Bus Stops:**\n"
                for name, dist in nearest["bmtc"]:
                    reply += f"- {name} (~{dist:.2f} km)\n"
            if nearest.get("metro"):
                reply += "\n**Metro Stations:**\n"
                for name, dist in nearest["metro"]:
                    reply += f"- {name} Metro Station (~{dist:.2f} km)\n"
            return reply

        else:
            # Handle general conversational requests
            msg = params.get("message", "").lower() if params else ""
            if any(k in msg for k in ["hello", "hi", "hey"]):
                return "Hello! How can I help you navigate Bangalore today? Ask me about routes, nearest stops, fares, or weather!"
            elif any(k in msg for k in ["thank", "thanks"]):
                return "You're welcome! Safe travels. Let me know if you need anything else!"
            elif any(k in msg for k in ["help", "what can you"]):
                return (
                    "I am your Commuter Assistant. I can help you with:\n"
                    "1. Finding routes (e.g., 'how to go from Majestic to Silk Board')\n"
                    "2. Checking AC Vajra bus availability ('is AC bus available from Indiranagar to Majestic?')\n"
                    "3. Finding nearby stops ('nearest bus stop to Electronic City')\n"
                    "4. Weather checks ('will it rain at 5 PM?')\n"
                    "5. Comparing public transit vs driving ('should I take my bike to Indiranagar?')\n"
                    "6. Finding routes under budget ('cheapest route under ₹50')"
                )
            else:
                return (
                    "Hello! I am your Commuter Assistant. I can help you plan your journey, "
                    "find options matching your budget, check rain forecast impact, compare transit vs. driving, "
                    "look up AC Vajra buses, or find nearby stops. "
                    "Try asking: 'How long does it take from Majestic to Silk Board?' or 'Nearest stop to Indiranagar'"
                )
