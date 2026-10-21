"""Regression coverage for clipping beacons when fitting a map."""
import os
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

import pygame  # noqa: E402

from map_loader import discover_maps, load_simulation  # noqa: E402
from renderer.pygame_renderer import PygameRenderer  # noqa: E402


class MapBoundsTests(unittest.TestCase):
    def test_beacons_and_names_stay_inside_viewport(self) -> None:
        pygame.init()
        try:
            for path in discover_maps():
                simulation = load_simulation(path)
                for size in ((800, 600), (1024, 768), (1920, 1080)):
                    with self.subTest(map=path.name, size=size):
                        view = PygameRenderer(simulation, pygame.Surface(size))
                        bounds = view.map_rect.inflate(-16, -16)
                        for hub, (x, y) in view.positions.items():
                            # Include the largest possible terminal/zone ring.
                            radius = view.hub_radius + 10
                            self.assertGreaterEqual(x - radius, bounds.left)
                            self.assertLessEqual(x + radius, bounds.right)
                            self.assertGreaterEqual(y - radius, bounds.top)
                            self.assertLessEqual(y + radius, bounds.bottom)
                            if view.map_view.name_fits(hub):
                                width, height = view.map_view.name_font.size(
                                    hub.name,
                                )
                                label = pygame.Rect(0, 0, width, height)
                                label.midtop = (round(x), round(
                                    y + view.hub_radius + 12,
                                ))
                                self.assertTrue(bounds.contains(label))
        finally:
            pygame.quit()
