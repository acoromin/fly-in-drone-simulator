from graph.hub import Hub


class Connection:
    """Represent a bidirectional link with shared traversal capacity."""

    def __init__(
            self,
            source: Hub,
            target: Hub,
            max_link_capacity: int
            ) -> None:
        """Store the two endpoints and their shared capacity."""
        self.source = source
        self.target = target
        self.max_link_capacity = max_link_capacity

    def get_other_hub(self, hub: Hub) -> Hub:
        """Return the opposite endpoint, or raise for an unrelated hub."""
        if hub == self.source:
            return self.target
        if hub == self.target:
            return self.source
        raise ValueError("Hub is not part of this connection.")
