"""Exercise map switching and playback through public UI entry points."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

import pygame  # noqa: E402

from map_loader import MAPS_DIR  # noqa: E402
from renderer.application import Application  # noqa: E402


class ApplicationTests(unittest.TestCase):
    def test_playback_and_failed_map_preserve_current_session(self) -> None:
        app = Application(MAPS_DIR / 'easy/01_linear_path.txt')
        try:
            view = app.renderer
            assert view is not None
            view.handle_key(pygame.K_PLUS)
            self.assertEqual(view.playback_speed, 2)
            view.handle_key(pygame.K_SPACE)
            with patch('builtins.print'):
                view.update(0.25)
            self.assertEqual(view.simulation.turn, 1)
            app.toggle_fullscreen()
            self.assertEqual(view.simulation.turn, 1)
            self.assertEqual(view.playback_speed, 2)
            with TemporaryDirectory() as directory:
                path = Path(directory) / 'invalid.txt'
                path.write_text('not a map', encoding='utf-8')
                app.load(path)
            self.assertIs(app.renderer, view)
            self.assertTrue(app.picker)
            self.assertTrue(app.error)
            app.handle_event(pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='',
            ))
            self.assertFalse(app.picker)
            view.handle_key(pygame.K_LEFT)
            self.assertEqual(view.simulation.turn, 0)
            view.handle_key(pygame.K_p)
            with patch('builtins.print'):
                view.update(0.25)
            view.handle_key(pygame.K_p)
            view.update(1)
            self.assertEqual(view.simulation.turn, 1)
            view.handle_key(pygame.K_r)
            self.assertEqual(view.simulation.turn, 0)
            self.assertEqual(view.playback_speed, 1)
            app.load(MAPS_DIR / 'medium/02_circular_loop.txt')
            self.assertIsNot(app.renderer, view)
            assert app.renderer is not None
            self.assertEqual(app.renderer.simulation.turn, 0)
            self.assertFalse(app.picker)
        finally:
            pygame.quit()

    def test_library_refresh_discovers_custom_nested_maps(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('map_loader.MAPS_DIR', root):
                app = Application()
                try:
                    self.assertEqual(app.maps, [])
                    path = root / 'easy/custom/new_map.txt'
                    path.parent.mkdir(parents=True)
                    path.write_text('invalid but discoverable',
                                    encoding='utf-8')
                    app.open_picker()
                    self.assertEqual(app.maps, [path])
                finally:
                    pygame.quit()
