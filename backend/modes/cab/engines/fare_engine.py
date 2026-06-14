import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class FareEngine:
    """
    Computes Namma Yatri ride fares.

    Formula (calibrated from real Namma Yatri app, Apr 2026):

        estimate = effective_base + distance_km * per_km
        night    = estimate * night_surcharge_pct   [if 10PM–5AM IST]
        estimate = round(estimate + night)
        fare_min = estimate
        fare_max = estimate + fare_range_buffer  (default +10)

    Calibrated reference: 4.9km route
        Auto ₹111, Non-AC ₹161, AC ₹171, XL ₹236, XL Premium ₹264
    """

    def __init__(self, fare_config_path: str = None):
        if fare_config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fare_config_path = os.path.abspath(
                os.path.join(base_dir, "..", "..", "..", "database", "cab", "fare_config.json")
            )
        self.config      = self._load_config(fare_config_path)
        self.vehicles    = self.config["vehicles"]
        self.night_start = self.config["night_hours"]["start"]
        self.night_end   = self.config["night_hours"]["end"]
        self._ensure_effective_base()

    def _load_config(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ensure_effective_base(self):
        """
        Backward-compat: if config still uses old base_fare + base_dist_km style,
        compute effective_base automatically so both formats work.
        """
        for cfg in self.vehicles.values():
            if "effective_base" not in cfg:
                cfg["effective_base"] = (
                    cfg.get("base_fare", 0)
                    - cfg.get("base_dist_km", 0) * cfg.get("per_km", 0)
                )

    def is_night(self, current_time: datetime = None) -> bool:
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)
        hour = current_time.hour
        return hour >= self.night_start or hour < self.night_end

    def get_fare(self, distance_km: float, vehicle_type: str,
                 current_time: datetime = None) -> dict:
        vehicle_type = vehicle_type.lower()
        if vehicle_type not in self.vehicles:
            raise ValueError(
                f"Unknown vehicle type '{vehicle_type}'. "
                f"Valid options: {', '.join(self.vehicles.keys())}"
            )

        cfg   = self.vehicles[vehicle_type]
        night = self.is_night(current_time)

        estimate = max(
            cfg["effective_base"] + distance_km * cfg["per_km"],
            cfg["min_fare"]
        )
        if night:
            estimate += estimate * cfg["night_surcharge_pct"]

        estimate = round(estimate)
        buf      = cfg.get("fare_range_buffer", 10)

        return {
            "vehicle":       cfg["name"],
            "description":   cfg["description"],
            "capacity":      cfg["capacity"],
            "distance_km":   distance_km,
            "fare_estimate": estimate,
            "fare_min":      estimate,
            "fare_max":      estimate + buf,
            "fare_display":  f"Rs. {estimate} - Rs. {estimate + buf}",
            "is_night":      night
        }

    def get_all_fares(self, distance_km: float,
                      current_time: datetime = None) -> list:
        return sorted(
            [self.get_fare(distance_km, v, current_time) for v in self.vehicles],
            key=lambda x: x["fare_min"]
        )