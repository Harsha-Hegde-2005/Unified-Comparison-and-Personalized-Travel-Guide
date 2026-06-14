class DistanceEngine:
    def __init__(self, station_lookup, lines):
        """
        station_lookup:
          {
            station_name: {
              line: "Green",
              index: 0
            }
          }

        lines:
          {
            "Green": [...],
            "Purple": [...],
            "Yellow": [...]
          }
        """
        self.stations = station_lookup
        self.lines = lines

    def enrich_leg(self, leg):
        from_station = leg["from"]
        to_station = leg["to"]
        line = leg["line"]

        from_index = self.lines[line].index(from_station)
        to_index = self.lines[line].index(to_station)

        stations_crossed = abs(to_index - from_index)

        if to_index > from_index:
            direction = self.lines[line][-1]
        else:
            direction = self.lines[line][0]

        return {
            **leg,
            "stations_crossed": stations_crossed,
            "direction": direction
        }

    
    def enrich_route(self, route):
        enriched_legs = []

        for leg in route["legs"]:
            enriched_legs.append(self.enrich_leg(leg))

        return {
            "legs": enriched_legs,
            "interchanges": route["interchanges"]
        }

if __name__ == "__main__":
    from routing_engine import RoutingEngine

    routing_engine = RoutingEngine()
    route = routing_engine.get_route("Peenya", "Kudlu Gate")

    distance_engine = DistanceEngine(
        routing_engine.stations,
        routing_engine.lines
    )

    enriched_route = distance_engine.enrich_route(route)
    print(enriched_route)

