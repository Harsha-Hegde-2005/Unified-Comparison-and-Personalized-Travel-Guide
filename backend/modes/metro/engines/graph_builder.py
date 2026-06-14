from collections import defaultdict, deque


class MetroGraph:
    """
    Graph representation of the metro network.
    - Each station is a node
    - Each adjacent station is an undirected edge
    - Interchanges work automatically because stations
      appear in multiple lines
    """

    def __init__(self, lines):
        self.graph = defaultdict(list)
        self._build_graph(lines)

    def _build_graph(self, lines):
        """
        Builds adjacency list from line-wise station ordering
        """
        for stations in lines.values():
            for i in range(len(stations) - 1):
                a = stations[i]
                b = stations[i + 1]

                # Undirected edge
                self.graph[a].append(b)
                self.graph[b].append(a)

    def shortest_path(self, source, destination):
        """
        Breadth-First Search (BFS) to find the shortest path
        in terms of number of stations (minimum hops)
        """

        if source == destination:
            return [source]

        visited = set([source])
        queue = deque([[source]])

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == destination:
                return path

            for neighbor in self.graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        # No route found
        return None
