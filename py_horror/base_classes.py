import pygame
import random
from constants import *
from sprites import coin_sprite, boss_sprite

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
        bar_width = self.rect.width * 1.5  # Increased width
        bar_height = 10  # Increased height
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                   self.rect.y - 20 - camera_y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                self.rect.y - 20 - camera_y, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

class Monster(Entity):
    def __init__(self, x, y, sprite, speed, max_health, monster_type):
        super().__init__(x, y, sprite, speed, max_health)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.monster_type = monster_type

    def update(self):
        if random.random() < 0.01:
            self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        self.rect.x = max(0, min(self.rect.x, MAP_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, MAP_HEIGHT - self.rect.height))

class BossMonster(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, boss_sprite, 1, 200)
        self.monster_type = "Boss"

    def update(self):
        pass

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = coin_sprite
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)