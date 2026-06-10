import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

GOOGLE_MAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
GOOGLE_DIST_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


class DistanceEngine:
    """
    Calculates driving distance (km) and duration (min) between two coordinates.

    Uses: Google Maps Distance Matrix API
    """

    def get_distance(self, source_coords: dict, destination_coords: dict) -> dict:
        """
        Returns driving distance and duration.

        Returns:
            { "distance_km": 17.99, "duration_min": 22 }
        """
        if not GOOGLE_MAPS_KEY:
            raise ValueError("Google Maps API key is missing")

        return self._google(source_coords, destination_coords)

    def _google(self, src: dict, dst: dict) -> dict:
        resp = requests.get(
            GOOGLE_DIST_URL,
            params={
                "origins": f"{src['latitude']},{src['longitude']}",
                "destinations": f"{dst['latitude']},{dst['longitude']}",
                "mode": "driving",
                "units": "metric",
                "key": GOOGLE_MAPS_KEY,
            },
            timeout=8,
        )

        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            raise ValueError(f"Google Maps error: {data.get('status')}")

        elem = data["rows"][0]["elements"][0]

        if elem["status"] != "OK":
            raise ValueError(f"Route not found: {elem['status']}")

        return {
            "distance_km": round(elem["distance"]["value"] / 1000, 2),
            "duration_min": round(elem["duration"]["value"] / 60, 2),
        }