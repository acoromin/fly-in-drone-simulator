from graph import Graph, Hub
from planner import Pathfinder, Reservations


class Planner:
    """Plan drones in order against a shared set of capacity reservations."""

    def __init__(self, graph: Graph) -> None:
        """Create a pathfinder and empty reservations for the graph."""
        self.graph = graph
        self.pathfinder = Pathfinder(graph)
        self.reservations = Reservations()

    def plan_itineraries(
            self,
            nb_drones: int
            ) -> list[list[tuple[Hub, int]]]:
        """Return ``nb_drones`` reserved itineraries, or [] if unreachable.

        Sequential planning does not guarantee a globally optimal schedule.
        """
        if not self.pathfinder.find_route_dijkstra():
            return []
        itineraries = []
        for i in range(nb_drones):
            route = self.pathfinder.find_itinerary(self.reservations)
            self.reservations.reserve_itinerary(route, self.graph)
            itineraries.append(route)
        return itineraries
