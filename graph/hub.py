from typing import Literal


class Hub:
    """Represent a map zone with coordinates, entry cost, and capacity."""

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
        """Store the validated properties of one map zone."""
        self.type = type
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drones = max_drones

    def get_entry_cost(self) -> int:
        """Return two turns for restricted entry and one otherwise."""
        if self.zone == "restricted":
            return 2
        return 1

    def is_blocked(self) -> bool:
        """Return whether drones are forbidden from entering this hub."""
        return self.zone == "blocked"
