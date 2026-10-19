from graph import Graph
import pygame


class PygameRenderer:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        pygame.init()
        self.screen = pygame.display.set_mode((1000, 700))

    def _calculate_positions(self) -> None:
        hubs = list(self.graph.hubs.values())
        min_x = min(hub.x for hub in hubs)
        max_x = max(hub.x for hub in hubs)
        min_y = min(hub.y for hub in hubs)
        max_y = max(hub.y for hub in hubs)
        map_width = max_x - min_x
        map_height = max_y - min_y
