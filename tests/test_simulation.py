"""Check complete schedules and validation independently of the renderer."""
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from map_loader import discover_maps, load_simulation
from parser import MapError


class SimulationTests(unittest.TestCase):
    def test_included_schedules_respect_capacity_and_targets(self) -> None:
        targets = {
            '01_linear_path': 4, '02_simple_fork': 4, '03_basic_capacity': 4,
            '01_dead_end_trap': 8, '02_circular_loop': 15,
            '03_priority_puzzle': 7, '01_maze_nightmare': 13,
            '02_capacity_hell': 16, '03_ultimate_challenge': 26,
            '01_the_impossible_dream': 43,
        }
        for path in discover_maps():
            if path.stem not in targets:
                continue
            with self.subTest(map=path.name):
                simulation = load_simulation(path)
                graph = simulation.graph
                hubs: Counter[tuple[str, int]] = Counter()
                links: Counter[tuple[str, str, int]] = Counter()
                for drone in simulation.drones:
                    self.assertIs(drone.itinerary[0][0], graph.start_hub)
                    self.assertIs(drone.end_hub, graph.end_hub)
                    for hub, turn in drone.itinerary:
                        self.assertFalse(hub.is_blocked())
                        hubs[hub.name, turn] += 1
                        if hub.type == 'hub':
                            self.assertLessEqual(hubs[hub.name, turn],
                                                 hub.max_drones)
                    for (a, t0), (b, t1) in zip(drone.itinerary,
                                                drone.itinerary[1:]):
                        self.assertEqual(t1 - t0,
                                         1 if a is b else b.get_entry_cost())
                        if a is b:
                            continue
                        connection = graph.get_connection(a, b)
                        self.assertIsNotNone(connection)
                        assert connection is not None
                        first, second = sorted((a.name, b.name))
                        for turn in range(t0 + 1, t1 + 1):
                            links[first, second, turn] += 1
                            self.assertLessEqual(
                                links[first, second, turn],
                                connection.max_link_capacity,
                            )
                expected = targets[path.stem]
                for _ in range(expected):
                    self.assertFalse(simulation.is_finished())
                    simulation.step()
                self.assertTrue(simulation.is_finished())
                self.assertEqual(simulation.step(), [])
                self.assertEqual(simulation.turn, expected)
                simulation.rewind()
                self.assertEqual(simulation.turn, expected - 1)
                simulation.reset()
                simulation.rewind()
                self.assertEqual(simulation.turn, 0)

    def test_invalid_maps_raise_readable_errors(self) -> None:
        base = 'nb_drones: 1\nstart_hub: start 0 0\nend_hub: end 1 0\n'
        cases = [b'not a map', b'\xff', base.encode(),
                 (base + 'connection: start-missing\n').encode(),
                 (base.replace('nb_drones: 1', 'nb_drones: 0')
                  + 'connection: start-end\n').encode()]
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.txt'
            for content in cases:
                with self.subTest(content=content):
                    path.write_bytes(content)
                    with self.assertRaises(MapError) as caught:
                        load_simulation(path)
                    self.assertTrue(str(caught.exception))
