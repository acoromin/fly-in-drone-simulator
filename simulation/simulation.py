from graph import Graph, Hub, Connection
from simulation import Drone


class Simulation:
    def __init__(self, graph: Graph, drones: list[Drone]) -> None:
        self.graph = graph
        self.drones = drones
        self.turn = 0

    def is_finished(self) -> bool:
        return all(
                drone.is_delivered(self.turn) for drone in self.drones
                )

    def step(self) -> list[tuple[Drone, Hub | Connection]]:
        if self.is_finished():
            return []
        self.turn += 1
        movements: list[tuple[Drone, Hub | Connection]] = []
        for drone in self.drones:
            if drone.is_delivered(self.turn - 1):
                continue
            current_hub = drone.get_hub_at_turn(self.turn)
            if current_hub is not None:
                if current_hub is drone.get_hub_at_turn(self.turn - 1):
                    continue
                movements.append((drone, current_hub))
            else:
                current_connection = drone.get_connection_at_turn(
                    self.turn, self.graph
                    )
                if current_connection is None:
                    raise ValueError(
                            f"Drone {drone.id}: invalid connection at "
                            f"turn {self.turn}"
                            )
                movements.append((drone, current_connection))
        return movements
