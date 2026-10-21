from graph import Hub, Graph, Connection


class Drone:
    """Associate a drone ID with its planned, time-stamped itinerary."""

    def __init__(
            self,
            drone_id: int,
            itinerary: list[tuple[Hub, int]]
            ) -> None:
        """Store a nonempty itinerary and its delivery state."""
        self.id = drone_id
        self.itinerary = itinerary
        self.end_hub, self.end_turn = self.itinerary[-1]

    def is_delivered(self, turn: int) -> bool:
        """Return whether the drone has reached its final hub by this turn."""
        if turn >= self.end_turn:
            return True
        return False

    def get_hub_at_turn(self, turn: int) -> Hub | None:
        """Return the hub after ``turn``, or ``None`` while in transit."""
        if self.is_delivered(turn):
            return self.end_hub
        for hub, state_turn in self.itinerary:
            if turn == state_turn:
                return hub
        return None

    def get_connection_at_turn(
            self,
            turn: int,
            graph: Graph,
            ) -> Connection | None:
        """Return the ``graph`` link occupied at ``turn``, if any."""

        for i in range(1, len(self.itinerary)):
            previous_hub, previous_turn = self.itinerary[i - 1]
            current_hub, current_turn = self.itinerary[i]
            if previous_turn < turn < current_turn:
                return graph.get_connection(previous_hub, current_hub)
        return None
