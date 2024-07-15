import pygame
import os

def create_placeholder_sprite(color, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, width, height))
    pygame.draw.line(surface, (0, 0, 0), (0, 0), (width, height))
    pygame.draw.line(surface, (0, 0, 0), (width, 0), (0, height))
    return surface

def load_sprite(filename, scale=0.1, placeholder_color=(255, 0, 0), placeholder_size=(32, 32)):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sprite_path = os.path.join(project_root, 'assets', 'sprites', filename)
    
    print(f"Attempting to load sprite: {sprite_path}")
    
    if not os.path.exists(sprite_path):
        print(f"Error: File does not exist: {sprite_path}")
        return create_placeholder_sprite(placeholder_color, *placeholder_size)
    
    try:
        image = pygame.image.load(sprite_path)
        print(f"Successfully loaded sprite: {filename}")
        print(f"Image info - Size: {image.get_size()}, Color key: {image.get_colorkey()}, Alpha: {image.get_alpha()}")
        return pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    except pygame.error as e:
        print(f"Pygame error loading image: {filename}. Error: {e}")
        return create_placeholder_sprite(placeholder_color, *placeholder_size)
    except Exception as e:
        print(f"Unexpected error loading image: {filename}. Error: {e}")
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