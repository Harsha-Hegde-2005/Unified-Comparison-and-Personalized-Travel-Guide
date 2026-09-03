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
        Loads fare slabs:
        [
          { "min": 0, "max": 2, "fare": 10 },
          ...
        ]
        """
        slabs = []

        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                slabs.append({
                    "min": int(row["min_stations"]),
                    "max": int(row["max_stations"]),
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

    def get_fare(self, stations_crossed):
        """
        Returns token fare and smart card fare
        based on stations crossed
        """
        for slab in self.slabs:
            if slab["min"] <= stations_crossed <= slab["max"]:
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

        raise ValueError(
            f"No fare slab found for {stations_crossed} stations"
        )

if __name__ == "__main__":
    engine = FareEngine()

    fare = engine.get_fare(24)
    print(fare)


