# File: wave_manager.py

import random
import pygame

from config import WAVE_INTERVAL, ENEMIES_PER_WAVE, SCREEN_WIDTH, SCREEN_HEIGHT
from enemy import Enemy

class WaveManager:
    """
    Spawns waves of enemies every WAVE_INTERVAL frames.
    Each wave has ENEMIES_PER_WAVE.
    Chooses among 3 attacker images randomly.
    """
    def __init__(self, base, all_sprites, enemy_group, assets):
        self.base = base
        self.all_sprites = all_sprites
        self.enemy_group = enemy_group
        self.assets = assets

        self.wave_timer = 0
        self.wave_count = 0

        # Pool of possible enemy sprites
        self.attacker_images = [
            self.assets["attacker1"],
            self.assets["attacker2"],
            self.assets["attacker3"]
        ]

    def update(self):
        self.wave_timer += 1
        if self.wave_timer >= WAVE_INTERVAL:
            self.spawn_wave()
            self.wave_timer = 0

    def spawn_wave(self):
        self.wave_count += 1
        for _ in range(ENEMIES_PER_WAVE):
            x, y = self.get_random_edge_position()

            # Pick one of the three attacker images
            attacker_img = random.choice(self.attacker_images)

            enemy = Enemy(x, y, self.base, attacker_img)
            self.enemy_group.add(enemy)
            self.all_sprites.add(enemy)

    def get_random_edge_position(self):
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            return (random.randint(0, SCREEN_WIDTH), 0)
        elif edge == "bottom":
            return (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT)
        elif edge == "left":
            return (0, random.randint(0, SCREEN_HEIGHT))
        else:  # right
            return (SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT))
