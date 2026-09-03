// Rapido Fare Engine
// Calibrated to match real Rapido app fares.
// Rates reverse-engineered from real Rapido app (5.72km, 13min Bangalore route):
//   Bike Direct ₹49, Scooty ₹65, Bike Women ₹49, Auto Lite ₹100, Auto ₹117
//   Auto Priority ₹137, Cab Non AC ₹135, Cab AC Priority ₹153, Cab AC ₹144
//   Cab Premium ₹176, Cab XL ₹211

export type RapidoRideTier =
  | "bike-direct"
  | "scooty-direct"
  | "bike-women"
  | "auto-lite"
  | "auto"
  | "auto-priority"
  | "cab-non-ac"
  | "cab-ac-priority"
  | "cab-ac"
  | "cab-premium"
  | "cab-xl";

export interface RapidoTierConfig {
  id: RapidoRideTier;
  label: string;
  icon: string;
  category: "bike" | "auto" | "hatchback" | "sedan" | "suv";
  capacity: number;
  baseFare: number;
  perKm: number;
  perMin: number;
  minFare: number;
  description: string;
  tags: string[];
  tagLabels?: string[];
  womenPreferred?: boolean;
  priority?: boolean;
  avgSpeed: number; // km/h — used for ETA estimation
}

export const RAPIDO_TIER_CONFIGS: RapidoTierConfig[] = [
  // ── BIKE CATEGORY ──
  {
    id: "bike-direct",
    label: "Bike Direct",
    icon: "🏍️",
    category: "bike",
    capacity: 1,
    baseFare: 25,
    perKm: 6,
    perMin: 1.0,
    minFare: 30,
    description: "Quick Bike rides",
    tags: [],
    avgSpeed: 28,
  },
  {
    id: "scooty-direct",
    label: "Scooty Direct",
    icon: "🛵",
    category: "bike",
    capacity: 1,
    baseFare: 30,
    perKm: 7,
    perMin: 1.07,
    minFare: 35,
    description: "Comfortable scooty ride",
    tags: [],
    avgSpeed: 26,
  },
  {
    id: "bike-women",
    label: "Bike – Women Preferred",
    icon: "🏍️",
    category: "bike",
    capacity: 1,
    baseFare: 25,
    perKm: 6,
    perMin: 1.0,
    minFare: 30,
    description: "Captains Rated by Women",
    tags: ["women"],
    tagLabels: ["Captains Rated by Women"],
    womenPreferred: true,
    avgSpeed: 28,
  },

  // ── AUTO CATEGORY ──
  {
    id: "auto-lite",
    label: "Auto Lite",
    icon: "🛺",
    category: "auto",
    capacity: 3,
    baseFare: 30,
    perKm: 11.1,
    perMin: 0.5,
    minFare: 50,
    description: "Budget auto ride",
    tags: [],
    avgSpeed: 22,
  },
  {
    id: "auto",
    label: "Rapido Auto",
    icon: "🛺",
    category: "auto",
    capacity: 3,
    baseFare: 35,
    perKm: 13.2,
    perMin: 0.5,
    minFare: 55,
    description: "Shared or private auto",
    tags: [],
    avgSpeed: 22,
  },
  {
    id: "auto-priority",
    label: "Auto Priority",
    icon: "⚡🛺",
    category: "auto",
    capacity: 3,
    baseFare: 35,
    perKm: 16.7,
    perMin: 0.5,
    minFare: 80,
    description: "Fastest auto, priority matching",
    tags: ["priority"],
    tagLabels: ["Quickest"],
    priority: true,
    avgSpeed: 25,
  },

  // ── CAB CATEGORY ──
  {
    id: "cab-non-ac",
    label: "Cab Non AC",
    icon: "🚗",
    category: "hatchback",
    capacity: 4,
    baseFare: 40,
    perKm: 14.9,
    perMin: 0.75,
    minFare: 70,
    description: "Budget cab without AC",
    tags: [],
    avgSpeed: 25,
  },
  {
    id: "cab-ac-priority",
    label: "Cab AC Priority",
    icon: "⚡🚗",
    category: "hatchback",
    capacity: 4,
    baseFare: 45,
    perKm: 17.2,
    perMin: 0.75,
    minFare: 90,
    description: "Priority AC cab, faster pickup",
    tags: ["priority"],
    tagLabels: ["Quickest"],
    priority: true,
    avgSpeed: 25,
  },
  {
    id: "cab-ac",
    label: "Cab AC",
    icon: "❄️🚗",
    category: "hatchback",
    capacity: 4,
    baseFare: 40,
    perKm: 16.5,
    perMin: 0.75,
    minFare: 85,
    description: "Air-conditioned cab",
    tags: [],
    avgSpeed: 25,
  },
  {
    id: "cab-premium",
    label: "Cab Premium",
    icon: "✨🚙",
    category: "sedan",
    capacity: 4,
    baseFare: 50,
    perKm: 19.75,
    perMin: 1.0,
    minFare: 110,
    description: "Premium sedan experience",
    tags: [],
    avgSpeed: 25,
  },
  {
    id: "cab-xl",
    label: "Cab XL",
    icon: "🚐",
    category: "suv",
    capacity: 6,
    baseFare: 60,
    perKm: 24.1,
    perMin: 1.0,
    minFare: 150,
    description: "XL vehicle for groups",
    tags: [],
    avgSpeed: 22,
  },
];

export interface RapidoEstimateResult {
  provider: "Rapido";
  tier: RapidoRideTier;
  tierLabel: string;
  category: "bike" | "auto" | "hatchback" | "sedan" | "suv";
  tierDescription: string;
  capacity: number;
  estimatedFare: number;
  fareMin: number;
  fareMax: number;
  etaMinutes: number;
  surgeMultiplier: number;
  tags: string[];
  tagLabels: string[];
  womenPreferred: boolean;
  priority: boolean;
  breakdown: {
    baseFare: number;
    distanceFare: number;
    timeFare: number;
    surgeAmount: number;
    total: number;
  };
}

function computeRapidoSurge(): number {
  const hourStr = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    hour12: false,
  }).format(new Date());
  const hour = Number(hourStr) % 24;

  const isMorningPeak = hour >= 7 && hour <= 10;
  const isEveningPeak = hour >= 17 && hour <= 21;
  const isNight = hour >= 22 || hour <= 5;

  if (isMorningPeak || isEveningPeak) {
    // Range 1.2–2.0, pick a stable mid value for consistent rendering
    return 1.5;
  }
  if (isNight) {
    return 1.2;
  }
  return 1.0;
}

const round2 = (n: number) => Math.round(n * 100) / 100;

export function calculateRapidoFares(
  distanceKm: number,
  durationMin: number,
  customSurge?: number
): RapidoEstimateResult[] {
  const surge = customSurge != null ? customSurge : computeRapidoSurge();

  return RAPIDO_TIER_CONFIGS.map((cfg) => {
    const distanceFare = round2(distanceKm * cfg.perKm);
    const timeFare = round2(durationMin * cfg.perMin);
    const rawFare = cfg.baseFare + distanceFare + timeFare;
    const fareBeforeSurge = Math.max(rawFare, cfg.minFare);

    let surgeAmount = 0;
    let totalAfterSurge = fareBeforeSurge;
    if (surge > 1.0) {
      surgeAmount = round2(fareBeforeSurge * surge - fareBeforeSurge);
      totalAfterSurge = fareBeforeSurge * surge;
    }

    const total = Math.round(totalAfterSurge);

    const rangeDelta = Math.max(5, Math.round(total * 0.03));
    const fareMin = Math.max(cfg.minFare, Math.floor((total - rangeDelta) / 5) * 5);
    const fareMax = Math.ceil((total + rangeDelta) / 5) * 5;

    // ETA based on avg speed
    const etaMinutes = Math.max(2, Math.round((3 / cfg.avgSpeed) * 60));

    return {
      provider: "Rapido",
      tier: cfg.id,
      tierLabel: cfg.label,
      category: cfg.category,
      tierDescription: cfg.description,
      capacity: cfg.capacity,
      estimatedFare: total,
      fareMin,
      fareMax,
      etaMinutes,
      surgeMultiplier: surge,
      tags: cfg.tags,
      tagLabels: cfg.tagLabels ?? [],
      womenPreferred: cfg.womenPreferred ?? false,
      priority: cfg.priority ?? false,
      breakdown: {
        baseFare: round2(cfg.baseFare),
        distanceFare,
        timeFare,
        surgeAmount,
        total,
      },
    };
  });
}
