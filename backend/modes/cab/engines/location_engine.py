import requests

# Photon — far better coverage than Nominatim for Indian cities.
# Indexes every OSM node: streets, landmarks, areas, shops, hospitals etc.
PHOTON_URL     = "https://photon.komoot.io/api"
NOMINATIM_REV  = "https://nominatim.openstreetmap.org/reverse"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
HEADERS        = {"User-Agent": "NammaYatri-FareCalculator/1.0"}

# Bengaluru city center — used to bias Photon results toward Bengaluru
BLORE_LAT, BLORE_LON = 12.9716, 77.5946


class LocationEngine:
    """
    Handles all map/location operations for Namma Yatri.

    Search engine: Photon (photon.komoot.io) — indexes every OSM node
    including local streets, hospitals, malls, apartments, bus stops etc.
    Much better Bengaluru coverage than Nominatim alone.

    Methods:
      autocomplete()        — live place search as user types
      reverse_geocode()     — GPS coordinates → readable address
      get_route_geometry()  — driving route polyline for map display
    """

    def autocomplete(self, query: str, limit: int = 7) -> list:
        """
        Return place suggestions for a partial query string.
        Biased toward Bengaluru — shows nearest results first.

        Args:
            query: Partial place name e.g. "Kora", "HSR", "Forum Mall"
            limit: Max suggestions (default 7)

        Returns:
            [
              {
                "name":      "Koramangala 5th Block",
                "address":   "Bengaluru South, Karnataka",
                "latitude":  12.9352,
                "longitude": 77.6245
              }, ...
            ]
        """
        q = query.strip()
        if len(q) < 2:
            return []

        params = {
            "q":      q,
            "limit":  limit,
            "lat":    BLORE_LAT,   # bias center toward Bengaluru
            "lon":    BLORE_LON,
            "lang":   "en"
        }
        resp = requests.get(PHOTON_URL, params=params, headers=HEADERS, timeout=5)
        resp.raise_for_status()

        results  = []
        seen     = set()

        for feat in resp.json().get("features", []):
            props = feat.get("properties", {})
            coords = feat["geometry"]["coordinates"]  # [lon, lat]
            lat, lon = coords[1], coords[0]

            # Filter: keep only results within Bengaluru metro area
            if not (12.70 <= lat <= 13.20 and 77.35 <= lon <= 77.85):
                continue

            name = (
                props.get("name") or
                props.get("street") or
                props.get("locality") or
                ""
            ).strip()

            if not name or name in seen:
                continue
            seen.add(name)

            # Build a clean address line
            parts = []
            for key in ("locality", "district", "city", "county", "state"):
                val = props.get(key, "")
                if val and val != name and val not in parts:
                    parts.append(val)
                    if len(parts) == 2:
                        break

            address = ", ".join(parts) if parts else "Bengaluru"

            results.append({
                "name":      name,
                "address":   address,
                "latitude":  round(lat, 6),
                "longitude": round(lon, 6)
            })

        return results[:limit]

    def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """
        Convert GPS coordinates to a human-readable place name.
        Called when user taps 'Use my location'.
        """
        params = {
            "lat":    latitude,
            "lon":    longitude,
            "format": "json",
            "zoom":   17,
            "addressdetails": 1
        }
        resp = requests.get(NOMINATIM_REV, params=params, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        r    = resp.json()
        addr = r.get("address", {})

        name = (
            addr.get("amenity") or
            addr.get("building") or
            addr.get("road") or
            addr.get("suburb") or
            addr.get("neighbourhood") or
            r.get("display_name", "").split(",")[0]
        )

        parts = [
            addr.get("suburb") or addr.get("neighbourhood"),
            addr.get("city_district"),
            addr.get("city") or "Bengaluru"
        ]
        address_line = ", ".join(p for p in parts if p)

        return {
            "name":      name,
            "address":   address_line,
            "latitude":  latitude,
            "longitude": longitude
        }

    def get_route_geometry(self, src_lat: float, src_lon: float,
                           dst_lat: float, dst_lon: float) -> dict:
        """
        Get the driving route polyline from OSRM for map display.

        Returns:
            {
                "distance_km":  15.12,
                "duration_min": 18,
                "geometry":     [[lat, lon], ...]
            }
        """
        url    = f"{OSRM_ROUTE_URL}/{src_lon},{src_lat};{dst_lon},{dst_lat}"
        params = {"overview": "full", "geometries": "geojson"}
        resp   = requests.get(url, params=params, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        data   = resp.json()

        if data.get("code") != "Ok":
            raise ValueError(f"OSRM routing error: {data.get('message', 'Route not found')}")

        route    = data["routes"][0]
        polyline = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]

        return {
            "distance_km":  round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60),
            "geometry":     polyline
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = LocationEngine()
    tests  = ["HSR Layout", "Forum Mall", "Yelahanka", "Hebbal flyover", "KR Puram"]
    print("Photon autocomplete coverage test:\n")
    for q in tests:
        results = engine.autocomplete(q, limit=2)
        if results:
            r = results[0]
            print(f"  '{q}' -> {r['name']} | {r['address']}")
        else:
            print(f"  '{q}' -> NO RESULTS")
