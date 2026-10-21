from pydantic import BaseModel, model_validator
from typing import Literal


class HubModel(BaseModel):
    """Validate one hub definition and its optional metadata."""

    type: Literal["hub", "start_hub", "end_hub"]
    name: str
    x: int
    y: int
    n_line: int
    zone: Literal["normal", "blocked", "restricted", "priority"] = "normal"
    color: str | None = None
    max_drones: int = 1

    @model_validator(mode="after")
    def validate_max_drones(self) -> "HubModel":
        """Require positive capacity for ordinary hubs."""
        if self.type == "hub" and self.max_drones < 1:
            raise ValueError(
                    f"Line {self.n_line}: max_drones must be greater than 0."
                    )
        return self

    @model_validator(mode="before")
    @classmethod
    def validate_zone(cls, data: object) -> object:
        """Reject unknown zone types with the source line number."""
        if not isinstance(data, dict):
            return data

        zone = data.get("zone", "normal")
        zones = ["normal", "blocked", "restricted", "priority"]
        if zone not in zones:
            raise ValueError(
                    f"Line {data.get('n_line', '?')}: invalid zone '{zone}'."
                    )
        return data

    @model_validator(mode="after")
    def validate_name(self) -> "HubModel":
        """Reject dashes in names reserved for connection syntax."""
        if "-" in self.name:
            raise ValueError(
                f"Line {self.n_line}: hub name '{self.name}' "
                "cannot contain '-'."
            )
        return self


class ConnectionModel(BaseModel):
    """Validate a connection definition and its capacity."""

    source: str
    target: str
    n_line: int
    max_link_capacity: int = 1

    @model_validator(mode="after")
    def validate_capacity(self) -> "ConnectionModel":
        """Require a positive connection capacity."""
        if self.max_link_capacity < 1:
            raise ValueError(
                    f"Line {self.n_line}: connection capacity can't be less "
                    "than 1."
                    )
        return self


class MapModel(BaseModel):
    """Validate the drone count, hubs, and connections of a map."""

    nb_drones: int
    nb_drones_line: int
    nodes: list[HubModel]
    connections: list[ConnectionModel]

    @model_validator(mode="after")
    def validate_nb_drones(self) -> "MapModel":
        """Require at least one drone."""
        if self.nb_drones < 1:
            raise ValueError(
                    f"Line {self.nb_drones_line}: nb_drones must be greater"
                    " than or equal to 1."
                    )
        return self

    @model_validator(mode="after")
    def validate_start_end_hubs(self) -> "MapModel":
        """Require exactly one start hub and one end hub."""
        starts = [hub for hub in self.nodes if hub.type == "start_hub"]
        ends = [hub for hub in self.nodes if hub.type == "end_hub"]
        if len(starts) != 1:
            if len(starts) > 1:
                raise ValueError(
                        f"Line {starts[1].n_line}: "
                        "only one start_hub is allowed."
                        )
            else:
                raise ValueError(
                        "Missing start_hub: the map must contain exactly "
                        "one start_hub."
                        )
        if len(ends) != 1:
            if len(ends) > 1:
                raise ValueError(
                        f"Line {ends[1].n_line}: "
                        "only one end_hub is allowed."
                        )
            else:
                raise ValueError(
                        "Missing end_hub: the map must contain exactly "
                        "one end_hub."
                        )
        return self

    @model_validator(mode="after")
    def validate_unique_hubs(self) -> "MapModel":
        """Reject duplicate hub names or coordinates."""
        seen_names = set()
        seen_coordinates = set()
        for hub in self.nodes:
            coordinates = (hub.x, hub.y)
            if hub.name in seen_names:
                raise ValueError(
                        f"Line {hub.n_line}: hub name '{hub.name}' "
                        "must be unique."
                        )
            if coordinates in seen_coordinates:
                raise ValueError(
                        f"Line {hub.n_line}: hub coordinates "
                        f"({hub.x}, {hub.y}) must be unique."
                        )
            seen_names.add(hub.name)
            seen_coordinates.add(coordinates)
        return self

    @model_validator(mode="after")
    def validate_connections(self) -> "MapModel":
        """Reject unknown endpoints and duplicate undirected links."""
        names = [hub.name for hub in self.nodes]
        seen = set()
        for connection in self.connections:
            if (
                    connection.source not in names or
                    connection.target not in names
                    ):
                raise ValueError(
                        f"Line {connection.n_line}: "
                        "Connections must reference existing hubs."
                        )
            pairs = tuple(sorted((connection.source, connection.target)))
            if pairs in seen:
                raise ValueError(
                        f"Line {connection.n_line}: "
                        f"Duplicate connection between '{connection.source}' "
                        f"and '{connection.target}'."
                        )
            seen.add(pairs)
        return self
