import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import math

IST = ZoneInfo("Asia/Kolkata")

def round2(n: float) -> float:
    return round(n, 2)

EXACT_NAMMA_YATRI_RATES = [
    { "vehicleType": "AUTO", "label": "Auto", "category": "auto", "capacity": 3, "minFare": 36, "minDistanceKm": 2, "slab1Rate": 18, "slab1EndKm": None, "slab2Rate": None, "pickupCharge": 0, "driverAdditions": 10, "priorityTip": 0, "icon": "🛺" },
    { "vehicleType": "AUTO_PRIORITY", "label": "Auto Priority", "category": "auto", "capacity": 3, "minFare": 36, "minDistanceKm": 2, "slab1Rate": 18, "slab1EndKm": None, "slab2Rate": None, "pickupCharge": 0, "driverAdditions": 10, "priorityTip": 30, "icon": "🛺⚡" },
    { "vehicleType": "NON_AC_CAB", "label": "Non-AC Cab", "category": "hatchback", "capacity": 4, "minFare": 85, "minDistanceKm": 4, "slab1Rate": 20, "slab1EndKm": 10, "slab2Rate": 16, "pickupCharge": 20, "driverAdditions": 0, "priorityTip": 0, "icon": "🚗" },
    { "vehicleType": "AC_CAB", "label": "AC Cab", "category": "hatchback", "capacity": 4, "minFare": 100, "minDistanceKm": 4, "slab1Rate": 23, "slab1EndKm": 10, "slab2Rate": 18.4, "pickupCharge": 20, "driverAdditions": 0, "priorityTip": 0, "icon": "🚗❄️" },
    { "vehicleType": "SEDAN_PREMIUM", "label": "Sedan Premium", "category": "sedan", "capacity": 4, "minFare": 121, "minDistanceKm": 4, "slab1Rate": 28.5, "slab1EndKm": 10, "slab2Rate": 22.5, "pickupCharge": 21, "driverAdditions": 0, "priorityTip": 0, "icon": "🚕" },
    { "vehicleType": "XL_CAB", "label": "XL Cab", "category": "suv", "capacity": 6, "minFare": 130, "minDistanceKm": 4, "slab1Rate": 30, "slab1EndKm": None, "slab2Rate": None, "pickupCharge": 40, "driverAdditions": 0, "priorityTip": 0, "icon": "🚙" },
    { "vehicleType": "XL_PREMIUM", "label": "XL Premium", "category": "suv", "capacity": 6, "minFare": 150, "minDistanceKm": 4, "slab1Rate": 36, "slab1EndKm": None, "slab2Rate": None, "pickupCharge": 60, "driverAdditions": 0, "priorityTip": 0, "icon": "🚙✨" },
]

OLA_TIER_CONFIGS = [
    { "id": "auto", "name": "Ola Auto", "description": "Quickest auto ride in town", "capacity": 3, "category": "auto", "iconEmoji": "🛺", "baseFare": 36, "regularPerKmRate": 16.0, "longTripPerKmRate": 13.5, "minDistanceKm": 2, "minimumFare": 45, "cancellationFee": 30, "etaBaseMinutes": 2 },
    { "id": "bike", "name": "Ola Bike", "description": "Beat the traffic on a bike", "capacity": 1, "category": "bike", "iconEmoji": "🏍️", "baseFare": 20, "regularPerKmRate": 9.0, "longTripPerKmRate": 7.6, "minDistanceKm": 0, "minimumFare": 30, "cancellationFee": 20, "etaBaseMinutes": 2 },
    { "id": "mini-non-ac", "name": "Mini Non AC", "description": "Everyday affordable rides", "capacity": 4, "category": "hatchback", "iconEmoji": "🚘", "baseFare": 35, "regularPerKmRate": 16.8, "longTripPerKmRate": 13.5, "minDistanceKm": 0, "minimumFare": 75, "cancellationFee": 40, "etaBaseMinutes": 3 },
    { "id": "mini", "name": "Ola Mini", "description": "Comfy, economical AC cars", "capacity": 4, "category": "hatchback", "iconEmoji": "🚗", "baseFare": 35, "regularPerKmRate": 16.8, "longTripPerKmRate": 13.5, "minDistanceKm": 0, "minimumFare": 80, "cancellationFee": 50, "etaBaseMinutes": 3 },
    { "id": "priority", "name": "Ola Priority", "description": "Priority Pickup with top drivers", "capacity": 4, "category": "hatchback", "iconEmoji": "⚡", "baseFare": 40, "regularPerKmRate": 16.8, "longTripPerKmRate": 13.5, "minDistanceKm": 0, "minimumFare": 80, "cancellationFee": 50, "etaBaseMinutes": 1 },
    { "id": "prime-sedan", "name": "Prime Sedan", "description": "Top sedans with high-rated drivers", "capacity": 4, "category": "sedan", "iconEmoji": "🚕", "baseFare": 40, "regularPerKmRate": 17.0, "longTripPerKmRate": 13.8, "minDistanceKm": 0, "minimumFare": 100, "cancellationFee": 60, "etaBaseMinutes": 4 },
    { "id": "prime-plus", "name": "Prime Plus", "description": "Top-rated drivers in premium sedan comfort", "capacity": 4, "category": "sedan", "iconEmoji": "✨", "baseFare": 45, "regularPerKmRate": 17.3, "longTripPerKmRate": 14.1, "minDistanceKm": 0, "minimumFare": 120, "cancellationFee": 75, "etaBaseMinutes": 3 },
    { "id": "prime-suv", "name": "Prime SUV", "description": "Spacious SUVs for groups up to 6", "capacity": 6, "category": "suv", "iconEmoji": "🚙", "baseFare": 65, "regularPerKmRate": 27.8, "longTripPerKmRate": 22.0, "minDistanceKm": 0, "minimumFare": 180, "cancellationFee": 100, "etaBaseMinutes": 4 },
]

UBER_TIER_CONFIGS = [
    { "tier": "moto", "tierLabel": "Uber Moto", "category": "bike", "tierDescription": "Affordable bike rides", "capacity": 1, "baseFare": 8, "perMinute": 0.75, "perKm": 9, "minimumFare": 35, "bookingFee": 5, "etaBaseMinutes": 2 },
    { "tier": "auto", "tierLabel": "Uber Auto", "category": "auto", "tierDescription": "Pay directly to driver, cash/UPI only", "capacity": 3, "baseFare": 8, "perMinute": 1.0, "perKm": 13, "minimumFare": 50, "bookingFee": 10, "etaBaseMinutes": 2 },
    { "tier": "gonoac", "tierLabel": "Go Non AC", "category": "hatchback", "tierDescription": "Everyday affordable rides", "capacity": 4, "baseFare": 15, "perMinute": 1.3, "perKm": 14, "minimumFare": 65, "bookingFee": 9, "etaBaseMinutes": 4 },
    { "tier": "ubergoac", "tierLabel": "Uber Go AC", "category": "hatchback", "tierDescription": "Affordable compact AC rides", "capacity": 4, "baseFare": 20, "perMinute": 1.5, "perKm": 16, "minimumFare": 120, "bookingFee": 12, "etaBaseMinutes": 3 },
    { "tier": "premierac", "tierLabel": "Premier AC", "category": "sedan", "tierDescription": "Comfortable sedans, top-quality drivers", "capacity": 4, "baseFare": 16, "perMinute": 2.5, "perKm": 28, "minimumFare": 290, "bookingFee": 18, "etaBaseMinutes": 3 },
    { "tier": "comfort", "tierLabel": "Comfort", "category": "sedan", "tierDescription": "New Sedans, Highly rated drivers", "capacity": 4, "baseFare": 20, "perMinute": 2.0, "perKm": 24, "minimumFare": 260, "bookingFee": 15, "etaBaseMinutes": 2 },
    { "tier": "uberxl", "tierLabel": "UberXL", "category": "suv", "tierDescription": "Affordable rides for groups up to 6", "capacity": 6, "baseFare": 100, "perMinute": 1.5, "perKm": 22, "minimumFare": 260, "bookingFee": 20, "etaBaseMinutes": 4 },
    { "tier": "black", "tierLabel": "Uber Black", "category": "sedan", "tierDescription": "Elevated ride experience with top tier cars", "capacity": 4, "baseFare": 150, "perMinute": 3.0, "perKm": 35, "minimumFare": 350, "bookingFee": 25, "etaBaseMinutes": 1 },
    { "tier": "blacksuv", "tierLabel": "Uber Black SUV", "category": "suv", "tierDescription": "Luxury SUV for groups up to 6", "capacity": 6, "baseFare": 200, "perMinute": 3.5, "perKm": 42, "minimumFare": 450, "bookingFee": 30, "etaBaseMinutes": 2 },
]


class FareEngine:
    def __init__(self, fare_config_path: str = None):
        if fare_config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fare_config_path = os.path.abspath(
                os.path.join(base_dir, "..", "..", "..", "database", "cab", "fare_config.json")
            )
        self._fare_config_path = fare_config_path
        self._fare_config_mtime = None
        self._reload_config()

    def _reload_config(self):
        mtime = os.path.getmtime(self._fare_config_path)
        if mtime != self._fare_config_mtime:
            with open(self._fare_config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.providers = self.config["providers"]
            self._fare_config_mtime = mtime

    def is_night(self, current_time: datetime = None) -> bool:
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        else:
            current_time = current_time.astimezone(IST)
        hour = current_time.hour
        return hour >= 22 or hour < 5

    def compute_uber_surge(self, current_time: datetime = None) -> float:
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        else:
            current_time = current_time.astimezone(IST)
        hourIst = current_time.hour
        if (8 <= hourIst < 10) or (17 <= hourIst < 20) or (hourIst >= 23) or (hourIst < 1):
            return 1.3
        if (10 <= hourIst < 12) or (20 <= hourIst < 23) or (7 <= hourIst < 8):
            return 1.1
        return 1.0

    def compute_ola_surge(self, current_time: datetime = None, weather: str = "clear", is_auto: bool = False) -> float:
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        else:
            current_time = current_time.astimezone(IST)
        hourIst = current_time.hour
        delta_time = 0.0
        if is_auto:
            if hourIst >= 22 or hourIst < 5:
                delta_time = 0.50
        else:
            time_minutes = hourIst * 60 + current_time.minute
            if (8 * 60 + 30) <= time_minutes <= (10 * 60 + 30):
                delta_time = 0.25
            elif (17 * 60 + 30) <= time_minutes <= (20 * 60 + 30):
                delta_time = 0.30
            elif hourIst >= 22 or hourIst < 5:
                delta_time = 0.50
                
        delta_weather = 0.0
        weather_lower = weather.lower()
        if "light rain" in weather_lower or "drizzle" in weather_lower:
            delta_weather = 0.15
        elif "heavy rain" in weather_lower or "thunderstorm" in weather_lower:
            delta_weather = 0.40
        elif "storm" in weather_lower or "flood" in weather_lower:
            delta_weather = 0.75

        return 1.0 + delta_time + delta_weather

    def get_all_fares_for_provider(self, provider_key: str, distance_km: float,
                                   duration_min: float, current_time: datetime = None,
                                   weather: str = "clear") -> list:
        provider_key = provider_key.lower()
        results = []
        
        if provider_key == "namma_yatri":
            night = self.is_night(current_time)
            for cfg in EXACT_NAMMA_YATRI_RATES:
                if cfg["category"] == "auto" and distance_km > 25.0:
                    continue
                distanceFare = 0
                extraKm = max(0, distance_km - cfg["minDistanceKm"])
                if extraKm > 0:
                    if cfg["slab1EndKm"] is not None and cfg["slab2Rate"] is not None:
                        slab1Km = min(extraKm, cfg["slab1EndKm"] - cfg["minDistanceKm"])
                        slab2Km = max(0, distance_km - cfg["slab1EndKm"])
                        distanceFare = slab1Km * cfg["slab1Rate"] + slab2Km * cfg["slab2Rate"]
                    else:
                        distanceFare = extraKm * cfg["slab1Rate"]
                
                subtotal = cfg["minFare"] + distanceFare + cfg["pickupCharge"] + cfg["driverAdditions"] + cfg["priorityTip"]
                nightMultiplier = 1.5 if cfg["category"] == "auto" else 1.25
                nightSurcharge = (cfg["minFare"] + distanceFare) * (nightMultiplier - 1) if night else 0
                total = round2(subtotal + nightSurcharge)
                
                if cfg["category"] == "auto":
                    fareMin = round(total - 10)
                    fareMax = round(total)
                    estimate = round(total)
                else:
                    fareMin = round(total)
                    fareMax = round(total + 10)
                    estimate = round(total)
                    
                results.append({
                    "vehicle": cfg["label"],
                    "description": "",
                    "capacity": cfg["capacity"],
                    "icon": cfg.get("icon", "🚗"),
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "fare_estimate": estimate,
                    "fare_min": fareMin,
                    "fare_max": fareMax,
                    "fare_display": f"Rs. {fareMin} - Rs. {fareMax}",
                    "is_night": night,
                    "surge": 1.0,
                    "vtype": cfg["vehicleType"]
                })
                
        elif provider_key == "ola":
            for cfg in OLA_TIER_CONFIGS:
                if cfg["category"] == "auto" and distance_km > 25.0:
                    continue
                if cfg["category"] == "bike" and distance_km > 15.0:
                    continue
                
                is_auto = cfg["category"] in ["auto", "bike"]
                surge = self.compute_ola_surge(current_time, weather, is_auto)
                
                baseFare = cfg["baseFare"]
                distanceFare = 0
                if cfg["id"] == "auto":
                    baseFare = 36
                    extraKm = max(0, distance_km - cfg["minDistanceKm"])
                    ratePerKm = cfg["longTripPerKmRate"] if distance_km > 18 else cfg["regularPerKmRate"]
                    distanceFare = round2(extraKm * ratePerKm + 10)
                else:
                    ratePerKm = cfg["longTripPerKmRate"] if distance_km > 18 else cfg["regularPerKmRate"]
                    distanceFare = round2(distance_km * ratePerKm)
                    
                subtotalBeforeSurge = baseFare + distanceFare
                subtotal = round2(max(subtotalBeforeSurge * surge, cfg["minimumFare"]))
                taxes = round2(subtotal * 0.05)
                total = round2(subtotal + taxes)
                
                rangeDelta = max(5, round(total * 0.025))
                fareMin = max(cfg["minimumFare"], math.floor((total - rangeDelta) / 5) * 5)
                fareMax = math.ceil((total + rangeDelta) / 5) * 5
                estimate = round(total)
                
                results.append({
                    "vehicle": cfg["name"],
                    "description": cfg["description"],
                    "capacity": cfg["capacity"],
                    "icon": cfg.get("iconEmoji", "🚗"),
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "fare_estimate": estimate,
                    "fare_min": fareMin,
                    "fare_max": fareMax,
                    "fare_display": f"Rs. {fareMin} - Rs. {fareMax}",
                    "is_night": False,
                    "surge": round2(surge),
                    "vtype": cfg["id"]
                })

        elif provider_key == "uber":
            surge = self.compute_uber_surge(current_time)
            for cfg in UBER_TIER_CONFIGS:
                if cfg["category"] == "auto" and distance_km > 25.0:
                    continue
                if cfg["category"] == "bike" and distance_km > 15.0:
                    continue
                    
                distanceFare = cfg["perKm"] * distance_km
                timeFare = cfg["perMinute"] * duration_min
                subtotal = cfg["baseFare"] + distanceFare + timeFare
                surgedSubtotal = subtotal * surge
                totalWithBooking = surgedSubtotal + cfg["bookingFee"]
                total = max(cfg["minimumFare"], totalWithBooking)
                
                fareMin = round2(total * 0.97)
                fareMax = round2(total * 1.03)
                estimate = round(total)
                
                results.append({
                    "vehicle": cfg["tierLabel"],
                    "description": cfg["tierDescription"],
                    "capacity": cfg["capacity"],
                    "icon": "🚗",
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "fare_estimate": estimate,
                    "fare_min": round(fareMin),
                    "fare_max": round(fareMax),
                    "fare_display": f"Rs. {round(fareMin)} - Rs. {round(fareMax)}",
                    "is_night": False,
                    "surge": round2(surge),
                    "vtype": cfg["tier"]
                })

        else:
            # Fallback for rapido and others if they exist in fare_config.json
            self._reload_config()
            if provider_key in self.providers:
                vehicles = self.providers[provider_key]["vehicles"]
                for vehicle_key, cfg in vehicles.items():
                    v_lower = vehicle_key.lower()
                    if ("bike" in v_lower or "scooty" in v_lower or "moto" in v_lower) and distance_km > 15.0:
                        continue
                    if "auto" in v_lower and distance_km > 25.0:
                        continue
                        
                    base_fare = cfg.get("base_fare", 0.0)
                    base_dist = cfg.get("base_dist", 0.0)
                    per_km_rate = cfg.get("per_km", 0.0)
                    per_min_rate = cfg.get("per_min", 0.0)
            
                    billable_km = max(0.0, distance_km - base_dist)
                    
                    rate_tiers = cfg.get("rate_tiers", [])
                    if rate_tiers:
                        remaining = billable_km
                        prev_boundary = 0
                        distance_charge = 0.0
                        for tier in rate_tiers:
                            if remaining <= 0:
                                break
                            upto_km = tier.get("upto_km", float('inf'))
                            rate = tier.get("rate", 0.0)
                            band_size = upto_km - prev_boundary
                            km_in_band = min(remaining, band_size)
                            distance_charge += km_in_band * rate
                            remaining -= km_in_band
                            prev_boundary = upto_km
                    else:
                        distance_charge = billable_km * per_km_rate
            
                    distance_charge = round(distance_charge, 2)
                    duration_charge = round(duration_min * per_min_rate, 2)
            
                    pre_surge_subtotal = round(base_fare + distance_charge + duration_charge, 2)
                    
                    surge_mult_base = cfg.get("surge_multiplier", 1.0)
                    is_auto = "auto" in vehicle_key or "bike" in vehicle_key
                    surge_mult_dynamic = self.compute_ola_surge(current_time, weather, is_auto) # reuse ola surge loosely
                    surge_mult = surge_mult_base * surge_mult_dynamic
                    surge_amount = round(pre_surge_subtotal * (surge_mult - 1.0), 2)
                    
                    night_cfg = cfg.get("night_charge")
                    night_active = False
                    night_mult = 1.0
                    if night_cfg and night_cfg.get("enabled", False):
                        night_active = self.is_night(current_time)
                        if night_active:
                            night_mult = night_cfg.get("multiplier", 1.0)
                    
                    night_amount = round((pre_surge_subtotal + surge_amount) * (night_mult - 1.0), 2)
                    booking_fee = cfg.get("booking_fee", 0.0)
            
                    raw_total = round(pre_surge_subtotal + surge_amount + night_amount + booking_fee, 2)
                    min_fare = cfg.get("min_fare", 0.0)
                    estimate = round(max(raw_total, min_fare))
                    buf = cfg.get("fare_range_buffer", 10)
            
                    results.append({
                        "vehicle":       cfg["name"],
                        "description":   cfg.get("description", ""),
                        "capacity":      cfg.get("capacity", 4),
                        "icon":          cfg.get("icon", "🚗"),
                        "distance_km":   distance_km,
                        "duration_min":  duration_min,
                        "fare_estimate": estimate,
                        "fare_min":      estimate,
                        "fare_max":      estimate + buf,
                        "fare_display":  f"Rs. {estimate} - Rs. {estimate + buf}",
                        "is_night":      night_active,
                        "surge":         round(surge_mult, 2),
                        "vtype":         cfg.get("vtype", "")
                    })

        return sorted(results, key=lambda x: x["fare_min"])
