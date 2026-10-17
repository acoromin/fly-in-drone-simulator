class Reservations:
    def __init__(self) -> None:
        self.hubs = {}
        self.connections = {}

    def reserve_hub(self, hub: Hub, turn: int) -> None:
        if turn not in self.hubs:
            self.hubs[turn] = {}
        if hub not in self.hubs[turn]:
            self.hubs[turn][hub] = 1
        else:
            self.hubs[turn][hub] += 1

    def reserve_connection(self, connection: Connection, turn: int) -> None:
        if turn not in self.connections:
            self.connections[turn] = {}
        if connection not in self.connections[turn]:
            self.connections[turn][connection] = 1
        else:
            self.connections[turn][connection] += 1

    def can_reserve_hub(self, hub: Hub, turn: int) -> bool:

