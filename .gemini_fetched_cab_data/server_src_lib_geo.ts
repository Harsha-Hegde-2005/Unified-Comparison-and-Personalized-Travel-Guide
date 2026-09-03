export interface RouteEstimate {
  distanceKm: number;
  distanceMeters: number;
  durationMin: number;
  durationSeconds: number;
  source: "haversine" | "google_maps";
}

const EARTH_RADIUS_KM = 6371;

function toRad(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Calculates Haversine straight-line distance, then applies a ~1.25x
 * multiplier to approximate urban driving road distance in Bengaluru.
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): RouteEstimate {
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const straightKm = EARTH_RADIUS_KM * c;

  // Road factor (~1.25)
  const roadKm = Math.max(0.5, Math.round(straightKm * 1.25 * 10) / 10);
  const distanceMeters = Math.round(roadKm * 1000);

  // Average city driving speed: ~22 km/h in Bengaluru
  const avgSpeedKmh = roadKm > 25 ? 40 : 22; // Highway speed for airport trips
  const durationMin = Math.max(3, Math.round((roadKm / avgSpeedKmh) * 60));
  const durationSeconds = durationMin * 60;

  return {
    distanceKm: roadKm,
    distanceMeters,
    durationMin,
    durationSeconds,
    source: "haversine",
  };
}
