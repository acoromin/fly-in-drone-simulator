"""Desktop shell with fullscreen navigation and an in-app map library."""
from pathlib import Path
import textwrap

import pygame

from map_loader import MAPS_DIR, discover_maps, load_simulation
from parser import MapError
from renderer.pygame_renderer import PygameRenderer
from renderer.tactical_theme import TacticalTheme


class Application:
    def __init__(self, initial_map: Path | None = None) -> None:
        pygame.init()
        pygame.display.set_caption('Fly-In · Drone Traffic Simulator')
        self.desktop = pygame.display.get_desktop_sizes()[0]
        self.fullscreen = True
        self.screen = pygame.display.set_mode(self.desktop, pygame.FULLSCREEN)
        self.theme = TacticalTheme()
        self.renderer: PygameRenderer | None = None
        self.current_map: Path | None = None
        self.maps = discover_maps()
        self.picker = True
        self.selected = 0
        self.scroll = 0
        self.error = ''
        self.running = True
        if initial_map is not None:
            self.load(initial_map)

    def load(self, path: Path) -> None:
        """Commit a new view only after parsing and planning succeed."""
        self.draw()
        bounds = self.screen.get_rect()
        message = pygame.Rect(0, 0, min(640, bounds.width - 40), 80)
        message.center = bounds.center
        pygame.draw.rect(self.screen, self.theme.panel, message,
                         border_radius=8)
        pygame.draw.rect(self.screen, self.theme.accent, message, 2,
                         border_radius=8)
        label = self.theme.font(22).render('Cargando y planificando rutas…',
                                           True, self.theme.text)
        self.screen.blit(label, label.get_rect(center=message.center))
        pygame.display.flip()
        try:
            simulation = load_simulation(path)
            renderer = PygameRenderer(simulation, self.screen)
        except (MapError, OSError) as error:
            self.error = str(error)
            self.picker = True
            return
        self.renderer = renderer
        self.current_map = path
        self.error = ''
        self.picker = False

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        size = self.desktop if self.fullscreen else (
            min(1280, self.desktop[0]), min(800, self.desktop[1]))
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode(size, flags)
        if self.renderer:
            self.renderer.resize(self.screen)

    def navigation(self) -> dict[str, pygame.Rect]:
        width = self.screen.get_width()
        return {'maps': pygame.Rect(160, 18, width - 520, 48),
                'fullscreen': pygame.Rect(width - 344, 18, 220, 48),
                'exit': pygame.Rect(width - 112, 18, 92, 48)}

    def picker_geometry(self) -> tuple[pygame.Rect, int]:
        width, height = self.screen.get_size()
        rect = pygame.Rect(0, 0, min(920, width - 64), height - 100)
        rect.center = self.screen.get_rect().center
        return rect, max(1, (rect.height - 230) // 48)

    def open_picker(self) -> None:
        self.maps = discover_maps()
        self.selected = (self.maps.index(self.current_map)
                         if self.current_map in self.maps else 0)
        self.scroll = self.selected
        self.error = ''
        self.picker = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
            size = (max(800, event.w), max(600, event.h))
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            if self.renderer:
                self.renderer.resize(self.screen)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif event.key == pygame.K_ESCAPE:
                if self.picker and self.renderer:
                    self.picker = False
                else:
                    self.running = False
            elif self.picker:
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    delta = 1 if event.key == pygame.K_DOWN else -1
                    self.selected = max(0, min(len(self.maps) - 1,
                                               self.selected + delta))
                    _, count = self.picker_geometry()
                    self.scroll = min(self.scroll, self.selected)
                    self.scroll = max(self.scroll, self.selected - count + 1)
                elif event.key == pygame.K_RETURN and self.maps:
                    self.load(self.maps[self.selected])
            elif event.key == pygame.K_m:
                self.open_picker()
            elif self.renderer:
                self.renderer.handle_key(event.key, event.unicode)
        elif event.type == pygame.MOUSEWHEEL and self.picker:
            _, count = self.picker_geometry()
            self.scroll = max(0, min(max(0, len(self.maps) - count),
                                     self.scroll - event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.picker:
                rect, count = self.picker_geometry()
                close = pygame.Rect(rect.right - 138, rect.y + 18, 118, 42)
                if close.collidepoint(event.pos):
                    if self.renderer:
                        self.picker = False
                    else:
                        self.running = False
                for row in range(count):
                    index = self.scroll + row
                    hit = pygame.Rect(rect.x + 20, rect.y + 100 + row * 48,
                                      rect.width - 40, 44)
                    if index < len(self.maps) and hit.collidepoint(event.pos):
                        self.selected = index
                        self.load(self.maps[index])
                        break
                return
            for action, rect in self.navigation().items():
                if rect.collidepoint(event.pos):
                    if action == 'maps':
                        self.open_picker()
                    elif action == 'fullscreen':
                        self.toggle_fullscreen()
                    else:
                        self.running = False
                    return
            if self.renderer:
                self.renderer.handle_click(event.pos)

    def draw(self) -> None:
        t = self.theme
        if self.renderer:
            self.renderer.draw()
        else:
            self.screen.fill(t.background)
        t.write(self.screen, 'FLY-IN', (20, 25), 28, t.accent)
        name = self.current_map.stem if self.current_map else 'Escoger mapa'
        labels = {'maps': f'Mapas · M  /  {name}',
                  'fullscreen': 'Ventana · F11' if self.fullscreen
                  else 'Pantalla · F11', 'exit': 'Salir'}
        for action, rect in self.navigation().items():
            pygame.draw.rect(self.screen, t.border, rect, 1, border_radius=6)
            label = t.fit(labels[action], rect.width - 20, 18)
            surface = t.font(18).render(label, True, t.text)
            self.screen.blit(surface, surface.get_rect(center=rect.center))
        if self.picker:
            self.draw_picker()

    def draw_picker(self) -> None:
        t = self.theme
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 190))
        self.screen.blit(shade, (0, 0))
        rect, count = self.picker_geometry()
        self.scroll = max(0, min(self.scroll, max(0, len(self.maps) - count)))
        pygame.draw.rect(self.screen, t.panel, rect, border_radius=12)
        pygame.draw.rect(self.screen, t.border, rect, 2, border_radius=12)
        t.write(self.screen, 'Biblioteca de mapas', (rect.x + 24, rect.y + 20),
                26, t.accent)
        t.write(self.screen,
                'Clic para cargar · ↑ ↓ y Enter · rueda para bajar',
                (rect.x + 24, rect.y + 65), 16, t.muted)
        close = pygame.Rect(rect.right - 138, rect.y + 18, 118, 42)
        pygame.draw.rect(self.screen, t.border, close, 1, border_radius=5)
        t.write(self.screen, 'Cerrar' if self.renderer else 'Salir',
                (close.x + 18, close.y + 10), 18)
        if not self.maps:
            t.write(self.screen, 'No hay archivos .txt en maps/.',
                    (rect.x + 24, rect.y + 110), 18)
        for row, path in enumerate(self.maps[self.scroll:self.scroll + count]):
            index = self.scroll + row
            hit = pygame.Rect(rect.x + 20, rect.y + 100 + row * 48,
                              rect.width - 40, 44)
            color = t.accent if index == self.selected else t.border
            pygame.draw.rect(self.screen, color, hit, 1, border_radius=5)
            relative = path.relative_to(MAPS_DIR)
            group = str(relative.parent).upper()
            t.write(self.screen, t.fit(group, 155, 16),
                    (hit.x + 12, hit.y + 12), 16, t.accent)
            label = path.stem.replace('_', ' ')
            t.write(self.screen, t.fit(label, hit.width - 190, 20),
                    (hit.x + 175, hit.y + 9), 20)
        footer = rect.y + 108 + count * 48
        t.write(self.screen, f'{len(self.maps)} mapas · '
                'Cada mapa comienza en el turno 0',
                (rect.x + 24, footer), 16, t.muted)
        if self.error:
            message = 'No se pudo cargar: ' + self.error
            columns = max(20, (rect.width - 48) // 10)
            lines = textwrap.wrap(message, columns)
            for i, line in enumerate(lines[:3]):
                t.write(self.screen, line, (rect.x + 24, footer + 27 + i * 20),
                        16, t.zone_colors['restricted'])

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            delta = clock.tick(60) / 1000
            was_picker = self.picker
            for event in pygame.event.get():
                self.handle_event(event)
            if self.renderer and not self.picker and not was_picker:
                self.renderer.update(delta)
            self.draw()
            pygame.display.flip()
