from datetime import datetime

class TimeEngine:
    def __init__(self):
        # Average assumptions (minutes)
        self.avg_time_per_station = 2.0
        self.interchange_penalty = 5

    def is_peak(self, current_time):
        """
        Peak hours:
          Morning: 07:30 – 10:30
          Evening: 16:30 – 19:30
        """
        hour = current_time.hour
        minute = current_time.minute
        time_val = hour + minute / 60

        return (
            7.5 <= time_val <= 10.5 or
            16.5 <= time_val <= 19.5
        )

    def get_frequency(self, line, is_peak):
        if line in ["Green", "Purple"]:
            return 8 if is_peak else 10

        if line == "Yellow":
            return 15 if is_peak else 20

        return 10  # safe default

    def calculate_leg_time(self, leg, current_time):
        is_peak = self.is_peak(current_time)
        frequency = self.get_frequency(leg["line"], is_peak)

        waiting_time = frequency / 2
        running_time = leg["stations_crossed"] * self.avg_time_per_station

        return waiting_time + running_time

    def calculate_total_time(self, route):
        current_time = datetime.now()
        total_time = 0

        for leg in route["legs"]:
            total_time += self.calculate_leg_time(leg, current_time)

        # Add interchange penalties
        total_time += len(route["interchanges"]) * self.interchange_penalty

        return {
            "minutes": round(total_time),
            "text": f"~{int(total_time // 60)} hr {int(total_time % 60)} mins"
        }

if __name__ == "__main__":
    from routing_engine import RoutingEngine
    from distance_engine import DistanceEngine

    routing_engine = RoutingEngine()
    route = routing_engine.get_route("Ragigudda", "Hosa Road")

    distance_engine = DistanceEngine(
        routing_engine.stations,
        routing_engine.lines
    )
    enriched_route = distance_engine.enrich_route(route)

    time_engine = TimeEngine()
    time_estimate = time_engine.calculate_total_time(enriched_route)

    print(time_estimate)
