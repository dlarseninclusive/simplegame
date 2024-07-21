import pygame

# Game constants
WIDTH, HEIGHT = 1280, 720
FPS = 60  # Keeping at 60, but we'll adjust speeds

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

# Player constants
PLAYER_SPEED = 3
PLAYER_MAX_HEALTH = 100
PLAYER_INVINCIBILITY_TIME = 1000  # milliseconds

# Monster constants
MONSTER_SPEED = 1
MONSTER_ATTACK_DAMAGE = 5
MONSTER_ATTACK_COOLDOWN = 1000  # milliseconds

# Initialize pygame font
pygame.font.init()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)