import pygame
import random
from constants import *
from entities.monsters import Monster
from utils.sprite_loader import headstone_sprite, graveyard_floor_sprite, zombie_sprite, tracker_sprite, bat_sprite

class GraveyardScene:
    def __init__(self):
        self.monsters = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.headstones = pygame.sprite.Group()
        self.setup_graveyard()

    def setup_graveyard(self):
        # Add headstones
        for _ in range(20):
            headstone = pygame.sprite.Sprite()
            headstone.image = headstone_sprite
            headstone.rect = headstone.image.get_rect()
            headstone.rect.x = random.randint(50, WIDTH - 50)
            headstone.rect.y = random.randint(50, HEIGHT - 50)
            self.headstones.add(headstone)

        # Add monsters
        for _ in range(10):
            monster_type = random.choice(["zombie", "tracker", "bat"])
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            sprite = {
                "zombie": zombie_sprite,
                "tracker": tracker_sprite,
                "bat": bat_sprite
            }[monster_type]
            monster = Monster(x, y, sprite, 1, 40, monster_type)
            self.monsters.add(monster)

    def update(self, player):
        self.monsters.update(player)
        self.coins.update()

    def draw(self, screen, camera_x, camera_y):
        # Draw graveyard floor
        for y in range(0, HEIGHT, graveyard_floor_sprite.get_height()):
            for x in range(0, WIDTH, graveyard_floor_sprite.get_width()):
                screen.blit(graveyard_floor_sprite, (x, y))

        # Draw headstones
        for headstone in self.headstones:
            screen.blit(headstone.image, headstone.rect)

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