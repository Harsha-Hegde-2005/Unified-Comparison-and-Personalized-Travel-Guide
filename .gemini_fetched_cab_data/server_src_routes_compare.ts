import { Router, Request, Response } from "express";
import https from "https";
import { searchLocations, BENGALURU_LOCATIONS } from "../lib/locations";
import { calculateDistance } from "../lib/geo";
import { calculateNammaYatriFares, isNightFareIST } from "../engines/nammaYatri";
import { calculateUberFares } from "../engines/uber";
import { calculateOlaFares } from "../engines/ola";
import { calculateRapidoFares } from "../engines/rapido";
import {
  googlePlacesAutocomplete,
  googlePlaceDetails,
  googleDirectionsMatrix,
} from "../lib/googleMaps";

export const compareRouter = Router();

function fetchJson<T>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const req = https.request(
      parsedUrl,
      {
        method: "GET",
        headers: {
          "User-Agent": "RideAggregatorApp/1.0 (Bengaluru)",
        },
      },
      (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      }
    );
    req.on("error", (err) => reject(err));
    req.end();
  });
}

// Global Free Search via Photon OSM engine (fallback when Google Maps key is not supplied)
async function globalFreeSearch(query: string) {
  try {
    const q = encodeURIComponent(`${query.trim()} Bengaluru`);
    const url = `https://photon.komoot.io/api/?q=${q}&limit=6&bbox=77.3,12.7,77.8,13.2`;
    const data: any = await fetchJson(url);

    if (data && Array.isArray(data.features) && data.features.length > 0) {
      return data.features.map((f: any, idx: number) => {
        const props = f.properties || {};
        const coords = f.geometry?.coordinates || [77.5946, 12.9716];
        const name = props.name || props.street || query;
        const area = [props.street, props.district, props.city || "Bengaluru"].filter(Boolean).join(", ");
        return {
          placeId: `free_${props.osm_id || idx}`,
          mainText: name,
          secondaryText: area || "Bengaluru",
          fullText: `${name}, ${area}`,
          lat: coords[1],
          lng: coords[0],
        };
      });
    }
  } catch (err) {
    console.error("Global free search error:", err);
  }
  return [];
}

// GET /api/places/autocomplete — Live search for any street, colony, or landmark
compareRouter.get("/places/autocomplete", async (req: Request, res: Response) => {
  const query = (req.query.query as string) || "";
  const userApiKey = (req.query.apiKey as string) || process.env.GOOGLE_MAPS_API_KEY;

  if (query.trim().length === 0) {
    const formatted = BENGALURU_LOCATIONS.map((loc) => ({
      placeId: loc.id,
      mainText: loc.name,
      secondaryText: loc.area,
      fullText: `${loc.name}, ${loc.area}`,
      lat: loc.lat,
      lng: loc.lng,
    }));
    return res.json({ suggestions: formatted, source: "local" });
  }

  if (userApiKey && userApiKey.trim().length > 5) {
    const googleSuggestions = await googlePlacesAutocomplete(query, userApiKey);
    if (googleSuggestions.length > 0) {
      return res.json({ suggestions: googleSuggestions, source: "google_places" });
    }
  }

  const localMatches = searchLocations(query).map((loc) => ({
    placeId: loc.id,
    mainText: loc.name,
    secondaryText: loc.area,
    fullText: `${loc.name}, ${loc.area}`,
    lat: loc.lat,
    lng: loc.lng,
  }));

  const freeMatches = await globalFreeSearch(query);

  const combined = [...localMatches, ...freeMatches];
  return res.json({ suggestions: combined, source: userApiKey ? "google_places" : "free_search" });
});

// GET /api/places/details — Get coordinates for a place_id
compareRouter.get("/places/details", async (req: Request, res: Response) => {
  const placeId = req.query.placeId as string;
  const userApiKey = (req.query.apiKey as string) || process.env.GOOGLE_MAPS_API_KEY;

  if (userApiKey && userApiKey.trim().length > 5 && !placeId.startsWith("free_") && !BENGALURU_LOCATIONS.some((l) => l.id === placeId)) {
    const details = await googlePlaceDetails(placeId, userApiKey);
    if (details) {
      return res.json({ details, source: "google_places" });
    }
  }

  const match = BENGALURU_LOCATIONS.find((l) => l.id === placeId);
  if (match) {
    return res.json({
      details: {
        placeId: match.id,
        name: match.name,
        formattedAddress: `${match.name}, ${match.area}`,
        lat: match.lat,
        lng: match.lng,
      },
      source: "local",
    });
  }

  res.status(404).json({ error: "Place details not found" });
});

// GET /api/locations — List static landmarks
compareRouter.get("/locations", (req: Request, res: Response) => {
  const query = req.query.query as string | undefined;
  const locations = searchLocations(query);
  res.json({ locations });
});

// GET /api/compare — Compare Namma Yatri vs Uber vs Ola fares
compareRouter.get("/compare", async (req: Request, res: Response) => {
  const pickupLatStr = req.query.pickupLat as string;
  const pickupLngStr = req.query.pickupLng as string;
  const dropLatStr = req.query.dropLat as string;
  const dropLngStr = req.query.dropLng as string;
  const forceNight = req.query.forceNight === "true";
  const customSurgeStr = req.query.surge as string;
  const userApiKey = (req.query.apiKey as string) || process.env.GOOGLE_MAPS_API_KEY;

  let pickupLat = parseFloat(pickupLatStr);
  let pickupLng = parseFloat(pickupLngStr);
  let dropLat = parseFloat(dropLatStr);
  let dropLng = parseFloat(dropLngStr);

  if (isNaN(pickupLat) || isNaN(pickupLng)) {
    pickupLat = BENGALURU_LOCATIONS[0].lat; // PES University
    pickupLng = BENGALURU_LOCATIONS[0].lng;
  }
  if (isNaN(dropLat) || isNaN(dropLng)) {
    dropLat = BENGALURU_LOCATIONS[4].lat; // Koramangala
    dropLng = BENGALURU_LOCATIONS[4].lng;
  }

  let route = calculateDistance(pickupLat, pickupLng, dropLat, dropLng);

  if (userApiKey && userApiKey.trim().length > 5) {
    const googleRoute = await googleDirectionsMatrix(pickupLat, pickupLng, dropLat, dropLng, userApiKey);
    if (googleRoute) {
      route = {
        distanceKm: googleRoute.distanceKm,
        distanceMeters: Math.round(googleRoute.distanceKm * 1000),
        durationMin: googleRoute.durationMin,
        durationSeconds: googleRoute.durationMin * 60,
        source: "google_maps",
      };
    }
  }

  const customSurge = customSurgeStr ? parseFloat(customSurgeStr) : undefined;
  const nammaYatriEstimates = calculateNammaYatriFares(route.distanceKm, route.durationMin, forceNight);
  const uberEstimates = calculateUberFares(route.distanceKm, route.durationMin, customSurge);
  const olaEstimates = calculateOlaFares(route.distanceKm, route.durationMin, customSurge);
  const rapidoEstimates = calculateRapidoFares(route.distanceKm, route.durationMin, customSurge);

  const categories = [
    { id: "auto", name: "Auto Rickshaw", icon: "🛺" },
    { id: "hatchback", name: "Mini / Hatchback", icon: "🚗" },
    { id: "sedan", name: "Sedan / Comfort", icon: "🚘" },
    { id: "suv", name: "SUV / Large Group", icon: "🚙" },
    { id: "bike", name: "Bike / Moto", icon: "🏍️" },
  ] as const;

  const categoryComparisons = categories.map((cat) => {
    const ny = nammaYatriEstimates.filter((item) => item.category === cat.id);
    const uber = uberEstimates.filter((item) => item.category === cat.id);
    const ola = olaEstimates.filter((item) => item.category === cat.id);
    const rapido = rapidoEstimates.filter((item) => item.category === cat.id);

    const allInCat = [...ny, ...uber, ...ola, ...rapido];
    let cheapest = null;
    let savings = 0;
    let savingsWinner: "Namma Yatri" | "Uber" | "Ola" | "Rapido" | "Equal" = "Equal";

    if (allInCat.length > 0) {
      cheapest = allInCat.reduce((prev, curr) =>
        curr.estimatedFare < prev.estimatedFare ? curr : prev
      );

      const minNy = ny.length > 0 ? Math.min(...ny.map((i) => i.estimatedFare)) : null;
      const minUber = uber.length > 0 ? Math.min(...uber.map((i) => i.estimatedFare)) : null;
      const minOla = ola.length > 0 ? Math.min(...ola.map((i) => i.estimatedFare)) : null;
      const minRapido = rapido.length > 0 ? Math.min(...rapido.map((i) => i.estimatedFare)) : null;

      const validMins = [
        { provider: "Namma Yatri" as const, fare: minNy },
        { provider: "Uber" as const, fare: minUber },
        { provider: "Ola" as const, fare: minOla },
        { provider: "Rapido" as const, fare: minRapido },
      ].filter((item): item is { provider: "Namma Yatri" | "Uber" | "Ola" | "Rapido"; fare: number } => item.fare !== null);

      if (validMins.length > 1) {
        validMins.sort((a, b) => a.fare - b.fare);
        savingsWinner = validMins[0].provider;
        savings = Math.round((validMins[1].fare - validMins[0].fare) * 100) / 100;
      }
    }

    return {
      category: cat.id,
      categoryName: cat.name,
      icon: cat.icon,
      nammaYatri: ny,
      uber,
      ola,
      rapido,
      cheapest,
      savingsWinner,
      savings,
    };
  });

  res.json({
    route,
    isNightFare: forceNight || isNightFareIST(),
    nammaYatriEstimates,
    uberEstimates,
    olaEstimates,
    rapidoEstimates,
    categoryComparisons,
  });
});
