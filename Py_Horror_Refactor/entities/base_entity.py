import pygame
from constants import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite, speed, max_health):
        super().__init__()
        self.image = sprite
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.max_health = max_health
        self.health = max_health

    def draw_health_bar(self, surface, camera_x, camera_y):
        bar_width = self.rect.width * 1.5
        bar_height = 10
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                   self.rect.y - 20 - camera_y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                self.rect.y - 20 - camera_y, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)