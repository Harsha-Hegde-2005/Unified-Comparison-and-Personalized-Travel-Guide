import csv
import os
from datetime import datetime


class FareEngine:
    def __init__(self, fare_matrix_path=None):

        if fare_matrix_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fare_matrix_path = os.path.abspath(
                os.path.join(base_dir, "..", "..", "..", "database", "metro", "fare_matrix.csv")
            )

        self.slabs = self._load_fare_slabs(fare_matrix_path)

    def _load_fare_slabs(self, path):
        """
        Loads fare slabs (distance-based, BMRCL 2026):
        [
          { "min_km": 0, "max_km": 2, "fare": 11 },
          ...
        ]
        """
        slabs = []

        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                slabs.append({
                    "min_km": float(row["min_km"]),
                    "max_km": float(row["max_km"]),
                    "fare": float(row["fare_rs"])
                })

        return slabs

    def _is_peak(self):
        """
        Peak hours:
        07:30–10:30 and 16:30–19:30
        """
        now = datetime.now()
        time_val = now.hour + now.minute / 60

        return (
            7.5 <= time_val <= 10.5 or
            16.5 <= time_val <= 19.5
        )

    def get_fare(self, distance_km: float):
        """
        Returns token fare and smart card fare
        based on distance_km (BMRCL 2026 official distance-based slabs)
        """
        for slab in self.slabs:
            if slab["min_km"] <= distance_km <= slab["max_km"]:
                token_fare = slab["fare"]

                # Smart card discount
                if self._is_peak():
                    smart_card_fare = round(token_fare * 0.95, 2)  # 5% off
                else:
                    smart_card_fare = round(token_fare * 0.90, 2)  # 10% off

                return {
                    "token": token_fare,
                    "smart_card": smart_card_fare
                }

        # Fallback: max fare
        return {
            "token": 95.0,
            "smart_card": round(95.0 * 0.90, 2)
        }

if __name__ == "__main__":
    engine = FareEngine()

    fare = engine.get_fare(21.8)  # e.g. S4 Fragrance -> Konanakunte Cross
    print(fare)
