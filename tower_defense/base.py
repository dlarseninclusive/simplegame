# File: base.py

import pygame
from config import BASE_MAX_HEALTH, BASE_POSITION, BASE_RADIUS, RED, GREEN

class Base:
    """
    The base to defend. Takes damage from enemies.
    """
    def __init__(self):
        self.x, self.y = BASE_POSITION
        self.radius = BASE_RADIUS
        self.max_health = BASE_MAX_HEALTH
        self.current_health = BASE_MAX_HEALTH

    def draw(self, surface):
        # Draw the base as a red circle
        pygame.draw.circle(surface, RED, (self.x, self.y), self.radius)

        # Health bar above
        bar_width = 50
        bar_height = 6
        health_ratio = self.current_health / self.max_health
        pygame.draw.rect(surface, GREEN,
                         (self.x - bar_width // 2,
                          self.y - self.radius - 15,
                          int(bar_width * health_ratio),
                          bar_height))

    def take_damage(self, amount):
        self.current_health -= amount
        if self.current_health < 0:
            self.current_health = 0

    def is_destroyed(self):
        return self.current_health <= 0
