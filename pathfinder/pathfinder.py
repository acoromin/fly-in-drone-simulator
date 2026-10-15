from collections import deque
from graph.hub import Hub
from graph.connection import Connection
import heapq

class Pathfinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def find_route_bfs(self) -> list[Hub]:
        for hub in self.graph:
            if hub.type == "start_hub":
                start = hub
            elif hub.type == "end_hub":
                end = hub
        queue = deque([start])
        visited = [start]
        parents = {}

        while queue:
            current = queue.popleft()
            for connection in self.graph[current]:
                if current == connection.target:
                    neighbour = connection.source
                else:
                    neighbour = connection.target
                if neighbour not in visited:
                    visited.append(neighbour)
                    queue.append(neighbour)
                    parents[neighbour] = current
            if end in parents:
                break
        path: list[Hub] = []
        current = end
        while current != start:
            path.append(current)
            current = parents[current]
        path.append(current)
        path.reverse()
        return path

    def find_route_dijkstra(self) -> list[Hub]:
        start = self.graph.start_hub
        end = self.graph.end_hub
        distances = {
                start: 0,
                }
        visited = set()
        parents = {}
        queue = [(0, start)]
        
        while queue:
            current_cost, current = heapq.heappop(queue)
            if current in visited:
                continue
            if current == end:
                visited.add(current)
                break
            connections = self.graph.adjacency[current]
            for connection in connections:
                next_hub = connection.get_other_hub(current)
                if next_hub.is_blocked():
                    continue
                new_cost = next_hub.get_zone_cost() + current_cost
                if next_hub not in distances or new_cost < distances[next_hub]:
                    parents[next_hub] = current
                    distances[next_hub] = new_cost
                    heapq.heappush(queue, (new_cost, next_hub))
            visited.add(current)

        path = []
        current = end
        while current != start:
            path.append(current)
            current = parents[current]
        path.append(current)
        path.reverse()
        return path



        
