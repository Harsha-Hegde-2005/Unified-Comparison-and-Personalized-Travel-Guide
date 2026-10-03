import os
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "NammaYatri-FareCalculator/1.0"}


class GeocodingEngine:
    """
    Converts a human-readable place name into (latitude, longitude)
    using OpenStreetMap Nominatim API - free, no API key required.

    Handles both short names ("Koramangala") and long full addresses
    ("PES PU College, 50 Feet Road, Banashankari, Bengaluru") using
    a multi-strategy fallback approach.
    """

    def __init__(self):
        self.url = NOMINATIM_URL
        self.headers = HEADERS

    def geocode(self, place: str) -> dict:
        """
        Geocode a place name and return coordinates.
        Tries multiple query strategies automatically - so users can pass
        short names, landmarks, or full addresses and it will just work.

        Args:
            place: Location string e.g. "Koramangala" or a full address

        Returns:
            {
                "place":     "Koramangala",
                "display":   "Koramangala, Bengaluru South, ...",
                "latitude":  12.9352,
                "longitude": 77.6245
            }

        Raises:
            ValueError: if the place cannot be found after all attempts
        """
        from dotenv import load_dotenv
        load_dotenv(override=True)
        gmaps_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        if gmaps_key:
            try:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {"address": place, "key": gmaps_key}
                r = requests.get(url, params=params, timeout=5)
                r.raise_for_status()
                data = r.json()
                if data.get("status") == "OK" and data.get("results"):
                    result = data["results"][0]
                    return {
                        "place":     place,
                        "display":   result["formatted_address"],
                        "latitude":  float(result["geometry"]["location"]["lat"]),
                        "longitude": float(result["geometry"]["location"]["lng"])
                    }
                else:
                    print(f"Google Geocoding failed with status {data.get('status')}. Falling back to Nominatim.")
            except Exception as e:
                print(f"Google Geocoding error: {e}. Falling back to Nominatim.")

        queries = self._build_queries(place)

        for query in queries:
            results = self._fetch(query)
            if results:
                result = results[0]
                return {
                    "place":     place,
                    "display":   result["display_name"],
                    "latitude":  float(result["lat"]),
                    "longitude": float(result["lon"])
                }

        raise ValueError(
            f"Location not found: '{place}'. "
            "Try a shorter name e.g. 'Banashankari' or 'Dasarhalli'."
        )

    def _fetch(self, query: str) -> list:
        """Make a single Nominatim request and return results list."""
        response = requests.get(
            self.url,
            params={"q": query, "format": "json", "limit": 1},
            headers=self.headers,
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    def _build_queries(self, place: str) -> list:
        """
        Build a prioritised list of queries to try in order.

        Strategy:
          1. Use as-is (if address already contains Bengaluru/Bangalore)
          2. Append 'Bengaluru, India' context for short/no-city names
          3. For long comma-separated addresses - try first 2 parts only
          4. Try just the very first part (landmark / building name)

        This ensures both "Koramangala" and full pasted addresses work.
        """
        place = place.strip()
        lowered = place.lower()
        has_city = "bengaluru" in lowered or "bangalore" in lowered

        queries = []

        # 1. Try exactly as provided if city is already mentioned
        if has_city:
            queries.append(place)

        # 2. Append city context if not already present
        if not has_city:
            queries.append(f"{place}, Bengaluru, India")

        # 3 & 4. If it looks like a long address (multiple commas), simplify it
        parts = [p.strip() for p in place.split(",") if p.strip()]
        if len(parts) > 2:
            # Try first 2 meaningful parts e.g. "PES PU College, Banashankari"
            short = ", ".join(parts[:2])
            queries.append(f"{short}, Bengaluru, India")

            # Try just the first part e.g. "PES PU College"
            queries.append(f"{parts[0]}, Bengaluru, India")

        return queries


# Quick test
if __name__ == "__main__":
    engine = GeocodingEngine()

    tests = [
        "Koramangala",
        "Devegowda Petrol Bunk",
        "PES PU College 50 Feet Main Road, 1st Block, Dasarhalli, Srinagar, Banashankari, Bengaluru, Karnataka, India",
    ]

    for t in tests:
        try:
            result = engine.geocode(t)
            print(f"OK   -> lat: {result['latitude']}, lon: {result['longitude']}")
            print(f"      display: {result['display'][:80]}")
        except ValueError as e:
            print(f"ERR  -> {e}")
        print()
