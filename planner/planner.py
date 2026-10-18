from graph import Graph, Hub
from planner import Pathfinder, Reservations

class Planner:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.pathfinder = Pathfinder(graph)
        self.reservations = Reservations()

    def plan_itineraries(
            self,
            nb_drones: int
            ) -> list[list[tuple[Hub, int]]]:
        if not self.pathfinder.find_route_dijkstra():
            return []
        itineraries = []
        for i in range(nb_drones):
            route = self.pathfinder.find_itinerary(self.reservations)
            self.reservations.reserve_itinerary(route, self.graph)
            itineraries.append(route)
        return itineraries
