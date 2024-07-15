import pygame
import math
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import player_sprite
from entities.magic_missile import MagicMissile

class Player(Entity):
    def __init__(self):
        super().__init__(MAP_WIDTH // 2, MAP_HEIGHT // 2, player_sprite, 3, 100)
        self.coins = 0
        self.facing_right = True
        self.attack_cooldown = 0
        self.magic_missile_cooldown = 0
        self.camera_x = 0
        self.camera_y = 0

    def move(self, dx, dy, buildings):
        new_x = self.rect.x + dx * self.speed
        new_y = self.rect.y + dy * self.speed

        new_x = max(0, min(new_x, MAP_WIDTH - self.rect.width))
        new_y = max(0, min(new_y, MAP_HEIGHT - self.rect.height))

        new_rect = self.rect.copy()
        new_rect.x = new_x
        new_rect.y = new_y

        for building in buildings:
            if building.collide_with_player(new_rect):
                if dx > 0:
                    new_x = building.rect.left - self.rect.width
                elif dx < 0:
                    new_x = building.rect.right
                if dy > 0:
                    new_y = building.rect.top - self.rect.height
                elif dy < 0:
                    new_y = building.rect.bottom

        self.rect.x = new_x
        self.rect.y = new_y

        # Update camera position
        self.camera_x = max(0, min(self.rect.centerx - WIDTH // 2, MAP_WIDTH - WIDTH))
        self.camera_y = max(0, min(self.rect.centery - HEIGHT // 2, MAP_HEIGHT - HEIGHT))

    def attack(self, monsters):
        if self.attack_cooldown == 0:
            for monster in monsters:
                if self.rect.colliderect(monster.rect):
                    monster.health -= 20  # Attack damage
                    print(f"Attacked {monster.__class__.__name__} for 20 damage")
            self.attack_cooldown = 30
        else:
            self.attack_cooldown -= 1

    def fire_magic_missile(self, target_pos):
        if self.magic_missile_cooldown == 0:
            self.magic_missile_cooldown = 60  # 1 second cooldown at 60 FPS
            return MagicMissile(self.rect.center, target_pos)
        return None

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.magic_missile_cooldown > 0:
            self.magic_missile_cooldown -= 1

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x - self.camera_x, self.rect.y - self.camera_y))
        self.draw_health_bar(surface, self.camera_x, self.camera_y)