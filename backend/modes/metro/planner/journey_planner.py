import json
import os
import math
from engines.routing_engine import RoutingEngine
from engines.distance_engine import DistanceEngine
from engines.fare_engine import FareEngine
from engines.time_engine import TimeEngine


def _haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


class JourneyPlanner:
    def __init__(self):
        self.routing_engine = RoutingEngine()
        self.distance_engine = DistanceEngine(
            self.routing_engine.stations,
            self.routing_engine.lines
        )
        self.fare_engine = FareEngine()
        self.time_engine = TimeEngine()

        # Load station coordinates for km-based fare calculation
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        coords_path = os.path.abspath(
            os.path.join(base_dir, "..", "..", "database", "metro", "metro_coords.json")
        )
        self._station_coords = {}
        if os.path.exists(coords_path):
            with open(coords_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for st, c in data.items():
                    if "lat" in c and "lng" in c:
                        self._station_coords[st] = (float(c["lat"]), float(c["lng"]))

    def _route_distance_km(self, enriched_route):
        """
        Compute total route distance in km by summing Haversine distances
        between consecutive stations in each leg.
        """
        total_km = 0.0
        for leg in enriched_route["legs"]:
            line = leg["line"]
            line_stations = self.routing_engine.lines[line]
            fi = line_stations.index(leg["from"])
            ti = line_stations.index(leg["to"])
            lo, hi = min(fi, ti), max(fi, ti)
            segment = line_stations[lo:hi + 1]
            for i in range(len(segment) - 1):
                s1 = segment[i]
                s2 = segment[i + 1]
                c1 = self._station_coords.get(s1)
                c2 = self._station_coords.get(s2)
                if c1 and c2:
                    total_km += _haversine_km(c1[0], c1[1], c2[0], c2[1])
                else:
                    # fallback: ~1.2 km per station gap
                    total_km += 1.2
        return total_km

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

        # -------- 3. TOTAL STATIONS CROSSED (kept for reference) --------
        total_stations = sum(
            leg["stations_crossed"] for leg in enriched_route["legs"]
        )

        # -------- 4. ROUTE DISTANCE IN KM --------
        route_km = self._route_distance_km(enriched_route)

        # -------- 5. FARE (DISTANCE-BASED, BMRCL 2026) --------
        fare = self.fare_engine.get_fare(route_km)

        # -------- 6. TIME ESTIMATION --------
        time_estimate = self.time_engine.calculate_total_time(enriched_route)

        # -------- 7. USER INSTRUCTIONS --------
        instructions = self._build_instructions(enriched_route)

        return {
            "source": source,
            "destination": destination,
            "stations_crossed": total_stations,
            "route_km": round(route_km, 2),
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
        journey = planner.plan_journey("Cubbon Park", "Konanakunte Cross")
        from pprint import pprint
        pprint(journey)

    except ValueError as e:
        print("Error:", e)
