import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

GOOGLE_MAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
GOOGLE_DIST_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


class DistanceEngine:
    """
    Calculates driving distance (km) and duration (min) between two coordinates.
    Gracefully falls back from Google Maps to public OSRM, and then to Haversine.
    """

    google_maps_disabled = False

    def __init__(self):
        # Instance-level cache so it resets cleanly on every server reload
        self._cache = {}


    def get_distance(self, source_coords: dict, destination_coords: dict, departure_time = None) -> dict:
        """
        Returns driving distance and duration.

        Returns:
            { "distance_km": 17.99, "duration_min": 22 }
        """
        # Round coordinates to 5 decimals to avoid float mismatch in cache keys
        time_key = departure_time.hour if departure_time else -1
        cache_key = (
            round(source_coords["latitude"], 5),
            round(source_coords["longitude"], 5),
            round(destination_coords["latitude"], 5),
            round(destination_coords["longitude"], 5),
            time_key
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._get_distance_raw(source_coords, destination_coords, departure_time)
        self._cache[cache_key] = result
        return result

    def _get_distance_raw(self, source_coords: dict, destination_coords: dict, departure_time = None) -> dict:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        if key:
            try:
                return self._google(source_coords, destination_coords, key, departure_time)
            except Exception as e:
                print(f"Google Maps API failed: {e}. Falling back to OSRM.")

        try:
            return self._osrm(source_coords, destination_coords)
        except Exception as e:
            print(f"OSRM API failed: {e}. Falling back to Haversine × 1.3 road factor.")
            return self._haversine(source_coords, destination_coords)

    def _google(self, src: dict, dst: dict, key: str, departure_time = None) -> dict:
        params = {
            "origins": f"{src['latitude']},{src['longitude']}",
            "destinations": f"{dst['latitude']},{dst['longitude']}",
            "mode": "driving",
            "units": "metric",
            "key": key,
        }
        if departure_time:
            epoch = int(departure_time.timestamp())
            now_epoch = int(datetime.now().timestamp())
            params["departure_time"] = max(now_epoch, epoch)
            params["traffic_model"] = "best_guess"

        resp = requests.get(
            GOOGLE_DIST_URL,
            params=params,
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            raise ValueError(f"Google Maps error: {data.get('status')}")

        elem = data["rows"][0]["elements"][0]
        if elem["status"] != "OK":
            raise ValueError(f"Route not found: {elem['status']}")

        free_flow_sec = elem["duration"]["value"]
        duration_sec = elem.get("duration_in_traffic", elem["duration"])["value"]

        return {
            "distance_km": round(elem["distance"]["value"] / 1000, 2),
            "duration_min": round(duration_sec / 60, 2),
            "free_flow_duration_min": round(free_flow_sec / 60, 2)
        }

    def _osrm(self, src: dict, dst: dict) -> dict:
        url = f"https://router.project-osrm.org/route/v1/driving/{src['longitude']},{src['latitude']};{dst['longitude']},{dst['latitude']}"
        params = {"overview": "false"}
        resp = requests.get(
            url,
            params=params,
            headers={"User-Agent": "NammaYatri-FareCalculator/1.0"},
            timeout=8
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "Ok":
            raise ValueError(f"OSRM routing error: {data.get('message', 'Route not found')}")

        route = data["routes"][0]
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 2),
        }

    def _haversine(self, src: dict, dst: dict) -> dict:
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = src["latitude"], src["longitude"]
        lat2, lon2 = dst["latitude"], dst["longitude"]
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        dist_km = 2 * R * atan2(sqrt(a), sqrt(1 - a)) * 1.3  # 1.3 road factor correction

        # Zero-traffic driving speed approximation: 30 km/h
        duration_min = dist_km / 30 * 60
        return {
            "distance_km": round(dist_km, 2),
            "duration_min": round(duration_min, 2),
        }