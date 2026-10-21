import math

import pygame

from graph import Connection, Hub
from renderer.drone_sprite import DroneSprite
from renderer.operations_panel import OperationsPanel
from renderer.tactical_map import TacticalMap
from renderer.tactical_theme import TacticalTheme
from simulation import Drone, Simulation


class PygameRenderer:
    """Coordinate the tactical view, flight selection and playback."""

    def __init__(self, simulation: Simulation,
                 screen: pygame.Surface) -> None:
        """Prepare the window and its independent map and panel views."""
        self.simulation = simulation
        self.graph = simulation.graph
        self.positions: dict[Hub, tuple[float, float]] = {}
        self.map_scale = 1.0
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_duration = 0.5
        self.auto_play = False
        self.paused = False
        self.speed_levels = (0.25, 0.5, 1.0, 2.0, 4.0)
        self.playback_speed = 1.0
        self.elapsed_seconds = 0.0
        self.delivery_display_duration = 0.5
        self.delivery_times: dict[int, float] = {}
        self.selected_drone: Drone | None = None

        self.theme = TacticalTheme()
        self.resize(screen)
        self._record_deliveries()

    def resize(self, screen: pygame.Surface) -> None:
        """Rebuild viewport geometry without changing playback state."""
        self.screen = screen
        width, height = screen.get_size()
        panel_height = 264 if width < 900 else 232
        panel_rect = pygame.Rect(20, 82, width - 40, panel_height)
        map_top = panel_rect.bottom + 12
        self.map_rect = pygame.Rect(20, map_top, width - 40,
                                    height - map_top - 20)
        self.margin = min(66, max(30, int(self.map_rect.height * 0.10)))
        self._calculate_positions()
        # Reserve the complete beacon, outer rings and label, not just
        # its center. Bound the first radius so padding fits small windows.
        self.hub_radius = min(
            70, min(self.map_rect.size) / 4,
            self._get_min_hub_distance() / 4,
        )
        name_size = max(11, min(18, round(self.hub_radius * 0.3)))
        label_height = self.theme.font(name_size).get_height()
        self.margin = max(self.margin, math.ceil(
            self.hub_radius + 12 + label_height + 12,
        ))
        self._calculate_positions()
        self.hub_radius = min(self.hub_radius,
                              self._get_min_hub_distance() / 4)
        self.drone_size = max(8, round(self.hub_radius * 1.5))
        self.drone_sprite = DroneSprite(self.drone_size)
        self.map_view = TacticalMap(
            self.graph, self.map_rect, self.positions, self.hub_radius,
            self.map_scale, self.theme,
        )
        self.panel = OperationsPanel(panel_rect, self.theme)

    def _calculate_positions(self) -> None:
        """Fit the map into the viewport using one scale for both axes."""
        hubs = list(self.graph.hubs.values())
        min_x = min(hub.x for hub in hubs)
        max_x = max(hub.x for hub in hubs)
        min_y = min(hub.y for hub in hubs)
        max_y = max(hub.y for hub in hubs)
        map_width = max_x - min_x
        map_height = max_y - min_y
        available_width = self.map_rect.width - 2 * self.margin
        available_height = self.map_rect.height - 2 * self.margin
        scale_x = available_width / map_width if map_width else float("inf")
        scale_y = available_height / map_height if map_height else float("inf")
        self.map_scale = min(scale_x, scale_y)
        if not math.isfinite(self.map_scale):
            self.map_scale = 1.0
        offset_x = (
            self.map_rect.x + self.margin
            + (available_width - map_width * self.map_scale) / 2
        )
        offset_y = (
            self.map_rect.y + self.margin
            + (available_height - map_height * self.map_scale) / 2
        )
        for hub in hubs:
            self.positions[hub] = (
                (hub.x - min_x) * self.map_scale + offset_x,
                (max_y - hub.y) * self.map_scale + offset_y,
            )

    def _get_min_hub_distance(self) -> float:
        """Measure the nearest pair of beacon centers in screen pixels."""
        positions = list(self.positions.values())
        min_distance = float("inf")
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                min_distance = min(
                    min_distance, math.dist(positions[i], positions[j])
                )
        return min_distance

    def handle_key(self, key: int, character: str = "") -> None:
        """Map keyboard shortcuts to the same actions as the buttons."""
        if key == pygame.K_SPACE:
            self._manual_step()
        elif key == pygame.K_p:
            self._toggle_playback()
        elif key in (pygame.K_LEFT, pygame.K_LESS, pygame.K_GREATER) \
                or character in ("<", ">"):
            self._previous_step()
        elif key == pygame.K_r:
            self._restart()
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self._change_speed(1)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._change_speed(-1)

    def handle_click(self, position: tuple[int, int]) -> None:
        """Activate a panel control or inspect a flight on the map."""
        action = self.panel.action_at(position)
        if action == "back":
            self._previous_step()
        elif action == "play":
            self._toggle_playback()
        elif action == "step":
            self._manual_step()
        elif action == "restart":
            self._restart()
        elif action == "slower":
            self._change_speed(-1)
        elif action == "faster":
            self._change_speed(1)
        elif self.map_rect.collidepoint(position):
            group = self._pick_group(position)
            if group is None:
                self.selected_drone = None
            else:
                drones = group[1]
                if self.selected_drone in drones:
                    index = drones.index(self.selected_drone)
                    self.selected_drone = drones[(index + 1) % len(drones)]
                else:
                    self.selected_drone = drones[0]

    def _manual_step(self) -> None:
        """Resume or start exactly one turn without automatic playback."""
        self.auto_play = False
        self.paused = False
        self._start_animation()

    def _toggle_playback(self) -> None:
        """Toggle continuous playback and pause without losing progress."""
        if self.simulation.is_finished():
            return
        if self.auto_play and not self.paused:
            self.paused = True
        else:
            self.auto_play = True
            self.paused = False
            self._start_animation()

    def _change_speed(self, direction: int) -> None:
        """Select a bounded playback speed without changing turns."""
        index = self.speed_levels.index(self.playback_speed)
        index = max(0, min(len(self.speed_levels) - 1, index + direction))
        self.playback_speed = self.speed_levels[index]

    def _stop_playback(self) -> None:
        """Cancel an active or paused animation before changing turns."""
        self.auto_play = False
        self.paused = False
        self.is_animating = False
        self.animation_progress = 0.0
        self.elapsed_seconds = 0.0
        self.delivery_times.clear()

    def _previous_step(self) -> None:
        """Return to the previous completed turn in manual mode."""
        self._stop_playback()
        self.simulation.rewind()
        self._record_deliveries()

    def _restart(self) -> None:
        """Return the simulation and interface to their initial state."""
        self._stop_playback()
        self.simulation.reset()
        self.playback_speed = 1.0
        self.selected_drone = None

    def _start_animation(self) -> None:
        """Start a turn only when no turn is already being animated."""
        if self.is_animating or self.simulation.is_finished():
            return
        self.animation_progress = 0.0
        self.is_animating = True

    def _record_deliveries(self) -> None:
        """Remember arrivals for a short final display at the destination."""
        for drone in self.simulation.drones:
            if drone.is_delivered(self.simulation.turn):
                self.delivery_times.setdefault(drone.id, self.elapsed_seconds)

    def update(self, delta_seconds: float) -> None:
        """Advance visual time, preserving leftover time in automatic mode."""
        remaining = delta_seconds
        if self.auto_play and not self.paused:
            self._start_animation()
        while self.is_animating and not self.paused and remaining > 0:
            duration = self.animation_duration / self.playback_speed
            until_end = (1 - self.animation_progress) * duration
            consumed = min(remaining, until_end)
            self.animation_progress += consumed / duration
            self.elapsed_seconds += consumed
            remaining -= consumed
            if self.animation_progress >= 1 - 1e-9:
                steps = self.simulation.step()
                self.print_movements(steps)
                self.animation_progress = 0.0
                self.is_animating = False
                self._record_deliveries()
                if self.simulation.is_finished():
                    self.auto_play = False
                elif self.auto_play:
                    self._start_animation()
        self.elapsed_seconds += remaining
        self._record_deliveries()

    def _get_drone_position(
        self, drone: Drone, turn: float
    ) -> tuple[float, float]:
        """Interpolate positions, including two-turn restricted links."""
        if turn >= drone.end_turn:
            return self.positions[drone.end_hub]
        for i in range(1, len(drone.itinerary)):
            previous_hub, previous_turn = drone.itinerary[i - 1]
            next_hub, next_turn = drone.itinerary[i]
            if previous_turn <= turn <= next_turn:
                progress = (turn - previous_turn) / (next_turn - previous_turn)
                x1, y1 = self.positions[previous_hub]
                x2, y2 = self.positions[next_hub]
                return (x1 + (x2 - x1) * progress,
                        y1 + (y2 - y1) * progress)
        raise ValueError(f"No position for drone {drone.id} at turn {turn}")

    def _get_drone_heading(self, drone: Drone, turn: float) -> float:
        """Follow each segment and keep the previous heading during waits."""
        heading = None
        for i in range(1, len(drone.itinerary)):
            previous_hub, previous_turn = drone.itinerary[i - 1]
            next_hub, next_turn = drone.itinerary[i]
            if previous_hub is next_hub:
                continue
            x1, y1 = self.positions[previous_hub]
            x2, y2 = self.positions[next_hub]
            next_heading = math.degrees(math.atan2(-(y2 - y1), x2 - x1))
            if turn < previous_turn:
                return next_heading if heading is None else heading
            heading = next_heading
            if turn < next_turn:
                break
        return heading if heading is not None else 0.0

    def _get_drone_groups(self) -> dict[tuple[int, int], list[Drone]]:
        """Group visible flights that occupy the same screen pixel."""
        turn = self.simulation.turn + self.animation_progress
        groups: dict[tuple[int, int], list[Drone]] = {}
        for drone in self.simulation.drones:
            arrival = self.delivery_times.get(drone.id)
            if arrival is not None:
                if (
                    self.elapsed_seconds - arrival
                    >= self.delivery_display_duration
                ):
                    continue
            x, y = self._get_drone_position(drone, turn)
            groups.setdefault((round(x), round(y)), []).append(drone)
        return groups

    def _pick_group(
        self, mouse: tuple[int, int]
    ) -> tuple[tuple[int, int], list[Drone]] | None:
        """Find the nearest visible aircraft under the cursor."""
        groups = self._get_drone_groups()
        if not groups:
            return None
        position = min(groups, key=lambda point: math.dist(point, mouse))
        if math.dist(position, mouse) <= max(10, self.drone_size * 0.45):
            return position, groups[position]
        return None

    def draw(self) -> None:
        """Compose the map layers before drawing the operations panel."""
        self.screen.fill(self.theme.background)
        self.map_view.draw_background(self.screen)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(self.map_rect)
        self.map_view.draw_connections(self.screen)
        if self.selected_drone is not None:
            self.map_view.draw_route(self.screen, self.selected_drone)
        self._draw_trails()
        self.map_view.draw_hubs(self.screen)
        self._draw_drones()
        self._draw_hover_label()
        self.screen.set_clip(previous_clip)
        self._draw_status()

    def _draw_trails(self) -> None:
        """Draw short fading trails from real recent itinerary positions."""
        if not self.is_animating:
            return
        turn = self.simulation.turn + self.animation_progress
        layer = pygame.Surface(self.map_rect.size, pygame.SRCALPHA)
        for drones in self._get_drone_groups().values():
            drone = drones[0]
            points = []
            for index in range(7):
                time = max(0.0, turn - 0.6 + index * 0.1)
                x, y = self._get_drone_position(drone, time)
                points.append((x - self.map_rect.x, y - self.map_rect.y))
            for index in range(1, len(points)):
                if math.dist(points[index - 1], points[index]) > 0.5:
                    pygame.draw.line(
                        layer, (*self.theme.accent, 20 + index * 20),
                        points[index - 1], points[index], 2,
                    )
        self.screen.blit(layer, self.map_rect)

    def _draw_drones(self) -> None:
        """Draw one aircraft per group, with identifiers and count badges."""
        groups = self._get_drone_groups()
        hub_positions = {
            (round(x), round(y)) for x, y in self.positions.values()
        }
        turn = self.simulation.turn + self.animation_progress
        for position, drones in groups.items():
            selected = self.selected_drone in drones
            representative = self.selected_drone if selected else drones[0]
            if representative is None:
                continue
            heading = self._get_drone_heading(representative, turn)
            self.drone_sprite.draw(self.screen, position, heading)
            if selected:
                rect = pygame.Rect(0, 0, self.drone_size, self.drone_size)
                rect.center = position
                pygame.draw.rect(self.screen, self.theme.accent,
                                 rect.inflate(8, 8), 1)
        for (x, y), drones in groups.items():
            label = ""
            if (
                self.selected_drone is not None
                and self.selected_drone in drones
            ):
                label = f"D{self.selected_drone.id:02d}"
            if len(drones) > 1:
                label += f" ×{len(drones)}"
            if label:
                surface = self.theme.font(12).render(
                    label.strip(), True, self.theme.text, self.theme.background
                )
                offset = (self.hub_radius + 14 if (x, y) in hub_positions
                          else self.drone_size / 2 + 8)
                rect = surface.get_rect(midleft=(x + offset, y))
                rect.clamp_ip(self.map_rect.inflate(-8, -8))
                self.screen.blit(surface, rect)

    def _draw_hover_label(self) -> None:
        """Inspect flight identifiers first, then the underlying beacons."""
        mouse = pygame.mouse.get_pos()
        if not self.map_rect.collidepoint(mouse):
            return
        group = self._pick_group(mouse)
        if group is None:
            self.map_view.draw_hover_label(self.screen, mouse)
            return
        drones = group[1]
        names = ", ".join(f"D{drone.id:02d}" for drone in drones[:4])
        if len(drones) > 4:
            names += f" +{len(drones) - 4}"
        self.theme.tooltip(
            self.screen, [names, "Clic para seleccionar el vuelo"],
            (mouse[0] + 16, mouse[1] + 16), self.map_rect,
        )

    def _get_in_flight_count(self) -> int:
        """Count flights separately from waits and completed deliveries."""
        turn = self.simulation.turn + self.animation_progress
        count = 0
        for drone in self.simulation.drones:
            if drone.is_delivered(self.simulation.turn):
                continue
            if not self.is_animating:
                count += drone.get_hub_at_turn(self.simulation.turn) is None
                continue
            for i in range(1, len(drone.itinerary)):
                previous_hub, previous_turn = drone.itinerary[i - 1]
                next_hub, next_turn = drone.itinerary[i]
                if previous_turn <= turn < next_turn:
                    count += previous_hub is not next_hub
                    break
        return count

    def _draw_status(self) -> None:
        """Present real fleet metrics and the current playback state."""
        if self.simulation.is_finished():
            status = "FINALIZADA"
        elif self.paused:
            status = "PAUSA"
        elif self.auto_play:
            status = "AUTO"
        elif self.is_animating:
            status = "PASO"
        else:
            status = "MANUAL"
        self.panel.draw(
            self.screen, self.simulation, selected=self.selected_drone,
            in_flight=self._get_in_flight_count(), status=status,
            speed=self.playback_speed,
        )

    def print_movements(
        self, steps: list[tuple[Drone, Hub | Connection]]
    ) -> None:
        """Print one line of movements after a simulation turn."""
        movements = []
        for drone, position in steps:
            if isinstance(position, Hub):
                name = position.name
            else:
                name = f"{position.source.name}-{position.target.name}"
            movements.append(f"D{drone.id}-{name}")
        print(" ".join(movements))
