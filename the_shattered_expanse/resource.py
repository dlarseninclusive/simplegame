import pygame
from data import RESOURCE_DATA, get_resource_data

class ResourceNode:
    """
    Collectible resource node with respawn logic.
    """
    def __init__(self, x, y, width, height, resource_type):
        self.rect = pygame.Rect(x, y, width, height)
        self.resource_type = resource_type
        self.collected = False

        # 1) Respawn timer
        self.respawn_time = 30.0  # seconds
        self.current_timer = 0.0

    @property
    def data(self):
        return get_resource_data(self.resource_type)

    def update(self, dt):
        """
        If collected, increment the timer. Once it hits respawn_time, reset.
        """
        if self.collected:
            self.current_timer += dt
            if self.current_timer >= self.respawn_time:
                self.collected = False
                self.current_timer = 0.0
