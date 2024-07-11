import pygame
import random
import math

def distance(obj1, obj2):
    return math.sqrt((obj1.x - obj2.x)**2 + (obj1.y - obj2.y)**2)

def find_valid_spawn(buildings, width, height, player_size=35):
    while True:
        x = random.randint(0, width - player_size)
        y = random.randint(0, height - player_size)
        rect = pygame.Rect(x, y, player_size, player_size)
        if not any(building.is_colliding(rect) for building in buildings):
            return x, y
