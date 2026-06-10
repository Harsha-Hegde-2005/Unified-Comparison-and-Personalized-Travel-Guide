from dataclasses import dataclass
from typing import Optional


@dataclass
class StopLocation:
    name: str
    latitude: float
    longitude: float
    mode: str  # "BMTC" | "Metro"
    stop_id: Optional[str] = None

    def to_dict(self):
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "mode": self.mode,
            "stop_id": self.stop_id,
        }
