import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import math

IST = ZoneInfo("Asia/Kolkata")

def round2(n: float) -> float:
    return round(n, 2)

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
        mtime = os.path.getmtime(self._fare_config_path) if os.path.exists(self._fare_config_path) else None
        if mtime != self._fare_config_mtime:
            if os.path.exists(self._fare_config_path):
                with open(self._fare_config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self.providers = self.config.get("providers", {})
            else:
                self.config = {"providers": {}}
                self.providers = {}
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

    def get_all_fares_for_provider(self, provider_key: str, distance_km: float,
                                   duration_min: float, current_time: datetime = None,
                                   weather: str = "clear", ignore_constraints: bool = False) -> list:
        self._reload_config()
        provider_key = provider_key.lower().replace("-", "_")
        if provider_key == "nammayatri":
            provider_key = "namma_yatri"

        results = []
        if provider_key not in self.providers:
            return results

        provider_cfg = self.providers[provider_key]
        vehicles = provider_cfg.get("vehicles", {})

        for vehicle_key, cfg in vehicles.items():
            v_lower = vehicle_key.lower()
            # Constraints
            if not ignore_constraints:
                if ("bike" in v_lower or "scooty" in v_lower or "moto" in v_lower) and distance_km > 15.0:
                    continue
                if "auto" in v_lower and distance_km > 25.0:
                    continue

            is_auto = "auto" in v_lower or "bike" in v_lower or "scooty" in v_lower or "moto" in v_lower

            # 1. Base fare, distance, and rates
            base_fare = cfg.get("base_fare", 0.0)
            base_dist = cfg.get("base_dist", 0.0)
            per_km_rate = cfg.get("per_km", 0.0)
            per_min_rate = cfg.get("per_min", 0.0)

            # 2. Distance and duration charges
            billable_km = max(0.0, distance_km - base_dist)
            distance_charge = round(billable_km * per_km_rate, 2)
            duration_charge = round(duration_min * per_min_rate, 2)
            pre_surge_subtotal = round(base_fare + distance_charge + duration_charge, 2)

            # 3. Dynamic Surge Multiplier
            if current_time is None:
                current_time = datetime.now(IST)
            elif current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=IST)
            else:
                current_time = current_time.astimezone(IST)

            time_minutes = current_time.hour * 60 + current_time.minute
            delta_time = 0.0
            if is_auto:
                if time_minutes >= (22 * 60) or time_minutes < (5 * 60):
                    delta_time = 0.50
            else:
                if (8 * 60 + 30) <= time_minutes <= (10 * 60 + 30):
                    delta_time = 0.25
                elif (17 * 60 + 30) <= time_minutes <= (20 * 60 + 30):
                    delta_time = 0.30
                elif time_minutes >= (22 * 60) or time_minutes < (5 * 60):
                    delta_time = 0.50

            delta_weather = 0.0
            weather_lower = weather.lower()
            if "light rain" in weather_lower or "drizzle" in weather_lower:
                delta_weather = 0.15
            elif "heavy rain" in weather_lower or "thunderstorm" in weather_lower:
                delta_weather = 0.40
            elif "storm" in weather_lower or "flood" in weather_lower:
                delta_weather = 0.75

            surge_mult = 1.0 + delta_time + delta_weather
            surge_amount = round(pre_surge_subtotal * (surge_mult - 1.0), 2)

            # 4. Night Surcharge
            night_cfg = cfg.get("night_charge")
            night_active = False
            night_mult = 1.0
            if night_cfg and night_cfg.get("enabled", False):
                start_hour = night_cfg.get("start_hour", 22)
                end_hour = night_cfg.get("end_hour", 5)
                hour = current_time.hour
                if start_hour == end_hour:
                    night_active = False
                elif start_hour < end_hour:
                    night_active = start_hour <= hour < end_hour
                else:
                    night_active = hour >= start_hour or hour < end_hour

                if night_active:
                    night_mult = night_cfg.get("multiplier", 1.0)

            night_amount = round((pre_surge_subtotal + surge_amount) * (night_mult - 1.0), 2)

            # 5. Booking Fee
            booking_fee = cfg.get("booking_fee", 0.0)

            # 6. Long Distance Surcharge
            long_distance_cfg = cfg.get("long_distance")
            long_distance_charge = 0.0
            if long_distance_cfg:
                threshold_km = long_distance_cfg.get("threshold_km", 0.0)
                if distance_km > threshold_km:
                    long_distance_charge = long_distance_cfg.get("surcharge", 0.0)

            # 7. Total estimate
            raw_total = round(pre_surge_subtotal + surge_amount + night_amount + booking_fee + long_distance_charge, 2)
            min_fare = cfg.get("min_fare", 0.0)
            estimate = round(max(raw_total, min_fare))

            # Range buffers for UI display
            if provider_key == "ola":
                rangeDelta = max(5, round(estimate * 0.025))
                fareMin = max(min_fare, math.floor((estimate - rangeDelta) / 5) * 5)
                fareMax = math.ceil((estimate + rangeDelta) / 5) * 5
            elif provider_key == "uber":
                fareMin = round(estimate * 0.97)
                fareMax = round(estimate * 1.03)
            elif provider_key == "rapido":
                rangeDelta = max(5, round(estimate * 0.03))
                fareMin = max(min_fare, math.floor((estimate - rangeDelta) / 5) * 5)
                fareMax = math.ceil((estimate + rangeDelta) / 5) * 5
            else:
                if "auto" in v_lower:
                    fareMin = round(estimate - 10)
                    fareMax = round(estimate)
                else:
                    fareMin = round(estimate)
                    fareMax = round(estimate + 10)

            results.append({
                "vehicle":       cfg.get("name", vehicle_key),
                "description":   cfg.get("description", ""),
                "capacity":      cfg.get("capacity", 4),
                "icon":          cfg.get("icon", "🚗"),
                "distance_km":   distance_km,
                "duration_min":  duration_min,
                "fare_estimate": estimate,
                "fare_min":      int(fareMin),
                "fare_max":      int(fareMax),
                "fare_display":  f"Rs. {int(fareMin)} - Rs. {int(fareMax)}",
                "is_night":      self.is_night(current_time),
                "surge":         round(surge_mult, 2),
                "vtype":         cfg.get("vtype", vehicle_key)
            })

        return sorted(results, key=lambda x: x["fare_min"])

    def get_all_fares(self, distance_km: float) -> list:
        # Default provider is namma_yatri for legacy usage
        return self.get_all_fares_for_provider("namma_yatri", distance_km, distance_km / 30 * 60, None, "clear")

    def get_fare(self, provider_key: str, vehicle_key: str, distance_km: float,
                 duration_min: float, current_time: datetime = None,
                 weather: str = "clear") -> dict:
        # Support legacy 2-argument signature: get_fare(distance_km, vehicle_type)
        if isinstance(provider_key, (int, float)):
            distance_km = float(provider_key)
            vehicle_type = vehicle_key
            fares = self.get_all_fares_for_provider("namma_yatri", distance_km, distance_km / 30 * 60, None, "clear", ignore_constraints=True)
            for f in fares:
                if f["vtype"].lower().replace("-", "_") == vehicle_type.lower().replace("-", "_"):
                    return f
            return fares[0] if fares else {}

        # Standard call: get_fare(provider_key, vehicle_key, distance_km, duration_min, current_time, weather)
        fares = self.get_all_fares_for_provider(provider_key, distance_km, duration_min, current_time, weather, ignore_constraints=True)
        
        target = vehicle_key.lower().replace("-", "_")
        prefix = provider_key.lower() + "_"
        if target.startswith(prefix):
            target = target[len(prefix):]
            
        rapido_special_map = {
            "bike": "bike_direct",
            "scooty": "scooty_direct",
            "cab": "cab_non_ac",
            "cab_ac": "cab_ac"
        }
        if provider_key.lower() == "rapido" and target in rapido_special_map:
            target = rapido_special_map[target]

        for f in fares:
            f_vtype = f["vtype"].lower().replace("-", "_")
            if f_vtype == target:
                return f
                
        for f in fares:
            f_name = f["vehicle"].lower().replace("-", "_").replace(" ", "_")
            if target in f_name or f_name in target:
                return f
                
        return fares[0] if fares else {}


