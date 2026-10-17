from collections import deque
from graph import Hub, Graph
import heapq

class Pathfinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def find_route_dijkstra(self) -> list[Hub]:
        start = self.graph.start_hub
        end = self.graph.end_hub

        if start is None or end is None:
            return []

        distances = {start: 0,}
        visited = set()
        parents = {}
        counter = 0
        queue = [(0, counter, start)]

        while queue:
            current_cost, _, current = heapq.heappop(queue)
            if current in visited:
                continue
            if current == end:
                break
            visited.add(current)

            for connection in self.graph.adjacency[current]:
                next_hub = connection.get_other_hub(current)

                if next_hub.is_blocked():
                    continue

                new_cost = current_cost + next_hub.get_zone_cost()

                if (
                    next_hub not in distances
                    or new_cost < distances[next_hub]
                ):
                    distances[next_hub] = new_cost
                    parents[next_hub] = current

                    counter += 1
                    heapq.heappush(
                        queue,
                        (new_cost, counter, next_hub)
                    )

        if end not in distances:
            return []
        path = []
        current = end
        while current != start:
            path.append(current)
            current = parents[current]

        path.append(start)
        path.reverse()

        return path

    
        
