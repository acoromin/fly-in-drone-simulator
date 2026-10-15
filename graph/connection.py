from graph.hub import Hub

class Connection:
    def __init__(
            self, 
            source: Hub, 
            target: Hub, 
            max_link_capacity: int
            ) -> None:
        self.source = source
        self.target = target
        self.max_link_capacity = max_link_capacity

    def get_other_hub(self, hub: Hub) -> Hub:
        if hub == self.source:
            return self.target
        if hub == self.target:
            return self.source
        raise ValueError("Hub is not part of this connection.")
