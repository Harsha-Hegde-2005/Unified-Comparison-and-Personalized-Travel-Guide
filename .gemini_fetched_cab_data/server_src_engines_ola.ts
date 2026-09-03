export type OlaRideTier =
  | "auto"
  | "bike"
  | "mini-non-ac"
  | "mini"
  | "priority"
  | "prime-sedan"
  | "prime-plus"
  | "prime-suv";

export interface OlaTierConfig {
  id: OlaRideTier;
  name: string;
  description: string;
  capacity: number;
  category: "bike" | "auto" | "hatchback" | "sedan" | "suv";
  iconEmoji: string;
  baseFare: number;
  regularPerKmRate: number;
  longTripPerKmRate: number; // for distance > 18km
  minDistanceKm: number;
  minimumFare: number;
  cancellationFee: number;
  etaBaseMinutes: number;
}

export const OLA_TIER_CONFIGS: OlaTierConfig[] = [
  {
    id: "auto",
    name: "Ola Auto",
    description: "Quickest auto ride in town",
    capacity: 3,
    category: "auto",
    iconEmoji: "🛺",
    baseFare: 36,
    regularPerKmRate: 16.0,
    longTripPerKmRate: 13.5,
    minDistanceKm: 2,
    minimumFare: 45,
    cancellationFee: 30,
    etaBaseMinutes: 2,
  },
  {
    id: "bike",
    name: "Ola Bike",
    description: "Beat the traffic on a bike",
    capacity: 1,
    category: "bike",
    iconEmoji: "🏍️",
    baseFare: 20,
    regularPerKmRate: 9.0,
    longTripPerKmRate: 7.6,
    minDistanceKm: 0,
    minimumFare: 30,
    cancellationFee: 20,
    etaBaseMinutes: 2,
  },
  {
    id: "mini-non-ac",
    name: "Mini Non AC",
    description: "Everyday affordable rides",
    capacity: 4,
    category: "hatchback",
    iconEmoji: "🚘",
    baseFare: 35,
    regularPerKmRate: 16.8,
    longTripPerKmRate: 13.5,
    minDistanceKm: 0,
    minimumFare: 75,
    cancellationFee: 40,
    etaBaseMinutes: 3,
  },
  {
    id: "mini",
    name: "Ola Mini",
    description: "Comfy, economical AC cars",
    capacity: 4,
    category: "hatchback",
    iconEmoji: "🚗",
    baseFare: 35,
    regularPerKmRate: 16.8,
    longTripPerKmRate: 13.5,
    minDistanceKm: 0,
    minimumFare: 80,
    cancellationFee: 50,
    etaBaseMinutes: 3,
  },
  {
    id: "priority",
    name: "Ola Priority",
    description: "Priority Pickup with top drivers",
    capacity: 4,
    category: "hatchback",
    iconEmoji: "⚡",
    baseFare: 40,
    regularPerKmRate: 16.8,
    longTripPerKmRate: 13.5,
    minDistanceKm: 0,
    minimumFare: 80,
    cancellationFee: 50,
    etaBaseMinutes: 1,
  },
  {
    id: "prime-sedan",
    name: "Prime Sedan",
    description: "Top sedans with high-rated drivers",
    capacity: 4,
    category: "sedan",
    iconEmoji: "🚕",
    baseFare: 40,
    regularPerKmRate: 17.0,
    longTripPerKmRate: 13.8,
    minDistanceKm: 0,
    minimumFare: 100,
    cancellationFee: 60,
    etaBaseMinutes: 4,
  },
  {
    id: "prime-plus",
    name: "Prime Plus",
    description: "Top-rated drivers in premium sedan comfort",
    capacity: 4,
    category: "sedan",
    iconEmoji: "✨",
    baseFare: 45,
    regularPerKmRate: 17.3,
    longTripPerKmRate: 14.1,
    minDistanceKm: 0,
    minimumFare: 120,
    cancellationFee: 75,
    etaBaseMinutes: 3,
  },
  {
    id: "prime-suv",
    name: "Prime SUV",
    description: "Spacious SUVs for groups up to 6",
    capacity: 6,
    category: "suv",
    iconEmoji: "🚙",
    baseFare: 65,
    regularPerKmRate: 27.8,
    longTripPerKmRate: 22.0,
    minDistanceKm: 0,
    minimumFare: 180,
    cancellationFee: 100,
    etaBaseMinutes: 4,
  },
];

export interface OlaEstimateResult {
  provider: "Ola";
  tier: OlaRideTier;
  tierLabel: string;
  category: "bike" | "auto" | "hatchback" | "sedan" | "suv";
  tierDescription: string;
  capacity: number;
  estimatedFare: number;
  fareMin: number;
  fareMax: number;
  etaMinutes: number;
  surgeMultiplier: number;
  breakdown: {
    baseFare: number;
    distanceFare: number;
    timeFare: number;
    taxes: number;
    surgeAmount: number;
    total: number;
  };
}

const round2 = (n: number) => Math.round(n * 100) / 100;

export function calculateOlaFares(
  distanceKm: number,
  durationMin: number,
  customSurge?: number
): OlaEstimateResult[] {
  const surge = customSurge != null ? customSurge : 1.0;

  return OLA_TIER_CONFIGS.map((cfg) => {
    let baseFare = cfg.baseFare;
    let distanceFare = 0;

    if (cfg.id === "auto") {
      baseFare = 36;
      const extraKm = Math.max(0, distanceKm - cfg.minDistanceKm);
      const ratePerKm = distanceKm > 18 ? cfg.longTripPerKmRate : cfg.regularPerKmRate;
      distanceFare = round2(extraKm * ratePerKm + 10);
    } else {
      const ratePerKm = distanceKm > 18 ? cfg.longTripPerKmRate : cfg.regularPerKmRate;
      distanceFare = round2(distanceKm * ratePerKm);
    }

    const timeFare = 0;
    const subtotalBeforeSurge = baseFare + distanceFare;
    const subtotal = round2(
      Math.max(subtotalBeforeSurge * surge, cfg.minimumFare)
    );
    const surgeAmount = round2(subtotal - subtotalBeforeSurge);
    const taxes = round2(subtotal * 0.05); // 5% GST
    const total = round2(subtotal + taxes);

    const rangeDelta = Math.max(5, Math.round(total * 0.025));
    const fareMin = Math.max(cfg.minimumFare, Math.floor((total - rangeDelta) / 5) * 5);
    const fareMax = Math.ceil((total + rangeDelta) / 5) * 5;
    const etaMinutes = cfg.etaBaseMinutes + 1;

    return {
      provider: "Ola",
      tier: cfg.id,
      tierLabel: cfg.name,
      category: cfg.category,
      tierDescription: cfg.description,
      capacity: cfg.capacity,
      estimatedFare: round2(total),
      fareMin,
      fareMax,
      etaMinutes,
      surgeMultiplier: surge,
      breakdown: {
        baseFare: round2(baseFare),
        distanceFare: round2(distanceFare),
        timeFare: round2(timeFare),
        taxes: round2(taxes),
        surgeAmount: round2(Math.max(0, surgeAmount)),
        total: round2(total),
      },
    };
  });
}
