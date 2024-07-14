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

# Initialize pygame and create window
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Village Horror")
clock = pygame.time.Clock()

# Font setup
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)