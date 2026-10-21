from .hub import Hub
from .connection import Connection
from parser.models import MapModel


class Graph:
    """Build the fixed map topology from validated map data."""

    def __init__(self, map_model: MapModel) -> None:
        """Create hubs, connections, and adjacency lists."""
        self.hubs: dict[str, Hub] = {}
        self.connections: list[Connection] = []
        self.adjacency: dict[Hub, list[Connection]] = {}
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None
        self._generate_graph(map_model)

    def _create_hubs(self, map_model: MapModel) -> None:
        """Create hub objects and identify the start and end hubs."""
        for node_model in map_model.nodes:
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

    def _create_connections(self, map_model: MapModel) -> None:
        """Connect the existing hub objects using validated edges."""
        for connection_model in map_model.connections:
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
        """Return the link between ``hub_a`` and ``hub_b``, or ``None``."""

        for connection in self.adjacency[hub_a]:
            if hub_b == connection.get_other_hub(hub_a):
                return connection
        return None

    def _generate_graph(self, map_model: MapModel) -> None:
        """Populate each hub's list of incident connections."""
        self._create_hubs(map_model)
        self._create_connections(map_model)
        for hub in self.hubs.values():
            self.adjacency[hub] = []
        for connection in self.connections:
            self.adjacency[connection.source].append(connection)
            self.adjacency[connection.target].append(connection)
