import pygame
import random
from constants import *
from entities.monsters import Monster
from environment.building import Building, MansionBuilding
from utils.sprite_loader import house_sprites, mansion_sprite, zombie_sprite, tracker_sprite, bat_sprite, grass_sprite

class Village:
    def __init__(self):
        self.buildings = pygame.sprite.Group()
        self.monsters = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.setup_village()

    def setup_village(self):
        # Create buildings
        building_positions = [
            (MAP_WIDTH // 4, MAP_HEIGHT // 4),
            (3 * MAP_WIDTH // 4, MAP_HEIGHT // 4),
            (MAP_WIDTH // 4, 3 * MAP_HEIGHT // 4),
            (3 * MAP_WIDTH // 4, 3 * MAP_HEIGHT // 4),
        ]
        for pos in building_positions:
            house = Building(pos, random.choice(house_sprites))
            self.buildings.add(house)

        # Add a mansion
        mansion = MansionBuilding((MAP_WIDTH // 2, MAP_HEIGHT // 2), mansion_sprite)
        self.buildings.add(mansion)

        # Create graveyard entrance
        self.graveyard_entrance = pygame.Rect(MAP_WIDTH - 100, MAP_HEIGHT // 2, 50, 50)

        # Create monsters
        for _ in range(10):
            monster_type = random.choice(["zombie", "tracker", "bat"])
            x = random.randint(0, MAP_WIDTH)
            y = random.randint(0, MAP_HEIGHT)
            sprite = {
                "zombie": zombie_sprite,
                "tracker": tracker_sprite,
                "bat": bat_sprite
            }[monster_type]
            monster = Monster(x, y, sprite, 1, 50, monster_type)
            self.monsters.add(monster)

    def update(self, player):
        self.monsters.update(player)
        self.coins.update()

    def draw(self, screen, camera_x, camera_y):
        # Draw background
        for y in range(0, MAP_HEIGHT, grass_sprite.get_height()):
            for x in range(0, MAP_WIDTH, grass_sprite.get_width()):
                screen.blit(grass_sprite, (x - camera_x, y - camera_y))

        # Draw buildings
        for building in self.buildings:
            screen.blit(building.image, (building.rect.x - camera_x, building.rect.y - camera_y))

        # Draw monsters
        for monster in self.monsters:
            screen.blit(monster.image, (monster.rect.x - camera_x, monster.rect.y - camera_y))
            monster.draw_health_bar(screen, camera_x, camera_y)

        # Draw coins
        for coin in self.coins:
            screen.blit(coin.image, (coin.rect.x - camera_x, coin.rect.y - camera_y))

        # Draw graveyard entrance
        pygame.draw.rect(screen, GRAY, (self.graveyard_entrance.x - camera_x, self.graveyard_entrance.y - camera_y, 
                                        self.graveyard_entrance.width, self.graveyard_entrance.height))