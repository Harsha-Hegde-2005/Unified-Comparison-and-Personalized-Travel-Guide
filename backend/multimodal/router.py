"""Multimodal journey router coordinating BMTC and Metro."""

from typing import List, Optional, Tuple
from shared.interfaces.journey_plan import JourneyResult
from adapters.bmtc_adapter import BMTCAdapter
from adapters.metro_adapter import MetroAdapter
from multimodal.interchange_matcher import InterchangeMatcher
from multimodal.config import (
    INTERCHANGE_POINTS,
    TRANSFER_BUFFER_MINUTES,
    MAX_MULTIMODAL_OPTIONS,
)


class MultimodalRouter:
    """Orchestrates multimodal journeys combining BMTC and Metro."""

    def __init__(self):
        self.bmtc = BMTCAdapter()
        self.metro = MetroAdapter()

        # Load BMTC stops with coordinates for interchange matching
        try:
            import sys
            import os
            sys.path.insert(
                0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modes", "bmtc"))
            )
            from core.loader import stops_df

            self.bmtc_stops = [
                {
                    "name": row.get("stop_name", row.get("stop_norm", "")),
                    "latitude": row.get("latitude", 0),
                    "longitude": row.get("longitude", 0),
                }
                for _, row in stops_df.iterrows()
            ]
        except Exception as e:
            print(f"Warning: Could not load BMTC stops: {e}")
            self.bmtc_stops = []

        self.matcher = InterchangeMatcher(self.bmtc_stops)

    def plan_multimodal(
        self, source: str, destination: str, max_options: int = MAX_MULTIMODAL_OPTIONS
    ) -> List[JourneyResult]:
        """Plan multimodal journeys combining BMTC and Metro.

        Strategy: Try different BMTC-Metro-BMTC combinations and rank by fare/time.

        Args:
            source: Starting BMTC stop
            destination: Ending BMTC stop
            max_options: Maximum number of options to return

        Returns:
            List of multimodal journey options, sorted by total fare
        """
        options = []

        # Get all interchange points that could help
        for interchange_name, interchange_info in INTERCHANGE_POINTS.items():
            try:
                # Step 1: BMTC from source to metro access point
                bmtc_to_metro_stop = None
                for nearby in interchange_info.get("nearby_bmtc_stops", []):
                    # Try to find BMTC route to this stop
                    try:
                        bmtc_leg1 = self.bmtc.plan(source, nearby)
                        bmtc_to_metro_stop = nearby
                        break
                    except:
                        continue

                if not bmtc_to_metro_stop:
                    continue

                # Get metro station name
                metro_entry = interchange_name

                # Step 2: Metro from entry to exit
                try:
                    # Find a good exit metro station
                    metro_exit = self._find_best_metro_exit(
                        destination, metro_entry
                    )
                    if not metro_exit:
                        continue

                    metro_leg = self.metro.plan(metro_entry, metro_exit)
                except:
                    continue

                # Step 3: BMTC from metro exit to destination
                bmtc_exit_stop = None
                metro_exit_nearby = self.matcher.find_bmtc_stops_near_metro_station(
                    metro_exit
                )
                for nearby in metro_exit_nearby:
                    try:
                        bmtc_leg2 = self.bmtc.plan(nearby, destination)
                        bmtc_exit_stop = nearby
                        break
                    except:
                        continue

                if not bmtc_exit_stop:
                    continue

                # Combine all three legs
                combined = self._combine_journeys(
                    bmtc_leg1, metro_leg, bmtc_leg2
                )
                if combined:
                    options.append(combined)

            except Exception as e:
                # Skip this interchange if any step fails
                continue

        # Sort by total fare, then by total time
        options.sort(
            key=lambda x: (
                x.total_fare if isinstance(x.total_fare, (int, float)) else x.total_fare.get("token", float("inf")),
                x.total_time,
            )
        )

        return options[:max_options]

    def _find_best_metro_exit(self, bmtc_dest: str, metro_entry: str) -> Optional[str]:
        """Find best metro exit station to reach BMTC destination.

        Args:
            bmtc_dest: Destination BMTC stop
            metro_entry: Metro entry point

        Returns:
            Best metro exit station or None
        """
        # Find metro station closest to destination
        best_exit = None
        min_distance = float("inf")

        for station_name, point in INTERCHANGE_POINTS.items():
            # Skip entry point, look for different line if possible
            if station_name == metro_entry:
                continue

            # Check if this station has nearby BMTC stops
            nearby = self.matcher.find_bmtc_stops_near_metro_station(station_name)
            if nearby:
                # Try to reach destination from these stops
                for stop in nearby:
                    try:
                        self.bmtc.plan(stop, bmtc_dest)
                        # If we can reach, this is viable
                        best_exit = station_name
                        return best_exit
                    except:
                        continue

        return best_exit

    def _combine_journeys(
        self,
        leg1_bmtc: JourneyResult,
        leg2_metro: JourneyResult,
        leg3_bmtc: JourneyResult,
    ) -> Optional[JourneyResult]:
        """Combine three legs (BMTC, Metro, BMTC) into one multimodal journey.

        Args:
            leg1_bmtc: BMTC leg to metro entry
            leg2_metro: Metro leg
            leg3_bmtc: BMTC leg from metro exit

        Returns:
            Combined JourneyResult or None if invalid
        """
        # Combine all legs
        combined_legs = leg1_bmtc.legs + leg2_metro.legs + leg3_bmtc.legs

        # Calculate total fare
        fare1 = leg1_bmtc.total_fare if isinstance(leg1_bmtc.total_fare, (int, float)) else 0
        fare2 = leg2_metro.total_fare
        if isinstance(fare2, dict):
            fare2 = fare2.get("token", 0)
        fare3 = leg3_bmtc.total_fare if isinstance(leg3_bmtc.total_fare, (int, float)) else 0
        total_fare = int(fare1 + fare2 + fare3)

        # Calculate total time (add transfer buffers)
        total_time = (
            leg1_bmtc.total_time
            + TRANSFER_BUFFER_MINUTES
            + leg2_metro.total_time
            + TRANSFER_BUFFER_MINUTES
            + leg3_bmtc.total_time
        )

        # Total transfers = sum of all transfers
        total_transfers = (
            leg1_bmtc.transfers + 1 + leg2_metro.transfers + 1 + leg3_bmtc.transfers
        )

        # Get source and destination
        source = leg1_bmtc.source
        destination = leg3_bmtc.destination

        return JourneyResult(
            mode="Multimodal",
            source=source,
            destination=destination,
            total_fare=total_fare,
            total_time=total_time,
            transfers=total_transfers,
            legs=combined_legs,
            raw_output={
                "leg1_bmtc": leg1_bmtc.to_dict(),
                "leg2_metro": leg2_metro.to_dict(),
                "leg3_bmtc": leg3_bmtc.to_dict(),
            },
        )
