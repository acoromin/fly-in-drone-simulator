from simulation import Drone, Simulation
from graph import Hub, Connection
import pygame
import math


class PygameRenderer:
    def __init__(self, simulation: Simulation) -> None:
        self.simulation = simulation
        self.graph = simulation.graph
        self.margin = 100
        self.status_height = 140
        self.positions: dict[Hub, tuple[float, float]] = {}
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_duration = 0.5
        self.elapsed_seconds = 0.0
        self.delivery_display_duration = 0.5
        self.delivery_times: dict[int, float] = {}

        pygame.init()

        info = pygame.display.Info()
        width = int(info.current_w * 0.75)
        height = int(info.current_h * 0.75)

        self.screen = pygame.display.set_mode((width, height))
        self._calculate_positions()
        min_distance = self._get_min_hub_distance()
        self.hub_radius = min(70, min_distance / 4)
        font_size = max(24, int(self.hub_radius * 0.5))
        self.font = pygame.font.Font(None, font_size)
        self.marker_font = pygame.font.Font(None, 40)
        self.drone_radius = max(4, min(10, round(self.hub_radius / 3)))

    def run(self) -> None:
        running = True
        clock = pygame.time.Clock()

        while running:
            delta_seconds = clock.tick(60) / 1000
            self._update_animation(delta_seconds)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self._start_animation()

            self.screen.fill((20, 25, 30))
            self._draw_connections()
            self._draw_hubs()
            self._draw_drones()
            self._draw_hover_label()
            self._draw_status()
            pygame.display.flip()

        pygame.quit()

    def _calculate_positions(self) -> None:
        hubs = list(self.graph.hubs.values())

        min_x = min(hub.x for hub in hubs)
        max_x = max(hub.x for hub in hubs)
        min_y = min(hub.y for hub in hubs)
        max_y = max(hub.y for hub in hubs)

        map_width = max_x - min_x
        map_height = max_y - min_y

        screen_width, screen_height = self.screen.get_size()

        available_width = screen_width - 2 * self.margin
        available_height = screen_height - 2 * self.margin - self.status_height

        scale_x = (
            available_width / map_width if map_width > 0 else float("inf")
        )
        scale_y = (
            available_height / map_height if map_height > 0 else float("inf")
        )
        scale = min(scale_x, scale_y)
        if not math.isfinite(scale):
            scale = 1.0

        offset_x = self.margin + (available_width - map_width * scale) / 2
        offset_y = (
            self.status_height
            + self.margin
            + (available_height - map_height * scale) / 2
        )

        for hub in hubs:
            x = (hub.x - min_x) * scale + offset_x
            y = (max_y - hub.y) * scale + offset_y
            self.positions[hub] = (x, y)

    def _get_min_hub_distance(self) -> float:
        positions = list(self.positions.values())
        min_distance = float("inf")

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                distance = math.dist(positions[i], positions[j])
                min_distance = min(min_distance, distance)

        return min_distance

    def _start_animation(self) -> None:
        if self.is_animating or self.simulation.is_finished():
            return

        self.animation_progress = 0.0
        self.is_animating = True

    def _update_animation(self, delta_seconds: float) -> None:
        self.elapsed_seconds += delta_seconds

        if self.is_animating:
            self.animation_progress += delta_seconds / self.animation_duration

            if self.animation_progress >= 1.0:
                steps = self.simulation.step()
                self.print_movements(steps)
                self.animation_progress = 0.0
                self.is_animating = False

        for drone in self.simulation.drones:
            if drone.is_delivered(self.simulation.turn):
                self.delivery_times.setdefault(drone.id, self.elapsed_seconds)

    def _get_drone_position(
        self, drone: Drone, turn: float
    ) -> tuple[float, float]:
        if turn >= drone.end_turn:
            return self.positions[drone.end_hub]

        for i in range(1, len(drone.itinerary)):
            previous_hub, previous_turn = drone.itinerary[i - 1]
            next_hub, next_turn = drone.itinerary[i]

            if previous_turn <= turn <= next_turn:
                progress = (turn - previous_turn) / (next_turn - previous_turn)
                x1, y1 = self.positions[previous_hub]
                x2, y2 = self.positions[next_hub]

                return (
                    x1 + (x2 - x1) * progress,
                    y1 + (y2 - y1) * progress,
                )

        raise ValueError(f"No position for drone {drone.id} at turn {turn}")

    def _draw_connections(self) -> None:
        for connection in self.graph.connections:
            start = self.positions[connection.source]
            end = self.positions[connection.target]

            pygame.draw.line(
                self.screen,
                (80, 100, 120),
                start,
                end,
                2,
            )

    def _draw_hubs(self) -> None:
        zone_ring_colors = {
            "blocked": (240, 70, 70),
            "priority": (80, 220, 110),
            "restricted": (255, 160, 60),
        }

        for hub in self.graph.hubs.values():
            position = self.positions[hub]
            hub_color = self._get_hub_color(hub.color)
            text_color = self._get_text_color(hub_color)
            pygame.draw.circle(
                self.screen,
                hub_color,
                position,
                self.hub_radius,
            )
            if hub is self.graph.start_hub:
                pygame.draw.circle(
                    self.screen,
                    (80, 220, 200),
                    position,
                    self.hub_radius + 5,
                    3,
                )
            elif hub is self.graph.end_hub:
                pygame.draw.circle(
                    self.screen,
                    (255, 210, 80),
                    position,
                    self.hub_radius + 5,
                    3,
                )
            text = self.font.render(hub.name, True, text_color)
            text_width, text_height = text.get_size()

            text_diagonal = math.hypot(text_width, text_height)
            available_diameter = 2 * (self.hub_radius - 4)

            if text_diagonal <= available_diameter:
                text_rect = text.get_rect(center=position)
                self.screen.blit(text, text_rect)

            ring_color = zone_ring_colors.get(hub.zone)

            if ring_color is not None:
                ring_offset = 5
                if hub is self.graph.start_hub or hub is self.graph.end_hub:
                    ring_offset = 10

                pygame.draw.circle(
                    self.screen,
                    ring_color,
                    position,
                    self.hub_radius + ring_offset,
                    3,
                )

    def _get_drone_groups(self) -> dict[tuple[int, int], list[Drone]]:
        turn = self.simulation.turn + self.animation_progress
        groups: dict[tuple[int, int], list[Drone]] = {}

        for drone in self.simulation.drones:
            arrival_time = self.delivery_times.get(drone.id)
            if arrival_time is not None:
                if (
                    self.elapsed_seconds - arrival_time
                    >= self.delivery_display_duration
                ):
                    continue

            position = self._get_drone_position(drone, turn)
            pixel_position = (round(position[0]), round(position[1]))
            groups.setdefault(pixel_position, []).append(drone)

        return groups

    def _draw_drones(self) -> None:
        groups = self._get_drone_groups()
        hub_positions = {
            (round(x), round(y)) for x, y in self.positions.values()
        }

        for position in groups:
            pygame.draw.circle(
                self.screen, (255, 255, 255), position, self.drone_radius
            )
            pygame.draw.circle(
                self.screen, (20, 25, 30), position, self.drone_radius, 1
            )

        for (x, y), drones in groups.items():
            count = len(drones)
            if count > 1:
                text = self.marker_font.render(
                    f"×{count}", True, (255, 255, 255), (20, 25, 30)
                )
                offset = (
                    self.hub_radius + 10
                    if (x, y) in hub_positions
                    else self.drone_radius + 4
                )
                text_rect = text.get_rect(midleft=(x + offset, y))
                text_rect.clamp_ip(self.screen.get_rect())
                self.screen.blit(text, text_rect)

    def _draw_hover_label(self) -> None:
        mouse_position = pygame.mouse.get_pos()

        for hub, position in self.positions.items():
            distance = math.dist(mouse_position, position)

            if distance <= self.hub_radius:
                text = self.font.render(hub.name, True, (220, 230, 240))
                text_width, text_height = text.get_size()

                text_diagonal = math.hypot(text_width, text_height)
                available_diameter = 2 * (self.hub_radius - 4)

                if text_diagonal > available_diameter:
                    x, y = position
                    text_rect = text.get_rect(
                        midtop=(x, y + self.hub_radius + 4)
                    )
                    self.screen.blit(text, text_rect)

                break

    def _draw_status(self) -> None:
        last_turn = max(
            (drone.end_turn for drone in self.simulation.drones),
            default=0,
        )
        total = len(self.simulation.drones)
        delivered = sum(
            drone.is_delivered(self.simulation.turn)
            for drone in self.simulation.drones
        )
        summary = (
            f"Turno: {self.simulation.turn} / {last_turn}"
            f"    Entregados: {delivered} / {total}"
        )

        if self.simulation.is_finished():
            status = "Simulación finalizada"
        elif self.is_animating:
            status = "En movimiento..."
        else:
            status = "Listo para el siguiente turno"

        messages = [
            summary, "Espacio: siguiente turno · Esc: salir", status,
        ]
        for index, message in enumerate(messages):
            text = self.marker_font.render(message, True, (220, 230, 240))
            self.screen.blit(text, (20, 12 + index * 42))

    def _get_hub_color(self, color: str | None) -> pygame.Color:
        if color is None:
            return pygame.Color(180, 200, 220)

        try:
            return pygame.Color(color)
        except ValueError:
            return pygame.Color(180, 200, 220)

    def _get_text_color(
        self, background: pygame.Color
    ) -> tuple[int, int, int]:
        brightness = background.grayscale().r

        if brightness < 128:
            return (245, 245, 245)

        return (20, 25, 30)
    
    def print_movements(
        self,
        steps: list[tuple[Drone, Hub | Connection]],
    ) -> None:
        movements = []

        for drone, position in steps:
            if isinstance(position, Hub):
                name = position.name
            else:
                name = f"{position.source.name}-{position.target.name}"

            movements.append(f"D{drone.id}-{name}")

        print(" ".join(movements))
