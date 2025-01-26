import pygame
from settings import BLUE

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, target_scene):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.target_scene = target_scene
