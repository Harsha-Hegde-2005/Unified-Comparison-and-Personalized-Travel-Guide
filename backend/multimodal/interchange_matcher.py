"""Interchange point matching for BMTC-Metro transfers."""

from typing import List, Dict, Tuple, Optional
from shared.utils.distance import find_nearby_stops, haversine_distance
from multimodal.config import INTERCHANGE_POINTS, WALKING_RADIUS_M


class InterchangeMatcher:
    """Matches BMTC stops to metro stations for multimodal journeys."""

    def __init__(self, bmtc_stops_with_coords: List[Dict]):
        """Initialize with BMTC stops data.

        Args:
            bmtc_stops_with_coords: List of dicts with keys:
                {name, latitude, longitude, ...}
        """
        self.bmtc_stops = bmtc_stops_with_coords

    def find_metro_station_near_stop(
        self, bmtc_stop: str, radius_m: int = WALKING_RADIUS_M
    ) -> Optional[str]:
        """Find nearest metro station within walking distance.

        Args:
            bmtc_stop: BMTC stop name
            radius_m: Search radius in meters

        Returns:
            Nearest metro station name or None if not found
        """
        # Find BMTC stop coords
        bmtc_coords = None
        for stop in self.bmtc_stops:
            if stop["name"].lower() == bmtc_stop.lower():
                bmtc_coords = (stop["latitude"], stop["longitude"])
                break

        if not bmtc_coords:
            return None

        # Find nearest metro station
        min_distance = float("inf")
        nearest_station = None

        for station_name, point in INTERCHANGE_POINTS.items():
            metro_coords = point["coords"]
            distance = haversine_distance(
                bmtc_coords[0],
                bmtc_coords[1],
                metro_coords[0],
                metro_coords[1],
            )

            if distance <= radius_m and distance < min_distance:
                min_distance = distance
                nearest_station = station_name

        return nearest_station

    def find_bmtc_stops_near_metro_station(
        self, metro_station: str, radius_m: int = WALKING_RADIUS_M
    ) -> List[str]:
        """Find BMTC stops within walking distance of metro station.

        Args:
            metro_station: Metro station name
            radius_m: Search radius in meters

        Returns:
            List of nearby BMTC stops (closest first)
        """
        if metro_station not in INTERCHANGE_POINTS:
            return []

        metro_coords = INTERCHANGE_POINTS[metro_station]["coords"]

        # Build list of BMTC stops with distances
        nearby = []
        for stop in self.bmtc_stops:
            distance = haversine_distance(
                metro_coords[0],
                metro_coords[1],
                stop["latitude"],
                stop["longitude"],
            )

            if distance <= radius_m:
                nearby.append({"name": stop["name"], "distance_m": distance})

        # Sort by distance (closest first)
        nearby.sort(key=lambda x: x["distance_m"])
        return [s["name"] for s in nearby]

    def is_interchange_point(self, location: str) -> bool:
        """Check if a location is a known interchange point.

        Args:
            location: Location name (could be metro station or BMTC stop)

        Returns:
            True if it's a known interchange point
        """
        if location in INTERCHANGE_POINTS:
            return True

        # Check if it's mentioned in nearby_bmtc_stops
        for point in INTERCHANGE_POINTS.values():
            if location.lower() in [s.lower() for s in point["nearby_bmtc_stops"]]:
                return True

        return False

    def get_metro_station_coords(self, station: str) -> Optional[Tuple[float, float]]:
        """Get coordinates of a metro station.

        Args:
            station: Metro station name

        Returns:
            (latitude, longitude) tuple or None
        """
        if station in INTERCHANGE_POINTS:
            return INTERCHANGE_POINTS[station]["coords"]
        return None
