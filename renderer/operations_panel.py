import pygame

from renderer.tactical_theme import TacticalTheme
from simulation import Drone, Simulation


class OperationsPanel:
    """Readable playback controls, fleet metrics and a full-width legend."""

    def __init__(self, rect: pygame.Rect, theme: TacticalTheme) -> None:
        self.rect = rect
        self.theme = theme
        x, y = rect.x + 16, rect.y + 12
        button_width = min(200, (rect.width - 310) // 4)
        self.buttons = {
            action: pygame.Rect(x + i * (button_width + 8), y,
                                button_width, 58)
            for i, action in enumerate(('back', 'step', 'play', 'restart'))
        }
        self.speed_x = self.buttons['restart'].right + 32
        self.buttons['slower'] = pygame.Rect(self.speed_x, y + 22, 40, 36)
        self.buttons['faster'] = pygame.Rect(self.speed_x + 136, y + 22,
                                             40, 36)

    def action_at(self, position: tuple[int, int]) -> str | None:
        return next((action for action, rect in self.buttons.items()
                     if rect.collidepoint(position)), None)

    def draw(self, screen: pygame.Surface, simulation: Simulation, *,
             selected: Drone | None, in_flight: int, status: str,
             speed: float) -> None:
        t = self.theme
        x, y = self.rect.x + 16, self.rect.y
        pygame.draw.rect(screen, t.panel, self.rect, border_radius=8)
        pygame.draw.rect(screen, t.border, self.rect, 1, border_radius=8)
        captions = {
            'back': ('Atrás', '← / <'), 'step': ('Paso', 'Espacio'),
            'play': ('Pausa' if status == 'AUTO' else 'Iniciar', 'P'),
            'restart': ('Reiniciar', 'R'),
        }
        for action, (label, shortcut) in captions.items():
            rect = self.buttons[action]
            color = t.accent if action == 'play' else t.border
            pygame.draw.rect(screen, color, rect, 2, border_radius=6)
            for text, size, dy in ((label, 18, 7), (shortcut, 16, 32)):
                surface = t.font(size).render(text, True, t.text)
                screen.blit(surface, surface.get_rect(
                    midtop=(rect.centerx, rect.y + dy)))
        t.write(screen, 'VELOCIDAD', (self.speed_x, y + 10), 16,
                t.muted)
        for action, label in (('slower', '−'), ('faster', '+')):
            rect = self.buttons[action]
            pygame.draw.rect(screen, t.border, rect, 2, border_radius=5)
            surface = t.font(22).render(label, True, t.text)
            screen.blit(surface, surface.get_rect(center=rect.center))
        t.write(screen, f'{speed:g}×', (self.speed_x + 54, y + 38),
                22, t.accent)
        total = len(simulation.drones)
        delivered = sum(d.is_delivered(simulation.turn)
                        for d in simulation.drones)
        last = max((d.end_turn for d in simulation.drones), default=0)
        metrics = [('TURNO', f'{simulation.turn} / {last}'),
                   ('ENTREGADOS', f'{delivered} / {total}'),
                   ('EN ESPERA', str(total - delivered - in_flight)),
                   ('EN VUELO', str(in_flight)), ('ESTADO', status)]
        cell = (self.rect.width - 32) // 5
        for i, (label, value) in enumerate(metrics):
            t.write(screen, label, (x + i * cell, y + 82), 16, t.muted)
            t.write(screen, value, (x + i * cell, y + 105),
                    22 if i == 4 else 28, t.accent if i == 4 else t.text)
        legend_y = y + 150
        entries = [(t.start, 'Salida'), (t.end, 'Meta'),
                   (t.zone_colors['blocked'], 'Bloqueado'),
                   (t.zone_colors['priority'], 'Prioritario'),
                   (t.zone_colors['restricted'], 'Restringido · 2 turnos')]
        lx = x
        for color, label in entries:
            item_width = t.font(18).size(label)[0] + 48
            if lx + item_width > self.rect.right:
                lx = x
                legend_y += 32
            pygame.draw.circle(screen, color, (lx + 8, legend_y + 10), 8, 3)
            t.write(screen, label, (lx + 24, legend_y), 18)
            lx += t.font(18).size(label)[0] + 48
        selection = ('Clic en un dron para inspeccionar su ruta'
                     if selected is None else
                     f'D{selected.id:02d} → {selected.end_hub.name}'
                     f' · llegada: turno {selected.end_turn}')
        sx, sy = x, legend_y + 34
        available = self.rect.width - 32
        if available > 100:
            t.write(screen, t.fit(selection, available, 16), (sx, sy),
                    16, t.muted)
