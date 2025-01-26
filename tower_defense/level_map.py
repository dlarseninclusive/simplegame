# File: level_map.py

from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

# Calculate how many tiles fit horizontally and vertically
TILES_X = SCREEN_WIDTH // TILE_SIZE
TILES_Y = SCREEN_HEIGHT // TILE_SIZE

# We'll make an array of all zeroes for a "grass" tile
LEVEL_DATA = [[0 for _ in range(TILES_X)] for _ in range(TILES_Y)]
