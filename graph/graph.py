from .hub import Hub
from .connection import Connection
from parser.models import MapModel

class Graph:
    def __init__(self, map_model: MapModel) -> None:
        self.map_model = map_model
        self.hubs: dict[str, Hub] = {}
        self.connections: list[Connection] = []
        self.adjacency: dict[Hub, list[Connection]] = {}
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None

    def _create_hubs(self) -> None:
        for node_model in self.map_model.nodes:
            self.hubs[node_model.name] = Hub(
                    node_model.type,
                    node_model.name,
                    node_model.x,
                    node_model.y,
                    node_model.zone,
                    node_model.color,
                    node_model.max_drones,
                    )
            if node_model.type == "start_hub":
                self.start_hub = self.hubs[node_model.name]
            elif node_model.type == "end_hub":
                self.end_hub = self.hubs[node_model.name]

    def _create_connections(self) -> None:
        for connection_model in self.map_model.connections:
            source = self.hubs[connection_model.source]
            target = self.hubs[connection_model.target]
            self.connections.append(Connection(
                source,
                target,
                connection_model.max_link_capacity
                ))

    def get_connection(
            self,
            hub_a: Hub,
            hub_b: Hub
            ) -> Connection | None:

        for connection in self.connections:
            if (
                    connection.source == hub_a and
                    connection.target == hub_b
                    ):
                return connection

            if (
                    connection.source == hub_b and
                    connection.target == hub_a
                    ):
                return connection

        return None

    def generate_graph(self) -> None:
        self._create_hubs()
        self._create_connections()
        for hub in self.hubs.values():
            self.adjacency[hub] = []
        for connection in self.connections:
            self.adjacency[connection.source].append(connection)
            self.adjacency[connection.target].append(connection)
