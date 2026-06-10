from engines.routing_engine import RoutingEngine
from engines.distance_engine import DistanceEngine
from engines.fare_engine import FareEngine
from engines.time_engine import TimeEngine


class JourneyPlanner:
    def __init__(self):
        self.routing_engine = RoutingEngine()
        self.distance_engine = DistanceEngine(
            self.routing_engine.stations,
            self.routing_engine.lines
        )
        self.fare_engine = FareEngine()
        self.time_engine = TimeEngine()

    def plan_journey(self, source, destination):
        # -------- VALIDATION --------
        if source not in self.routing_engine.stations:
            raise ValueError(f"Invalid source station: {source}")

        if destination not in self.routing_engine.stations:
            raise ValueError(f"Invalid destination station: {destination}")

        # -------- 1. ROUTE (BFS, multi-interchange) --------
        route = self.routing_engine.get_route(source, destination)

        # -------- 2. DISTANCE & DIRECTION --------
        enriched_route = self.distance_engine.enrich_route(route)

        # -------- 3. TOTAL STATIONS CROSSED --------
        total_stations = sum(
            leg["stations_crossed"] for leg in enriched_route["legs"]
        )

        # -------- 4. FARE (SLAB-BASED) --------
        fare = self.fare_engine.get_fare(total_stations)

        # -------- 5. TIME ESTIMATION --------
        time_estimate = self.time_engine.calculate_total_time(enriched_route)

        # -------- 6. USER INSTRUCTIONS --------
        instructions = self._build_instructions(enriched_route)

        return {
            "source": source,
            "destination": destination,
            "stations_crossed": total_stations,
            "fare": fare,
            "estimated_time": time_estimate,
            "route": enriched_route,
            "instructions": instructions
        }

    def _build_instructions(self, route):
        instructions = []

        for i, leg in enumerate(route["legs"]):
            instructions.append(
                f"Board the {leg['line']} Line at {leg['from']} "
                f"towards {leg['direction']}"
            )

            instructions.append(
                f"Get down at {leg['to']}"
            )

            if i < len(route["legs"]) - 1:
                instructions.append("Change lines")

        return instructions


# =========================
# TEST
# =========================
if __name__ == "__main__":
    planner = JourneyPlanner()

    try:
        journey = planner.plan_journey("Hosa Road", "Majestic")
        from pprint import pprint
        pprint(journey)

    except ValueError as e:
        print("Error:", e)
