import sys

import pygame
from pydantic import ValidationError

from graph import Graph
from parser import MapError, MapModel, MapParser
from planner import Planner
from renderer import PygameRenderer
from simulation import Drone, Simulation


def main() -> int:
    """Run the drone simulation and return an exit status."""
    if len(sys.argv) != 2:
        print(
            f"Usage: python3 {sys.argv[0]} <map_file>",
            file=sys.stderr,
        )
        return 1

    try:
        parser = MapParser()
        map_data = parser.convert_data(sys.argv[1])
        validated_map = MapModel.model_validate(map_data)

        graph = Graph(validated_map)
        planner = Planner(graph)
        itineraries = planner.plan_itineraries(
            validated_map.nb_drones
        )

        if not itineraries:
            print(
                "Error: no route connects start to goal.",
                file=sys.stderr,
            )
            return 1

        drones = []
        for drone_id, itinerary in enumerate(itineraries, start=1):
            drones.append(Drone(drone_id, itinerary))

        simulation = Simulation(graph, drones)
        renderer = PygameRenderer(simulation)
        renderer.run()

        return 0

    except MapError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    except ValidationError as error:
        for validation_error in error.errors():
            message = validation_error["msg"].removeprefix(
                "Value error, "
            )
            print(f"Error: {message}", file=sys.stderr)
        return 1

    except pygame.error as error:
        print(f"Graphics error: {error}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nSimulation interrupted.", file=sys.stderr)
        return 130

    finally:
        pygame.quit()


if __name__ == "__main__":
    raise SystemExit(main())
