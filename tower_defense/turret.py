# turret.py

import math
import pygame
from config import (
    TURRET_RANGE,
    TURRET_FIRE_RATE,
    TURRET_BULLET_SPEED,
    TURRET_BULLET_DAMAGE,
)

class Turret(pygame.sprite.Sprite):
    def __init__(self, x, y, turret_image, fireball_image):
        """
        x, y: turret position
        turret_image: the tower sprite
        fireball_image: the bullet sprite to be fired
        """
        super().__init__()
        self.image = turret_image
        self.rect = self.image.get_rect(center=(x, y))

        self.range = TURRET_RANGE
        self.fire_rate = TURRET_FIRE_RATE
        self.fire_timer = 0
        self.fireball_image = fireball_image

    def update(self, enemies, bullet_group):
        if self.fire_timer > 0:
            self.fire_timer -= 1
        else:
            target = self.find_target_in_range(enemies)
            if target:
                # Create a bullet using the fireball sprite
                bullet = Bullet(
                    self.rect.centerx,
                    self.rect.centery,
                    target.rect.center,
                    self.fireball_image
                )
                bullet_group.add(bullet)
                # Reset firing cooldown
                self.fire_timer = self.fire_rate

    def find_target_in_range(self, enemies):
        for enemy in enemies:
            dist = math.dist(self.rect.center, enemy.rect.center)
            if dist <= self.range:
                return enemy
        return None

# --------------------------------------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, target_pos, bullet_image):
        """
        start_x, start_y: initial position of the bullet
        target_pos: (x, y) of enemy's position at firing
        bullet_image: the base image (fireball.png)
        """
        super().__init__()
        self.original_image = bullet_image

        # Calculate direction
        dx = target_pos[0] - start_x
        dy = target_pos[1] - start_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 0.0001  # Avoid division-by-zero

        # Velocity
        self.speed = TURRET_BULLET_SPEED
        self.damage = TURRET_BULLET_DAMAGE
        self.vel_x = (dx / dist) * self.speed
        self.vel_y = (dy / dist) * self.speed

        # Rotate sprite so it points in travel direction
        # atan2 returns the angle in radians between the x-axis and the point (dx, -dy)
        angle_radians = math.atan2(-dy, dx)  
        angle_degrees = math.degrees(angle_radians)
        
        self.image = pygame.transform.rotate(self.original_image, angle_degrees)
        self.rect = self.image.get_rect(center=(start_x, start_y))

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # If bullet goes off-screen, remove it
        if (self.rect.x < -100 or self.rect.x > 2000 or
            self.rect.y < -100 or self.rect.y > 2000):
            self.kill()
