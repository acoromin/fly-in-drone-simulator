from graph import Hub, Graph
from planner import Reservations
import heapq


class Pathfinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def find_route_dijkstra(self) -> list[Hub]:
        start = self.graph.start_hub
        end = self.graph.end_hub

        if start is None or end is None:
            return []
        distances = {start: 0}
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
                new_cost = current_cost + next_hub.get_entry_cost()
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

    def find_itinerary(
            self,
            reservations: Reservations,
            ) -> list[tuple[Hub, int]]:
        start = self.graph.start_hub
        end = self.graph.end_hub
        if start is None or end is None:
            return []
        visited = set()
        parents = {}
        initial_state = (start, 0)
        best: dict[tuple[Hub, int], int] = {initial_state: 0}
        counter = 0
        queue = [(0, 0, 1, counter, initial_state)]
        while queue:
            _, movements, _, _, current_state = heapq.heappop(queue)
            current_hub, current_turn = current_state
            if current_state in visited:
                continue
            visited.add(current_state)
            if current_hub == end:
                break
            for connection in self.graph.adjacency[current_hub]:
                next_hub = connection.get_other_hub(current_hub)
                if next_hub.is_blocked():
                    continue
                if not reservations.can_move(
                        connection, next_hub, current_turn
                        ):
                    continue
                arrival_turn = current_turn + next_hub.get_entry_cost()
                next_state = (next_hub, arrival_turn)
                next_movements = movements + 1

                if next_state in best:
                    if next_movements >= best[next_state]:
                        continue
                best[next_state] = next_movements
                parents[next_state] = current_state
                counter += 1
                priority = 0 if next_hub.zone == "priority" else 1
                heapq.heappush(
                    queue,
                    (
                        arrival_turn,
                        next_movements,
                        priority,
                        counter,
                        next_state
                    )
                )
            wait_turn = current_turn + 1
            if reservations.can_reserve_hub(current_hub, wait_turn):
                wait_state = (current_hub, wait_turn)
                if wait_state not in best or movements < best[wait_state]:
                    best[wait_state] = movements
                    parents[wait_state] = current_state
                    counter += 1
                    heapq.heappush(
                            queue,
                            (
                                wait_turn,
                                movements,
                                1,
                                counter,
                                wait_state
                            )
                    )
        path: list[tuple[Hub, int]] = []
        if current_hub != end:
            return path
        while current_state != initial_state:
            path.append(current_state)
            current_state = parents[current_state]
        path.append(initial_state)
        path.reverse()

        return path
