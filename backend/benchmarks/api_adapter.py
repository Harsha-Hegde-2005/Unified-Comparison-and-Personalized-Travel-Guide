"""
api_adapter.py
==============
Adapter for the BMTC Journey Planning API endpoint / function.
Executes test cases, measures backend response latency, and captures
returned journey options.
"""

from __future__ import annotations

import time
import sys
import os
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


class JourneyAPIAdapter:
    """Adapter for querying the BMTC journey planner."""

    def __init__(self, mode: str = "direct", base_url: str = "http://127.0.0.1:8000"):
        """
        :param mode: 'direct' to call python function bmtc_plan directly,
                     'http' to send HTTP POST requests to backend server.
        """
        self.mode = mode
        self.base_url = base_url.rstrip('/')
        self._direct_planner = None

        if self.mode == "direct":
            try:
                from main import bmtc_plan, JourneyRequest
                self._bmtc_plan_fn = bmtc_plan
                self._JourneyRequest_cls = JourneyRequest
            except Exception as e:
                # If direct import fails, fallback to HTTP
                print(f"Direct import of main.py bmtc_plan failed ({e}). Defaulting to HTTP adapter.")
                self.mode = "http"

    def execute_test_case(self, test_case: Dict[str, Any], max_options: int = 5) -> Dict[str, Any]:
        """
        Executes a single test case dictionary.
        Returns normalized result dictionary.
        """
        origin = test_case.get("origin")
        destination = test_case.get("destination")
        dep_time = test_case.get("departure_time", "08:30")
        preference = test_case.get("preference", "fastest")

        start_timer = time.perf_counter()
        
        raw_response = None
        error_msg = None
        status_code = 200

        try:
            if self.mode == "direct":
                req_obj = self._JourneyRequest_cls(
                    source=origin,
                    destination=destination,
                    time=dep_time,
                    preference=preference
                )
                raw_response = self._bmtc_plan_fn(req_obj, max_options=max_options)
            else:
                import requests
                payload = {
                    "source": origin,
                    "destination": destination,
                    "time": dep_time,
                    "preference": preference
                }
                resp = requests.post(f"{self.base_url}/api/bmtc/plan", json=payload, timeout=10)
                status_code = resp.status_code
                if resp.status_code == 200:
                    raw_response = resp.json()
                else:
                    error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            error_msg = str(e)
            status_code = 500

        end_timer = time.perf_counter()
        latency_ms = round((end_timer - start_timer) * 1000.0, 2)

        return self._normalize_response(
            test_case=test_case,
            raw_response=raw_response,
            latency_ms=latency_ms,
            status_code=status_code,
            error_msg=error_msg
        )

    def _normalize_response(
        self,
        test_case: Dict[str, Any],
        raw_response: Optional[Dict[str, Any]],
        latency_ms: float,
        status_code: int,
        error_msg: Optional[str]
    ) -> Dict[str, Any]:
        """Convert raw response into standardized dictionary."""
        is_success = (status_code == 200) and (error_msg is None) and (raw_response is not None)
        
        options = []
        if is_success and isinstance(raw_response, dict):
            options = raw_response.get("options") or raw_response.get("buses") or []
            if not options and raw_response.get("available"):
                options = [raw_response]

        normalized_options = []
        for opt in options:
            if not isinstance(opt, dict):
                continue
            
            # Extract routes, legs, stops
            route_name = opt.get("route") or opt.get("route_no") or opt.get("route_number") or "N/A"
            segments = opt.get("segments") or []
            
            routes_list = []
            boarding_stops = []
            alighting_stops = []
            legs = []

            if segments:
                for idx, seg in enumerate(segments):
                    r_num = seg.get("route") or seg.get("route_no") or seg.get("route_number") or "N/A"
                    b_stop = seg.get("board_stop") or seg.get("from_stop") or seg.get("boarding_stop") or "N/A"
                    a_stop = seg.get("alight_stop") or seg.get("to_stop") or seg.get("alighting_stop") or "N/A"
                    
                    routes_list.append(str(r_num))
                    boarding_stops.append(str(b_stop))
                    alighting_stops.append(str(a_stop))

                    leg_type = "bus"
                    r_lower = str(r_num).strip().lower()
                    if r_lower in ("walk", "walking", "foot", "transfer_walk") or seg.get("mode") == "walk":
                        leg_type = "walk"
                    elif r_lower in ("metro", "namma metro", "purple", "green") or seg.get("mode") == "metro":
                        leg_type = "metro"
                    elif seg.get("mode") and seg["mode"] not in ("bmtc", "bus"):
                        leg_type = str(seg["mode"])

                    legs.append({
                        "leg_index": idx,
                        "leg_type": leg_type,
                        "route_id": str(r_num),
                        "boarding_stop": str(b_stop),
                        "alighting_stop": str(a_stop),
                        "fare_inr": float(seg.get("cost") or seg.get("fare") or 0.0),
                        "duration_mins": float(seg.get("time") or seg.get("duration") or 0.0),
                        "distance_km": float(seg.get("distance_km") or seg.get("distance") or 0.0),
                        "raw_segment": seg
                    })
            else:
                b_stop = opt.get("from_stop") or opt.get("boarding_stop") or test_case.get("origin") or "N/A"
                a_stop = opt.get("to_stop") or opt.get("alighting_stop") or test_case.get("destination") or "N/A"
                routes_list.append(str(route_name))
                boarding_stops.append(str(b_stop))
                alighting_stops.append(str(a_stop))

                leg_type = "bus"
                r_lower = str(route_name).strip().lower()
                if r_lower in ("walk", "walking", "foot", "transfer_walk"):
                    leg_type = "walk"
                elif r_lower in ("metro", "namma metro"):
                    leg_type = "metro"

                fare_val = opt.get("cost") if opt.get("cost") is not None else opt.get("fare")
                dur_val = opt.get("time") if opt.get("time") is not None else opt.get("duration")

                legs.append({
                    "leg_index": 0,
                    "leg_type": leg_type,
                    "route_id": str(route_name),
                    "boarding_stop": str(b_stop),
                    "alighting_stop": str(a_stop),
                    "fare_inr": float(fare_val) if fare_val is not None else 0.0,
                    "duration_mins": float(dur_val) if dur_val is not None else 0.0,
                    "distance_km": float(opt.get("distance_km") or opt.get("distance") or 0.0),
                    "raw_segment": opt
                })

            fare = opt.get("cost") if opt.get("cost") is not None else opt.get("fare")
            duration = opt.get("time") if opt.get("time") is not None else opt.get("duration")

            normalized_options.append({
                "mode": opt.get("mode", "bmtc"),
                "routes": routes_list,
                "boarding_stops": boarding_stops,
                "alighting_stops": alighting_stops,
                "legs": legs,
                "transfers": opt.get("transfers", max(0, sum(1 for l in legs if l["leg_type"] == "bus") - 1)),
                "fare_inr": float(fare) if fare is not None else None,
                "duration_mins": float(duration) if duration is not None else None,
                "departure_time": opt.get("departure"),
                "arrival_time": opt.get("arrival"),
                "raw": opt
            })

        top_rec = normalized_options[0] if normalized_options else None

        return {
            "test_id": test_case["test_id"],
            "status_code": status_code,
            "latency_ms": latency_ms,
            "is_success": is_success,
            "error_message": error_msg,
            "options_count": len(normalized_options),
            "has_options": len(normalized_options) > 0,
            "recommended_option": top_rec,
            "all_options": normalized_options,
            "raw_response": raw_response
        }
