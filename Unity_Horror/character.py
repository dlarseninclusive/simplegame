import pygame
import math
from settings import RED, WHITE, WORLD_WIDTH, WORLD_HEIGHT

class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.max_health = 100
        self.health = self.max_health
        self.inventory = []
        self.target_pos = None

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
        # Keep character within world boundaries
        self.rect.x = max(0, min(self.rect.x, WORLD_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, WORLD_HEIGHT - self.rect.height))

    def update(self):
        if self.target_pos:
            dx = self.target_pos[0] - self.rect.centerx
            dy = self.target_pos[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > self.speed:
                dx, dy = dx / dist, dy / dist
                self.move(dx * self.speed, dy * self.speed)
            else:
                self.target_pos = None

    def attack(self):
        return pygame.Rect(self.rect.centerx - 15, self.rect.centery - 15, 30, 30)

    def draw_health_bar(self, surface, camera):
        bar_width = 30
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)
