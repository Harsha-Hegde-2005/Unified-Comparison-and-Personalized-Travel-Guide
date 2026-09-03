import math
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def round2(n: float) -> float:
    return round(n, 2)


def get_bengaluru_hour(at: datetime = None) -> int:
    if at is None:
        at = datetime.now(IST)
    elif at.tzinfo is None:
        at = at.replace(tzinfo=IST)
    else:
        at = at.astimezone(IST)
    return at.hour


def is_night_fare_ist(at: datetime = None) -> bool:
    hour = get_bengaluru_hour(at)
    return hour >= 22 or hour < 5


def compute_uber_surge(at: datetime = None) -> float:
    hour = get_bengaluru_hour(at)
    if (8 <= hour < 10) or (17 <= hour < 20) or (hour >= 23 or hour < 1):
        return 1.3
    if (10 <= hour < 12) or (20 <= hour < 23) or (7 <= hour < 8):
        return 1.1
    return 1.0


def compute_rapido_surge(at: datetime = None) -> float:
    hour = get_bengaluru_hour(at)
    if (7 <= hour <= 10) or (17 <= hour <= 21):
        return 1.5
    if hour >= 22 or hour <= 5:
        return 1.2
    return 1.0


# ── EXACT RATE CARDS (from Eshwarkota47/Ola-Uber-NammaYatri-Rapido) ───────────

NAMMA_YATRI_CONFIGS = [
    {
        "vehicleType": "AUTO",
        "label": "Auto (Easy Commute)",
        "category": "auto",
        "capacity": 3,
        "minFare": 40,
        "minDistanceKm": 2,
        "slab1Rate": 19,
        "slab1EndKm": None,
        "slab2Rate": None,
        "pickupCharge": 25,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 0,
        "icon": "🛺",
        "description": "Easy commute auto",
        "vtype": "auto",
    },
    {
        "vehicleType": "AUTO_PRIORITY",
        "label": "Auto Priority",
        "category": "auto",
        "capacity": 3,
        "minFare": 44,
        "minDistanceKm": 2,
        "slab1Rate": 20,
        "slab1EndKm": None,
        "slab2Rate": None,
        "pickupCharge": 25,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 10,
        "icon": "⚡🛺",
        "description": "Priority auto booking",
        "vtype": "auto_priority",
    },
    {
        "vehicleType": "NON_AC_CAB",
        "label": "Non-AC Cab",
        "category": "hatchback",
        "capacity": 4,
        "minFare": 85,
        "minDistanceKm": 4,
        "slab1Rate": 20,
        "slab1EndKm": 12,
        "slab2Rate": 25,
        "pickupCharge": 30,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 9,
        "icon": "🚗",
        "description": "Budget non-AC cab",
        "vtype": "non_ac_cab",
    },
    {
        "vehicleType": "AC_CAB",
        "label": "AC Cab",
        "category": "hatchback",
        "capacity": 4,
        "minFare": 100,
        "minDistanceKm": 4,
        "slab1Rate": 23,
        "slab1EndKm": 10,
        "slab2Rate": 18.40,
        "pickupCharge": 30,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 15,
        "icon": "❄️🚗",
        "description": "Comfortable AC cab",
        "vtype": "ac_cab",
    },
    {
        "vehicleType": "SEDAN_PREMIUM",
        "label": "Sedan Priority",
        "category": "sedan",
        "capacity": 4,
        "minFare": 115,
        "minDistanceKm": 4,
        "slab1Rate": 27,
        "slab1EndKm": 12,
        "slab2Rate": 21,
        "pickupCharge": 30,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 5,
        "icon": "✨🚗",
        "description": "AC, Premium Comfort",
        "vtype": "sedan_premium",
    },
    {
        "vehicleType": "XL_CAB",
        "label": "XL Cab",
        "category": "suv",
        "capacity": 6,
        "minFare": 130,
        "minDistanceKm": 4,
        "slab1Rate": 30,
        "slab1EndKm": None,
        "slab2Rate": None,
        "pickupCharge": 50,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 5,
        "icon": "🚐",
        "description": "Spacious SUV cab",
        "vtype": "xl_cab",
    },
    {
        "vehicleType": "XL_PREMIUM",
        "label": "XL Premium",
        "category": "suv",
        "capacity": 6,
        "minFare": 150,
        "minDistanceKm": 4,
        "slab1Rate": 36,
        "slab1EndKm": None,
        "slab2Rate": None,
        "pickupCharge": 70,
        "driverAdditions": 0,
        "priorityTip": 0,
        "congestionPercentage": 10,
        "icon": "❄️🚐",
        "description": "Comfortable Premium SUV",
        "vtype": "xl_premium",
    },
]

OLA_CONFIGS = [
    {
        "id": "auto",
        "name": "Ola Auto",
        "description": "Quickest auto ride in town",
        "capacity": 3,
        "category": "auto",
        "icon": "🛺",
        "baseFare": 30,
        "regularPerKmRate": 14.0,
        "longTripPerKmRate": 12.0,
        "minimumFare": 46,
        "bookingFee": 6,
        "vtype": "auto",
    },
    {
        "id": "bike",
        "name": "Ola Bike",
        "description": "Beat the traffic on a bike",
        "capacity": 1,
        "category": "bike",
        "icon": "🏍️",
        "baseFare": 20,
        "regularPerKmRate": 7.0,
        "longTripPerKmRate": 6.0,
        "minimumFare": 30,
        "bookingFee": 5,
        "vtype": "bike",
    },
    {
        "id": "mini-non-ac",
        "name": "Mini Non AC",
        "description": "Everyday affordable rides",
        "capacity": 4,
        "category": "hatchback",
        "icon": "🚘",
        "baseFare": 50,
        "regularPerKmRate": 12.0,
        "longTripPerKmRate": 10.0,
        "minimumFare": 75,
        "bookingFee": 30,
        "vtype": "mini_non_ac",
    },
    {
        "id": "mini",
        "name": "Ola Mini",
        "description": "Comfy, economical AC cars",
        "capacity": 4,
        "category": "hatchback",
        "icon": "🚗",
        "baseFare": 50,
        "regularPerKmRate": 14.0,
        "longTripPerKmRate": 11.5,
        "minimumFare": 80,
        "bookingFee": 30,
        "vtype": "mini",
    },
    {
        "id": "priority",
        "name": "Ola Priority",
        "description": "Priority Pickup with top drivers",
        "capacity": 4,
        "category": "hatchback",
        "icon": "⚡",
        "baseFare": 50,
        "regularPerKmRate": 14.0,
        "longTripPerKmRate": 11.5,
        "minimumFare": 80,
        "bookingFee": 30,
        "vtype": "priority",
    },
    {
        "id": "prime-sedan",
        "name": "Prime Sedan",
        "description": "Top sedans with high-rated drivers",
        "capacity": 4,
        "category": "sedan",
        "icon": "🚕",
        "baseFare": 50,
        "regularPerKmRate": 16.0,
        "longTripPerKmRate": 13.0,
        "minimumFare": 100,
        "bookingFee": 30,
        "vtype": "prime_sedan",
    },
    {
        "id": "prime-plus",
        "name": "Prime Plus",
        "description": "Top-rated drivers in premium sedan comfort",
        "capacity": 4,
        "category": "sedan",
        "icon": "✨",
        "baseFare": 50,
        "regularPerKmRate": 18.0,
        "longTripPerKmRate": 14.5,
        "minimumFare": 120,
        "bookingFee": 30,
        "vtype": "prime_plus",
    },
    {
        "id": "prime-suv",
        "name": "Prime SUV",
        "description": "Spacious SUVs for groups up to 6",
        "capacity": 6,
        "category": "suv",
        "icon": "🚙",
        "baseFare": 80,
        "regularPerKmRate": 30.0,
        "longTripPerKmRate": 24.0,
        "minimumFare": 180,
        "bookingFee": 34,
        "vtype": "prime_suv",
    },
]

UBER_CONFIGS = [
    {
        "tier": "moto",
        "tierLabel": "Uber Moto",
        "category": "bike",
        "tierDescription": "Affordable bike rides",
        "capacity": 1,
        "baseFare": 8,
        "perMinute": 0.75,
        "perKm": 9,
        "minimumFare": 35,
        "bookingFee": 5,
        "icon": "🏍️",
        "vtype": "moto",
    },
    {
        "tier": "auto",
        "tierLabel": "Uber Auto",
        "category": "auto",
        "tierDescription": "Pay directly to driver, cash/UPI only",
        "capacity": 3,
        "baseFare": 8,
        "perMinute": 1.0,
        "perKm": 13,
        "minimumFare": 50,
        "bookingFee": 10,
        "icon": "🛺",
        "vtype": "auto",
    },
    {
        "tier": "gonoac",
        "tierLabel": "Go Non AC",
        "category": "hatchback",
        "tierDescription": "Everyday affordable rides",
        "capacity": 4,
        "baseFare": 15,
        "perMinute": 1.3,
        "perKm": 14,
        "minimumFare": 65,
        "bookingFee": 9,
        "icon": "🚗",
        "vtype": "gonoac",
    },
    {
        "tier": "ubergoac",
        "tierLabel": "Uber Go AC",
        "category": "hatchback",
        "tierDescription": "Affordable compact AC rides",
        "capacity": 4,
        "baseFare": 20,
        "perMinute": 1.5,
        "perKm": 16,
        "minimumFare": 120,
        "bookingFee": 12,
        "icon": "❄️🚗",
        "vtype": "ubergoac",
    },
    {
        "tier": "premierac",
        "tierLabel": "Premier AC",
        "category": "sedan",
        "tierDescription": "Comfortable sedans, top-quality drivers",
        "capacity": 4,
        "baseFare": 16,
        "perMinute": 2.5,
        "perKm": 28,
        "minimumFare": 290,
        "bookingFee": 18,
        "icon": "⭐🚗",
        "vtype": "premierac",
    },
    {
        "tier": "comfort",
        "tierLabel": "Comfort",
        "category": "sedan",
        "tierDescription": "New Sedans, Highly rated drivers",
        "capacity": 4,
        "baseFare": 20,
        "perMinute": 2.0,
        "perKm": 24,
        "minimumFare": 260,
        "bookingFee": 15,
        "icon": "🚘",
        "vtype": "comfort",
    },
    {
        "tier": "uberxl",
        "tierLabel": "UberXL",
        "category": "suv",
        "tierDescription": "Affordable rides for groups up to 6",
        "capacity": 6,
        "baseFare": 100,
        "perMinute": 1.5,
        "perKm": 22,
        "minimumFare": 260,
        "bookingFee": 20,
        "icon": "🚙",
        "vtype": "uberxl",
    },
    {
        "tier": "black",
        "tierLabel": "Uber Black",
        "category": "sedan",
        "tierDescription": "Elevated ride experience with top tier cars",
        "capacity": 4,
        "baseFare": 150,
        "perMinute": 3.0,
        "perKm": 35,
        "minimumFare": 350,
        "bookingFee": 25,
        "icon": "🖤🚗",
        "vtype": "black",
    },
    {
        "tier": "blacksuv",
        "tierLabel": "Uber Black SUV",
        "category": "suv",
        "tierDescription": "Luxury SUV for groups up to 6",
        "capacity": 6,
        "baseFare": 200,
        "perMinute": 3.5,
        "perKm": 42,
        "minimumFare": 450,
        "bookingFee": 30,
        "icon": "🖤🚙",
        "vtype": "blacksuv",
    },
]

RAPIDO_CONFIGS = [
    {
        "id": "bike-direct",
        "label": "Bike Direct",
        "icon": "🏍️",
        "category": "bike",
        "capacity": 1,
        "baseFare": 25,
        "perKm": 6,
        "perMin": 1.0,
        "minFare": 30,
        "description": "Quick Bike rides",
        "vtype": "bike_direct",
    },
    {
        "id": "scooty-direct",
        "label": "Scooty Direct",
        "icon": "🛵",
        "category": "bike",
        "capacity": 1,
        "baseFare": 30,
        "perKm": 7,
        "perMin": 1.07,
        "minFare": 35,
        "description": "Comfortable scooty ride",
        "vtype": "scooty_direct",
    },
    {
        "id": "bike-women",
        "label": "Bike – Women Preferred",
        "icon": "🏍️",
        "category": "bike",
        "capacity": 1,
        "baseFare": 25,
        "perKm": 6,
        "perMin": 1.0,
        "minFare": 30,
        "description": "Captains Rated by Women",
        "vtype": "bike_women",
    },
    {
        "id": "auto-lite",
        "label": "Auto Lite",
        "icon": "🛺",
        "category": "auto",
        "capacity": 3,
        "baseFare": 30,
        "perKm": 11.1,
        "perMin": 0.5,
        "minFare": 50,
        "description": "Budget auto ride",
        "vtype": "auto_lite",
    },
    {
        "id": "auto",
        "label": "Rapido Auto",
        "icon": "🛺",
        "category": "auto",
        "capacity": 3,
        "baseFare": 35,
        "perKm": 13.2,
        "perMin": 0.5,
        "minFare": 55,
        "description": "Shared or private auto",
        "vtype": "auto",
    },
    {
        "id": "auto-priority",
        "label": "Auto Priority",
        "icon": "⚡🛺",
        "category": "auto",
        "capacity": 3,
        "baseFare": 35,
        "perKm": 16.7,
        "perMin": 0.5,
        "minFare": 80,
        "description": "Fastest auto, priority matching",
        "vtype": "auto_priority",
    },
    {
        "id": "cab-non-ac",
        "label": "Cab Non AC",
        "icon": "🚗",
        "category": "hatchback",
        "capacity": 4,
        "baseFare": 40,
        "perKm": 14.9,
        "perMin": 0.75,
        "minFare": 70,
        "description": "Budget cab without AC",
        "vtype": "cab_non_ac",
    },
    {
        "id": "cab-ac-priority",
        "label": "Cab AC Priority",
        "icon": "⚡🚗",
        "category": "hatchback",
        "capacity": 4,
        "baseFare": 45,
        "perKm": 17.2,
        "perMin": 0.75,
        "minFare": 90,
        "description": "Priority AC cab, faster pickup",
        "vtype": "cab_ac_priority",
    },
    {
        "id": "cab-ac",
        "label": "Cab AC",
        "icon": "❄️🚗",
        "category": "hatchback",
        "capacity": 4,
        "baseFare": 40,
        "perKm": 16.5,
        "perMin": 0.75,
        "minFare": 85,
        "description": "Air-conditioned cab",
        "vtype": "cab_ac",
    },
    {
        "id": "cab-premium",
        "label": "Cab Premium",
        "icon": "✨🚙",
        "category": "sedan",
        "capacity": 4,
        "baseFare": 50,
        "perKm": 19.75,
        "perMin": 1.0,
        "minFare": 110,
        "description": "Premium sedan experience",
        "vtype": "cab_premium",
    },
    {
        "id": "cab-xl",
        "label": "Cab XL",
        "icon": "🚐",
        "category": "suv",
        "capacity": 6,
        "baseFare": 60,
        "perKm": 24.1,
        "perMin": 1.0,
        "minFare": 150,
        "description": "XL vehicle for groups",
        "vtype": "cab_xl",
    },
]


class FareEngine:
    def __init__(self, fare_config_path: str = None):
        self.providers = {
            "namma_yatri": {"name": "Namma Yatri"},
            "ola": {"name": "Ola"},
            "uber": {"name": "Uber"},
            "rapido": {"name": "Rapido"},
        }

    def is_night(self, current_time: datetime = None) -> bool:
        return is_night_fare_ist(current_time)

    def _calc_namma_yatri(self, distance_km: float, duration_min: float, current_time: datetime = None, surge: float = 1.0) -> list[dict]:
        night = is_night_fare_ist(current_time)
        speed_kmh = distance_km / max(0.1, duration_min / 60)
        results = []

        for cfg in NAMMA_YATRI_CONFIGS:
            extra_km = max(0.0, distance_km - cfg["minDistanceKm"])
            distance_fare = 0.0

            if extra_km > 0:
                if cfg["slab1EndKm"] is not None and cfg["slab2Rate"] is not None:
                    slab1_km = min(extra_km, cfg["slab1EndKm"] - cfg["minDistanceKm"])
                    slab2_km = max(0.0, distance_km - cfg["slab1EndKm"])
                    distance_fare = slab1_km * cfg["slab1Rate"] + slab2_km * cfg["slab2Rate"]
                else:
                    distance_fare = extra_km * cfg["slab1Rate"]

            congestion_percentage = cfg.get("congestionPercentage", 0)
            if cfg["vehicleType"] == "NON_AC_CAB":
                if surge <= 1.0:
                    congestion_percentage = 0
                else:
                    congestion_percentage = round(congestion_percentage * surge)
            else:
                if surge > 1.0:
                    congestion_percentage = round(congestion_percentage * surge)
                if speed_kmh > 30:
                    if cfg["vehicleType"] == "AC_CAB":
                        congestion_percentage = 0
                    elif cfg["vehicleType"] == "SEDAN_PREMIUM":
                        congestion_percentage = 10
                    elif cfg["vehicleType"] in ("XL_CAB", "XL_PREMIUM"):
                        congestion_percentage = 0

            congestion_charge = (
                round((cfg["minFare"] + distance_fare) * (congestion_percentage / 100))
                if congestion_percentage > 0
                else 0
            )

            subtotal = (
                cfg["minFare"]
                + distance_fare
                + cfg["pickupCharge"]
                + cfg["driverAdditions"]
                + cfg["priorityTip"]
                + congestion_charge
            )

            night_multiplier = 1.5 if cfg["category"] == "auto" else 1.1
            night_base = (
                (cfg["minFare"] + distance_fare)
                if cfg["category"] == "auto"
                else (cfg["minFare"] + distance_fare + cfg["pickupCharge"])
            )
            night_surcharge = night_base * (night_multiplier - 1.0) if night else 0.0

            total = round2(subtotal + night_surcharge)
            fare_min = int(round(total - 10))
            fare_max = int(round(total))

            results.append({
                "vehicle": cfg["label"],
                "description": cfg["description"],
                "capacity": cfg["capacity"],
                "icon": cfg["icon"],
                "distance_km": distance_km,
                "duration_min": duration_min,
                "fare_estimate": int(round(total)),
                "fare_min": max(cfg["minFare"], fare_min),
                "fare_max": max(cfg["minFare"], fare_max),
                "fare_display": f"Rs. {max(cfg['minFare'], fare_min)} - Rs. {max(cfg['minFare'], fare_max)}",
                "is_night": night,
                "surge": surge,
                "vtype": cfg["vtype"],
                "category": cfg["category"],
            })
        return results

    def _calc_ola(self, distance_km: float, duration_min: float, current_time: datetime = None, surge: float = 1.0, is_airport: bool = False) -> list[dict]:
        night = is_night_fare_ist(current_time)
        results = []

        for cfg in OLA_CONFIGS:
            rate_per_km = cfg["longTripPerKmRate"] if distance_km > 18 else cfg["regularPerKmRate"]
            if is_airport:
                if cfg["id"] == "mini-non-ac":
                    rate_per_km = 15.00
                elif cfg["id"] in ("mini", "priority"):
                    rate_per_km = 15.30
                elif cfg["id"] == "prime-sedan":
                    rate_per_km = 15.80
                elif cfg["id"] == "prime-plus":
                    rate_per_km = 17.50
                elif cfg["id"] == "prime-suv":
                    rate_per_km = 27.50

            distance_fare = round2(distance_km * rate_per_km)
            subtotal_before_surge = cfg["baseFare"] + distance_fare + cfg["bookingFee"]

            if cfg["id"] == "priority":
                if is_airport:
                    subtotal_before_surge = round2(subtotal_before_surge + 25)
                else:
                    subtotal_before_surge = round2(subtotal_before_surge * 1.25)

            if not is_airport and distance_km <= 10:
                if cfg["id"] == "mini-non-ac":
                    subtotal_before_surge *= 0.86
                elif cfg["id"] == "mini":
                    subtotal_before_surge *= 0.783
                elif cfg["id"] == "priority":
                    subtotal_before_surge *= 0.79
                elif cfg["id"] in ("prime-sedan", "prime-plus"):
                    subtotal_before_surge *= 0.795
                elif cfg["id"] == "prime-suv":
                    subtotal_before_surge *= 0.816
                elif cfg["id"] == "auto":
                    subtotal_before_surge *= 0.956

            subtotal = round2(max(subtotal_before_surge * surge, cfg["minimumFare"]))
            taxes = round2(subtotal * 0.05)
            toll_fee = 120 if is_airport else 0
            total = round2(subtotal + taxes + toll_fee)

            range_delta = max(5, round(total * 0.025))
            fare_min = max(cfg["minimumFare"], math.floor((total - range_delta) / 5) * 5)
            fare_max = math.ceil((total + range_delta) / 5) * 5

            results.append({
                "vehicle": cfg["name"],
                "description": cfg["description"],
                "capacity": cfg["capacity"],
                "icon": cfg["icon"],
                "distance_km": distance_km,
                "duration_min": duration_min,
                "fare_estimate": int(round(total)),
                "fare_min": int(fare_min),
                "fare_max": int(fare_max),
                "fare_display": f"Rs. {int(fare_min)} - Rs. {int(fare_max)}",
                "is_night": night,
                "surge": surge,
                "vtype": cfg["vtype"],
                "category": cfg["category"],
            })
        return results

    def _calc_uber(self, distance_km: float, duration_min: float, current_time: datetime = None, surge: float = None) -> list[dict]:
        night = is_night_fare_ist(current_time)
        effective_surge = surge if surge is not None else compute_uber_surge(current_time)
        results = []

        for cfg in UBER_CONFIGS:
            distance_fare = cfg["perKm"] * distance_km
            time_fare = cfg["perMinute"] * duration_min
            subtotal = cfg["baseFare"] + distance_fare + time_fare
            surged_subtotal = subtotal * effective_surge
            total_with_booking = surged_subtotal + cfg["bookingFee"]
            total = max(float(cfg["minimumFare"]), total_with_booking)

            fare_min = round2(total * 0.97)
            fare_max = round2(total * 1.03)

            results.append({
                "vehicle": cfg["tierLabel"],
                "description": cfg["tierDescription"],
                "capacity": cfg["capacity"],
                "icon": cfg["icon"],
                "distance_km": distance_km,
                "duration_min": duration_min,
                "fare_estimate": int(round(total)),
                "fare_min": int(round(fare_min)),
                "fare_max": int(round(fare_max)),
                "fare_display": f"Rs. {int(round(fare_min))} - Rs. {int(round(fare_max))}",
                "is_night": night,
                "surge": effective_surge,
                "vtype": cfg["vtype"],
                "category": cfg["category"],
            })
        return results

    def _calc_rapido(self, distance_km: float, duration_min: float, current_time: datetime = None, surge: float = None) -> list[dict]:
        night = is_night_fare_ist(current_time)
        effective_surge = surge if surge is not None else compute_rapido_surge(current_time)
        results = []

        for cfg in RAPIDO_CONFIGS:
            distance_fare = round2(distance_km * cfg["perKm"])
            time_fare = round2(duration_min * cfg["perMin"])
            raw_fare = cfg["baseFare"] + distance_fare + time_fare
            fare_before_surge = max(float(raw_fare), float(cfg["minFare"]))

            if effective_surge > 1.0:
                total_after_surge = fare_before_surge * effective_surge
            else:
                total_after_surge = fare_before_surge

            total = round(total_after_surge)
            range_delta = max(5, round(total * 0.03))
            fare_min = max(cfg["minFare"], math.floor((total - range_delta) / 5) * 5)
            fare_max = math.ceil((total + range_delta) / 5) * 5

            results.append({
                "vehicle": cfg["label"],
                "description": cfg["description"],
                "capacity": cfg["capacity"],
                "icon": cfg["icon"],
                "distance_km": distance_km,
                "duration_min": duration_min,
                "fare_estimate": int(total),
                "fare_min": int(fare_min),
                "fare_max": int(fare_max),
                "fare_display": f"Rs. {int(fare_min)} - Rs. {int(fare_max)}",
                "is_night": night,
                "surge": effective_surge,
                "vtype": cfg["vtype"],
                "category": cfg["category"],
            })
        return results

    def get_all_fares_for_provider(
        self,
        provider_key: str,
        distance_km: float,
        duration_min: float,
        current_time: datetime = None,
        weather: str = "clear",
        ignore_constraints: bool = False,
    ) -> list[dict]:
        p = provider_key.lower().replace("-", "_")
        if p == "nammayatri":
            p = "namma_yatri"

        # Apply realistic weather surge delta
        weather_surge = 1.0
        weather_lower = weather.lower()
        if "light rain" in weather_lower or "drizzle" in weather_lower:
            weather_surge = 1.15
        elif "heavy rain" in weather_lower or "thunderstorm" in weather_lower:
            weather_surge = 1.35
        elif "storm" in weather_lower or "flood" in weather_lower:
            weather_surge = 1.60

        if p == "namma_yatri":
            fares = self._calc_namma_yatri(distance_km, duration_min, current_time, surge=weather_surge)
        elif p == "ola":
            fares = self._calc_ola(distance_km, duration_min, current_time, surge=weather_surge)
        elif p == "uber":
            fares = self._calc_uber(distance_km, duration_min, current_time, surge=weather_surge if weather_surge > 1.0 else None)
        elif p == "rapido":
            fares = self._calc_rapido(distance_km, duration_min, current_time, surge=weather_surge if weather_surge > 1.0 else None)
        else:
            return []

        # Filter vehicle constraints
        if not ignore_constraints:
            filtered = []
            for f in fares:
                cat = f.get("category", "")
                if cat == "bike" and distance_km > 15.0:
                    continue
                if cat == "auto" and distance_km > 25.0:
                    continue
                filtered.append(f)
            fares = filtered

        return sorted(fares, key=lambda x: x["fare_min"])

    def get_all_fares(self, distance_km: float) -> list[dict]:
        return self.get_all_fares_for_provider("namma_yatri", distance_km, distance_km / 30 * 60, None, "clear")

    def get_fare(
        self,
        provider_key: str,
        vehicle_key: str,
        distance_km: float,
        duration_min: float,
        current_time: datetime = None,
        weather: str = "clear",
    ) -> dict:
        if isinstance(provider_key, (int, float)):
            distance_km = float(provider_key)
            vehicle_type = vehicle_key
            fares = self.get_all_fares_for_provider(
                "namma_yatri", distance_km, distance_km / 30 * 60, None, "clear", ignore_constraints=True
            )
            for f in fares:
                if f["vtype"].lower().replace("-", "_") == vehicle_type.lower().replace("-", "_"):
                    return f
            return fares[0] if fares else {}

        fares = self.get_all_fares_for_provider(
            provider_key, distance_km, duration_min, current_time, weather, ignore_constraints=True
        )
        target = vehicle_key.lower().replace("-", "_")
        prefix = provider_key.lower() + "_"
        if target.startswith(prefix):
            target = target[len(prefix):]

        for f in fares:
            if f["vtype"].lower().replace("-", "_") == target:
                return f

        for f in fares:
            f_name = f["vehicle"].lower().replace("-", "_").replace(" ", "_")
            if target in f_name or f_name in target:
                return f

        return fares[0] if fares else {}
