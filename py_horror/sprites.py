import pygame
import os

# Get the directory of the current script
current_dir = os.path.dirname(__file__)
# Construct the path to the sprites folder
sprites_dir = os.path.join(current_dir, 'sprites')

def create_placeholder_sprite(color, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, width, height))
    pygame.draw.line(surface, (0, 0, 0), (0, 0), (width, height))
    pygame.draw.line(surface, (0, 0, 0), (width, 0), (0, height))
    return surface

def load_sprite(filename, scale=0.1, placeholder_color=(255, 0, 0), placeholder_size=(32, 32)):
    try:
        image = pygame.image.load(os.path.join(sprites_dir, filename)).convert_alpha()
        return pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    except pygame.error:
        print(f"Warning: Unable to load image: {filename}. Using placeholder.")
        return create_placeholder_sprite(placeholder_color, *placeholder_size)

# Load all sprites with consistent scale
player_sprite = load_sprite('player.png', placeholder_color=(0, 255, 0))
zombie_sprite = load_sprite('zombie.png', placeholder_color=(0, 0, 255))
tracker_sprite = load_sprite('tracker.png', placeholder_color=(255, 0, 255))
bat_sprite = load_sprite('bat.png', placeholder_color=(255, 255, 0))
boss_sprite = load_sprite('boss.png', 0.2, placeholder_color=(255, 0, 0), placeholder_size=(64, 64))
coin_sprite = load_sprite('coin.png',0.05, placeholder_color=(255, 215, 0))
house_sprites = [load_sprite('house.png', placeholder_color=(139, 69, 19), placeholder_size=(100, 100)) for _ in range(4)]
mansion_sprite = load_sprite('mansion.png', 0.3, placeholder_color=(70, 130, 180), placeholder_size=(150, 150))
dirt_road_sprite = load_sprite('dirt_road.png', 0.5, placeholder_color=(101, 67, 33), placeholder_size=(50, 50))
grass_sprite = load_sprite('grass.png', 0.5, placeholder_color=(34, 139, 34), placeholder_size=(50, 50))

# Create magic missile sprite
magic_missile_sprite = create_placeholder_sprite((0, 255, 255), 16, 16)  # Cyan color, 16x16 pixels

# Create furniture sprites using Pygame's drawing functions
def create_furniture_sprite(color, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, width, height))
    return surface

furniture_sprites = [
    create_furniture_sprite((139, 69, 19), 40, 40),  # Table (brown)
    create_furniture_sprite((160, 82, 45), 30, 30),  # Chair (sienna)
    create_furniture_sprite((101, 67, 33), 50, 60),  # Bookshelf (dark brown)
    create_furniture_sprite((70, 130, 180), 60, 40),  # Bed (steel blue)
    create_furniture_sprite((205, 133, 63), 45, 50)   # Cabinet (peru)
]

print("Sprites loaded successfully.")