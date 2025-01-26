# File: player.py

import pygame
from config import PLAYER_SPEED

class Player(pygame.sprite.Sprite):
    """
    Represents the player character.
    """
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, keys_pressed):
        dx = (keys_pressed[pygame.K_d] - keys_pressed[pygame.K_a]) * PLAYER_SPEED
        dy = (keys_pressed[pygame.K_s] - keys_pressed[pygame.K_w]) * PLAYER_SPEED

        self.rect.x += dx
        self.rect.y += dy
