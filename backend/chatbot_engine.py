import os
import json
import requests
import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

class ChatbotEngine:
    def __init__(self, bmtc_stops, metro_stations, all_vehicles=None):
        self.bmtc_stops = bmtc_stops
        self.metro_stations = metro_stations
        self.all_stops = list(set(list(bmtc_stops) + list(metro_stations)))
        self.all_vehicles = all_vehicles or []

    def query_llm(self, message, history=None):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        contents = []
        if history:
            for msg in history:
                role = "user" if msg.get("sender") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
        contents.append({"role": "user", "parts": [{"text": message}]})
        system_instruction = (
            "You are a comprehensive Bangalore commuter assistant that helps with ALL transport modes.\n"
            "Parse the user query, classify intent, extract parameters, answer general questions.\n\n"
            "INTENTS:\n"
            "- \"journey_time\": User wants to travel from A to B — fastest route, any mode.\n"
            "- \"journey_cost\": User wants to know fare/cost from A to B.\n"
            "- \"budget_constrained\": User wants to travel from A to B under a specific budget.\n"
            "- \"possible_ways\": User wants ALL modes/routes from A to B.\n"
            "- \"ride_cost\": User asks for cab/ride cost (Ola, Uber, Namma Yatri, Rapido, auto, bike taxi). Extract source+destination.\n"
            "- \"fuel_cost\": User asks about fuel/petrol/diesel consumption or private vehicle cost. Extract source, destination, vehicle_type (car/bike).\n"
            "- \"nearest_stops\": User wants nearest bus stop or metro station. Extract the location name (ANY Bangalore landmark, address, area).\n"
            "- \"traffic_query\": User asks about traffic, congestion, road conditions, drive time.\n"
            "- \"multimodal_journey\": User asks for Bus+Metro combined route, or says 'multimodal'.\n"
            "- \"weather_query\": User asks about weather or rain forecast.\n"
            "- \"vehicle_vs_transit\": User wants to compare driving vs public transit.\n"
            "- \"general\": General transit rules, Metro timings (5AM-11PM), greetings, help.\n"
            "- \"clarification\": Journey intent but source or destination is missing.\n\n"
            "RULES:\n"
            "1. For ride_cost: extract source, destination. User may say Ola/Uber/Namma Yatri/Rapido/cab/auto/taxi.\n"
            "2. For fuel_cost: extract source, destination, vehicle_type (car/bike default car).\n"
            "3. For nearest_stops: extract location from message. It can be ANY Bangalore place name.\n"
            "4. For traffic_query: extract source+destination if mentioned, else leave null.\n"
            "5. For general: answer directly about Metro/BMTC rules in the 'answer' field.\n"
            "6. For clarification: write a polite question in 'clarification_question'.\n\n"
            "Output MUST be a single JSON object:\n"
            "{\n"
            "  \"intent\": \"intent_name\",\n"
            "  \"parameters\": {\n"
            "    \"source\": \"string or null\",\n"
            "    \"destination\": \"string or null\",\n"
            "    \"location\": \"string or null\",\n"
            "    \"time\": \"string or null\",\n"
            "    \"budget\": 0,\n"
            "    \"vehicle_type\": \"string or null\",\n"
            "    \"clarification_question\": \"string or null\"\n"
            "  },\n"
            "  \"answer\": \"string or null\"\n"
            "}\n"
            "No markdown formatting. Response MIME type is application/json."
        )
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {"responseMimeType": "application/json"}
        }
        try:
            resp = requests.post(url, json=payload, timeout=3.0)
            if resp.status_code == 200:
                result = resp.json()
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
            return None
        except Exception:
            return None

    def resolve_context_from_history(self, message, history=None):
        if not history:
            return None
        last_bot_msg = None
        user_msg_before_bot = None
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if msg.get("sender") == "bot":
                last_bot_msg = msg.get("text", "")
                for j in range(i - 1, -1, -1):
                    if history[j].get("sender") == "user":
                        user_msg_before_bot = history[j].get("text", "")
                        break
                break
        if not last_bot_msg:
            return None
        last_lower = last_bot_msg.lower()
        is_asking_source = any(k in last_lower for k in ["starting from", "start location", "origin", "starting your journey"])
        is_asking_destination = any(k in last_lower for k in ["going to", "destination", "travel to", "reach"])
        if not (is_asking_source or is_asking_destination):
            return None
        current_stop = self._clean_place_name(message)
        if not current_stop:
            return None

        # Parse previous source/destination using our regex parser
        prev_stops = self.extract_stops(user_msg_before_bot) if user_msg_before_bot else []
        prev_src, prev_dst = self.parse_source_dest_from_text(user_msg_before_bot, prev_stops)

        source = None
        destination = None
        if is_asking_source:
            source = current_stop
            destination = prev_dst or (prev_stops[0] if prev_stops else None)
        elif is_asking_destination:
            destination = current_stop
            source = prev_src or (prev_stops[0] if prev_stops else None)

        if not source or not destination:
            return None
        prev_lower = user_msg_before_bot.lower() if user_msg_before_bot else ""
        params = {"source": source, "destination": destination, "message": (user_msg_before_bot + " " + message) if user_msg_before_bot else message}
        if any(k in prev_lower for k in ["ola", "uber", "namma yatri", "rapido", "cab", "taxi", "auto"]):
            return "ride_cost", params
        if any(k in prev_lower for k in ["fuel", "petrol", "diesel", "consume", "litres"]):
            vtype = self.extract_vehicle_type(prev_lower) or "car"
            params["vehicle_type"] = vtype
            return "fuel_cost", params
        if any(k in prev_lower for k in ["ac bus", "vajra", "volvo"]):
            return "ac_bus_available", params
        if any(k in prev_lower for k in ["possible ways", "all ways", "all options"]):
            return "possible_ways", params
        budget = self.extract_budget(prev_lower)
        if budget is not None:
            params["budget"] = budget
            return "budget_constrained", params
        vtype = self.extract_vehicle_type(prev_lower)
        if vtype is not None:
            params["vtype"] = vtype
            return "vehicle_vs_transit", params
        if any(k in prev_lower for k in ["cost", "price", "fare", "cheap", "rupee"]):
            return "journey_cost", params
        return "journey_time", params

    def get_simulated_weather(self, time):
        from weather_helper import get_realtime_weather
        return get_realtime_weather(time)

    def extract_stops(self, text):
        text_lower = text.lower()
        matched = []
        used_indices = []
        coord_matches = re.finditer(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", text)
        for m in coord_matches:
            start_idx = m.start()
            end_idx = m.end()
            matched.append((start_idx, text[start_idx:end_idx].strip()))
            used_indices.append((start_idx, end_idx))
        sorted_stops = sorted(self.all_stops, key=len, reverse=True)
        for stop in sorted_stops:
            stop_lower = stop.lower()
            if len(stop_lower) < 3:
                continue
            start_idx = 0
            while True:
                idx = text_lower.find(stop_lower, start_idx)
                if idx == -1:
                    break
                overlap = any(not (idx + len(stop_lower) <= s or idx >= e) for s, e in used_indices)
                if not overlap:
                    is_word = True
                    if len(stop_lower) <= 5:
                        before_char = text_lower[idx - 1] if idx > 0 else " "
                        after_char = text_lower[idx + len(stop_lower)] if idx + len(stop_lower) < len(text_lower) else " "
                        if before_char.isalnum() or after_char.isalnum():
                            is_word = False
                    if is_word:
                        matched.append((idx, stop))
                        used_indices.append((idx, idx + len(stop_lower)))
                start_idx = idx + 1
        matched.sort(key=lambda x: x[0])
        return [name for _, name in matched]

    def _clean_place_name(self, name):
        if not name:
            return None
        # Clean punctuation and noise
        name = re.sub(r"[^\w\s\-\.\,]", "", name).strip()
        words = name.split()
        if not words:
            return None
        # Clean leading noise
        leading_noise = {"my", "the", "a", "an", "any", "some", "at", "from", "to"}
        while words and words[0].lower() in leading_noise:
            words.pop(0)
        # Clean trailing noise
        trailing_noise = {"now", "today", "please", "tonight", "morning", "evening"}
        while words and words[-1].lower() in trailing_noise:
            words.pop()
        cleaned = " ".join(words).strip()
        cleaned_lower = cleaned.lower()
        # Avoid common verbs/noise words as place names
        noise_place_words = {"travel", "go", "commute", "ride", "walk", "leave", "start", "get", "reach", "here", "there", "somewhere", "anywhere", "bus", "metro", "cab", "taxi", "auto", "train", "vehicle", "car", "bike"}
        if cleaned_lower in noise_place_words:
            return None
        
        # Check exact or word-boundary matches in all_stops
        # Sort stops by length descending so we match the longest/most specific stop name first
        for stop in sorted(self.all_stops, key=len, reverse=True):
            if re.search(r"\b" + re.escape(stop.lower()) + r"\b", cleaned_lower):
                return stop
                
        if len(cleaned) < 3:
            return None
        return cleaned if cleaned else None

    def parse_source_dest_from_text(self, text, matched_stops):
        # 1. Prioritize matched stops ONLY if we have 2 or more exact stops
        if matched_stops and len(matched_stops) >= 2:
            stop1, stop2 = matched_stops[0], matched_stops[1]
            idx1 = text.lower().find(stop1.lower())
            idx2 = text.lower().find(stop2.lower())
            before1 = text[max(0, idx1 - 10):idx1].lower()
            before2 = text[max(0, idx2 - 10):idx2].lower()
            if "from" in before2:
                return stop2, stop1
            elif "from" in before1:
                return stop1, stop2
            elif any(k in before2 for k in ["to", "reach", "destination", "dest"]):
                return stop1, stop2
            return stop1, stop2

        # 2. Otherwise, use regex extraction to support landmarks
        text_lower = text.lower()
        cleaned_text = re.sub(r"\b(?:how|want|need|like|wish|try|going|plan)\s+to\b", "", text_lower)
        # Check pattern: "from <src> to <dst>"
        m_from_to = re.search(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\?|$|\.|,)", cleaned_text)
        if m_from_to:
            src = m_from_to.group(1).strip()
            dst = m_from_to.group(2).strip()
            return self._clean_place_name(src), self._clean_place_name(dst)
        # Check pattern: "to <dst> from <src>"
        m_to_from = re.search(r"\bto\s+(.+?)\s+from\s+(.+?)(?:\?|$|\.|,)", cleaned_text)
        if m_to_from:
            dst = m_to_from.group(1).strip()
            src = m_to_from.group(2).strip()
            return self._clean_place_name(src), self._clean_place_name(dst)
        # Check pattern: "between <src> and <dst>"
        m_between = re.search(r"\bbetween\s+(.+?)\s+and\s+(.+?)(?:\?|$|\.|,)", cleaned_text)
        if m_between:
            src = m_between.group(1).strip()
            dst = m_between.group(2).strip()
            return self._clean_place_name(src), self._clean_place_name(dst)
        # Check individual parts
        src, dst = None, None
        m_src = re.search(r"\bfrom\s+(.+?)(?:\s+to\s+|\?|$|\.|,)", cleaned_text)
        if m_src:
            src = m_src.group(1).strip()
        m_dst = re.search(r"\b(?:go\s+to|reach|travel\s+to|way\s+to|to)\s+(.+?)(?:\s+from\s+|\?|$|\.|,)", cleaned_text)
        if m_dst:
            dst = m_dst.group(1).strip()

        src_cleaned = self._clean_place_name(src)
        dst_cleaned = self._clean_place_name(dst)

        # Fallback to matched stops if nothing resolved via regex
        if not src_cleaned and not dst_cleaned and matched_stops:
            stop = matched_stops[0]
            stop_idx = text.lower().find(stop.lower())
            before_text = text[:stop_idx].lower()
            last_from = before_text.rfind("from")
            last_to = -1
            for k in ["to", "reach", "dest", "destination"]:
                pos = before_text.rfind(k)
                if pos > last_to:
                    is_valid = True
                    if k == "to":
                        if pos > 0 and before_text[pos - 1].isalnum():
                            is_valid = False
                        if pos + 2 < len(before_text) and before_text[pos + 2].isalnum():
                            is_valid = False
                        if is_valid:
                            last_to = pos
            if last_to > last_from:
                return None, stop
            return stop, None

        return src_cleaned, dst_cleaned

    def determine_source_dest(self, matched_stops, text):
        return self.parse_source_dest_from_text(text, matched_stops)

    def extract_budget(self, text):
        text_lower = text.lower()
        m1 = re.search(r"\b(\d+)\s*(?:rupees|rs\.?|bucks|inr|₹)\b", text_lower)
        if m1:
            return int(m1.group(1))
        m2 = re.search(r"(?:rs\.?|inr|₹)\s*(\d+)\b", text_lower)
        if m2:
            return int(m2.group(1))
        m3 = re.search(r"\b(?:under|below|max|budget|within|only|less than)\s*(?:rs\.?|inr|₹)?\s*(\d+)\b", text_lower)
        if m3:
            return int(m3.group(1))
        if any(k in text_lower for k in ["budget", "rupee", "rs", "₹", "cost", "cheap", "max", "price"]):
            nums = re.findall(r"\b(\d+)\b", text_lower)
            for n_str in nums:
                n = int(n_str)
                if 15 <= n <= 2000:
                    return n
        return None

    def extract_time(self, text):
        text_lower = text.lower()
        now = datetime.now()
        m1 = re.search(r"\b(\d{1,2}):(\d{2})\s*(pm|am)?\b", text_lower)
        if m1:
            h, m = int(m1.group(1)), int(m1.group(2))
            if m1.group(3) == "pm" and h < 12:
                h += 12
            elif m1.group(3) == "am" and h == 12:
                h = 0
            return now.replace(hour=h, minute=m, second=0, microsecond=0)
        m2 = re.search(r"\b(\d{1,2})\s*(pm|am)\b", text_lower)
        if m2:
            h = int(m2.group(1))
            if m2.group(2) == "pm" and h < 12:
                h += 12
            elif m2.group(2) == "am" and h == 12:
                h = 0
            return now.replace(hour=h, minute=0, second=0, microsecond=0)
        m3 = re.search(r"\b(?:at|today at|around)\s*(\d{1,2})\b", text_lower)
        if m3:
            h = int(m3.group(1))
            if h <= 12 and (h < 7 or (h >= 7 and now.hour > h)):
                h += 12
            if 0 <= h < 24:
                return now.replace(hour=h, minute=0, second=0, microsecond=0)
        return now

    def extract_vehicle_type(self, text):
        text_lower = text.lower()
        if any(re.search(r"\b" + re.escape(k) + r"\b", text_lower) for k in ["bike", "motorcycle", "scooter", "two wheeler", "activa", "bullet"]):
            return "bike"
        if any(re.search(r"\b" + re.escape(k) + r"\b", text_lower) for k in ["car", "sedan", "suv", "vehicle", "four wheeler", "swift"]):
            return "car"
        return None

    def classify_intent(self, text, matched_stops):
        text_lower = text.lower()
        params = {"message": text}

        if any(k in text_lower for k in ["weather", "rain", "shower", "storm", "flood", "precipitation", "drizzle", "umbrella", "rainy", "forecast"]):
            params["time"] = self.extract_time(text)
            return "weather_query", params

        if any(k in text_lower for k in ["traffic", "congestion", "congested", "road condition", "jam", "jammed", "gridlock", "bumper", "slow traffic", "traffic update"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            params["source"] = src
            params["destination"] = dst
            params["time"] = self.extract_time(text)
            return "traffic_query", params

        if any(k in text_lower for k in ["nearest", "closest", "nearby", "close to", "near me", "bus stop near", "metro near", "nearest bus", "nearest metro", "closest to", "near my location"]):
            loc = None
            if matched_stops:
                loc = matched_stops[0]
            else:
                m = re.search(r"(?:near(?:est|by)?|close(?:st)?\s+to|to)\s+(?:the\s+)?(.+?)(?:\?|$|,)", text, re.IGNORECASE)
                if m:
                    loc = m.group(1).strip()
            params["location"] = loc
            return "nearest_stops", params

        if any(k in text_lower for k in ["ola", "uber", "namma yatri", "rapido", "cab", "taxi", "auto", "ride cost", "bike taxi", "surge"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            if not src or not dst:
                params["source"] = src
                params["destination"] = dst
                return "clarification", params
            params["source"] = src
            params["destination"] = dst
            return "ride_cost", params

        if any(k in text_lower for k in ["fuel", "petrol", "diesel", "consume", "litres", "liters", "mileage", "fuel cost", "own vehicle", "private vehicle", "own car", "drive to", "two-wheeler", "expense"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            vtype = self.extract_vehicle_type(text) or "car"
            params["source"] = src
            params["destination"] = dst
            params["vehicle_type"] = vtype
            if not src or not dst:
                return "clarification", params
            return "fuel_cost", params

        budget = self.extract_budget(text)
        if budget is not None:
            src, dst = self.determine_source_dest(matched_stops, text)
            params["budget"] = budget
            params["source"] = src
            params["destination"] = dst
            if not src or not dst:
                return "clarification", params
            return "budget_constrained", params

        vtype = self.extract_vehicle_type(text)
        if vtype is not None:
            _, dst = self.determine_source_dest(matched_stops, text)
            params["vtype"] = vtype
            params["destination"] = dst or (matched_stops[0] if matched_stops else None)
            return "vehicle_vs_transit", params

        is_route_request = any(k in text_lower for k in [
            "go to", "reach", "travel to", "how to go", "how can i get", "route to", "bus to", "metro to",
            "way to", "directions to", "fare to", "cost to", "price to", "how to travel", "how to reach",
            "ac bus", "vajra", "volvo", "possible ways", "all ways", "different ways",
            "all options", "routes to", "budget", "should i drive", "should i take my",
            "comparison", "compare", "transit vs", "multimodal", "combined route",
            "directions", "how long does it take", "how long", "get to", "timing from",
            "route from", "best way", "shortest route", "bus timing", "metro timing",
            "next bus", "next metro", "cheapest", "fare option", "combo", "bus + metro",
            "metro + bus", "bus-metro", "metro-bus", "choices to", "transport modes",
            "every way", "transport mode", "how do i get", "buses to", "air-conditioned"
        ])
        if is_route_request:
            src, dst = self.determine_source_dest(matched_stops, text)
            if not src or not dst:
                params["source"] = src
                params["destination"] = dst
                return "clarification", params
            else:
                params["source"] = src
                params["destination"] = dst
                if any(k in text_lower for k in ["ac bus", "ac buses", "vajra", "volvo", "ac available", "air-conditioned"]):
                    return "ac_bus_available", params
                if any(k in text_lower for k in ["multimodal", "combined route", "bus and metro", "metro and bus", "bus + metro", "metro + bus", "bus-metro", "metro-bus", "auto to the metro", "bus-metro-walk"]):
                    return "multimodal_journey", params
                if any(k in text_lower for k in ["possible ways", "all ways", "different ways", "all options", "routes to", "every way", "choices to", "transport modes", "transport mode"]):
                    return "possible_ways", params
                if any(k in text_lower for k in ["cost", "price", "fare", "cheap", "expensive", "rupee", "charge", "much", "ticket", "token", "cheapest"]):
                    return "journey_cost", params
                return "journey_time", params

        if any(k in text_lower for k in ["ac bus", "ac buses", "vajra", "volvo", "ac available", "air-conditioned"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "ac_bus_available", params

        if any(k in text_lower for k in ["multimodal", "combined route", "bus and metro", "metro and bus", "bus + metro", "metro + bus", "bus-metro", "metro-bus", "auto to the metro", "bus-metro-walk"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "multimodal_journey", params

        if any(k in text_lower for k in ["possible ways", "all ways", "different ways", "all options", "routes to", "every way", "choices to", "transport modes", "transport mode"]):
            src, dst = self.determine_source_dest(matched_stops, text)
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "possible_ways", params

        if len(matched_stops) >= 2:
            src, dst = self.determine_source_dest(matched_stops, text)
            params["source"] = src
            params["destination"] = dst
            if any(k in text_lower for k in ["cost", "price", "fare", "cheap", "expensive", "rupee", "charge", "much", "ticket", "token", "cheapest"]):
                return "journey_cost", params
            return "journey_time", params

        return "general", params

    def format_response(self, intent, params, data):
        if intent == "clarification":
            cq = params.get("clarification_question")
            if cq:
                return cq
            src = params.get("source")
            dst = params.get("destination")
            if not dst:
                return "Where do you want to go? Please specify your destination."
            elif not src:
                return "Where are you starting your journey from? Please specify your starting location."
            return "Where would you like to travel from and to?"

        if intent == "weather_query":
            weather = data.get("weather", "clear")
            t = params.get("time", datetime.now())
            time_str = t.strftime("%I:%M %p") if hasattr(t, "strftime") else str(t)
            if "heavy rain" in weather or "storm" in weather:
                return (
                    f"Rainy weather forecast at {time_str}. Road speeds will drop significantly. "
                    "I recommend taking Namma Metro to avoid traffic gridlock. "
                    "Cab surge pricing will also be much higher."
                )
            elif "light rain" in weather or "drizzle" in weather:
                return (
                    f"Light rain forecast at {time_str}. Roads may be slightly slower. "
                    "A direct Metro or AC Vajra Bus would be comfortable."
                )
            return f"Weather is clear at {time_str}. All modes are operating normally — good time to travel!"

        if intent == "traffic_query":
            src = params.get("source")
            dst = params.get("destination")
            level = data.get("congestion_level", "moderate")
            drive_time = data.get("drive_time_min")
            transit_time = data.get("transit_time")
            icons = {"clear": "Green", "moderate": "Yellow", "heavy": "Red"}
            labels = {"clear": "Traffic is clear", "moderate": "Moderate congestion", "heavy": "Heavy congestion"}
            label = labels.get(level, "Moderate traffic")
            icon = icons.get(level, "Yellow")
            if src and dst:
                base = f"{icon} light: {label} on the {src} to {dst} corridor."
                if drive_time:
                    base += f" Estimated drive time: {drive_time} mins."
                if transit_time:
                    base += f" Transit (Metro/Bus) estimated: {transit_time} mins."
                if level == "heavy":
                    base += " Tip: Take Namma Metro or BMTC to save time."
                return base
            if level == "heavy":
                return "Red light: Heavy traffic across Bengaluru. Drive times are 40-60% higher. Consider Metro or BMTC."
            elif level == "moderate":
                return "Yellow light: Moderate traffic in Bengaluru. Allow extra time if driving."
            return "Green light: Traffic is clear. Good time to travel by any mode."

        if intent == "ride_cost":
            src = params.get("source")
            dst = params.get("destination")
            providers = data.get("providers", {})
            distance_km = data.get("distance_km", 0)
            duration_min = data.get("duration_min", 0)
            if not providers:
                return f"Sorry, I could not calculate ride costs from {src} to {dst}. Locations may not be resolvable."
            lines = [f"Ride-hailing fares from {src} to {dst}"]
            lines.append(f"Distance: ~{distance_km:.1f} km, ~{int(duration_min)} min drive")
            lines.append("")
            provider_names = {"ola": "Ola", "uber": "Uber", "namma_yatri": "Namma Yatri", "rapido": "Rapido"}
            for pkey, vehicles in providers.items():
                label = provider_names.get(pkey, pkey.title())
                lines.append(f"{label}:")
                for v in vehicles[:3]:
                    lines.append(f"  - {v['vehicle']}: Rs.{v['fare_min']} - Rs.{v['fare_max']}")
                lines.append("")
            lines.append("Note: Fares include time-of-day surge. Actual app prices may vary slightly.")
            return "\n".join(lines)

        if intent == "fuel_cost":
            src = params.get("source")
            dst = params.get("destination")
            vtype = params.get("vehicle_type", "car")
            fuel_litres = data.get("fuel_litres", 0)
            fuel_cost = data.get("fuel_cost", 0)
            distance_km = data.get("distance_km", 0)
            efficiency = data.get("efficiency_kmpl", 0)
            fuel_type = data.get("fuel_type", "petrol")
            co2_kg = data.get("co2_kg", 0)
            lines = [f"Private vehicle fuel cost from {src} to {dst}"]
            lines.append(f"Vehicle: {vtype.title()}, Fuel: {fuel_type}")
            lines.append(f"Distance: ~{distance_km:.1f} km")
            lines.append(f"Fuel efficiency: {efficiency:.1f} km/L")
            lines.append(f"Fuel required: {fuel_litres:.2f} litres")
            lines.append(f"Fuel cost: Rs.{fuel_cost:.0f}")
            if co2_kg > 0:
                lines.append(f"CO2 emitted: ~{co2_kg:.2f} kg")
            lines.append("Note: Does not include toll, parking, or maintenance costs.")
            return "\n".join(lines)

        if intent == "nearest_stops":
            loc = params.get("location")
            nearest = data.get("nearest")
            if not nearest:
                return f"Sorry, I could not find nearby transit stops for '{loc}'. Try a more specific location name, e.g. 'Bangalore Palace' or 'Forum Mall Koramangala'."
            lines = [f"Nearest transit stops to {loc}:"]
            if nearest.get("bmtc"):
                lines.append("")
                lines.append("BMTC Bus Stops:")
                for name, dist in nearest["bmtc"]:
                    walk_mins = max(1, int(dist * 1000 / 80))
                    lines.append(f"  - {name} ({dist:.2f} km, ~{walk_mins} min walk)")
            if nearest.get("metro"):
                lines.append("")
                lines.append("Metro Stations:")
                for name, dist in nearest["metro"]:
                    walk_mins = max(1, int(dist * 1000 / 80))
                    lines.append(f"  - {name} Metro Station ({dist:.2f} km, ~{walk_mins} min walk)")
            return "\n".join(lines)

        if intent == "journey_time":
            src, dst = params.get("source"), params.get("destination")
            best_opt = data.get("best_option")
            if not best_opt:
                return f"Sorry, I could not find a route from {src} to {dst}."
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab/Auto", "car": "Personal Vehicle"}
            m_label = mode_labels.get(best_opt.get("mode"), "Transit")
            details = best_opt.get("details", {})
            dep = details.get("departure")
            arr = details.get("arrival")
            if dep and arr:
                return f"Next {m_label} from {src} to {dst} departs at {dep} and arrives at {arr}.\nTravel time: {best_opt.get('time')} mins | Cost: Rs.{best_opt.get('cost')}"
            return f"Fastest option from {src} to {dst}: {m_label}\nTime: {best_opt.get('time')} mins | Cost: Rs.{best_opt.get('cost')}"

        if intent == "journey_cost":
            src, dst = params.get("source"), params.get("destination")
            cheapest = data.get("best_option")
            if not cheapest:
                return f"Sorry, I could not find a route from {src} to {dst}."
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab/Auto", "car": "Personal Vehicle"}
            m_label = mode_labels.get(cheapest.get("mode"), "Transit")
            details = cheapest.get("details", {})
            dep = details.get("departure")
            arr = details.get("arrival")
            if dep and arr:
                return f"Cheapest option is {m_label} (departs {dep}, arrives {arr}).\nCost: Rs.{cheapest.get('cost')} | Travel time: {cheapest.get('time')} mins"
            return f"Cheapest way from {src} to {dst}: {m_label}\nCost: Rs.{cheapest.get('cost')} | Time: {cheapest.get('time')} mins"

        if intent == "budget_constrained":
            src, dst = params.get("source"), params.get("destination")
            budget = params.get("budget", 0)
            options = data.get("options", [])
            if options:
                best = options[0]
                mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab/Auto", "car": "Personal Vehicle"}
                m_label = mode_labels.get(best.get("mode"), "Transit")
                return f"Under Rs.{budget} budget, found {len(options)} option(s). Best: {m_label}: Rs.{best.get('cost')} in {best.get('time')} mins"
            cheapest = data.get("cheapest_available")
            if not cheapest:
                return f"Sorry, no travel options found from {src} to {dst}."
            diff = cheapest.get("cost", 0) - budget
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab/Auto", "car": "Personal Vehicle"}
            m_label = mode_labels.get(cheapest.get("mode"), "Transit")
            return f"Your budget of Rs.{budget} is a bit low. Cheapest option is {m_label} at Rs.{cheapest.get('cost')} (Rs.{diff} over budget) taking {cheapest.get('time')} mins."

        if intent == "vehicle_vs_transit":
            dst = params.get("destination")
            vtype = params.get("vtype", "bike")
            v_cost = data.get("vehicle_cost", 0)
            v_time = data.get("vehicle_time", 0)
            t_cost = data.get("transit_cost", 0)
            t_time = data.get("transit_time", 0)
            weather = data.get("weather", "clear")
            if "heavy rain" in weather or "storm" in weather:
                return (
                    f"Heavy rain warning! Driving your {vtype} to {dst} costs Rs.{v_cost:.0f} ({v_time:.0f} mins) but rain will slow traffic. "
                    f"Transit costs Rs.{t_cost} ({t_time} mins) and keeps you dry. Strongly recommend transit!"
                )
            if v_cost < t_cost:
                return (
                    f"Driving your {vtype} to {dst} is cost-effective: Rs.{v_cost:.0f} in {v_time:.0f} mins. "
                    f"Transit costs Rs.{t_cost} and takes {t_time} mins. Driving saves Rs.{t_cost - v_cost:.0f} today."
                )
            return (
                f"Public transit is recommended to {dst}: Rs.{t_cost} in {t_time} mins. "
                f"Driving your {vtype} costs Rs.{v_cost:.0f} ({v_time:.0f} mins). Transit saves Rs.{v_cost - t_cost:.0f} and avoids parking hassle."
            )

        if intent == "multimodal_journey":
            src, dst = params.get("source"), params.get("destination")
            options = data.get("options", [])
            if not options:
                return f"No combined Bus+Metro route found from {src} to {dst}. Try direct BMTC buses or Namma Metro via the Plan Journey feature."
            best = options[0]
            reply = f"Multimodal route from {src} to {dst}:\n"
            for leg in best.get("legs", []):
                mode = leg.get("mode", "")
                fr = leg.get("from", "")
                to = leg.get("to", "")
                if mode == "bmtc":
                    reply += f"  Take BMTC bus: {fr} to {to}\n"
                elif mode == "metro":
                    reply += f"  Take Metro: {fr} to {to}\n"
                elif mode == "walk":
                    reply += f"  Walk: {fr} to {to}\n"
            reply += f"Total time: {best.get('total_time')} mins | Total fare: Rs.{best.get('total_fare')}"
            return reply

        if intent == "possible_ways":
            src, dst = params.get("source"), params.get("destination")
            options = data.get("options", [])
            if not options:
                return f"Sorry, no transit options found from {src} to {dst}."
            mode_labels = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab (Ola/Uber)", "car": "Personal Vehicle"}
            reply = f"Possible ways to travel from {src} to {dst}:\n\n"
            for opt in options:
                m_label = mode_labels.get(opt.get("mode"), "Transit")
                reply += f"- {m_label}: ~{opt.get('time')} mins, Rs.{opt.get('cost')}\n"
            return reply

        if intent == "ac_bus_available":
            src, dst = params.get("source"), params.get("destination")
            has_ac = data.get("has_ac", False)
            ac_buses = data.get("ac_buses", [])
            if has_ac and ac_buses:
                return f"AC Vajra buses available from {src} to {dst}: {', '.join(ac_buses[:4])}"
            return f"No direct AC Vajra bus found between {src} and {dst}. Try regular BMTC buses or Namma Metro."

        # General
        msg = params.get("message", "").lower() if params else ""
        if any(k in msg for k in ["hello", "hi", "hey"]):
            return (
                "Hello! I am your Bangalore Commuter Assistant. I can help with:\n\n"
                "- BMTC bus routes and fares\n"
                "- Namma Metro timings\n"
                "- Ola/Uber/Namma Yatri/Rapido cab fares\n"
                "- Fuel cost for your car or bike\n"
                "- Nearest bus stops and metro stations (any Bangalore landmark)\n"
                "- Weather and traffic conditions\n\n"
                "Try asking: 'How much will Ola cost from Majestic to Indiranagar?' or 'Nearest metro to Bangalore Palace'"
            )
        elif any(k in msg for k in ["thank", "thanks"]):
            return "You're welcome! Safe travels. Let me know if you need anything else!"
        elif any(k in msg for k in ["help", "what can you"]):
            return (
                "I am your Bangalore Commuter Assistant. Here is what I can do:\n\n"
                "1. Route planning (Bus/Metro/Multimodal)\n"
                "2. Ride-hailing costs (Ola, Uber, Namma Yatri, Rapido)\n"
                "3. Fuel cost for your car or bike\n"
                "4. Nearest stops for any landmark in Bangalore\n"
                "5. Weather forecast and its impact on travel\n"
                "6. Traffic conditions and drive-time estimates\n"
                "7. Budget travel (cheapest routes under your budget)\n"
                "8. AC Vajra bus availability check"
            )
        return (
            "I am your Bangalore Commuter Assistant!\n\n"
            "Ask me about:\n"
            "- 'Ola fare from HSR to Majestic'\n"
            "- 'Nearest bus stop to Bangalore Palace'\n"
            "- 'How much fuel if I drive from Whitefield to Electronic City?'\n"
            "- 'Will it rain at 5 PM?'\n"
            "- 'Traffic from MG Road to Hebbal?'\n"
            "- 'Multimodal route from Silk Board to Yelahanka'"
        )
