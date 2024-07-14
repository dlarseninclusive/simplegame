import pygame
import random
from constants import *
from game_objects import Building, Monster, BossMonster
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
        road_width = 100
        self.vertical_road = self.create_textured_road(road_width, MAP_HEIGHT)
        self.vertical_road_rect = self.vertical_road.get_rect(center=(MAP_WIDTH // 2, MAP_HEIGHT // 2))

        self.horizontal_road = self.create_textured_road(MAP_WIDTH, road_width)
        self.horizontal_road_rect = self.horizontal_road.get_rect(center=(MAP_WIDTH // 2, MAP_HEIGHT // 2))

        # Define building positions
        building_positions = [
            (MAP_WIDTH // 2 - 300, MAP_HEIGHT // 2 - 250),  # Top left
            (MAP_WIDTH // 2 + 200, MAP_HEIGHT // 2 - 250),  # Top right
            (MAP_WIDTH // 2 - 300, MAP_HEIGHT // 2 + 150),  # Bottom left
            (MAP_WIDTH // 2 + 200, MAP_HEIGHT // 2 + 150),  # Bottom right
        ]

        for i, pos in enumerate(building_positions):
            house = Building(pos, house_sprites[i % len(house_sprites)], facing_south=(pos[1] < MAP_HEIGHT // 2))
            self.buildings.add(house)
            
            # Add monsters near the house
            for _ in range(random.randint(1, 3)):
                monster_type = random.choice(["zombie", "tracker", "bat"])
                monster_x = pos[0] + random.randint(0, house.rect.width)
                monster_y = pos[1] + random.randint(0, house.rect.height)
                monster = self.create_monster(monster_type, monster_x, monster_y)
                self.monsters.add(monster)

        # Add mansion at the top center
        mansion_pos = (MAP_WIDTH // 2 - mansion_sprite.get_width() // 2, 50)
        self.mansion = Building(mansion_pos, mansion_sprite, facing_south=True)
        self.buildings.add(self.mansion)

    def create_textured_road(self, width, height):
        road_surface = pygame.Surface((width, height))
        tile_width, tile_height = dirt_road_sprite.get_width(), dirt_road_sprite.get_height()
        
        for y in range(0, height, tile_height):
            for x in range(0, width, tile_width):
                road_surface.blit(dirt_road_sprite, (x, y))
        
        return road_surface

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

# ... (rest of the file remains the same)

class IndoorScene:
    def __init__(self, building):
        self.building = building
        self.monsters = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.furniture = pygame.sprite.Group()
        self.setup_room()

    def setup_room(self):
        room_width, room_height = WIDTH, HEIGHT
        furniture_positions = [
            (room_width * 0.2, room_height * 0.2),  # Top left
            (room_width * 0.8, room_height * 0.2),  # Top right
            (room_width * 0.2, room_height * 0.8),  # Bottom left
            (room_width * 0.8, room_height * 0.8),  # Bottom right
            (room_width * 0.5, room_height * 0.5),  # Center
        ]

        for pos in furniture_positions:
            furniture = pygame.sprite.Sprite()
            furniture.image = random.choice(furniture_sprites)
            furniture.rect = furniture.image.get_rect(center=pos)
            self.furniture.add(furniture)

        # Add monsters
        for _ in range(random.randint(1, 3)):
            monster_type = random.choice(["zombie", "tracker", "bat"])
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            monster = self.create_monster(monster_type, x, y)
            self.monsters.add(monster)

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
            furniture = pygame.sprite.Sprite()
            furniture.image = random.choice(furniture_sprites)
            furniture.rect = furniture.image.get_rect(topleft=(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)))
            self.furniture.add(furniture)

    def draw(self, screen, camera_x, camera_y):
        super().draw(screen, camera_x, camera_y)
        # Add any mansion-specific drawing here
        font = pygame.font.Font(None, 36)
        text = font.render("Mansion", True, RED)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))