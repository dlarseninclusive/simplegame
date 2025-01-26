# File: enemy.py

import math
import pygame
from config import ENEMY_SPEED, ENEMY_HEALTH, ENEMY_DAMAGE

class Enemy(pygame.sprite.Sprite):
    """
    An enemy that:
    - Spawns at (x, y) with a chosen sprite (random among 3).
    - Moves toward the base, deals damage, then disappears.
    - Can be killed by bullets.
    """
    def __init__(self, x, y, base, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))

        # Use float coordinates for smooth movement
        self.x = float(x)
        self.y = float(y)

        # Stats
        self.speed = ENEMY_SPEED
        self.health = ENEMY_HEALTH
        self.damage = ENEMY_DAMAGE

        self.base = base

    def update(self):
        dx = self.base.x - self.x
        dy = self.base.y - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        # Check collision with base
        if dist < 10:
            self.base.take_damage(self.damage)
            self.kill()

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()
