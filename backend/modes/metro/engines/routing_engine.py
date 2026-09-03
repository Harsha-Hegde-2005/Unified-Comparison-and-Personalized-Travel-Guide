import json
import os
from collections import defaultdict, deque


class MetroGraph:
    """
    Graph representation of the metro network.
    Each station is a node, adjacent stations are edges.
    """
    def __init__(self, lines):
        self.graph = defaultdict(list)
        self._build_graph(lines)

    def _build_graph(self, lines):
        for line, stations in lines.items():
            for i in range(len(stations) - 1):
                a = stations[i]
                b = stations[i + 1]

                # Undirected edges
                self.graph[a].append(b)
                self.graph[b].append(a)

    def shortest_path(self, source, destination):
        """
        BFS to find shortest path (minimum station hops)
        """
        if source == destination:
            return [source]

        visited = set()
        queue = deque([[source]])

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == destination:
                return path

            if current not in visited:
                visited.add(current)
                for neighbor in self.graph[current]:
                    queue.append(path + [neighbor])

        return None


class RoutingEngine:
    def __init__(self, station_master_path=None):

        if station_master_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            station_master_path = os.path.abspath(
                os.path.join(base_dir, "..", "..", "..", "database", "metro", "station_master.json")
            )

        with open(station_master_path, "r", encoding="utf-8") as f:
            self.station_master = json.load(f)

        self.lines = self.station_master["lines"]
        self.stations = self._build_station_lookup()

    def _build_station_lookup(self):
        """
        Builds:
        {
          station_name: {
            line: "Green",
            index: 0
          }
        }
        (Index here is informational; real index is resolved per-line)
        """
        stations = {}

        for line, station_list in self.lines.items():
            for index, station in enumerate(station_list):
                if station not in stations:
                    stations[station] = {
                        "line": line,
                        "index": index
                    }

        return stations

    def _path_to_legs(self, path):
        """
        Converts station path into line-based legs
        """
        legs = []

        start = path[0]
        current_line = self.stations[start]["line"]

        for i in range(1, len(path)):
            prev = path[i - 1]
            curr = path[i]

            # Determine which line connects prev → curr
            possible_lines = [
                line for line, stations in self.lines.items()
                if prev in stations and curr in stations
                and abs(stations.index(prev) - stations.index(curr)) == 1
            ]

            if not possible_lines:
                raise Exception(f"No line connects {prev} → {curr}")

            line = possible_lines[0]

            if line != current_line:
                # Line change → close previous leg
                if legs:
                    legs[-1]["to"] = prev
                current_line = line
                legs.append({
                    "from": prev,
                    "to": curr,
                    "line": line
                })
            else:
                if not legs:
                    legs.append({
                        "from": start,
                        "to": curr,
                        "line": line
                    })
                else:
                    legs[-1]["to"] = curr

        return legs

    def get_route(self, source, destination):
        """
        Multi-interchange routing using BFS
        """
        if source not in self.stations:
            raise ValueError(f"Unknown source station: {source}")

        if destination not in self.stations:
            raise ValueError(f"Unknown destination station: {destination}")

        # Build metro graph
        graph = MetroGraph(self.lines)

        # Find shortest station path
        station_path = graph.shortest_path(source, destination)

        if not station_path:
            raise Exception("No route found")

        # Convert path to legs
        legs = self._path_to_legs(station_path)

        # Interchanges = start of every leg except first
        interchanges = [
            legs[i]["from"]
            for i in range(1, len(legs))
        ]

        return {
            "legs": legs,
            "interchanges": interchanges
        }


# =========================
# TEST
# =========================
if __name__ == "__main__":
    engine = RoutingEngine()

    # 🔥 Multi-interchange test
    route = engine.get_route("Whitefield", "Hosa Road")
    print(route)
