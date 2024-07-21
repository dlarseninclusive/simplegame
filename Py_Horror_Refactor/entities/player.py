import pygame
import math
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import player_sprite
from entities.magic_missile import MagicMissile

class Player(Entity):
    def __init__(self):
        super().__init__(MAP_WIDTH // 2, MAP_HEIGHT // 2, player_sprite, PLAYER_SPEED, PLAYER_MAX_HEALTH)
        self.coins = 0
        self.facing_right = True
        self.attack_cooldown = 0
        self.magic_missile_cooldown = 0
        self.camera_x = 0
        self.camera_y = 0
        self.target_pos = None
        self.last_damage_time = 0
        self.invincible = False
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = 0.5
        self.friction = -0.1
        self.max_speed = PLAYER_SPEED

    def move(self, dx, dy, buildings):
        # Apply acceleration
        self.velocity.x += dx * self.acceleration
        self.velocity.y += dy * self.acceleration

        # Apply friction
        self.velocity.x += self.velocity.x * self.friction
        self.velocity.y += self.velocity.y * self.friction

        # Limit speed
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        # Calculate new position
        new_pos = self.rect.center + self.velocity

        # Horizontal movement and collision
        new_rect = self.rect.copy()
        new_rect.centerx = new_pos.x
        for building in buildings:
            if new_rect.colliderect(building.rect) and not building.entrance.colliderect(new_rect):
                if self.velocity.x > 0:  # Moving right
                    new_rect.right = building.rect.left
                elif self.velocity.x < 0:  # Moving left
                    new_rect.left = building.rect.right
                self.velocity.x = 0

        # Vertical movement and collision
        new_rect.centery = new_pos.y
        for building in buildings:
            if new_rect.colliderect(building.rect) and not building.entrance.colliderect(new_rect):
                if self.velocity.y > 0:  # Moving down
                    new_rect.bottom = building.rect.top
                elif self.velocity.y < 0:  # Moving up
                    new_rect.top = building.rect.bottom
                self.velocity.y = 0

        # Constrain player to map boundaries
        new_rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))

        # Update player position
        self.rect = new_rect

        # Update facing direction
        if self.velocity.x != 0:
            self.facing_right = self.velocity.x > 0

        # Update camera position
        self.update_camera()

    def update_camera(self):
        self.camera_x = max(0, min(self.rect.centerx - WIDTH // 2, MAP_WIDTH - WIDTH))
        self.camera_y = max(0, min(self.rect.centery - HEIGHT // 2, MAP_HEIGHT - HEIGHT))

    def collect_coin(self, coin):
        self.coins += 1
        coin.kill()

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
            start_pos = (self.rect.centerx, self.rect.centery)
            return MagicMissile(start_pos, target_pos)
        return None

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.magic_missile_cooldown > 0:
            self.magic_missile_cooldown -= 1

        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time > PLAYER_INVINCIBILITY_TIME:
            self.invincible = False

    def draw(self, surface):
        image = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)
        if self.invincible and pygame.time.get_ticks() % 200 < 100:
            image.set_alpha(128)
        else:
            image.set_alpha(255)
        surface.blit(image, (self.rect.x - self.camera_x, self.rect.y - self.camera_y))
        self.draw_health_bar(surface, self.camera_x, self.camera_y)

    def reset_position(self, x, y):
        self.rect.center = (x, y)
        self.camera_x = max(0, min(self.rect.centerx - WIDTH // 2, MAP_WIDTH - WIDTH))
        self.camera_y = max(0, min(self.rect.centery - HEIGHT // 2, MAP_HEIGHT - HEIGHT))

    def set_target(self, pos):
        self.target_pos = pos

    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()
        if not self.invincible:
            self.health -= amount
            self.health = max(0, self.health)
            self.last_damage_time = current_time
            self.invincible = True
            print(f"Player took {amount} damage. Current health: {self.health}")
