import pygame
import random
from constants import *
from entities.monsters import Monster
from utils.sprite_loader import floor_sprite, furniture_sprites, zombie_sprite, tracker_sprite, bat_sprite

class IndoorScene:
    def __init__(self):
        self.monsters = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.furniture = pygame.sprite.Group()
        self.setup_room()

    def setup_room(self):
        # Add furniture
        for _ in range(5):
            furniture = pygame.sprite.Sprite()
            furniture.image = random.choice(furniture_sprites)
            furniture.rect = furniture.image.get_rect()
            furniture.rect.x = random.randint(50, WIDTH - 50)
            furniture.rect.y = random.randint(50, HEIGHT - 50)
            self.furniture.add(furniture)

        # Add monsters
        for _ in range(3):
            monster_type = random.choice(["zombie", "tracker", "bat"])
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            sprite = {
                "zombie": zombie_sprite,
                "tracker": tracker_sprite,
                "bat": bat_sprite
            }[monster_type]
            monster = Monster(x, y, sprite, 1, 30, monster_type)
            self.monsters.add(monster)

    def update(self, player):
        self.monsters.update(player)
        self.coins.update()

    def draw(self, screen, camera_x, camera_y):
        # Draw floor
        for y in range(0, HEIGHT, floor_sprite.get_height()):
            for x in range(0, WIDTH, floor_sprite.get_width()):
                screen.blit(floor_sprite, (x, y))

        # Draw furniture
        for furniture in self.furniture:
            screen.blit(furniture.image, furniture.rect)

        # Draw monsters
        for monster in self.monsters:
            screen.blit(monster.image, monster.rect)
            monster.draw_health_bar(screen, 0, 0)

        # Draw coins
        for coin in self.coins:
            screen.blit(coin.image, coin.rect)

        # Draw exit
        pygame.draw.rect(screen, GREEN, (WIDTH // 2 - 25, HEIGHT - 20, 50, 20))
        exit_text = font.render("EXIT", True, BLACK)
        screen.blit(exit_text, (WIDTH // 2 - exit_text.get_width() // 2, HEIGHT - 20))