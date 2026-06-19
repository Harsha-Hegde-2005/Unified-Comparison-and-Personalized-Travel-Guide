import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class FareEngine:
    """
    Computes calibrated ride fares for Namma Yatri, Uber, Ola, and Rapido.

    Formula (calibrated from specification):
        subtotal = base_fare + max(0, distance_km - base_dist) * per_km + duration_min * per_min
        estimate = max(subtotal, min_fare) * surge_multiplier
        estimate = round(estimate)
    """

    def __init__(self, fare_config_path: str = None):
        if fare_config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fare_config_path = os.path.abspath(
                os.path.join(base_dir, "..", "..", "..", "database", "cab", "fare_config.json")
            )
        self.config = self._load_config(fare_config_path)
        self.providers = self.config["providers"]

    def _load_config(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_surge_multiplier(self, current_time: datetime = None, weather: str = "clear", is_auto: bool = False) -> float:
        """
        Compute dynamic surge multiplier based on peak hours and weather.
        S_surge = 1.0 + delta_time + delta_weather
        """
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        else:
            current_time = current_time.astimezone(IST)

        time_minutes = current_time.hour * 60 + current_time.minute

        # 1. Peak Commute Windows (delta_time)
        delta_time = 0.0
        if is_auto:
            # Autos only get late night flat surcharge (22:00 - 05:00)
            if time_minutes >= (22 * 60) or time_minutes < (5 * 60):
                delta_time = 0.50
        else:
            # Morning Peak (08:30 – 10:30 IST)
            if (8 * 60 + 30) <= time_minutes <= (10 * 60 + 30):
                delta_time = 0.25
            # Evening Peak (17:30 – 20:30 IST)
            elif (17 * 60 + 30) <= time_minutes <= (20 * 60 + 30):
                delta_time = 0.30
            # Late Night Surcharge (22:00 – 05:00 IST)
            elif time_minutes >= (22 * 60) or time_minutes < (5 * 60):
                delta_time = 0.50

        # 2. Weather Surcharges (delta_weather)
        delta_weather = 0.0
        weather_lower = weather.lower()
        if "light rain" in weather_lower or "drizzle" in weather_lower:
            delta_weather = 0.15
        elif "heavy rain" in weather_lower or "thunderstorm" in weather_lower:
            delta_weather = 0.40
        elif "storm" in weather_lower or "flood" in weather_lower:
            delta_weather = 0.75

        return 1.0 + delta_time + delta_weather

    def is_night(self, current_time: datetime = None) -> bool:
        """Return True if Late Night surcharge window (22:00 - 05:00 IST) is active."""
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        else:
            current_time = current_time.astimezone(IST)
        hour = current_time.hour
        return hour >= 22 or hour < 5

    def get_fare(self, provider_key: str, vehicle_key: str, distance_km: float,
                 duration_min: float, current_time: datetime = None, weather: str = "clear") -> dict:
        provider_key = provider_key.lower()
        vehicle_key = vehicle_key.lower()

        if provider_key not in self.providers:
            raise ValueError(
                f"Unknown provider '{provider_key}'. "
                f"Valid options: {', '.join(self.providers.keys())}"
            )

        provider_cfg = self.providers[provider_key]
        vehicles = provider_cfg["vehicles"]

        if vehicle_key not in vehicles:
            raise ValueError(
                f"Unknown vehicle type '{vehicle_key}' for provider '{provider_key}'. "
                f"Valid options: {', '.join(vehicles.keys())}"
            )

        cfg = vehicles[vehicle_key]
        is_auto = "auto" in vehicle_key or "bike" in vehicle_key
        surge_mult = self.get_surge_multiplier(current_time, weather, is_auto)
        night = self.is_night(current_time)

        # Base calculation
        distance_charge = max(0.0, distance_km - cfg["base_dist"]) * cfg["per_km"]
        duration_charge = duration_min * cfg["per_min"]
        subtotal = cfg["base_fare"] + distance_charge + duration_charge

        estimate = max(subtotal, cfg["min_fare"]) * surge_mult
        estimate = round(estimate)

        buf = cfg.get("fare_range_buffer", 10)

        return {
            "vehicle":       cfg["name"],
            "description":   cfg["description"],
            "capacity":      cfg["capacity"],
            "icon":          cfg.get("icon", "🚗"),
            "distance_km":   distance_km,
            "duration_min":  duration_min,
            "fare_estimate": estimate,
            "fare_min":      estimate,
            "fare_max":      estimate + buf,
            "fare_display":  f"Rs. {estimate} - Rs. {estimate + buf}",
            "is_night":      night,
            "surge":         round(surge_mult, 2)
        }

    def get_all_fares_for_provider(self, provider_key: str, distance_km: float,
                                   duration_min: float, current_time: datetime = None,
                                   weather: str = "clear") -> list:
        provider_key = provider_key.lower()
        if provider_key not in self.providers:
            raise ValueError(f"Unknown provider '{provider_key}'")

        vehicles = self.providers[provider_key]["vehicles"]
        return sorted(
            [self.get_fare(provider_key, v, distance_km, duration_min, current_time, weather) for v in vehicles],
            key=lambda x: x["fare_min"]
        )