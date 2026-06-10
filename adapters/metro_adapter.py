"""Adapter for BMRCL Metro journey planner to unified interface."""

import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "bmrcl_final", "bmrcl-journey-planner"
        )
    ),
)

from shared.interfaces.journey_plan import BaseJourneyPlanner, JourneyResult
from shared.utils.time import format_time


class MetroAdapter(BaseJourneyPlanner):
    """Wraps Metro (BMRCL) planner to unified JourneyPlanner interface."""

    def __init__(self):
        try:
            from planner.journey_planner import JourneyPlanner
            from engines.routing_engine import RoutingEngine

            self.planner = JourneyPlanner()
            routing_engine = RoutingEngine()

            # Collect all metro stations
            all_stations = set()
            for line, stations in routing_engine.lines.items():
                all_stations.update(stations)

            self.all_stations = sorted(list(all_stations))
        except ImportError as e:
            raise ImportError(f"Failed to import Metro modules: {e}")

    def get_all_stops(self) -> list[str]:
        """Return all metro stations."""
        return self.all_stations

    def plan(self, source: str, destination: str) -> JourneyResult:
        """Plan a metro journey and return unified result."""
        try:
            metro_result = self.planner.plan_journey(source, destination)
        except Exception as e:
            raise ValueError(f"Metro route planning failed: {str(e)}")

        # Convert metro output to unified legs format
        legs = self._convert_metro_legs_to_unified(metro_result)

        # Metro returns fare as dict {token, smart_card}
        fare = metro_result["fare"]
        if isinstance(fare, dict):
            total_fare = fare
        else:
            total_fare = {"token": fare, "smart_card": fare}

        # Calculate transfers (number of line changes)
        transfers = len(metro_result["route"]["interchanges"])

        return JourneyResult(
            mode="Metro",
            source=source,
            destination=destination,
            total_fare=total_fare,
            total_time=int(metro_result["estimated_time"]["minutes"]),
            transfers=transfers,
            legs=legs,
            raw_output=metro_result,
        )

    def _convert_metro_legs_to_unified(self, metro_result: dict) -> list[dict]:
        """Convert metro legs to unified leg format.

        Metro legs: {from, to, line, stations_crossed, direction}
        """
        legs = []

        for leg in metro_result["route"]["legs"]:
            leg_dict = {
                "mode": "Metro",
                "route": leg["line"],  # Line name: Green, Purple, Yellow
                "from": leg["from"],
                "to": leg["to"],
                "fare": None,  # Will be calculated separately per leg if needed
                "time": None,  # Will be calculated by time engine
                "instructions": f"Take {leg['line']} Line from {leg['from']} towards {leg['direction']}",
                "stations_crossed": leg.get("stations_crossed", 0),
            }
            legs.append(leg_dict)

        return legs
