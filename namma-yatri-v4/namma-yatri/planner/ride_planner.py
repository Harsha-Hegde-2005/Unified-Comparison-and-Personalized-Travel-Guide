from engines.geocoding_engine import GeocodingEngine
from engines.distance_engine  import DistanceEngine
from engines.fare_engine      import FareEngine
from engines.time_engine      import TimeEngine


class RidePlanner:
    """
    Orchestrates all Namma Yatri engines into one unified ride result.

    Two entry points:
      plan_ride()             — text-based (geocodes internally)
      plan_ride_from_coords() — coords-based (map/autocomplete picks)
    """

    def __init__(self):
        self.geocoding_engine = GeocodingEngine()
        self.distance_engine  = DistanceEngine()
        self.fare_engine      = FareEngine()
        self.time_engine      = TimeEngine()

    def plan_ride(self, source: str, destination: str,
                  vehicle_type: str = None) -> dict:
        """Plan ride from place name strings — geocodes first."""
        src_coords = self.geocoding_engine.geocode(source)
        dst_coords = self.geocoding_engine.geocode(destination)
        return self.plan_ride_from_coords(src_coords, dst_coords, vehicle_type)

    def plan_ride_from_coords(self, src_coords: dict, dst_coords: dict,
                               vehicle_type: str = None) -> dict:
        """
        Plan ride from pre-resolved coordinates.
        Used by /plan-ride-coords API and map-based frontend.

        Args:
            src_coords:   { place, latitude, longitude }
            dst_coords:   { place, latitude, longitude }
            vehicle_type: Optional — if None returns all vehicle fares

        Returns full ride plan with route geometry included.
        """
        # ── 1. DISTANCE + ROUTE GEOMETRY (OSRM) ──────────────────────────────
        distance = self.distance_engine.get_distance(src_coords, dst_coords)

        # ── 2. FARE ───────────────────────────────────────────────────────────
        if vehicle_type:
            fare_result = self.fare_engine.get_fare(distance["distance_km"], vehicle_type)
        else:
            fare_result = self.fare_engine.get_all_fares(distance["distance_km"])

        # ── 3. TIME ───────────────────────────────────────────────────────────
        time_estimate = self.time_engine.estimate_duration(
            distance["duration_min"],
            distance["distance_km"]
        )

        # ── 4. ASSEMBLE ───────────────────────────────────────────────────────
        result = {
            "source":         src_coords,
            "destination":    dst_coords,
            "distance":       distance,
            "estimated_time": time_estimate,
        }
        if vehicle_type:
            result["fare"]  = fare_result
        else:
            result["fares"] = fare_result

        return result
