import pygame
import math
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import player_sprite

class Player(Entity):
    def __init__(self):
        super().__init__(MAP_WIDTH // 2, MAP_HEIGHT // 2, player_sprite, 3, 100)
        self.camera_x = 0
        self.camera_y = 0
        self.coins = 0
        self.target_pos = None

    def set_target(self, pos):
        self.target_pos = pos

    def move(self, dx, dy, buildings):
        if self.target_pos:
            # Mouse movement
            target_dx = self.target_pos[0] - self.rect.centerx
            target_dy = self.target_pos[1] - self.rect.centery
            distance = math.hypot(target_dx, target_dy)
            if distance < self.speed:
                self.rect.center = self.target_pos
                self.target_pos = None
            else:
                dx = (target_dx / distance) * self.speed
                dy = (target_dy / distance) * self.speed
        else:
            # Keyboard movement
            dx *= self.speed
            dy *= self.speed

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

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

    def collect_coin(self, coin):
        self.coins += 1
        coin.kill()

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x - self.camera_x, self.rect.y - self.camera_y))
        self.draw_health_bar(surface, self.camera_x, self.camera_y)