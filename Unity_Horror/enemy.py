import pygame
import random
from settings import RED, WHITE

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = random.randint(1, 3)
        self.max_health = 50
        self.health = self.max_health

    def update(self, target):
        dx = target.rect.x - self.rect.x
        dy = target.rect.y - self.rect.y
        dist = max(abs(dx), abs(dy))
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

    def draw_health_bar(self, surface, camera):
        bar_width = 20
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)
