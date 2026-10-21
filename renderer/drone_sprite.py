import pygame


class DroneSprite:
    """Create and draw the shared fighter silhouette used for drones."""

    def __init__(self, size: int) -> None:
        """Prepare a reusable silhouette with the requested pixel size."""
        self.size = size
        self._drawing_scale = 4
        self.surface = self._create_surface()

    def draw(
        self,
        screen: pygame.Surface,
        position: tuple[float, float],
        heading: float,
    ) -> None:
        """Draw the silhouette centered at position and rotated to heading."""
        sprite = pygame.transform.rotozoom(self.surface, heading, 1)
        screen.blit(sprite, sprite.get_rect(center=position))

    def _create_surface(self) -> pygame.Surface:
        """Build the silhouette at high resolution and scale it to size."""
        scale = self._drawing_scale
        surface = pygame.Surface((80 * scale, 80 * scale), pygame.SRCALPHA)
        silhouette = [
            (72, 40), (52, 35), (34, 10), (25, 10),
            (34, 34), (20, 35), (12, 25), (7, 25),
            (11, 40), (7, 55), (12, 55), (20, 45),
            (34, 46), (25, 70), (34, 70), (52, 45),
        ]

        # Swept wings and tail, with an outline visible on colored hubs.
        self._draw_polygon(surface, (106, 132, 125), silhouette)
        self._draw_polygon(surface, (12, 20, 25), silhouette, 3)
        self._draw_polygon(surface, (225, 235, 225), silhouette, 1)

        # Fuselage and cockpit; the nose points to the right before rotation.
        self._draw_polygon(surface, (187, 204, 191), [
            (72, 40), (48, 35), (19, 37), (15, 40),
            (19, 43), (48, 45),
        ])
        self._draw_polygon(surface, (28, 52, 63), [
            (55, 40), (46, 37), (38, 38), (38, 42), (46, 43),
        ])
        self._draw_polygon(surface, (133, 209, 215), [
            (52, 40), (45, 38), (41, 39), (45, 40),
        ])
        self._draw_polygon(surface, (51, 72, 69), [
            (34, 17), (44, 33), (37, 31),
        ])
        self._draw_polygon(surface, (51, 72, 69), [
            (34, 63), (44, 47), (37, 49),
        ])
        self._draw_polygon(surface, (225, 175, 91), [
            (16, 38), (20, 38), (20, 42), (16, 42),
        ])

        return pygame.transform.smoothscale(surface, (self.size, self.size))

    def _draw_polygon(
        self,
        surface: pygame.Surface,
        color: tuple[int, int, int],
        points: list[tuple[int, int]],
        width: int = 0,
    ) -> None:
        """Draw a polygon using the internal high resolution coordinates."""
        scale = self._drawing_scale
        scaled_points = [(x * scale, y * scale) for x, y in points]
        pygame.draw.polygon(surface, color, scaled_points, width * scale)
