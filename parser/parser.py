from pathlib import Path
from lark import Lark, Tree, Token
from lark.exceptions import UnexpectedInput
from parser.parser_errors import MapError
from typing import TypedDict


class MapData(TypedDict):
    nb_drones: int
    nb_drones_line: int
    nodes: list[dict[str, str | int]]
    connections: list[dict[str, str | int]]


class MapParser:
    def __init__(self) -> None:
        grammar_path = Path(__file__).with_name("grammar.lark")
        self._parser = Lark.open(str(grammar_path), propagate_positions=True)

    def read_file(self, file_route: str) -> str:
        try:
            with open(file_route, "r", encoding="utf-8") as file:
                text = file.read()
        except (OSError, UnicodeError) as error:
            raise MapError.from_file(error, file_route)
        return text

    def parse_file(self, file_route: str) -> Tree[Token]:
        map_text = self.read_file(file_route)
        try:
            tree = self._parser.parse(map_text)
        except UnexpectedInput as error:
            raise MapError.from_lark(error, map_text)
        return tree

    def _parse_metadata(self, data: Tree[Token]) -> dict[str, int | str]:
        metadata_data: dict[str, int | str] = {}
        seen = set()
        for item in data.children:
            if not isinstance(item, Tree):
                raise MapError("Invalid metadata structure.")

            child = item.children[0]

            if not isinstance(child, Tree):
                raise MapError("Invalid metadata structure.")

            key = str(child.data)

            if key in seen:
                raise MapError(
                    f"Line {item.meta.line}: duplicated metadata '{key}'."
                )

            seen.add(key)

            if key == "color":
                metadata_data["color"] = str(child.children[0])
            elif key == "zone":
                metadata_data["zone"] = str(child.children[0])
            elif key == "max_drones":
                metadata_data["max_drones"] = int(str(child.children[0]))

        return metadata_data

    def _check_defined_hubs(
            self,
            connection_data: dict[str, int | str],
            defined_hubs: set[str]
            ) -> None:
        source = connection_data["source"]
        target = connection_data["target"]
        line = connection_data["n_line"]

        if source not in defined_hubs or target not in defined_hubs:
            raise MapError(
                f"Line {line}: connection '{source}-{target}' "
                "references a hub that was not previously defined."
            )

    def convert_data(self, file_route: str) -> MapData:
        tree = self.parse_file(file_route)
        branches = tree.children
        defined_hubs: set[str] = set()
        map_data: MapData = {
                "nb_drones": 0,
                "nb_drones_line": 0,
                "nodes": [],
                "connections": [],
                }
        for branch in branches:
            if not isinstance(branch, Tree):
                raise MapError("Invalid map structure.")

            if branch.data == "statement":
                child = branch.children[0]
                if not isinstance(child, Tree):
                    raise MapError("Invalid statement structure.")
                branch = child

            if branch.data == "count_drones":
                map_data["nb_drones"] = int(str(branch.children[0]))
                map_data["nb_drones_line"] = branch.meta.line

            elif branch.data in ("start_hub", "end_hub", "hub"):
                node_data: dict[str, str | int] = {
                        "type": str(branch.data),
                        "name": str(branch.children[0]),
                        "x": int(str(branch.children[1])),
                        "y": int(str(branch.children[2])),
                        "n_line": branch.meta.line,
                        }
                if len(branch.children) > 3:
                    metadata_tree = branch.children[3]
                    if not isinstance(metadata_tree, Tree):
                        raise MapError("Invalid metadata structure.")
                    metadata = self._parse_metadata(metadata_tree)
                    node_data.update(metadata)

                map_data["nodes"].append(node_data)
                defined_hubs.add(str(node_data["name"]))

            elif branch.data == "connections":
                connection_data: dict[str, str | int] = {
                        "source": str(branch.children[0]),
                        "target": str(branch.children[1]),
                        "n_line": branch.meta.line,
                        }
                if len(branch.children) > 2:
                    data = branch.children[2]
                    if not isinstance(data, Tree):
                        raise MapError(
                                "Invalid connection metadata structure."
                                )

                    metadata_child = data.children[0]
                    if not isinstance(metadata_child, Tree):
                        raise MapError(
                                "Invalid connection metadata structure."
                                )

                    capacity_value = metadata_child.children[0]
                    connection_data["max_link_capacity"] = int(str(
                        capacity_value
                        ))
                self._check_defined_hubs(connection_data, defined_hubs)
                map_data["connections"].append(connection_data)

        return map_data
