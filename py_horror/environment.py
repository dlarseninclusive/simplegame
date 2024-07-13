import pygame
import random
from constants import *
from base_classes import Monster, BossMonster, Coin
from sprites import house_sprites, mansion_sprite, zombie_sprite, tracker_sprite, bat_sprite, dirt_road_sprite, grass_sprite, furniture_sprites

class Village:
    def __init__(self):
        self.buildings = pygame.sprite.Group()
        self.monsters = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.mansion = None
        self.grass_sprite = pygame.transform.scale(grass_sprite, (grass_sprite.get_width() // 2, grass_sprite.get_height() // 2))
        self.setup_village()

    def setup_village(self):
        # Create horizontal and vertical roads
        self.vertical_road = pygame.Surface((100, MAP_HEIGHT))
        self.vertical_road.fill(BROWN)
        self.vertical_road_rect = self.vertical_road.get_rect(center=(MAP_WIDTH // 2, MAP_HEIGHT // 2))

        self.horizontal_road = pygame.Surface((MAP_WIDTH, 100))
        self.horizontal_road.fill(BROWN)
        self.horizontal_road_rect = self.horizontal_road.get_rect(center=(MAP_WIDTH // 2, MAP_HEIGHT // 2))

        # Scale up house sprites by 25%
        scaled_house_sprites = [pygame.transform.scale(sprite, (int(sprite.get_width() * 1.25), int(sprite.get_height() * 1.25))) for sprite in house_sprites]

        # Adjust house positions to be closer to the road
        house_positions = [
            (MAP_WIDTH // 2 - 300, 150), (MAP_WIDTH // 2 + 200, 150),
            (MAP_WIDTH // 2 - 300, 400), (MAP_WIDTH // 2 + 200, 400),
            (MAP_WIDTH // 2 - 300, MAP_HEIGHT - 250), (MAP_WIDTH // 2 + 200, MAP_HEIGHT - 250),
            (100, MAP_HEIGHT // 2 - 150), (100, MAP_HEIGHT // 2 + 50),
            (MAP_WIDTH - 300, MAP_HEIGHT // 2 - 150), (MAP_WIDTH - 300, MAP_HEIGHT // 2 + 50)
        ]

        for i, pos in enumerate(house_positions):
            house = Building(pos, scaled_house_sprites[i % len(scaled_house_sprites)], facing_south=(pos[1] < MAP_HEIGHT // 2))
            self.buildings.add(house)
            for _ in range(random.randint(1, 3)):
                monster_type = random.choice(["zombie", "tracker", "bat"])
                monster = self.create_monster(monster_type, pos[0] + random.randint(0, house.rect.width),
                                              pos[1] + random.randint(0, house.rect.height))
                self.monsters.add(monster)

        mansion_pos = (MAP_WIDTH // 2 - mansion_sprite.get_width() // 2, 50)
        self.mansion = Building(mansion_pos, mansion_sprite, facing_south=True)
        self.buildings.add(self.mansion)

        for _ in range(20):
            self.spawn_coin()

    def create_monster(self, monster_type, x, y):
        if monster_type == "zombie":
            return Monster(x, y, zombie_sprite, 0.5, 50, "zombie")
        elif monster_type == "tracker":
            return Monster(x, y, tracker_sprite, 1, 30, "tracker")
        else:
            bat_sprite_scaled = pygame.transform.scale(bat_sprite, (bat_sprite.get_width() // 2, bat_sprite.get_height() // 2))
            return Monster(x, y, bat_sprite_scaled, 1.5, 20, "bat")

    def update(self, player):
        self.monsters.update()
        self.coins.update()
        # Remove dead monsters
        self.monsters = pygame.sprite.Group([monster for monster in self.monsters if monster.health > 0])

    def draw(self, screen, camera_x, camera_y):
        for y in range(0, MAP_HEIGHT, self.grass_sprite.get_height()):
            for x in range(0, MAP_WIDTH, self.grass_sprite.get_width()):
                screen.blit(self.grass_sprite, (x - camera_x, y - camera_y))

        screen.blit(self.vertical_road, (self.vertical_road_rect.x - camera_x, self.vertical_road_rect.y - camera_y))
        screen.blit(self.horizontal_road, (self.horizontal_road_rect.x - camera_x, self.horizontal_road_rect.y - camera_y))

        for building in self.buildings:
            screen.blit(building.image, (building.rect.x - camera_x, building.rect.y - camera_y))
            pygame.draw.rect(screen, GREEN, (building.entrance.x - camera_x, building.entrance.y - camera_y, 
                                             building.entrance.width, building.entrance.height))

        for monster in self.monsters:
            screen.blit(monster.image, (monster.rect.x - camera_x, monster.rect.y - camera_y))
            monster.draw_health_bar(screen, camera_x, camera_y)
            font = pygame.font.Font(None, 20)
            text = font.render(monster.monster_type, True, WHITE)
            screen.blit(text, (monster.rect.x - camera_x, monster.rect.y - 25 - camera_y))

        for coin in self.coins:
            screen.blit(coin.image, (coin.rect.x - camera_x, coin.rect.y - camera_y))

    def spawn_coin(self):
        x = random.randint(0, MAP_WIDTH)
        y = random.randint(0, MAP_HEIGHT)
        coin = Coin(x, y)
        self.coins.add(coin)

class Building(pygame.sprite.Sprite):
    def __init__(self, pos, sprite, facing_south=True):
        super().__init__()
        self.image = sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        entrance_width = 50  # Increased entrance width
        entrance_height = 12  # Increased entrance height
        if facing_south:
            self.entrance = pygame.Rect(self.rect.centerx - entrance_width // 2, 
                                        self.rect.bottom - entrance_height, 
                                        entrance_width, entrance_height)
        else:
            self.entrance = pygame.Rect(self.rect.centerx - entrance_width // 2, 
                                        self.rect.top, 
                                        entrance_width, entrance_height)

class IndoorScene:
    def __init__(self, building):
        self.building = building
        self.monsters = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.furniture = pygame.sprite.Group()
        self.setup_room()

    def setup_room(self):
        for _ in range(random.randint(1, 3)):
            monster_type = random.choice(["zombie", "tracker", "bat"])
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            monster = self.create_monster(monster_type, x, y)
            self.monsters.add(monster)

        for _ in range(random.randint(1, 5)):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            coin = Coin(x, y)
            self.coins.add(coin)

        # Add furniture
        for _ in range(random.randint(3, 6)):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            furniture = pygame.sprite.Sprite()
            furniture.image = random.choice(furniture_sprites)
            furniture.rect = furniture.image.get_rect(topleft=(x, y))
            self.furniture.add(furniture)

    def create_monster(self, monster_type, x, y):
        if monster_type == "zombie":
            return Monster(x, y, zombie_sprite, 0.5, 50, "zombie")
        elif monster_type == "tracker":
            return Monster(x, y, tracker_sprite, 1, 30, "tracker")
        else:
            bat_sprite_scaled = pygame.transform.scale(bat_sprite, (bat_sprite.get_width() // 2, bat_sprite.get_height() // 2))
            return Monster(x, y, bat_sprite_scaled, 1.5, 20, "bat")

    def update(self, player):
        self.monsters.update()
        self.coins.update()
        # Remove dead monsters
        self.monsters = pygame.sprite.Group([monster for monster in self.monsters if monster.health > 0])

    def draw(self, screen, camera_x, camera_y):
        screen.fill(BROWN)  # Fill with a brown color to represent wooden floor
        
        # Draw furniture
        for furniture in self.furniture:
            screen.blit(furniture.image, (furniture.rect.x - camera_x, furniture.rect.y - camera_y))
        
        # Draw exit
        exit_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 20, 40, 20)
        pygame.draw.rect(screen, GREEN, exit_rect)
        font = pygame.font.Font(None, 20)
        text = font.render("EXIT", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT - 20))
        
        for monster in self.monsters:
            screen.blit(monster.image, (monster.rect.x - camera_x, monster.rect.y - camera_y))
            monster.draw_health_bar(screen, camera_x, camera_y)
            text = font.render(monster.monster_type, True, WHITE)
            screen.blit(text, (monster.rect.x - camera_x, monster.rect.y - 25 - camera_y))
        
        for coin in self.coins:
            screen.blit(coin.image, (coin.rect.x - camera_x, coin.rect.y - camera_y))

class MansionScene(IndoorScene):
    def __init__(self, building):
        super().__init__(building)
        self.boss = None
        self.setup_mansion()

    def setup_mansion(self):
        # Place the boss in the mansion
        boss_x = WIDTH // 2
        boss_y = HEIGHT // 2
        self.boss = BossMonster(boss_x, boss_y)
        self.monsters.add(self.boss)

        # Add more furniture and decorations specific to the mansion
        for _ in range(random.randint(5, 8)):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            furniture = pygame.sprite.Sprite()
            furniture.image = random.choice(furniture_sprites)
            furniture.rect = furniture.image.get_rect(topleft=(x, y))
            self.furniture.add(furniture)

    def draw(self, screen, camera_x, camera_y):
        super().draw(screen, camera_x, camera_y)
        # Add any mansion-specific drawing here
        font = pygame.font.Font(None, 36)
        text = font.render("Mansion", True, RED)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))