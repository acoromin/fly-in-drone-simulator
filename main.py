import sys
from pydantic import ValidationError
from pathfinder.pathfinder import Pathfinder
from parser import MapParser, MapError, MapModel
from graph import Graph
from planner.reservations import Reservations


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
    for hub, connections in graph.adjacency.items():
        print(f"Hub: {hub.name}")
        print("Connections")
        for connection in connections:
            other_hub = connection.get_other_hub(hub)
            print(other_hub.name)

    reservations = Reservations()
    hub_a = graph.hubs["waypoint1"]
    hub_b = graph.hubs["waypoint2"]

    reservations.reserve_hub(hub_a, 2)
    print(reservations.get_hub_reservations(hub_a, 2))  # Esperamos 1

    reservations.reserve_hub(hub_a, 2)
    print(reservations.get_hub_reservations(hub_a, 2))  # Esperamos 2

    reservations.reserve_hub(hub_b, 2)
    print(reservations.get_hub_reservations(hub_b, 2))  # Esperamos 1
    print(reservations.get_hub_reservations(hub_a, 2))  # Debe seguir en 2

    
if __name__ == "__main__":
    main()
