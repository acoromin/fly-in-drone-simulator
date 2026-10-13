from simulation.drone import Drone
from graph.graph import Graph
from graph.hub import Hub


class Simulation:
    def __init__(
            self,
            graph: Graph,
            nb_drones: int,
            ) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.drones: list[Drone] = []
        self._turn = 0
        self.resolver = MovemnentResolver(graph)

    def create_drones(self, path: list[Hub]) -> list[Drone]:
        for i in range(self.nb_drones):
            drone = Drone(i + 1, path)
            self.drones.append(drone)

        return self.drones

    def get_movement_proposals(self) -> list[dict]:
        proposals = []
        for drone in self.drones:
            if drone.delivered:
                continue
            proposals.append(drone.get_movement_info())

        return proposals

    def move_drones(self, proposals: list[dict]) -> None:
        for proposal in proposals:
            drone = proposal["drone"]
            drone.advance()

    def get_hub_occupancy(self) -> dict[Hub, int]:
        occupancy = {}
        for drone in self.drones:
            if drone.delivered:
                continue
            current_hub = drone.current_hub()
            if current_hub not in occupancy:
                occupancy[current_hub] = 1
            else:
                occupancy[current_hub] += 1

        return occupancy

    def get_next_hub_occupancy(self) -> dict[Hub, int]:
        occupancy = {}

        for drone in self.drones:
            if drone.delivered:
                continue
            next_hub = drone.next_hub()
            if next_hub not in occupancy:
                occupancy[next_hub] = 1
            else:
                occupancy[next_hub] += 1

        return occupancy

    def run_simulation(self) -> None:
        while not all(drone.delivered for drone in self.drones):
            proposals = self.get_movement_proposals()

            self.move_drones(proposals)
            valid_proposals = self.resolve_proposals(proposals)
            self._turn += 1
            for drone in self.drones:
                print(f"id{drone.id} name_hub{drone.current_hub().name}")
