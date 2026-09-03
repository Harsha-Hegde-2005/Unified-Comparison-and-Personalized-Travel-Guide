export type UberRideTier =
  | "moto"
  | "auto"
  | "gonoac"
  | "ubergoac"
  | "premierac"
  | "comfort"
  | "black"
  | "uberxl"
  | "blacksuv";

export interface UberTierConfig {
  tier: UberRideTier;
  tierLabel: string;
  category: "bike" | "auto" | "hatchback" | "sedan" | "suv";
  tierDescription: string;
  capacity: number;
  baseFare: number;
  perMinute: number;
  perKm: number;
  minimumFare: number;
  bookingFee: number;
  etaBaseMinutes: number;
}

export const UBER_TIER_CONFIGS: UberTierConfig[] = [
  {
    tier: "moto",
    tierLabel: "Uber Moto",
    category: "bike",
    tierDescription: "Affordable bike rides",
    capacity: 1,
    baseFare: 8,
    perMinute: 0.75,
    perKm: 9,
    minimumFare: 35,
    bookingFee: 5,
    etaBaseMinutes: 2,
  },
  {
    tier: "auto",
    tierLabel: "Uber Auto",
    category: "auto",
    tierDescription: "Pay directly to driver, cash/UPI only",
    capacity: 3,
    baseFare: 8,
    perMinute: 1.0,
    perKm: 13,
    minimumFare: 50,
    bookingFee: 10,
    etaBaseMinutes: 2,
  },
  {
    tier: "gonoac",
    tierLabel: "Go Non AC",
    category: "hatchback",
    tierDescription: "Everyday affordable rides",
    capacity: 4,
    baseFare: 15,
    perMinute: 1.3,
    perKm: 14,
    minimumFare: 65,
    bookingFee: 9,
    etaBaseMinutes: 4,
  },
  {
    tier: "ubergoac",
    tierLabel: "Uber Go AC",
    category: "hatchback",
    tierDescription: "Affordable compact AC rides",
    capacity: 4,
    baseFare: 20,
    perMinute: 1.5,
    perKm: 16,
    minimumFare: 120,
    bookingFee: 12,
    etaBaseMinutes: 3,
  },
  {
    tier: "premierac",
    tierLabel: "Premier AC",
    category: "sedan",
    tierDescription: "Comfortable sedans, top-quality drivers",
    capacity: 4,
    baseFare: 16,
    perMinute: 2.5,
    perKm: 28,
    minimumFare: 290,
    bookingFee: 18,
    etaBaseMinutes: 3,
  },
  {
    tier: "comfort",
    tierLabel: "Comfort",
    category: "sedan",
    tierDescription: "New Sedans, Highly rated drivers",
    capacity: 4,
    baseFare: 20,
    perMinute: 2.0,
    perKm: 24,
    minimumFare: 260,
    bookingFee: 15,
    etaBaseMinutes: 2,
  },
  {
    tier: "uberxl",
    tierLabel: "UberXL",
    category: "suv",
    tierDescription: "Affordable rides for groups up to 6",
    capacity: 6,
    baseFare: 100,
    perMinute: 1.5,
    perKm: 22,
    minimumFare: 260,
    bookingFee: 20,
    etaBaseMinutes: 4,
  },
  {
    tier: "black",
    tierLabel: "Uber Black",
    category: "sedan",
    tierDescription: "Elevated ride experience with top tier cars",
    capacity: 4,
    baseFare: 150,
    perMinute: 3.0,
    perKm: 35,
    minimumFare: 350,
    bookingFee: 25,
    etaBaseMinutes: 1,
  },
  {
    tier: "blacksuv",
    tierLabel: "Uber Black SUV",
    category: "suv",
    tierDescription: "Luxury SUV for groups up to 6",
    capacity: 6,
    baseFare: 200,
    perMinute: 3.5,
    perKm: 42,
    minimumFare: 450,
    bookingFee: 30,
    etaBaseMinutes: 2,
  },
];

export interface UberEstimateResult {
  provider: "Uber";
  tier: UberRideTier;
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
    bookingFee: number;
    surgeAmount: number;
    total: number;
  };
}

function computeSurgeMultiplier(at: Date = new Date()): number {
  const hourStr = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    hour12: false,
  }).format(at);
  const hourIst = Number(hourStr) % 24;

  if (
    (hourIst >= 8 && hourIst < 10) ||
    (hourIst >= 17 && hourIst < 20) ||
    hourIst >= 23 ||
    hourIst < 1
  ) {
    return 1.3;
  }
  if (
    (hourIst >= 10 && hourIst < 12) ||
    (hourIst >= 20 && hourIst < 23) ||
    (hourIst >= 7 && hourIst < 8)
  ) {
    return 1.1;
  }
  return 1.0;
}

const round2 = (n: number) => Math.round(n * 100) / 100;

export function calculateUberFares(
  distanceKm: number,
  durationMin: number,
  customSurge?: number
): UberEstimateResult[] {
  const surge = customSurge != null ? customSurge : computeSurgeMultiplier();

  return UBER_TIER_CONFIGS.map((cfg) => {
    const distanceFare = cfg.perKm * distanceKm;
    const timeFare = cfg.perMinute * durationMin;
    const subtotal = cfg.baseFare + distanceFare + timeFare;
    const surgedSubtotal = subtotal * surge;
    const surgeAmount = surgedSubtotal - subtotal;
    const totalWithBooking = surgedSubtotal + cfg.bookingFee;
    const total = Math.max(cfg.minimumFare, totalWithBooking);

    const fareMin = round2(total * 0.97);
    const fareMax = round2(total * 1.03);
    const etaMinutes = cfg.etaBaseMinutes + 1;

    return {
      provider: "Uber",
      tier: cfg.tier,
      tierLabel: cfg.tierLabel,
      category: cfg.category,
      tierDescription: cfg.tierDescription,
      capacity: cfg.capacity,
      estimatedFare: round2(total),
      fareMin,
      fareMax,
      etaMinutes,
      surgeMultiplier: surge,
      breakdown: {
        baseFare: round2(cfg.baseFare),
        distanceFare: round2(distanceFare),
        timeFare: round2(timeFare),
        bookingFee: round2(cfg.bookingFee),
        surgeAmount: round2(surgeAmount),
        total: round2(total),
      },
    };
  });
}
