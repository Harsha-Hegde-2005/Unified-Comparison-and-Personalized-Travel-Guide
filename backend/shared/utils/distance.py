import math
from typing import List, Tuple, Dict, Any


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters using Haversine formula."""
    R = 6371000  # Earth radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def find_nearby_stops(
    reference_coords: Tuple[float, float],
    stops_with_coords: List[Dict[str, Any]],
    radius_m: int = 500,
) -> List[Dict[str, Any]]:
    """Find stops within a radius of reference coordinates.

    Args:
        reference_coords: (latitude, longitude) tuple
        stops_with_coords: List of dicts with 'name', 'latitude', 'longitude'
        radius_m: Search radius in meters (default 500m walking distance)

    Returns:
        List of stops within radius, sorted by distance
    """
    ref_lat, ref_lon = reference_coords
    nearby = []

    for stop in stops_with_coords:
        dist = haversine_distance(ref_lat, ref_lon, stop["latitude"], stop["longitude"])
        if dist <= radius_m:
            nearby.append({**stop, "distance_m": dist})

    # Sort by distance (closest first)
    nearby.sort(key=lambda x: x["distance_m"])
    return nearby
