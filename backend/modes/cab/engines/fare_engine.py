import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class FareEngine:
    """
    Computes calibrated ride fares for Namma Yatri, Uber, Ola, and Rapido.
    Incorporates advanced calculations matching the improved JS fareCalculator:
      - billable distance beyond included Km
      - waiting time charge beyond free waiting minutes
      - surge multiplier applied to pre-surge subtotal
      - night surcharge multiplier applied to (subtotal + surge)
      - flat booking fee
      - flat long-distance surcharge threshold
    Config version: 2026-07-13-v3 (Rapido long-distance surcharge added)
    """

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
        """Load (or hot-reload) fare_config.json from disk."""
        mtime = os.path.getmtime(self._fare_config_path)
        if mtime != self._fare_config_mtime:
            with open(self._fare_config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.providers = self.config["providers"]
            self._fare_config_mtime = mtime

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

    def is_night(self, current_time: datetime = None, start_hour: int = 22, end_hour: int = 5) -> bool:
        """Return True if current time is within the night surcharge window."""
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        else:
            current_time = current_time.astimezone(IST)
        hour = current_time.hour
        if start_hour == end_hour:
            return False
        if start_hour < end_hour:
            return start_hour <= hour < end_hour
        # window wraps past midnight
        return hour >= start_hour or hour < end_hour

    def get_fare(self, provider_key: str, vehicle_key: str, distance_km: float,
                 duration_min: float, current_time: datetime = None, weather: str = "clear",
                 waiting_min: float = 0.0) -> dict:
        self._reload_config()
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

        # 1. Base Charge, Distance Charge, Duration Charge, Waiting Charge
        base_fare = cfg.get("base_fare", 0.0)
        base_dist = cfg.get("base_dist", 0.0)
        per_km_rate = cfg.get("per_km", 0.0)
        per_min_rate = cfg.get("per_min", 0.0)

        billable_km = max(0.0, distance_km - base_dist)
        distance_charge = round(billable_km * per_km_rate, 2)
        duration_charge = round(duration_min * per_min_rate, 2)

        free_waiting_mins = cfg.get("free_waiting_mins", 0.0)
        waiting_charge_per_min = cfg.get("waiting_charge_per_min", 0.0)
        billable_waiting_min = max(0.0, waiting_min - free_waiting_mins)
        waiting_charge = round(billable_waiting_min * waiting_charge_per_min, 2)

        pre_surge_subtotal = round(base_fare + distance_charge + duration_charge + waiting_charge, 2)

        # 2. Surge Multiplier (dynamic calculation based on peaks and weather)
        is_auto = "auto" in vehicle_key or "bike" in vehicle_key
        surge_mult = self.get_surge_multiplier(current_time, weather, is_auto)
        surge_amount = round(pre_surge_subtotal * (surge_mult - 1.0), 2)

        # 3. Night Charge
        night_cfg = cfg.get("night_charge")
        night_active = False
        night_mult = 1.0
        if night_cfg and night_cfg.get("enabled", False):
            night_active = self.is_night(current_time, night_cfg.get("start_hour", 22), night_cfg.get("end_hour", 5))
            if night_active:
                night_mult = night_cfg.get("multiplier", 1.0)
        
        night_amount = round((pre_surge_subtotal + surge_amount) * (night_mult - 1.0), 2)

        # 4. Booking Fee
        booking_fee = cfg.get("booking_fee", 0.0)

        # 5. Long Distance Surcharge
        long_distance_cfg = cfg.get("long_distance")
        long_distance_charge = 0.0
        if long_distance_cfg:
            threshold_km = long_distance_cfg.get("threshold_km", 0.0)
            if distance_km > threshold_km:
                long_distance_charge = long_distance_cfg.get("surcharge", 0.0)

        # 6. Totals
        raw_total = round(pre_surge_subtotal + surge_amount + night_amount + booking_fee + long_distance_charge, 2)
        min_fare = cfg.get("min_fare", 0.0)
        estimate = max(raw_total, min_fare)
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
            "is_night":      night_active,
            "surge":         round(surge_mult, 2),
            "pet":           cfg.get("pet", False),
            "rental":        cfg.get("rental", False),
            "parcel":        cfg.get("parcel", False),
            "book_any":      cfg.get("book_any", False),
            "black":         cfg.get("black", False),
            "saver":         cfg.get("saver", False),
            "vtype":         cfg.get("vtype", "")
        }

    def get_all_fares_for_provider(self, provider_key: str, distance_km: float,
                                   duration_min: float, current_time: datetime = None,
                                   weather: str = "clear") -> list:
        self._reload_config()
        provider_key = provider_key.lower()
        if provider_key not in self.providers:
            raise ValueError(f"Unknown provider '{provider_key}'")

        vehicles = self.providers[provider_key]["vehicles"]
        results = []
        for v in vehicles:
            v_lower = v.lower()
            if ("bike" in v_lower or "scooty" in v_lower or "moto" in v_lower) and distance_km > 15.0:
                continue
            if "auto" in v_lower and distance_km > 25.0:
                continue
            try:
                results.append(self.get_fare(provider_key, v, distance_km, duration_min, current_time, weather))
            except Exception:
                pass

        return sorted(results, key=lambda x: x["fare_min"])