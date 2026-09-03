from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any, Optional


@dataclass
class JourneyResult:
    mode: str  # "BMTC" | "Metro" | "Multimodal"
    source: str
    destination: str
    total_fare: float | dict  # Rs for BMTC, dict for Metro (token/card)
    total_time: int  # minutes
    transfers: int
    legs: list[dict] = field(default_factory=list)  # Unified leg format
    raw_output: dict = field(default_factory=dict)  # Original system output

    def to_dict(self):
        return {
            "mode": self.mode,
            "source": self.source,
            "destination": self.destination,
            "total_fare": self.total_fare,
            "total_time": self.total_time,
            "transfers": self.transfers,
            "legs": self.legs,
            "raw_output": self.raw_output,
        }


class BaseJourneyPlanner(ABC):
    @abstractmethod
    def plan(self, source: str, destination: str) -> JourneyResult:
        """Plan a journey between two stops/stations."""
        pass

    @abstractmethod
    def get_all_stops(self) -> list[str]:
        """Return list of all available stops/stations."""
        pass
