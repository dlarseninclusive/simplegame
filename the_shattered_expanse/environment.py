# environment.py
import pygame

class Environment:
    """
    Holds static obstacles for collision & pathfinding.
    """
    def __init__(self):
        self.obstacles = []

    def add_obstacle(self, x, y, width, height):
        rect = pygame.Rect(x, y, width, height)
        self.obstacles.append(rect)
