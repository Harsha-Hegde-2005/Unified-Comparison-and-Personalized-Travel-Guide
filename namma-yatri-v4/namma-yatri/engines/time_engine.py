from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class TimeEngine:
    """
    Estimates ride duration for Namma Yatri trips in Bengaluru.

    OSRM gives free-flow driving time (zero traffic, speed-limit speed).
    Bengaluru's real-world traffic requires distance-aware multipliers.

    Calibrated from 2 real Namma Yatri trips (Apr 2026):
        13.5 km: OSRM=18 min, App=58 min  -> peak multiplier = 3.2x
        21.2 km: OSRM=23 min, App=48 min  -> peak multiplier = 2.1x

    Shorter trips suffer more from signals, lane changes, local congestion.
    Longer trips use more flyovers/highways so the multiplier drops.
    All times evaluated in IST to avoid UTC confusion.
    """

    # Distance bands (km) -> peak multiplier
    # Derived from real trip calibration above
    DISTANCE_BANDS = [
        (0,   10,  3.5),   # <10 km  : dense city, many signals
        (10,  18,  3.2),   # 10-18km : mixed city roads
        (18,  30,  2.1),   # 18-30km : more flyovers/ring roads
        (30, 999,  1.8),   # >30 km  : significant highway stretches
    ]

    # Off-peak and late-night scale down from the peak multiplier
    TIME_LEVEL_SCALE = {
        "peak":       1.0,   # baseline (calibrated values above are for peak)
        "moderate":   0.75,  # ~25% faster than peak
        "off_peak":   0.55,  # midday — still congested but much better
        "late_night": 0.35,  # roads are mostly clear
    }

    PEAK_WINDOWS     = [(8.0, 10.5), (17.5, 21.0)]
    MODERATE_WINDOWS = [(7.0, 8.0),  (10.5, 12.0), (16.0, 17.5)]
    LATE_NIGHT_WINDOWS = [(23.0, 24.0), (0.0, 5.0)]

    def get_traffic_level(self, current_time: datetime = None) -> str:
        """Returns: 'peak', 'moderate', 'off_peak', or 'late_night'."""
        if current_time is None:
            current_time = datetime.now(IST)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=IST)

        t = current_time.hour + current_time.minute / 60

        for s, e in self.LATE_NIGHT_WINDOWS:
            if s <= t < e:
                return "late_night"
        for s, e in self.PEAK_WINDOWS:
            if s <= t < e:
                return "peak"
        for s, e in self.MODERATE_WINDOWS:
            if s <= t < e:
                return "moderate"
        return "off_peak"

    def _peak_multiplier(self, distance_km: float) -> float:
        """Returns the peak-hour multiplier for a given distance."""
        for low, high, mult in self.DISTANCE_BANDS:
            if low <= distance_km < high:
                return mult
        return 1.8

    def estimate_duration(self, osrm_duration_min: int,
                          distance_km: float = 0,
                          current_time: datetime = None) -> dict:
        """
        Apply distance-aware, traffic-calibrated multiplier to OSRM duration.

        Args:
            osrm_duration_min: Raw driving time from OSRM (zero-traffic)
            distance_km:       Trip distance — used to pick the right multiplier
            current_time:      Optional datetime (defaults to now in IST)

        Returns:
            {
                "minutes":         58,
                "text":            "~58 mins",
                "traffic_level":   "peak",
                "osrm_base_min":   18,
                "multiplier_used": 3.2
            }
        """
        traffic_level  = self.get_traffic_level(current_time)
        peak_mult      = self._peak_multiplier(distance_km)
        time_scale     = self.TIME_LEVEL_SCALE[traffic_level]
        multiplier     = round(peak_mult * time_scale, 2)

        adjusted_min = round(osrm_duration_min * multiplier)

        if adjusted_min >= 60:
            hours = adjusted_min // 60
            mins  = adjusted_min % 60
            text  = f"~{hours} hr {mins} mins"
        else:
            text = f"~{adjusted_min} mins"

        return {
            "minutes":         adjusted_min,
            "text":            text,
            "traffic_level":   traffic_level,
            "osrm_base_min":   osrm_duration_min,
            "multiplier_used": multiplier
        }


# ── Accuracy test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = TimeEngine()

    test_cases = [
        ("13.5km, OSRM=18min, App=58min", 18, 13.5, 58),
        ("21.2km, OSRM=23min, App=48min", 23, 21.2, 48),
    ]

    print("Time estimate accuracy (peak hours):\n")
    for label, osrm, dist, app_min in test_cases:
        peak_time = datetime.now(IST).replace(hour=9, minute=0)
        result    = engine.estimate_duration(osrm, dist, peak_time)
        match     = "✓" if abs(result["minutes"] - app_min) <= 5 else f"✗ (off by {result['minutes']-app_min})"
        print(f"  {label}")
        print(f"    Estimated: {result['text']}  |  App: ~{app_min} mins  |  {match}")
        print(f"    Multiplier: {result['multiplier_used']}x\n")
