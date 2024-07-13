import pygame
import random
from constants import *
from entities import Monster

class Building(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.entrance = pygame.Rect(x + width // 2 - 20, y + height - 10, 40, 10)

class Village:
    def __init__(self):
        self.buildings = pygame.sprite.Group()
        self.monsters = pygame.sprite.Group()
        self.setup_village()

    def setup_village(self):
        buildings = [
            (50, 50, 100, 100),
            (200, 100, 150, 120),
            (400, 50, 120, 100),
            (600, 100, 100, 100),
            (100, 300, 200, 150),
            (400, 300, 180, 130),
        ]
        for building in buildings:
            self.buildings.add(Building(*building))

        for _ in range(5):
            self.monsters.add(Monster("zombie", random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        for _ in range(2):
            self.monsters.add(Monster("tracker", random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        for _ in range(3):
            self.monsters.add(Monster("bat", random.randint(0, WIDTH), random.randint(0, HEIGHT)))

    def draw(self, screen):
        for building in self.buildings:
            screen.blit(building.image, building.rect)
            pygame.draw.rect(screen, GREEN, building.entrance)
        for monster in self.monsters:
            screen.blit(monster.image, monster.rect)
            monster.draw_health_bar(screen)

    def update(self, player):
        self.monsters.update(player)

class IndoorScene:
    def __init__(self):
        self.monsters = pygame.sprite.Group()
        self.setup_room()

    def setup_room(self):
        self.monsters.add(Monster("vampire", random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)))
        for _ in range(3):
            self.monsters.add(Monster("bat", random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)))

    def draw(self, screen):
        screen.fill(BLACK)
        pygame.draw.rect(screen, GREEN, (WIDTH // 2 - 20, HEIGHT - 10, 40, 10))  # Exit
        for monster in self.monsters:
            screen.blit(monster.image, monster.rect)
            monster.draw_health_bar(screen)

    def update(self, player):
        self.monsters.update(player)