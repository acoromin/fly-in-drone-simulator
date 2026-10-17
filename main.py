import sys
from pydantic import ValidationError
from pathfinder.pathfinder import Pathfinder
from parser import MapParser, MapError, MapModel
from graph.graph import Graph 


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <map_file>")
        return

    file_route = sys.argv[1]
    parser = MapParser()

    try:
        tree = parser.parse_file(sys.argv[1])
        print(tree.pretty())
        map_data = parser.convert_data(file_route)
        validated_map = MapModel(**map_data)

    except MapError as error:
        print(f"Error: {error}")
        return

    except ValidationError as error:
        for validation_error in error.errors():
            message = validation_error["msg"]

            if message.startswith("Value error, "):
                message = message.removeprefix("Value error, ")

            print(f"Error: {message}")
        return

    graph_object = Graph(validated_map)
    graph = graph_object.generate_graph()
    
if __name__ == "__main__":
    main()
