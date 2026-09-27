"""
session_manager.py
==================
Session-scoped conversation memory for the Bengaluru Travel Assistant chatbot.
Maintains structured travel context per session, resolves pronouns and ordinal
references, handles partial origin/destination updates, and isolates sessions.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Tuple


class SessionContext:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.created_at: float = time.time()
        self.last_accessed: float = time.time()
        
        # Core structured travel context fields (Section 5 schema)
        self.origin: Optional[Dict[str, Any]] = None  # {"name": str, "coords": Tuple[float, float], "source": str}
        self.destination: Optional[Dict[str, Any]] = None  # {"name": str, "coords": Tuple[float, float]}
        self.intermediate_stops: List[str] = []
        self.travel_date: Optional[str] = None
        self.departure_time: Optional[str] = None
        self.arrival_deadline: Optional[str] = None
        self.party_size: int = 1
        self.preferred_transport: List[str] = []
        self.preferred_route: Optional[str] = None
        self.optimization: Optional[str] = None  # "cheapest", "fastest", "least_walking", "fewest_transfers"
        self.max_walking_distance: Optional[float] = None
        self.max_transfers: Optional[int] = None
        self.ac_preference: Optional[bool] = None
        self.active_journey_id: Optional[str] = None
        self.last_recommendations: List[Dict[str, Any]] = []
        self.last_referenced_place: Optional[str] = None
        self.last_referenced_route: Optional[Dict[str, Any]] = None
        self.last_referenced_option: Optional[Dict[str, Any]] = None
        
        # Message history (session-scoped)
        self.history: List[Dict[str, Any]] = []

    def touch(self):
        self.last_accessed = time.time()

    def set_origin(self, name: str, coords: Optional[Tuple[float, float]] = None, source_type: str = "user_input"):
        self.origin = {"name": name, "coordinates": coords, "source": source_type}
        self.touch()

    def set_destination(self, name: str, coords: Optional[Tuple[float, float]] = None):
        self.destination = {"name": name, "coordinates": coords}
        self.last_referenced_place = name
        self.touch()

    def set_recommendations(self, recs: List[Dict[str, Any]]):
        self.last_recommendations = recs
        if recs and isinstance(recs[0], dict):
            self.active_journey_id = recs[0].get("journey_id")
            self.last_referenced_option = recs[0]
        self.touch()

    def update_origin(self, name: str, coords: Optional[Tuple[float, float]] = None, source: str = "user_input"):
        self.origin = {"name": name, "coords": coords, "source": source}
        self.last_referenced_place = name
        self.touch()

    def update_destination(self, name: str, coords: Optional[Tuple[float, float]] = None):
        self.destination = {"name": name, "coords": coords}
        self.last_referenced_place = name
        self.touch()

    def set_recommendations(self, journeys: List[Dict[str, Any]]):
        self.last_recommendations = journeys
        if journeys:
            self.active_journey_id = journeys[0].get("journey_id")
            self.last_referenced_option = journeys[0]
            if journeys[0].get("source") and journeys[0].get("destination"):
                self.last_referenced_route = {
                    "source": journeys[0]["source"],
                    "destination": journeys[0]["destination"],
                    "mode": journeys[0].get("mode")
                }
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "origin": self.origin,
            "destination": self.destination,
            "intermediate_stops": self.intermediate_stops,
            "travel_date": self.travel_date,
            "departure_time": self.departure_time,
            "arrival_deadline": self.arrival_deadline,
            "party_size": self.party_size,
            "preferred_transport": self.preferred_transport,
            "preferred_route": self.preferred_route,
            "optimization": self.optimization,
            "max_walking_distance": self.max_walking_distance,
            "max_transfers": self.max_transfers,
            "ac_preference": self.ac_preference,
            "active_journey_id": self.active_journey_id,
            "last_recommendations": self.last_recommendations,
            "last_referenced_place": self.last_referenced_place,
            "last_referenced_route": self.last_referenced_route,
            "last_referenced_option": self.last_referenced_option,
        }


class SessionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SessionManager, cls).__new__(cls)
                cls._instance._sessions = {}
                cls._instance._ttl_seconds = 1800  # 30 minutes TTL
            return cls._instance

    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionContext:
        with self._lock:
            self._cleanup_expired()
            if not session_id:
                session_id = f"session_{int(time.time() * 1000)}"
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionContext(session_id)
            session = self._sessions[session_id]
            session.touch()
            return session

    def resolve_references(self, session: SessionContext, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Scan user message against session state to resolve pronouns ('it', 'there',
        'that place', 'the second one', 'from there') and extra constraints.
        Returns (modified_message, resolved_overrides).
        """
        text = message.lower().strip()
        overrides: Dict[str, Any] = {}

        # 1. Resolve ordinal references: "the second one", "option 2", "2nd choice"
        import re
        ord_match = re.search(r'\b(?:the\s+)?(first|1st|second|2nd|third|3rd|fourth|4th|option\s+[1-4]|choice\s+[1-4])\b', text)
        if ord_match and session.last_recommendations:
            raw_ord = ord_match.group(1).lower()
            idx = 0
            if any(k in raw_ord for k in ["second", "2nd", "2"]):
                idx = 1
            elif any(k in raw_ord for k in ["third", "3rd", "3"]):
                idx = 2
            elif any(k in raw_ord for k in ["fourth", "4th", "4"]):
                idx = 3

            if 0 <= idx < len(session.last_recommendations):
                sel_opt = session.last_recommendations[idx]
                session.active_journey_id = sel_opt.get("journey_id")
                session.last_referenced_option = sel_opt
                overrides["selected_option"] = sel_opt
                if sel_opt.get("mode"):
                    overrides["mode"] = sel_opt.get("mode")

        # 2. Resolve "there", "this place", "that place" -> destination or last_referenced_place
        ref_place = (session.destination.get("name") if session.destination else None) or session.last_referenced_place
        if ref_place:
            for pattern in [
                r'\b(to|reach|get to|go to|near|close to|around|at)\s+(there|that place|this place|the place)\b',
                r'\b(there|that place|this place)\b'
            ]:
                if re.search(pattern, text):
                    overrides["destination"] = ref_place
                    break

        # 3. Resolve "from there" -> previous destination becomes new origin
        if re.search(r'\bfrom\s+(there|that place|the destination)\b', text) and ref_place:
            overrides["source"] = ref_place

        # 4. Resolve "it", "that", "this route", "the route" -> active journey / active route
        if session.origin and session.destination:
            src_name = session.origin["name"]
            dst_name = session.destination["name"]
            if any(k in text for k in ["the route", "this route", "that route", "same journey", "it"]):
                overrides["source"] = src_name
                overrides["destination"] = dst_name

        # 5. Optimization preferences extraction from text
        if any(k in text for k in ["cheapest", "lowest fare", "cheap", "most affordable"]):
            overrides["optimization"] = "cheapest"
            session.optimization = "cheapest"
        elif any(k in text for k in ["fastest", "quickest", "most time saving", "minimum time"]):
            overrides["optimization"] = "fastest"
            session.optimization = "fastest"
        elif any(k in text for k in ["less walking", "least walking", "minimum walk", "avoid walking"]):
            overrides["optimization"] = "least_walking"
            session.optimization = "least_walking"
        elif any(k in text for k in ["fewer transfers", "fewest transfers", "direct bus", "no transfers", "avoid changing"]):
            overrides["optimization"] = "fewest_transfers"
            session.optimization = "fewest_transfers"

        # 6. AC bus preference
        if any(k in text for k in ["ac bus", "vajra", "volvo"]):
            overrides["ac_preference"] = True
            session.ac_preference = True

        # 7. Carry over existing origin and destination if user asked a follow-up query
        if "source" not in overrides and session.origin:
            overrides["recalled_source"] = session.origin["name"]
        if "destination" not in overrides and session.destination:
            overrides["recalled_destination"] = session.destination["name"]

        return message, overrides

    def _cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, sess in self._sessions.items() if now - sess.last_accessed > self._ttl_seconds]
        for sid in expired:
            del self._sessions[sid]
