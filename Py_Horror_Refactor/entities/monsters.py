import pygame
import random
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import zombie_sprite, tracker_sprite, bat_sprite, boss_sprite

class Monster(Entity):
    def __init__(self, x, y, sprite, speed, max_health, monster_type):
        super().__init__(x, y, sprite, speed, max_health)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.monster_type = monster_type
        self.coin_drop_chance = 0.5  # 50% chance to drop a coin

    def update(self, player):
        if random.random() < 0.01:
            self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        self.rect.x = max(0, min(self.rect.x, MAP_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, MAP_HEIGHT - self.rect.height))

    def drop_coin(self):
        if random.random() < self.coin_drop_chance:
            from entities.coin import Coin
            return Coin(self.rect.centerx, self.rect.centery)
        return None

class BossMonster(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, boss_sprite, 1, 200)
        self.monster_type = "Boss"
        self.coin_drop_chance = 1.0  # Boss always drops a coin

    def update(self, player):
        # Boss-specific behavior
        pass

    def drop_coin(self):
        from entities.coin import Coin
        return Coin(self.rect.centerx, self.rect.centery)