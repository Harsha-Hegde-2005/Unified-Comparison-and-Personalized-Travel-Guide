"""Adapter for BMTC journey planner to unified interface."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modes", "bmtc")))

from shared.interfaces.journey_plan import BaseJourneyPlanner, JourneyResult
from shared.utils.time import format_time


class BMTCAdapter(BaseJourneyPlanner):
    """Wraps BMTC planner to unified JourneyPlanner interface."""

    def __init__(self):
        try:
            from core.loader import ALL_STOPS
            from features.journey import plan_journey_ui

            self.all_stops = ALL_STOPS
            self.plan_journey_fn = plan_journey_ui
        except ImportError as e:
            raise ImportError(f"Failed to import BMTC modules: {e}")

    def get_all_stops(self) -> list[str]:
        """Return all BMTC stops."""
        return sorted(self.all_stops)

    def plan(self, source: str, destination: str) -> JourneyResult:
        """Plan a BMTC journey and return unified result."""
        try:
            bmtc_result = self.plan_journey_fn(source, destination)
        except Exception as e:
            raise ValueError(f"BMTC route planning failed: {str(e)}")

        # Convert BMTC output to unified legs format
        legs = self._convert_segments_to_legs(bmtc_result)

        return JourneyResult(
            mode="BMTC",
            source=source,
            destination=destination,
            total_fare=int(bmtc_result["fare"]),
            total_time=int(bmtc_result["total_time"]),
            transfers=int(bmtc_result["transfers"]),
            legs=legs,
            raw_output=bmtc_result,
        )

    def _convert_segments_to_legs(self, bmtc_result: dict) -> list[dict]:
        """Convert BMTC segments to unified leg format.

        BMTC segments: list of (route, start_stop, end_stop, intermediate_stops)
        """
        legs = []
        segment_times = bmtc_result.get("segment_times", [])

        for i, segment in enumerate(bmtc_result.get("segments", [])):
            route_no = segment[0]
            start_stop = segment[1]
            end_stop = segment[2]

            # Get timing and fare for this segment
            seg_time = segment_times[i] if i < len(segment_times) else {}
            duration = seg_time.get("duration", 0)
            fare = seg_time.get("fare", 0)

            leg = {
                "mode": "BMTC",
                "route": str(route_no),
                "from": start_stop,
                "to": end_stop,
                "fare": int(fare),
                "time": int(duration),
                "instructions": f"Take bus {route_no} from {start_stop} to {end_stop}",
            }
            legs.append(leg)

        return legs
