import os
import sys

# Add parent directory to path for character_classes import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from utils import distance
from character_classes import Warrior

# Ensure colors are defined
RED = (255, 0, 0)
GREEN = (0, 255, 0)

class Player:
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.size = 35
        self.speed = 5
        self.sprite = sprite
        self.character_class = Warrior()
        self.health = self.character_class.base_health
        self.karma = 0
        self.alignment = "neutral"
        self.current_quest = None

    def move(self, dx, dy, buildings):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        new_rect = pygame.Rect(new_x, new_y, self.size, self.size)
        if not any(building.is_colliding(new_rect) for building in buildings):
            self.x = max(0, min(new_x, 1024 - self.size))  # Use WIDTH
            self.y = max(0, min(new_y, 768 - self.size))  # Use HEIGHT

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, self.size, 5))  # Use RED
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, self.size * (self.health / 100), 5))  # Use GREEN

    def change_alignment(self, alignment):
        self.alignment = alignment

    def interact(self, npcs, buildings):
        for npc in npcs:
            if distance(self, npc) < 50:
                return npc
        for building in buildings:
            if building.rect.collidepoint(self.x, self.y):
                return building
        return None
