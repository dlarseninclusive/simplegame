import os

def create_file(path, content):
    with open(path, 'w') as file:
        file.write(content)
    print(f"Created: {path}")

def create_directory(path):
    os.makedirs(path, exist_ok=True)
    print(f"Created directory: {path}")

def generate_game_structure():
    # Create main directories
    create_directory('entities')
    create_directory('environment')
    create_directory('ui')
    create_directory('utils')
    create_directory('assets/sprites')

    # Create and populate files
    files = {
        'main.py': '''
from game import Game

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
''',
        'constants.py': '''
import pygame

# Game constants
WIDTH, HEIGHT = 1280, 720
FPS = 60

# Map size
MAP_WIDTH, MAP_HEIGHT = 1920, 1080

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (165, 42, 42)
DARK_BROWN = (101, 67, 33)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)

# Initialize pygame font
pygame.font.init()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
''',
        'game.py': '''
import pygame
from constants import *
from entities.player import Player
from environment.village import Village
from environment.indoor_scene import IndoorScene
from environment.mansion_scene import MansionScene
from environment.graveyard_scene import GraveyardScene
from ui.hud import HUD

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Village Horror")
        self.clock = pygame.time.Clock()
        self.player = Player()
        self.village = Village()
        self.indoor_scenes = {}  # To be populated
        self.mansion_scene = MansionScene()
        self.graveyard_scene = GraveyardScene()
        self.current_scene = "village"
        self.hud = HUD()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Handle other events

            self.update()
            self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def update(self):
        # Update current scene and player
        if self.current_scene == "village":
            self.village.update(self.player)
        elif self.current_scene == "indoor":
            self.indoor_scenes[self.current_building].update(self.player)
        elif self.current_scene == "mansion":
            self.mansion_scene.update(self.player)
        elif self.current_scene == "graveyard":
            self.graveyard_scene.update(self.player)

        self.player.update()

    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw current scene
        if self.current_scene == "village":
            self.village.draw(self.screen, self.player.camera_x, self.player.camera_y)
        elif self.current_scene == "indoor":
            self.indoor_scenes[self.current_building].draw(self.screen, 0, 0)
        elif self.current_scene == "mansion":
            self.mansion_scene.draw(self.screen, 0, 0)
        elif self.current_scene == "graveyard":
            self.graveyard_scene.draw(self.screen, 0, 0)

        # Draw player
        self.player.draw(self.screen)

        # Draw HUD
        self.hud.draw(self.screen, self.player)

    # Add other necessary methods
''',
        'entities/base_entity.py': '''
import pygame
from constants import *

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
        bar_width = self.rect.width * 1.5
        bar_height = 10
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                   self.rect.y - 20 - camera_y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera_x - (bar_width - self.rect.width) / 2, 
                                self.rect.y - 20 - camera_y, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)
''',
        'entities/player.py': '''
import pygame
import math
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import player_sprite

class Player(Entity):
    def __init__(self):
        super().__init__(MAP_WIDTH // 2, MAP_HEIGHT // 2, player_sprite, 3, 100)
        self.coins = 0
        self.facing_right = True
        self.attack_cooldown = 0
        self.magic_missile_cooldown = 0
        self.camera_x = 0
        self.camera_y = 0

    def move(self, dx, dy, buildings):
        new_x = self.rect.x + dx * self.speed
        new_y = self.rect.y + dy * self.speed

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
            return MagicMissile(self.rect.center, target_pos)
        return None

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.magic_missile_cooldown > 0:
            self.magic_missile_cooldown -= 1

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x - self.camera_x, self.rect.y - self.camera_y))
        self.draw_health_bar(surface, self.camera_x, self.camera_y)
''',
        'entities/monsters.py': '''
import pygame
import random
from constants import *
from entities.base_entity import Entity
from utils.sprite_loader import zombie_sprite, tracker_sprite, bat_sprite, boss_sprite

class Monster(Entity):
    def __init__(self, x, y, sprite, speed, max_health, monster_type):
        super().__init__(x, y, sprite, speed, max_health)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.monster_type = monster_type
        self.coin_drop_chance = 0.5  # 50% chance to drop a coin

    def update(self, player):
        if random.random() < 0.01:
            self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        self.rect.x = max(0, min(self.rect.x, MAP_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, MAP_HEIGHT - self.rect.height))

    def drop_coin(self):
        if random.random() < self.coin_drop_chance:
            from entities.coin import Coin
            return Coin(self.rect.centerx, self.rect.centery)
        return None

class BossMonster(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, boss_sprite, 1, 200)
        self.monster_type = "Boss"
        self.coin_drop_chance = 1.0  # Boss always drops a coin

    def update(self, player):
        # Boss-specific behavior
        pass

    def drop_coin(self):
        from entities.coin import Coin
        return Coin(self.rect.centerx, self.rect.centery)
''',
        'entities/coin.py': '''
import pygame
from utils.sprite_loader import coin_sprite

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = coin_sprite
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
''',
        'entities/magic_missile.py': '''
import pygame
import math
from utils.sprite_loader import magic_missile_sprite

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
''',
        'environment/village.py': '''
import pygame
import random
from constants import *
from entities.monsters import Monster
from environment.building import Building
from utils.sprite_loader import house_sprites, grass_sprite, dirt_road_sprite

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

        # Create monsters
        for _ in range(10):
            monster_type = random.choice(["zombie", "tracker", "bat"])
            x = random.randint(0, MAP_WIDTH)
            y = random.randint(0, MAP_HEIGHT)
            monster = Monster(x, y, zombie_sprite, 1, 50, monster_type)  # Placeholder sprite
            self.monsters.add(monster)

    def update(self, player):
        self.monsters.update(player)
        self.coins.update()

    def draw(self, screen, camera_x, camera_y):
        # Draw grass background
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
''',
        'environment/building.py': '''
import pygame

class Building(pygame.sprite.Sprite):
    def __init__(self, pos, sprite):
        super().__init__()
        self.image = sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        entrance_width = 50
        entrance_height = 12
        self.entrance = pygame.Rect(self.rect.centerx - entrance_width // 2, 
                                    self.rect.bottom - entrance_height, 
                                    entrance_width, entrance_height)

    def collide_with_player(self, player_rect):
        return self.rect.colliderect(player_rect) and not self.entrance.colliderect(player_rect)
''',

'environment/indoor_scene.py': '''
import pygame
import random
from constants import *
from entities.monsters import Monster
from utils.sprite_loader import floor_sprite, furniture_sprites

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
            monster = Monster(x, y, zombie_sprite, 1, 30, monster_type)  # Placeholder sprite
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
''',
        'environment/mansion_scene.py': '''
from environment.indoor_scene import IndoorScene
from entities.monsters import BossMonster
from constants import *

class MansionScene(IndoorScene):
    def __init__(self):
        super().__init__()
        self.boss = None
        self.setup_mansion()

    def setup_mansion(self):
        # Add boss
        self.boss = BossMonster(WIDTH // 2, HEIGHT // 2)
        self.monsters.add(self.boss)

        # Add more furniture and decorations specific to the mansion
        # (You can add more complex setup here)

    def update(self, player):
        super().update(player)
        # Add any mansion-specific update logic here

    def draw(self, screen, camera_x, camera_y):
        super().draw(screen, camera_x, camera_y)
        # Add any mansion-specific drawing here
        mansion_text = font.render("Mansion", True, RED)
        screen.blit(mansion_text, (WIDTH // 2 - mansion_text.get_width() // 2, 20))
''',
        'environment/graveyard_scene.py': '''
import pygame
import random
from constants import *
from entities.monsters import Monster
from utils.sprite_loader import headstone_sprite, graveyard_floor_sprite

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
            monster = Monster(x, y, zombie_sprite, 1, 40, monster_type)  # Placeholder sprite
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
''',
        'ui/hud.py': '''
import pygame
from constants import *

class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def draw(self, surface, player):
        self.draw_health_bar(surface, player.health, player.max_health)
        self.draw_coin_counter(surface, player.coins)
        # Add more HUD elements as needed

    def draw_health_bar(self, surface, health, max_health):
        bar_width = 200
        bar_height = 20
        fill = (health / max_health) * bar_width
        outline_rect = pygame.Rect(10, 10, bar_width, bar_height)
        fill_rect = pygame.Rect(10, 10, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

    def draw_coin_counter(self, surface, coins):
        coin_text = self.font.render(f"Coins: {coins}", True, YELLOW)
        surface.blit(coin_text, (10, 40))

    def draw_instructions(self, surface):
        instructions = [
            "Arrow keys: Move",
            "SPACE: Enter/Exit buildings",
            "ENTER: Attack",
            "ESC: Quit game"
        ]
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            surface.blit(text, (10, HEIGHT - 100 + i * 20))
''',
        'ui/effects.py': '''
import pygame
from constants import YELLOW

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
''',
        'utils/sprite_loader.py': '''
import pygame
import os

def create_placeholder_sprite(color, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, width, height))
    pygame.draw.line(surface, (0, 0, 0), (0, 0), (width, height))
    pygame.draw.line(surface, (0, 0, 0), (width, 0), (0, height))
    return surface

def load_sprite(filename, scale=0.1, placeholder_color=(255, 0, 0), placeholder_size=(32, 32)):
    try:
        image = pygame.image.load(os.path.join('assets', 'sprites', filename)).convert_alpha()
        return pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    except pygame.error:
        print(f"Warning: Unable to load image: {filename}. Using placeholder.")
        return create_placeholder_sprite(placeholder_color, *placeholder_size)

# Load all game sprites
player_sprite = load_sprite('player.png', placeholder_color=(0, 255, 0))
zombie_sprite = load_sprite('zombie.png', placeholder_color=(0, 0, 255))
tracker_sprite = load_sprite('tracker.png', placeholder_color=(255, 0, 255))
bat_sprite = load_sprite('bat.png', placeholder_color=(255, 255, 0))
boss_sprite = load_sprite('boss.png', 0.2, placeholder_color=(255, 0, 0), placeholder_size=(64, 64))
coin_sprite = load_sprite('coin.png', scale=0.025, placeholder_color=(255, 215, 0), placeholder_size=(8, 8))
house_sprites = [load_sprite(f'house{i}.png', scale=0.2, placeholder_color=(139, 69, 19), placeholder_size=(100, 100)) for i in range(1, 6)]
mansion_sprite = load_sprite('mansion.png', 0.3, placeholder_color=(70, 130, 180), placeholder_size=(150, 150))
dirt_road_sprite = load_sprite('dirt_road.png', 0.1, placeholder_color=(101, 67, 33), placeholder_size=(50, 50))
grass_sprite = load_sprite('grass.png', 0.4, placeholder_color=(34, 139, 34), placeholder_size=(50, 50))
floor_sprite = load_sprite('floor.png', 0.2, placeholder_color=(139, 69, 19), placeholder_size=(64, 64))
magic_missile_sprite = create_placeholder_sprite((0, 255, 255), 16, 16)
furniture_sprites = [
    load_sprite('table.png', scale=0.25, placeholder_color=(139, 69, 19), placeholder_size=(40, 40)),
    load_sprite('chair.png', scale=0.35, placeholder_color=(160, 82, 45), placeholder_size=(30, 30)),
    load_sprite('bookshelf.png', scale=0.25, placeholder_color=(101, 67, 33), placeholder_size=(50, 60)),
    load_sprite('bed.png', scale=0.45, placeholder_color=(70, 130, 180), placeholder_size=(60, 40)),
    load_sprite('cabinet.png', scale=0.25, placeholder_color=(205, 133, 63), placeholder_size=(45, 50))
]
headstone_sprite = load_sprite('headstone.png', scale=0.1, placeholder_color=(105, 105, 105), placeholder_size=(30, 40))
graveyard_floor_sprite = load_sprite('graveyard_floor.png', scale=0.2, placeholder_color=(50, 70, 50), placeholder_size=(64, 64))
graveyard_entrance_sprite = load_sprite('graveyard_entrance.png', 0.2, placeholder_color=(169, 169, 169), placeholder_size=(80, 80))

print("Sprites loaded successfully.")
'''
    }

    for file_path, content in files.items():
        create_file(file_path, content.strip())

if __name__ == "__main__":
    generate_game_structure()
    print("Game structure generated successfully!")