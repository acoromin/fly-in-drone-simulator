from typing import Literal


class Hub:
    def __init__(
            self,
            type: Literal["hub", "start_hub", "end_hub"],
            name: str,
            x: int,
            y: int,
            zone: Literal["normal", "blocked", "restricted", "priority"],
            color: str | None,
            max_drones: int,
            ) -> None:
        self.type = type
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drones = max_drones

    def get_entry_cost(self) -> int:
        if self.zone == "restricted":
            return 2
        return 1

    def is_blocked(self) -> bool:
        return self.zone == "blocked"
