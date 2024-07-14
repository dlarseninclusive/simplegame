import pygame
import random
import math
from constants import *
from sprites import player_sprite, coin_sprite, boss_sprite, magic_missile_sprite

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
        bar_width = self.rect.width * 12
        bar_height = 12
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                   self.rect.y - 20 - camera_y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                self.rect.y - 20 - camera_y, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

class Player(Entity):
    def __init__(self):
        super().__init__(MAP_WIDTH // 2, MAP_HEIGHT // 2, player_sprite, 3, 100)
        self.attack_cooldown = 0
        self.attack_range = 30
        self.attack_damage = 20
        self.coins = 0
        self.facing_right = True
        self.target_pos = None
        self.magic_missile_cooldown = 0

    def move(self, dx, dy, buildings):
        if self.target_pos:
            dx = self.target_pos[0] - self.rect.centerx
            dy = self.target_pos[1] - self.rect.centery
            distance = math.hypot(dx, dy)
            
            if distance < self.speed:
                self.rect.center = self.target_pos
                self.target_pos = None
            else:
                dx = dx / distance * self.speed
                dy = dy / distance * self.speed
        
        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        new_x = max(0, min(new_x, MAP_WIDTH - self.rect.width))
        new_y = max(0, min(new_y, MAP_HEIGHT - self.rect.height))

        new_rect = self.rect.copy()
        new_rect.x = new_x
        new_rect.y = new_y

        for building in buildings:
            if new_rect.colliderect(building.rect) and not building.entrance.colliderect(new_rect):
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

        # Flip the character based on movement direction
        if dx > 0 and not self.facing_right:
            self.flip()
        elif dx < 0 and self.facing_right:
            self.flip()

    def set_target(self, pos):
        self.target_pos = pos

    def flip(self):
        self.image = pygame.transform.flip(self.image, True, False)
        self.facing_right = not self.facing_right

    def collect_coin(self, coin):
        self.coins += 1
        return CoinCollectEffect(coin.rect.center)

    def attack(self, monsters):
        if self.attack_cooldown == 0:
            for monster in monsters:
                if self.rect.colliderect(monster.rect):
                    monster.health -= self.attack_damage
                    print(f"Attacked {monster.__class__.__name__} for {self.attack_damage} damage")
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

class Monster(Entity):
    def __init__(self, x, y, sprite, speed, max_health, monster_type):
        super().__init__(x, y, sprite, speed, max_health)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.monster_type = monster_type
        self.coin_drop_chance = 0.5  # 50% chance to drop a coin

    def update(self):
        if random.random() < 0.01:
            self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        self.rect.x = max(0, min(self.rect.x, MAP_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, MAP_HEIGHT - self.rect.height))

    def drop_coin(self):
        if random.random() < self.coin_drop_chance:
            offset_x = random.randint(-30, 30)
            offset_y = random.randint(-30, 30)
            return Coin(self.rect.centerx + offset_x, self.rect.centery + offset_y)
        return None

class BossMonster(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, boss_sprite, 1, 200)
        self.monster_type = "Boss"
        self.coin_drop_chance = 1.0  # Boss always drops a coin

    def update(self):
        pass

    def drop_coin(self):
        offset_x = random.randint(-30, 30)
        offset_y = random.randint(-30, 30)
        return Coin(self.rect.centerx + offset_x, self.rect.centery + offset_y)

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = coin_sprite
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Building(pygame.sprite.Sprite):
    def __init__(self, pos, sprite, facing_south=True):
        super().__init__()
        self.image = sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        entrance_width = 50
        entrance_height = 12
        if facing_south:
            self.entrance = pygame.Rect(self.rect.centerx - entrance_width // 2, 
                                        self.rect.bottom - entrance_height, 
                                        entrance_width, entrance_height)
        else:
            self.entrance = pygame.Rect(self.rect.centerx - entrance_width // 2, 
                                        self.rect.top, 
                                        entrance_width, entrance_height)

    def collide_with_player(self, player_rect):
        return self.rect.colliderect(player_rect) and not self.entrance.colliderect(player_rect)

class CoinCollectEffect(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((50, 20), pygame.SRCALPHA)
        self.font = pygame.font.Font(None, 20)
        self.text = self.font.render("+1 Coin", True, YELLOW)
        self.image.blit(self.text, (0, 0))
        self.rect = self.image.get_rect(center=pos)
        self.timer = 60  # Effect lasts for 60 frames (1 second at 60 FPS)

    def update(self):
        self.rect.y -= 1
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

class MagicMissile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = magic_missile_sprite
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.speed = 5
        self.damage = 30
        angle = math.atan2(target_pos[1] - start_pos[1], target_pos[0] - start_pos[0])
        self.velocity = pygame.math.Vector2(math.cos(angle) * self.speed, math.sin(angle) * self.speed)

    def update(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # Remove the missile if it goes off-screen
        if not pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT).colliderect(self.rect):
            self.kill()