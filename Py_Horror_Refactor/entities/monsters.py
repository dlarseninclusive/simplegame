import pygame
import random
import math
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import zombie_sprite, tracker_sprite, bat_sprite, boss_sprite

class Monster(Entity):
    def __init__(self, x, y, sprite, speed, max_health, monster_type):
        super().__init__(x, y, sprite, speed, max_health)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.monster_type = monster_type
        self.coin_drop_chance = 0.5  # 50% chance to drop a coin
        self.last_attack_time = 0
        self.attack_damage = MONSTER_ATTACK_DAMAGE
        self.attack_range = 50  # pixels

    def update(self, player):
        if random.random() < 0.01:
            self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
    
    # Move towards player if in range
        distance_to_player = pygame.math.Vector2(player.rect.center) - pygame.math.Vector2(self.rect.center)
        if distance_to_player.length_squared() > 0:  # Check if the distance is not zero
            if distance_to_player.length() < 200:  # Start chasing when within 200 pixels
                self.direction = distance_to_player.normalize()
        else:
        # If the distance is zero, choose a random direction
            self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))

        new_x = self.rect.x + self.direction.x * self.speed
        new_y = self.rect.y + self.direction.y * self.speed

        self.rect.x = max(0, min(new_x, MAP_WIDTH - self.rect.width))
        self.rect.y = max(0, min(new_y, MAP_HEIGHT - self.rect.height))

    def can_attack(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time > MONSTER_ATTACK_COOLDOWN

    def attack(self, player):
        if self.can_attack():
            player.take_damage(self.attack_damage)
            self.last_attack_time = pygame.time.get_ticks()

    def drop_coin(self):
        if random.random() < self.coin_drop_chance:
            from entities.coin import Coin
            return Coin(self.rect.centerx, self.rect.centery)
        return None

class BossMonster(Monster):
    def __init__(self, x, y):
        super().__init__(x, y, boss_sprite, MONSTER_SPEED * 0.5, 200, "Boss")
        self.coin_drop_chance = 1.0  # Boss always drops a coin
        self.attack_damage = MONSTER_ATTACK_DAMAGE * 2
        self.attack_range = 100  # pixels

    def update(self, player):
        # Boss-specific behavior
        super().update(player)
        # Add any additional boss-specific behavior here