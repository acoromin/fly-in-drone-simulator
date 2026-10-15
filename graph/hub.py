class Hub:
    def __init__(
            self,
            type: str,
            name: str,
            x: int,
            y: int,
            zone: str,
            color: str,
            max_drone: int,
            ) -> None:
        self.type = type
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drone = max_drone

    def get_zone_cost(self) -> int:
        if self.zone == "restricted":
            return 2
        return 1

    def is_blocked(self) -> bool:
        return self.zone == "blocked"
