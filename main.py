import sys
from pydantic import ValidationError
from planner.pathfinder import Pathfinder
from parser import MapParser, MapError, MapModel
from graph import Graph
from planner import Planner


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <map_file>")
        return

    file_route = sys.argv[1]
    parser = MapParser()

    try:
        tree = parser.parse_file(sys.argv[1])
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

    graph = Graph(validated_map)
    planner = Planner(graph)
    itineraries = planner.plan_itineraries(validated_map.nb_drones)
    for drone_id, itinerary in enumerate(itineraries, start=1):
        print(f"D{drone_id}:")
        for hub, turn in itinerary:
            print(hub.name, turn)

    
    
if __name__ == "__main__":
    main()
