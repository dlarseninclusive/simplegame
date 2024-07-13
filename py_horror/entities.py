import pygame
import random
from constants import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, color, x, y, width, height, speed, max_health):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.max_health = max_health
        self.health = max_health

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x, self.rect.y - 10, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y - 10, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

class Player(Entity):
    def __init__(self):
        super().__init__(WHITE, WIDTH // 2, HEIGHT // 2, 20, 20, 5, 100)
        self.attack_cooldown = 0
        self.attack_range = 50
        self.attack_damage = 20

    def move(self, dx, dy, buildings):
        new_x = self.rect.x + dx * self.speed
        new_y = self.rect.y + dy * self.speed

        # Check x-axis movement
        self.rect.x = new_x
        collided = False
        for building in buildings:
            if self.rect.colliderect(building.rect) and not building.entrance.colliderect(self.rect):
                collided = True
                if dx > 0:  # Moving right
                    self.rect.right = building.rect.left
                elif dx < 0:  # Moving left
                    self.rect.left = building.rect.right
        if not collided:
            self.rect.x = new_x

        # Check y-axis movement
        self.rect.y = new_y
        collided = False
        for building in buildings:
            if self.rect.colliderect(building.rect) and not building.entrance.colliderect(self.rect):
                collided = True
                if dy > 0:  # Moving down
                    self.rect.bottom = building.rect.top
                elif dy < 0:  # Moving up
                    self.rect.top = building.rect.bottom
        if not collided:
            self.rect.y = new_y

        # Keep player within screen bounds
        self.rect.clamp_ip(screen.get_rect())

    def attack(self, monsters):
        if self.attack_cooldown == 0:
            for monster in monsters:
                if monster.rect.colliderect(self.rect.inflate(self.attack_range, self.attack_range)):
                    monster.take_damage(self.attack_damage)
            self.attack_cooldown = 30  # Set cooldown to 30 frames (0.5 seconds at 60 FPS)

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

class Monster(Entity):
    def __init__(self, monster_type, x, y):
        if monster_type == "zombie":
            super().__init__(GREEN, x, y, 30, 30, 0.5, 50)
        elif monster_type == "tracker":
            super().__init__(RED, x, y, 30, 30, 1, 30)
        elif monster_type == "vampire":
            super().__init__(PURPLE, x, y, 30, 30, 0.75, 80)
        elif monster_type == "bat":
            super().__init__(DARK_ORANGE, x, y, 20, 20, 1.5, 20)
        self.type = monster_type

    def update(self, player):
        dx = player.rect.x - self.rect.x
        dy = player.rect.y - self.rect.y
        dist = (dx**2 + dy**2)**0.5
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()