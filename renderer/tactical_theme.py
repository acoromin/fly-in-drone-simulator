import pygame


class TacticalTheme:
    """Share the colors, fonts and labels used by the tactical display."""

    background = (8, 16, 23)
    panel = (12, 24, 33)
    border = (37, 60, 72)
    grid = (16, 32, 42)
    text = (217, 231, 231)
    muted = (139, 163, 174)
    accent = (105, 225, 201)
    start = (80, 220, 200)
    end = (255, 210, 80)
    zone_colors = {
        "blocked": (240, 70, 70),
        "priority": (80, 220, 110),
        "restricted": (255, 160, 60),
    }

    def __init__(self) -> None:
        """Locate a local monospace font and prepare its size cache."""
        self.font_path = pygame.font.match_font(
            "dejavusansmono,liberationmono,monospace"
        )
        self.fonts: dict[int, pygame.font.Font] = {}

    def font(self, size: int) -> pygame.font.Font:
        """Return a cached font at the requested pixel size."""
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(self.font_path, size)
        return self.fonts[size]

    def write(
        self,
        screen: pygame.Surface,
        text: str,
        position: tuple[float, float],
        size: int = 13,
        color: tuple[int, int, int] | None = None,
    ) -> pygame.Rect:
        """Draw a text label and return its screen rectangle."""
        surface = self.font(size).render(text, True, color or self.text)
        return screen.blit(surface, position)

    def fit(self, text: str, width: int, size: int = 13) -> str:
        """Shorten a label to fit the available width."""
        font = self.font(size)
        if font.size(text)[0] <= width:
            return text
        while text and font.size(text + "...")[0] > width:
            text = text[:-1]
        return text + "..."

    def tooltip(
        self,
        screen: pygame.Surface,
        lines: list[str],
        anchor: tuple[int, int],
        bounds: pygame.Rect,
    ) -> None:
        """Draw a readable tooltip contained inside the map viewport."""
        lines = [self.fit(line, bounds.width - 24, 16) for line in lines]
        surfaces = [
            self.font(16).render(line, True, self.text) for line in lines
        ]
        width = max(surface.get_width() for surface in surfaces) + 20
        rect = pygame.Rect(anchor, (width, len(lines) * 25 + 16))
        rect.clamp_ip(bounds.inflate(-8, -8))
        pygame.draw.rect(screen, self.panel, rect, border_radius=4)
        pygame.draw.rect(screen, self.border, rect, 1, border_radius=4)
        for index, surface in enumerate(surfaces):
            screen.blit(surface, (rect.x + 10, rect.y + 8 + index * 25))
