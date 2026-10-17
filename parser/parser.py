from pathlib import Path
from lark import Lark, Tree
from lark.exceptions import UnexpectedInput
from parser.parser_errors import MapError
import sys


class MapParser:
    def __init__(self) -> None:
        grammar_path = Path(__file__).with_name("grammar.lark")
        self._parser = Lark.open(grammar_path, propagate_positions=True)

    def read_file(self, file_route: str) -> str:
        try:
            with open(file_route, "r", encoding="utf-8") as file:
                text = file.read()
        except (OSError, UnicodeError) as error:
            raise MapError.from_file(error, file_route)
        return text

    def parse_file(self, file_route: str) -> Tree:
        map_text = self.read_file(file_route)
        try:
            tree = self._parser.parse(map_text)
        except UnexpectedInput as error:
            raise MapError.from_lark(error, map_text)
        return tree

    def _parse_metadata(self, data) -> dict:
        metadata_data = {}
        seen = set()
        for item in data.children:
            item = item.children[0]
            key = str(item.data)

            if key in seen:
                raise MapError(
                    f"Line {item.meta.line}: duplicated metadata '{key}'."
                )

            seen.add(key)

            if key == "color":
                metadata_data["color"] = str(item.children[0])
            elif key == "zone":
                metadata_data["zone"] = str(item.children[0])
            elif key == "max_drones":
                metadata_data["max_drones"] = int(item.children[0])

        return metadata_data

    def _check_defined_hubs(
            self,
            connection_data: dict,
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

    def convert_data(self, file_route: str) -> dict:
        tree = self.parse_file(file_route)
        branches = tree.children
        defined_hubs = set()
        map_data = {}
        map_data["nodes"] = []
        map_data["connections"] = []
        for branch in branches:
            if branch.data == "statement":
                branch = branch.children[0]
            if branch.data == "count_drones":
                map_data["nb_drones"] = int(branch.children[0])
                map_data["nb_drones_line"] = branch.meta.line

            elif branch.data in ("start_hub", "end_hub", "hub"):
                node_data = {
                        "type": str(branch.data),
                        "name": str(branch.children[0]),
                        "x": int(branch.children[1]),
                        "y": int(branch.children[2]),
                        "n_line": branch.meta.line,
                        }
                if len(branch.children) > 3:
                    metadata = self._parse_metadata(branch.children[3])
                    node_data.update(metadata)

                map_data["nodes"].append(node_data)
                defined_hubs.add(node_data["name"])

            elif branch.data == "connections":
                connection_data = {
                        "source": str(branch.children[0]),
                        "target": str(branch.children[1]),
                        "n_line": branch.meta.line,
                        }
                if len(branch.children) > 2:
                    data = branch.children[2]
                    metadata = data.children
                    connection_data["max_link_capacity"] = int(
                            metadata[0].children[0])
                self._check_defined_hubs(connection_data, defined_hubs)
                map_data["connections"].append(connection_data)

        return map_data
