import math

import pygame

from graph import Graph, Hub
from renderer.tactical_theme import TacticalTheme
from simulation import Drone


class TacticalMap:
    """Draw the coordinate grid, network, beacons and selected itinerary."""

    def __init__(
        self,
        graph: Graph,
        rect: pygame.Rect,
        positions: dict[Hub, tuple[float, float]],
        radius: float,
        scale: float,
        theme: TacticalTheme,
    ) -> None:
        """Prepare the map view and cache its static grid."""
        self.graph = graph
        self.rect = rect
        self.positions = positions
        self.radius = radius
        self.scale = scale
        self.theme = theme
        self.name_font = theme.font(max(11, min(18, round(radius * 0.3))))
        self.background = self._create_background()

    def _create_background(self) -> pygame.Surface:
        """Draw a grid whose labels use the map's own coordinates."""
        surface = pygame.Surface(self.rect.size)
        surface.fill(self.theme.background)
        hub = next(iter(self.graph.hubs.values()))
        x, y = self.positions[hub]
        origin_x = x - self.rect.x - hub.x * self.scale
        origin_y = y - self.rect.y + hub.y * self.scale
        step = max(1, math.ceil(48 / self.scale))
        left = math.ceil(-origin_x / self.scale / step) * step
        right = math.floor((self.rect.width - origin_x) / self.scale)
        bottom = math.ceil((origin_y - self.rect.height) / self.scale / step)
        top = math.floor(origin_y / self.scale / step)

        for value in range(left, right + 1, step):
            px = round(origin_x + value * self.scale)
            pygame.draw.line(
                surface, self.theme.grid, (px, 0), (px, self.rect.height)
            )
            self.theme.write(surface, str(value), (px + 4, 5), 10,
                             self.theme.muted)
        for index in range(bottom, top + 1):
            value = index * step
            py = round(origin_y - value * self.scale)
            pygame.draw.line(
                surface, self.theme.grid, (0, py), (self.rect.width, py)
            )
            self.theme.write(surface, str(value), (5, py + 3), 10,
                             self.theme.muted)
        return surface

    def draw_background(self, screen: pygame.Surface) -> None:
        """Draw the grid, frame and north indicator."""
        screen.blit(self.background, self.rect)
        pygame.draw.rect(screen, self.theme.border, self.rect, 1)
        x, y = self.rect.right - 28, self.rect.top + 42
        pygame.draw.line(screen, self.theme.muted, (x, y + 18), (x, y), 1)
        pygame.draw.lines(screen, self.theme.accent, False,
                          [(x - 4, y + 6), (x, y), (x + 4, y + 6)], 1)
        self.theme.write(screen, "N", (x - 4, y - 18), 11)

    def draw_connections(self, screen: pygame.Surface) -> None:
        """Draw the fixed network beneath the beacons."""
        for connection in self.graph.connections:
            pygame.draw.line(
                screen, (49, 76, 90),
                self.positions[connection.source],
                self.positions[connection.target], 1,
            )

    def draw_route(self, screen: pygame.Surface, drone: Drone) -> None:
        """Highlight the selected drone's complete planned itinerary."""
        points: list[tuple[float, float]] = []
        for hub, _ in drone.itinerary:
            position = self.positions[hub]
            if not points or position != points[-1]:
                points.append(position)
        if len(points) > 1:
            pygame.draw.lines(screen, (21, 66, 67), False, points, 6)
            pygame.draw.lines(screen, self.theme.accent, False, points, 2)

    def draw_hubs(self, screen: pygame.Surface) -> None:
        """Draw beacons with map colors and independent zone rings."""
        for hub in self.graph.hubs.values():
            position = self.positions[hub]
            color = self._get_hub_color(hub.color)
            fill = color.lerp(self.theme.background, 0.85)
            pygame.draw.circle(screen, fill, position, self.radius)
            pygame.draw.circle(screen, color, position, self.radius, 2)
            if hub.color == "rainbow":
                self._draw_rainbow(screen, position)
            self._draw_rings(screen, hub)
            self._draw_name(screen, hub)

    def _draw_rings(self, screen: pygame.Surface, hub: Hub) -> None:
        """Keep start, destination and special zone rings distinguishable."""
        position = self.positions[hub]
        terminal_color = None
        if hub is self.graph.start_hub:
            terminal_color = self.theme.start
        elif hub is self.graph.end_hub:
            terminal_color = self.theme.end
        if terminal_color is not None:
            pygame.draw.circle(screen, terminal_color, position,
                               self.radius + 5, 3)
        zone_color = self.theme.zone_colors.get(hub.zone)
        if zone_color is not None:
            offset = 10 if terminal_color is not None else 5
            pygame.draw.circle(screen, zone_color, position,
                               self.radius + offset, 3)

    def _draw_rainbow(
        self, screen: pygame.Surface, position: tuple[float, float]
    ) -> None:
        """Represent the custom rainbow color with a multicolor outline."""
        colors = [(236, 91, 99), (242, 174, 82), (237, 218, 111),
                  (97, 211, 153), (103, 171, 237), (184, 129, 231)]
        radius = round(self.radius)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (round(position[0]), round(position[1]))
        for index, color in enumerate(colors):
            pygame.draw.arc(screen, color, rect, index * math.tau / 6,
                            (index + 1) * math.tau / 6, 2)

    def name_fits(self, hub: Hub) -> bool:
        """Check whether a permanent label has room at this beacon."""
        width, height = self.name_font.size(hub.name)
        return math.hypot(width, height) <= 2 * (self.radius - 4)

    def _draw_name(self, screen: pygame.Surface, hub: Hub) -> None:
        """Place readable names below spacious beacons."""
        if not self.name_fits(hub):
            return
        text = self.name_font.render(hub.name, True, self.theme.text)
        x, y = self.positions[hub]
        rect = text.get_rect(midtop=(x, y + self.radius + 12))
        rect.clamp_ip(self.rect.inflate(-8, -8))
        screen.blit(text, rect)

    def draw_hover_label(
        self, screen: pygame.Surface, mouse: tuple[int, int]
    ) -> None:
        """Show a hub's name and zone without permanent label clutter."""
        if not self.rect.collidepoint(mouse):
            return
        for hub, position in self.positions.items():
            if math.dist(mouse, position) <= self.radius + 5:
                zone = {"normal": "Normal", "blocked": "Bloqueada",
                        "restricted": "Restricted / 2 turnos",
                        "priority": "Prioritaria"}[hub.zone]
                self.theme.tooltip(screen, [hub.name, zone],
                                   (mouse[0] + 16, mouse[1] + 16), self.rect)
                break

    def _get_hub_color(self, color: str | None) -> pygame.Color:
        """Resolve map colors while accepting custom color names."""
        if color is not None:
            try:
                return pygame.Color(color)
            except ValueError:
                pass
        return pygame.Color(155, 178, 186)
