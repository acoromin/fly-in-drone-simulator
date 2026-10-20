from graph import Hub, Connection, Graph


class Reservations:
    def __init__(self) -> None:
        self.hubs: dict[int, dict[Hub, int]] = {}
        self.connections: dict[int, dict[Connection, int]] = {}

    def get_hub_reservations(self, hub: Hub, turn: int) -> int:
        if turn not in self.hubs or hub not in self.hubs[turn]:
            return 0
        return self.hubs[turn][hub]

    def reserve_hub(self, hub: Hub, turn: int) -> None:
        if turn not in self.hubs:
            self.hubs[turn] = {}
        current = self.get_hub_reservations(hub, turn)
        self.hubs[turn][hub] = current + 1

    def can_reserve_hub(self, hub: Hub, turn: int) -> bool:
        if hub.type == "start_hub" or hub.type == "end_hub":
            return True
        return hub.max_drones > self.get_hub_reservations(hub, turn)

    def get_connection_reservations(
            self,
            connection: Connection,
            turn: int,
            ) -> int:
        if (
                turn not in self.connections or
                connection not in self.connections[turn]
                ):
            return 0
        return self.connections[turn][connection]

    def reserve_connection(
            self,
            connection: Connection,
            turn: int,
            ) -> None:
        if turn not in self.connections:
            self.connections[turn] = {}
        current = self.get_connection_reservations(connection, turn)
        self.connections[turn][connection] = current + 1

    def can_reserve_connection(
            self,
            connection: Connection,
            turn: int,
            ) -> bool:
        capacity = connection.max_link_capacity
        reservations = self.get_connection_reservations(connection, turn)
        return capacity > reservations

    def can_move(
            self,
            connection: Connection,
            destination: Hub,
            departure_turn: int,
            ) -> bool:
        arrival_turn = departure_turn + destination.get_entry_cost()
        if not self.can_reserve_hub(destination, arrival_turn):
            return False
        for turn in range(departure_turn + 1, arrival_turn + 1):
            if not self.can_reserve_connection(connection, turn):
                return False
        return True

    def reserve_itinerary(
            self,
            itinerary: list[tuple[Hub, int]],
            graph: Graph,
            ) -> None:
        for hub, turn in itinerary:
            self.reserve_hub(hub, turn)
        for i in range(1, len(itinerary)):
            previous_hub, previous_turn = itinerary[i - 1]
            current_hub, current_turn = itinerary[i]
            if previous_hub == current_hub:
                continue
            connection = graph.get_connection(previous_hub, current_hub)
            if connection is None:
                raise ValueError(
                    f"Invalid itinerary: no connection between "
                    f"'{previous_hub.name}' and '{current_hub.name}'."
                )
            for turn in range(previous_turn + 1, current_turn + 1):
                self.reserve_connection(connection, turn)
