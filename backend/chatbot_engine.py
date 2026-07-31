import os
import json
import requests
import re
import difflib
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

# Common English filler words that should never be treated as a place-name
# candidate when hunting for unresolved locations to disambiguate.
_STOPWORDS = {
    "the", "and", "for", "with", "from", "to", "at", "in", "on", "is",
    "are", "how", "what", "when", "where", "which", "please", "today",
    "tomorrow", "now", "there", "here", "this", "that", "near", "nearest",
    "nearby", "reach", "get", "going", "want", "need", "trip", "travel",
    "journey", "route", "bus", "metro", "cab", "auto", "train", "budget",
    "rupees", "rupee", "cheap", "cheapest", "fastest", "best", "good",
    "have", "can", "you", "tell", "about", "cost", "fare", "time", "hour",
    "hours", "minutes", "min", "would", "like", "give", "show", "find",
    "i", "a", "my", "me", "of", "go", "do", "does", "it", "will", "should",
    "start", "starting", "leave", "arrive", "arriving", "departure", "destination",
    "traveling", "travelled", "traveler", "commuter", "commute", "way", "ways",
}

MODE_LABELS = {"bmtc": "BMTC Bus", "metro": "Namma Metro", "cab": "Cab / Auto", "car": "Personal Vehicle"}

# A handful of BMTC stop entries in the raw dataset are just generic single
# words (data artifacts, e.g. a stop literally named "Metro" or "Church")
# rather than an actual identifiable place. Matching on these produces
# confusing/wrong results (e.g. "nearest metro to X" matching the word
# "metro" itself as a location), so they're excluded from stop-name matching
# entirely -- real named landmarks (e.g. "Christ Church") are unaffected
# since only an EXACT, whole-name match against this list is blocked.
_GENERIC_STOP_BLOCKLIST = {
    "metro", "bus", "station", "stop", "junction", "circle", "cross", "gate",
    "road", "signal", "depot", "stand", "market", "park", "layout", "town",
    "city", "main", "center", "centre", "school", "college", "temple",
    "church", "the", "and", "for",
}


class ChatbotEngine:
    def __init__(
        self,
        bmtc_stops: List[str],
        metro_stations: List[str],
        all_vehicles: Optional[List[Dict[str, Any]]] = None,
        poi_names: Optional[List[str]] = None,
    ):
        self.bmtc_stops = bmtc_stops
        self.metro_stations = metro_stations
        self.poi_names = poi_names or []
        # Combine and deduplicate stop names -- POIs (colleges, hospitals,
        # tech parks, malls, attractions, hotels, railway stations, airport,
        # landmarks) are treated exactly like any other stop name so the
        # existing substring/alias/fuzzy matching below "just works" for them.
        combined_stops = list(set(list(bmtc_stops) + list(metro_stations) + list(self.poi_names)))
        self.all_stops = [s for s in combined_stops if s.strip().lower() not in _GENERIC_STOP_BLOCKLIST]
        self.all_vehicles = all_vehicles or []

    def query_llm(self, message: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
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
            "- \"journey_time\": User wants to travel between locations — fastest route, any mode.\n"
            "- \"journey_cost\": User asks about public transit (bus/metro) fares or general/comparative route costs.\n"
            "- \"budget_constrained\": User wants to travel under a specific budget.\n"
            "- \"possible_ways\": User wants ALL modes/routes compared.\n"
            "- \"ride_cost\": User asks specifically about cab, taxi, auto, Ola, Uber, Namma Yatri, or Rapido ride-hailing fares. Extract source+destination.\n"
            "- \"fuel_cost\": User asks about fuel/petrol/diesel or private vehicle cost. Extract source, destination, vehicle_type.\n"
            "- \"nearest_stops\": User wants nearest bus stop or metro station. Extract location.\n"
            "- \"traffic_query\": User asks about traffic, congestion, road conditions, drive time.\n"
            "- \"multimodal_journey\": User asks for Bus+Metro combined route.\n"
            "- \"weather_query\": User asks about weather or rain forecast.\n"
            "- \"vehicle_vs_transit\": User wants to compare driving vs public transit.\n"
            "- \"nearby_pois\": User wants to find nearby places, restaurants, cafes, attractions, hotels, or other POIs. Extract location and poi_type ('restaurant', 'cafe', 'attraction', 'places').\n"
            "- \"general\": General transit rules, Metro timings, greetings, help.\n"
            "- \"clarification\": Journey intent but source or destination is missing.\n\n"
            "RULES:\n"
            "1. Support multi-stop journeys: For journeys with 3 to 5 destinations, extract all destinations in order into the 'stops' parameter array.\n"
            "2. For nearby_pois: extract the center location into 'location' and the type of places (e.g. 'restaurant', 'cafe', 'attraction') into 'poi_type'.\n"
            "3. Output MUST be a single JSON object matching the structure below.\n\n"
            "Output structure:\n"
            "{\n"
            "  \"intent\": \"intent_name\",\n"
            "  \"parameters\": {\n"
            "    \"source\": \"string or null\",\n"
            "    \"destination\": \"string or null\",\n"
            "    \"stops\": [\"string\"] or null,\n"
            "    \"location\": \"string or null\",\n"
            "    \"poi_type\": \"string or null\",\n"
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

    def resolve_context_from_history(self, message: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
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

        # Clean/resolve current stop
        stops = self.extract_stops(message)
        current_stop = stops[0] if stops else None
        if not current_stop:
            from location_aliases import normalize_query_text, fuzzy_find_stop
            norm_msg = normalize_query_text(message)
            fuzzy_hit = fuzzy_find_stop(norm_msg, self.all_stops)
            if fuzzy_hit:
                current_stop = fuzzy_hit
            else:
                cleaned = message.strip()
                if cleaned:
                    current_stop = cleaned
                else:
                    return None

        # Parse previous source/destination
        prev_stops = self.extract_stops(user_msg_before_bot) if user_msg_before_bot else []
        prev_src, prev_dst = self.determine_source_dest(prev_stops, user_msg_before_bot) if user_msg_before_bot else (None, None)

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
        params = {"source": source, "destination": destination, "message": f"{user_msg_before_bot} {message}" if user_msg_before_bot else message}

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


    def get_simulated_weather(self, time: datetime) -> str:
        """Fetch weather condition (real-time Open-Meteo API, falls back to timeline)."""
        from weather_helper import get_realtime_weather
        return get_realtime_weather(time)

    def extract_stops(self, text: str) -> List[str]:
        """Fuzzy/exact substring stop name extraction."""
        from location_aliases import normalize_query_text, fuzzy_find_stop

        matched = []
        sorted_stops = sorted(self.all_stops, key=len, reverse=True)
        used_indices: List[Tuple[int, int]] = []

        # 1. Exact match on raw input text first to bypass conflicting global aliases
        raw_text_lower = text.lower()
        for stop in sorted_stops:
            stop_lower = stop.lower()
            if len(stop_lower) < 3:
                continue

            start_idx = 0
            while True:
                idx = raw_text_lower.find(stop_lower, start_idx)
                if idx == -1:
                    break

                overlap = False
                for s, e in used_indices:
                    if not (idx + len(stop_lower) <= s or idx >= e):
                        overlap = True
                        break

                if not overlap:
                    is_word = True
                    if len(stop_lower) <= 5:
                        before_char = raw_text_lower[idx - 1] if idx > 0 else ' '
                        after_char = raw_text_lower[idx + len(stop_lower)] if idx + len(stop_lower) < len(raw_text_lower) else ' '
                        if before_char.isalnum() or after_char.isalnum():
                            is_word = False

                    if is_word:
                        matched.append((idx, stop))
                        used_indices.append((idx, idx + len(stop_lower)))
                        break
                start_idx = idx + 1

        # 2. Match on normalized text (aliases/typos) for remaining unmatched stops
        norm_text = normalize_query_text(text)
        norm_text_lower = norm_text.lower()
        norm_used_indices = list(used_indices)

        for stop in sorted_stops:
            stop_lower = stop.lower()
            if len(stop_lower) < 3:
                continue
            if any(m[1] == stop for m in matched):
                continue

            start_idx = 0
            while True:
                idx = norm_text_lower.find(stop_lower, start_idx)
                if idx == -1:
                    break

                overlap = False
                for s, e in norm_used_indices:
                    if not (idx + len(stop_lower) <= s or idx >= e):
                        overlap = True
                        break

                if not overlap:
                    is_word = True
                    if len(stop_lower) <= 5:
                        before_char = norm_text_lower[idx - 1] if idx > 0 else ' '
                        after_char = norm_text_lower[idx + len(stop_lower)] if idx + len(stop_lower) < len(norm_text_lower) else ' '
                        if before_char.isalnum() or after_char.isalnum():
                            is_word = False

                    if is_word:
                        # Append with a high index offset to preserve raw-match sort order,
                        # but still allow sorting normalized matches among themselves.
                        matched.append((idx + len(text), stop))
                        norm_used_indices.append((idx, idx + len(stop_lower)))
                        break
                start_idx = idx + 1

        # 3. Fuzzy fallback pass: catch typos
        words = text.split()
        if words:
            for window in (3, 2, 1):
                for i in range(0, max(0, len(words) - window + 1)):
                    phrase = " ".join(words[i:i + window])
                    phrase_lower = phrase.lower()
                    if len(phrase_lower) < 5:
                        continue
                    idx = raw_text_lower.find(phrase_lower)
                    if idx == -1:
                        continue
                    overlap = any(not (idx + len(phrase_lower) <= s or idx >= e) for s, e in used_indices)
                    if overlap:
                        continue
                    fuzzy_hit = fuzzy_find_stop(phrase, self.all_stops)
                    if fuzzy_hit and not any(m[1] == fuzzy_hit for m in matched):
                        matched.append((idx, fuzzy_hit))
                        used_indices.append((idx, idx + len(phrase_lower)))

        # Sort matched stops by position
        matched.sort(key=lambda x: x[0])
        raw_names = [name for _, name in matched]
        
        # Deduplicate substring matches (e.g., Indiranagar vs Indiranagara)
        unique_names = []
        for name in raw_names:
            if not any(name.lower() in existing.lower() or existing.lower() in name.lower() for existing in unique_names):
                unique_names.append(name)
        return unique_names


    def find_unresolved_location_phrases(self, text: str, matched_stops: List[str]) -> List[str]:
        """Pull out place-name-shaped phrases the user typed that extract_stops()
        could NOT confidently resolve (e.g. a garbled/unknown spelling).

        Used to power a "Did you mean...?" clarification instead of silently
        guessing or letting the model hallucinate a location. Looks specifically
        at phrases following common location prepositions ("from X", "to X",
        "near X", "reach X") since those are the highest-confidence spots a
        rider would name a place.
        """
        from location_aliases import normalize_query_text
        norm_text = normalize_query_text(text)

        already_resolved = " ".join(matched_stops).lower()

        candidates: List[str] = []
        patterns = [
            r'\bfrom\s+([a-zA-Z][a-zA-Z\s]{2,30}?)(?=\s+to\b|[,.?!]|$)',
            r'\bto\s+([a-zA-Z][a-zA-Z\s]{2,30}?)(?=\s+from\b|[,.?!]|$)',
            r'\b(?:near|nearest|nearby|close to)\s+([a-zA-Z][a-zA-Z\s]{2,30}?)(?=[,.?!]|$)',
            r'\breach\s+([a-zA-Z][a-zA-Z\s]{2,30}?)(?=[,.?!]|$)',
        ]
        for pat in patterns:
            for m in re.finditer(pat, norm_text, flags=re.IGNORECASE):
                phrase = m.group(1).strip()
                # Strip trailing filler words one at a time (e.g. "Koliformgate please")
                words = [w for w in phrase.split() if w]
                while words and words[-1].lower() in _STOPWORDS:
                    words.pop()
                while words and words[0].lower() in _STOPWORDS:
                    words.pop(0)
                phrase = " ".join(words)
                if len(phrase) < 4:
                    continue
                phrase_lower = phrase.lower()
                # Already resolved by extract_stops()? skip it -- either by
                # direct substring containment, or because it confidently
                # fuzzy-matches a known stop/POI at the SAME cutoff
                # extract_stops() itself uses (0.82). Only phrases that
                # extract_stops() genuinely could not resolve should reach
                # the "did you mean...?" clarification below.
                from location_aliases import fuzzy_find_stop
                if phrase_lower in already_resolved or any(
                    phrase_lower in s.lower() or s.lower() in phrase_lower for s in matched_stops
                ):
                    continue
                if fuzzy_find_stop(phrase, self.all_stops):
                    continue
                if phrase_lower not in [c.lower() for c in candidates]:
                    candidates.append(phrase)
        return candidates

    def resolve_location_candidates(self, phrase: str, n: int = 3, cutoff: float = 0.5) -> List[str]:
        """Rank plausible location matches for a garbled/unresolved phrase,
        for use in a "Did you mean...?" clarification prompt. Never treat
        this as a confirmed match -- it is suggestions only."""
        from location_aliases import fuzzy_suggest_stops
        return fuzzy_suggest_stops(phrase, self.all_stops, n=n, cutoff=cutoff)

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

        # Look for "I have ₹X" / "I have X rupees" / "with X" patterns
        m1b = re.search(r'\b(?:i have|got|with)\s*(?:rs\.?|₹|inr)?\s*(\d+)\b', text_lower)
        if m1b and any(k in text_lower for k in ["₹", "rs", "rupee", "inr", "budget"]):
            return int(m1b.group(1))

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

    def extract_duration_hours(self, text: str) -> Optional[float]:
        """Extract an available-time budget in hours, e.g. "5 hours", "3 hrs",
        "2.5 hour trip". Used for budget-based attraction planning."""
        text_lower = text.lower()
        m = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:hours|hour|hrs|hr)\b', text_lower)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
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

    def classify_intent(self, raw_text: str, matched_stops: List[str]) -> Tuple[str, Dict[str, Any]]:
        """Classify conversational intent and compile parameters."""
        from location_aliases import normalize_query_text

        text = normalize_query_text(raw_text)
        text_lower = text.lower()
        params: Dict[str, Any] = {}

        # Keep original message for general replies
        params["message"] = raw_text

        # 0. Check for multi-stop journey first
        if len(matched_stops) >= 3:
            params["stops"] = matched_stops
            params["source"] = matched_stops[0]
            params["destination"] = matched_stops[-1]
            return "possible_ways", params

        # 0.1. Check for nearby POIs/places/restaurants
        is_nearby_request = any(k in text_lower for k in ["restaurant", "cafe", "food", "eat", "dining", "diner", "places to visit", "attractions", "sightseeing", "places to see", "tourist spot", "nearby places", "places near"])
        if is_nearby_request:
            loc = matched_stops[0] if matched_stops else None
            if not loc:
                unresolved = self.find_unresolved_location_phrases(text, matched_stops)
                if unresolved:
                    loc = unresolved[0]
            if loc:
                params["location"] = loc
                if any(k in text_lower for k in ["restaurant", "food", "eat", "dining", "diner"]):
                    params["poi_type"] = "restaurant"
                elif "cafe" in text_lower:
                    params["poi_type"] = "cafe"
                else:
                    params["poi_type"] = "attraction"
                return "nearby_pois", params

        # Determine source and destination first to see if we have a complete route request
        src, dst = self.determine_source_dest(matched_stops, text)

        # 0. Location disambiguation gate -- only run if we do not have a complete route request
        has_travel_cue = any(k in text_lower for k in [
            "from ", "to ", "near ", "nearest", "nearby", "reach ", "how do i get",
            "how to go", "route to", "way to",
        ])
        if not (src and dst) and has_travel_cue:
            unresolved = self.find_unresolved_location_phrases(text, matched_stops)
            for phrase in unresolved:
                suggestions = self.resolve_location_candidates(phrase)
                if suggestions:
                    params["unresolved_phrase"] = phrase
                    params["suggestions"] = suggestions
                    return "clarify_location", params

        # 0.5. Ride Cost & Fuel Cost Check
        if any(k in text_lower for k in ["ola", "uber", "namma yatri", "rapido", "cab", "taxi", "auto", "ride cost", "cab cost", "auto fare"]):
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "ride_cost", params
            else:
                params["source"] = src
                params["destination"] = dst
                return "clarification", params

        if any(k in text_lower for k in ["fuel", "petrol", "diesel", "consume", "litres", "mileage", "fuel cost"]):
            params["vehicle_type"] = self.extract_vehicle_type(text_lower) or "car"
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "fuel_cost", params
            else:
                params["source"] = src
                params["destination"] = dst
                return "clarification", params

        # 1. AC Bus Check
        if any(k in text_lower for k in ["ac bus", "ac buses", "vajra", "volvo", "ac available"]):
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "ac_bus_available", params
            else:
                params["source"] = src
                params["destination"] = dst
                return "clarification", params

        # 2. Possible Ways Check
        if any(k in text_lower for k in ["possible ways", "all ways", "different ways", "all options", "routes to"]):
            if src and dst:
                params["source"] = src
                params["destination"] = dst
                return "possible_ways", params
            else:
                params["source"] = src
                params["destination"] = dst
                return "clarification", params

        # 3. Nearest Stop Check
        if any(k in text_lower for k in ["nearest", "closest", "nearby", "close to"]):
            if matched_stops:
                params["location"] = matched_stops[0]
                return "nearest_stops", params

        # 4. Budget Constraint / Budget Exploration
        budget = self.extract_budget(text)
        if budget is not None:
            params["budget"] = budget
            params["source"] = src
            params["destination"] = dst
            params["available_hours"] = self.extract_duration_hours(text)
            if dst:
                return "budget_constrained", params
            else:
                return "budget_explore", params

        # 5. Vehicle vs Transit
        vtype = self.extract_vehicle_type(text)
        if vtype is not None:
            params["vtype"] = vtype
            params["destination"] = dst or (matched_stops[0] if matched_stops else None)
            return "vehicle_vs_transit", params

        # 6. Weather Forecast
        if any(k in text_lower for k in ["weather", "rain", "shower", "storm", "flood", "precipitation", "drizzle", "clear"]):
            params["time"] = self.extract_time(text)
            return "weather_query", params

        # 7. Journey Time vs Cost
        is_route_request = any(k in text_lower for k in [
            "go to", "reach", "travel to", "how to go", "how can i get", "route to", "way to", "directions to",
            "how to travel", "how to reach", "get to", "timing from", "route from", "how do i get"
        ])
        if len(matched_stops) >= 1 or is_route_request:
            params["source"] = src
            params["destination"] = dst

            if not src or not dst:
                return "clarification", params

            if any(k in text_lower for k in ["cost", "price", "fare", "cheap", "expensive", "rupee", "charge", "much"]):
                return "journey_cost", params
            else:
                return "journey_time", params

        # 8. General conversational fallback
        return "general", params


    def format_response(self, intent: str, params: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Construct conversational replies based on solver output data."""
        if intent == "nearby_pois":
            loc = params.get("location")
            poi_type = params.get("poi_type", "places")
            places = data.get("places", [])
            if not places:
                return f"I couldn't find any nearby {poi_type}s close to '{loc}'."
            return f"I found {len(places)} nearby {poi_type}(s) close to {loc}. You can view their details and walking distances in the cards below!"

        if "options" in data and data["options"]:
            src = params.get("source")
            dst = params.get("destination")
            stops = params.get("stops")
            
            journey_str = f"from {src} to {dst}"
            if stops and len(stops) >= 3:
                journey_str = " → ".join(stops)
                
            reply = f"I've generated all possible ways and complete itineraries for your journey ({journey_str}) and compared Bus, Metro, Cab, Personal Vehicle, and Multimodal options.\n\n"
            
            best = data.get("best_overall")
            if best and isinstance(best, dict):
                mode_label = MODE_LABELS.get(best.get("mode"), best.get("mode", ""))
                reply += f"⭐ **Recommendation**: {best.get('note', f'Taking {mode_label} is the best option for this trip.')}\n\n"
            
            reply += "Please review the travel time, fare, walking distance, transfers, and carbon footprint comparisons in the cards below."
            return reply

        if "legs" in data:
            legs = data["legs"]
            reply = f"Here are the possible ways to travel your multi-stop itinerary:\n\n"
            
            total_bmtc_cost, total_bmtc_time = 0, 0
            total_metro_cost, total_metro_time = 0, 0
            total_cab_cost, total_cab_time = 0, 0
            total_car_cost, total_car_time = 0, 0
            
            all_bmtc_avail, all_metro_avail = True, True
            
            for idx, leg in enumerate(legs):
                l_src = leg["source"]
                l_dst = leg["destination"]
                reply += f"🛣️ **Leg {idx+1}: {l_src} to {l_dst}**\n"
                
                b_avail = leg["bmtc"].get("available", False)
                m_avail = leg["metro"].get("available", False)
                
                if b_avail:
                    reply += f"• 🚌 BMTC Bus: ~{leg['bmtc'].get('time')} mins, ₹{leg['bmtc'].get('cost')}\n"
                    total_bmtc_cost += leg["bmtc"].get("cost", 0)
                    total_bmtc_time += leg["bmtc"].get("time", 0)
                else:
                    all_bmtc_avail = False
                    reply += "• 🚌 BMTC Bus: Not available\n"
                    
                if m_avail:
                    reply += f"• 🚇 Namma Metro: ~{leg['metro'].get('time')} mins, ₹{leg['metro'].get('cost')}\n"
                    total_metro_cost += leg["metro"].get("cost", 0)
                    total_metro_time += leg["metro"].get("time", 0)
                else:
                    all_metro_avail = False
                    reply += "• 🚇 Namma Metro: Not available\n"
                    
                cab = leg["cab"]
                if cab.get("available"):
                    reply += f"• 🚖 Cab/Auto: ~{cab.get('time')} mins, ₹{cab.get('cost')}\n"
                    total_cab_cost += cab.get("cost", 0)
                    total_cab_time += cab.get("time", 0)
                    
                car = leg["car"]
                if car.get("available"):
                    reply += f"• 🚗 Personal Vehicle: ~{car.get('time')} mins, ₹{car.get('cost')}\n"
                    total_car_cost += car.get("cost", 0)
                    total_car_time += car.get("time", 0)
                    
                reply += "\n"
                
            reply += "📊 **Itinerary Totals:**\n"
            if all_bmtc_avail:
                reply += f"• 🚌 BMTC Bus: ~{total_bmtc_time} mins, ₹{total_bmtc_cost}\n"
            if all_metro_avail:
                reply += f"• 🚇 Namma Metro: ~{total_metro_time} mins, ₹{total_metro_cost}\n"
            reply += f"• 🚖 Cab/Auto: ~{total_cab_time} mins, ₹{total_cab_cost}\n"
            reply += f"• 🚗 Personal Vehicle: ~{total_car_time} mins, ₹{total_car_cost}\n"
            
            best_mode = "Personal Vehicle"
            best_time = total_car_time
            best_cost = total_car_cost
            if all_metro_avail and total_metro_time < total_car_time + 30:
                best_mode = "Namma Metro"
                best_time = total_metro_time
                best_cost = total_metro_cost
            elif all_bmtc_avail and total_bmtc_cost < total_car_cost / 3:
                best_mode = "BMTC Bus"
                best_time = total_bmtc_time
                best_cost = total_bmtc_cost
                
            reply += f"\n⭐ **Recommended Strategy:** Taking **{best_mode}** for the entire journey offers the best overall experience."
            return reply

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

        elif intent == "weather_query":
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

        elif intent == "clarify_location":
            phrase = params.get("unresolved_phrase", "that place")
            suggestions = params.get("suggestions", [])
            if not suggestions:
                return f"I couldn't find \"{phrase}\" in Bengaluru. Could you double-check the spelling or try a nearby landmark?"
            if len(suggestions) == 1:
                return f"I couldn't find \"{phrase}\" exactly -- did you mean **{suggestions[0]}**?"
            options = ", ".join(f"**{s}**" for s in suggestions[:-1]) + f" or **{suggestions[-1]}**"
            return f"I couldn't find \"{phrase}\" exactly -- did you mean {options}?"

        elif intent in ("journey_time", "journey_cost", "possible_ways"):
            src, dst = params.get("source"), params.get("destination")
            options = data.get("options", [])
            best_opt = data.get("best_option")
            
            if not options and best_opt:
                options = [best_opt]

            if not options:
                return f"Sorry, I couldn't find a route from {src} to {dst}."

            if intent == "journey_time":
                reply = f"Here is a comparison of the fastest travel options from {src} to {dst}:\n\n"
            elif intent == "journey_cost":
                reply = f"Here is a comparison of the cheapest travel options from {src} to {dst}:\n\n"
            else:
                reply = f"Here are the possible ways to travel from {src} to {dst}:\n\n"
            for opt in options:
                m = opt.get("mode")
                m_label = MODE_LABELS.get(m, m)
                t = opt.get("time")
                c = opt.get("cost")
                
                emoji = "🚇" if m == "metro" else "🚌" if m == "bmtc" else "🚖" if m == "cab" else "🚗"
                
                suffix = ""
                best_pick = data.get("best_overall")
                if best_pick and best_pick.get("mode") == m:
                    suffix = " ⭐ (Recommended)"
                elif best_opt and best_opt.get("mode") == m:
                    suffix = " ⚡ (Fastest)" if intent == "journey_time" else " 💎 (Cheapest)"
                    
                reply += f"• {emoji} **{m_label}**: ~{t} mins, ₹{c}{suffix}\n"

            best_pick = data.get("best_overall")
            if best_pick and best_pick.get("note"):
                reply += f"\n**Recommendation:** {best_pick['note']}"
            return reply

        elif intent == "ride_cost":
            src, dst = params.get("source"), params.get("destination")
            providers = data.get("providers", {})
            dist_km = data.get("distance_km")
            duration_min = data.get("duration_min")
            
            if not providers:
                return f"Sorry, I couldn't calculate ride fares from {src} to {dst}."
                
            reply = f"Here is a cab cost comparison from {src} to {dst}:\n\n"
            for pkey, label, emoji in [("namma_yatri", "Namma Yatri", "🛺"), ("ola", "Ola", "🚕"), ("uber", "Uber", "🚙"), ("rapido", "Rapido", "🏍️")]:
                if pkey in providers and providers[pkey]:
                    fares = providers[pkey]
                    fare_min = fares[0].get("fare_min")
                    fare_max = fares[0].get("fare_max")
                    vname = fares[0].get("vehicle", "Cab")
                    reply += f"• {emoji} **{label}** ({vname}): ₹{fare_min} – ₹{fare_max}\n"
                    
            if dist_km and duration_min:
                reply += f"\nDistance: ~{dist_km:.1f} km | Est. drive time: ~{int(duration_min)} mins."
            return reply

        elif intent == "fuel_cost":
            src, dst = params.get("source"), params.get("destination")
            vtype = data.get("vehicle_type", "car")
            cost = data.get("fuel_cost")
            litres = data.get("fuel_litres")
            dist = data.get("distance_km")
            duration = data.get("duration_min")
            
            if cost is None:
                return f"Sorry, I couldn't calculate the fuel cost from {src} to {dst}."
                
            reply = (
                f"For a private vehicle ({vtype}) trip from {src} to {dst}:\n\n"
                f"• ⛽ **Estimated Fuel Cost**: ₹{cost:.1f}\n"
                f"• 🔋 **Fuel Consumption**: ~{litres:.2f} Litres (petrol)\n"
                f"• 📏 **Trip Distance**: ~{dist:.1f} km\n"
                f"• ⏱️ **Est. Drive Time**: ~{int(duration)} mins\n"
            )
            return reply

        elif intent == "budget_constrained":
            src, dst = params.get("source"), params.get("destination")
            budget = params.get("budget", 0)
            options = data.get("options", [])

            if options:
                # Recommend best option under budget
                best = options[0]
                m_label = MODE_LABELS.get(best.get("mode"), "Transit")

                return (
                    f"Under your ₹{budget} budget, I found {len(options)} options from {src} to {dst}. "
                    f"The recommended choice is the {m_label} which costs ₹{best.get('cost')} and takes {best.get('time')} minutes."
                )
            else:
                # Suggest cheapest available option and specify difference
                cheapest = data.get("cheapest_available")
                if not cheapest:
                    return f"Sorry, I couldn't find any travel options from {src} to {dst}."

                diff = cheapest.get("cost", 0) - budget
                m_label = MODE_LABELS.get(cheapest.get("mode"), "Transit")

                return (
                    f"Your budget of ₹{budget} is too low for a direct trip from {src} to {dst}. The cheapest option is the "
                    f"{m_label} at ₹{cheapest.get('cost')}, which is ₹{diff} over your budget."
                )

        elif intent == "budget_explore":
            budget = params.get("budget", 0)
            hours = params.get("available_hours")
            source = data.get("source_used")
            recs = data.get("attraction_recommendations", [])
            assumed_source = data.get("assumed_source", False)

            if not recs:
                shortfall = data.get("cheapest_shortfall")
                base = f"With ₹{budget}"
                if hours:
                    base += f" and {hours:g} hours"
                base += f" from {source}, I couldn't find an attraction that fits -- even the cheapest option "
                if shortfall:
                    base += f"({shortfall['name']}) needs about ₹{shortfall['total_cost']} round-trip with entry fee, which is over budget."
                else:
                    base += "needs more than your budget covers once travel and entry fees are included."
                return base

            lines = []
            prefix = f"With ₹{budget}"
            if hours:
                prefix += f" and about {hours:g} hours"
            prefix += f" from {source}"
            if assumed_source:
                prefix += " (assuming you're starting near the city center -- tell me your actual starting point for more accurate costs)"
            prefix += ", here's what you can comfortably do:\n"
            lines.append(prefix)

            for r in recs:
                lines.append(
                    f"- **{r['name']}**: ~₹{r['return_fare']} round-trip by {MODE_LABELS.get(r['mode'], r['mode'])} "
                    f"(~{r['one_way_time']} min each way) + ₹{r['entry_fee']} entry ≈ ₹{r['total_cost']} total, "
                    f"leaving you ₹{r['remaining_budget']}."
                )
            lines.append("(Entry fees are approximate reference values and travel costs are computed by the app's routing engines.)")
            return "\n".join(lines)

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
            
            # Bengaluru Transport FAQs
            if any(k in msg for k in ["metro timing", "metro hours", "metro open", "metro close", "last metro", "first metro"]):
                return (
                    "Namma Metro operating hours in Bengaluru are generally from **5:00 AM to 11:00 PM** daily.\n"
                    "• First train: 5:00 AM from all terminal stations (Sunday starts at 7:00 AM).\n"
                    "• Last train: 11:00 PM from terminal stations.\n"
                    "• Frequency: Ranges from 4 to 10 minutes depending on peak/non-peak hours."
                )
            elif any(k in msg for k in ["metro card", "smart card", "metro discount", "namma card"]):
                return (
                    "Using a Namma Metro Smart Card offers several benefits:\n"
                    "• **Discount**: Get a flat **5% discount** on all token fares.\n"
                    "• **Convenience**: Skip the ticket counter queues by tapping at entry/exit gates.\n"
                    "• **Reload**: Cards can be reloaded online via the Namma Metro app or website, or at station counters."
                )
            elif any(k in msg for k in ["bmtc pass", "daily pass", "monthly pass", "bus pass"]):
                return (
                    "BMTC offers convenient daily and monthly travel passes:\n"
                    "• **Ordinary Daily Pass**: ₹70 (valid on all ordinary/non-AC buses).\n"
                    "• **AC Vajra Daily Pass**: ₹140 (valid on both AC Vajra and ordinary buses).\n"
                    "• **Monthly Passes**: Ordinary pass is ₹1050, AC Vajra monthly pass is ₹2300 (+ ID card fee).\n"
                    "Passes can be purchased directly from the bus conductor or at major bus stations."
                )
            elif any(k in msg for k in ["airport", "kia", "kempegowda", "vayu vajra", "airport bus"]):
                return (
                    "BMTC operates Vayu Vajra (AC Volvo) bus services to Kempegowda International Airport (KIA) from major hubs across Bengaluru 24/7:\n"
                    "• **Routes**: Key routes include KIA-9 (Majestic), KIA-8 (Electronic City), KIA-5 (Banashankari), and KIA-14 (Whitefield).\n"
                    "• **Fares**: Typically range from ₹150 to ₹350 depending on the distance.\n"
                    "• **Timings**: Buses run round-the-clock. You can buy tickets directly from the conductor."
                )
            
            # General Greetings / conversational fallback
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
                    "6. Finding routes under budget ('cheapest route under ₹50')\n"
                    "7. Budget-based sightseeing ('I have ₹300 and 5 hours, where can I go?')"
                )
            else:
                return (
                    "Hello! I am your Commuter Assistant. I can help you plan your journey, "
                    "find options matching your budget, check rain forecast impact, compare transit vs. driving, "
                    "look up AC Vajra buses, or find nearby stops. "
                    "Try asking: 'How long does it take from Majestic to Silk Board?' or 'Nearest stop to Indiranagar'"
                )

    def _clean_place_name(self, name: Optional[str]) -> Optional[str]:
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
        for stop in sorted(self.all_stops, key=len, reverse=True):
            if re.search(r"\b" + re.escape(stop.lower()) + r"\b", cleaned_lower):
                return stop
                
        if len(cleaned) < 3:
            return None
        return cleaned if cleaned else None

    def parse_source_dest_from_text(self, text: str, matched_stops: List[str]) -> Tuple[Optional[str], Optional[str]]:
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

    def determine_source_dest(self, matched_stops: List[str], text: str) -> Tuple[Optional[str], Optional[str]]:
        return self.parse_source_dest_from_text(text, matched_stops)

