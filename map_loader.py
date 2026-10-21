"""Build a fresh simulation for each map selection."""
from pathlib import Path

from pydantic import ValidationError

from graph import Graph
from parser import MapError, MapModel, MapParser
from planner import Planner
from simulation import Drone, Simulation


MAPS_DIR = Path(__file__).resolve().parent / 'maps'


def discover_maps() -> list[Path]:
    """Include nested TXT maps, grouped by directory."""
    order = {'easy': 0, 'medium': 1, 'hard': 2, 'challenger': 3}
    return sorted(MAPS_DIR.rglob('*.txt'), key=lambda p: (
        order.get(p.relative_to(MAPS_DIR).parts[0], 4), str(p)))


def load_simulation(path: Path) -> Simulation:
    """Validate and plan before replacing the active simulation."""
    try:
        model = MapModel.model_validate(MapParser().convert_data(str(path)))
    except ValidationError as error:
        raise MapError('; '.join(e['msg'].removeprefix('Value error, ')
                                 for e in error.errors())) from error
    graph = Graph(model)
    plans = Planner(graph).plan_itineraries(model.nb_drones)
    if not plans:
        raise MapError('No route connects start to goal.')
    return Simulation(graph, [Drone(i, plan)
                              for i, plan in enumerate(plans, 1)])
