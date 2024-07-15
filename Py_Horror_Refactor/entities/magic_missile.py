import pygame
import math
from utils.sprite_loader import magic_missile_sprite

class MagicMissile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = magic_missile_sprite
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.speed = 5
        self.damage = 30
        angle = math.atan2(target_pos[1] - start_pos[1], target_pos[0] - start_pos[0])
        self.velocity = pygame.math.Vector2(math.cos(angle) * self.speed, math.sin(angle) * self.speed)

    def update(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # Remove the missile if it goes off-screen
        if not pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT).colliderect(self.rect):
            self.kill()