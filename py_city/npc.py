import pygame
import random
import math
from buildings import Building, House
from utils import distance

RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class NPC:
    def __init__(self, x, y, sprite, npc_type, grid_size, road_width, width, height, game_state):
        self.x = x
        self.y = y
        self.size = 35
        self.speed = 1  # Reduced from 2 to 1
        self.sprite = sprite
        self.type = npc_type
        self.direction = random.choice(["up", "down", "left", "right"])
        self.move_timer = 0
        self.in_jail = False
        self.jail_timer = 600
        self.crime_timer = random.randint(300, 600)
        self.health = 100
        self.committed_crime = False
        self.in_building = None
        self.building_timer = 0
        self.cooldown_timer = 0
        self.breaking_in = False
        self.break_in_timer = 0
        self.path = []
        self.path_index = 0
        self.dialog = self.generate_dialog()
        self.grid_size = grid_size
        self.road_width = road_width
        self.width = width
        self.height = height
        self.game_state = game_state

    def move(self, buildings, hospital):
        if self.in_jail or self.in_building:
            return

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if self.breaking_in:
            self.break_in_timer -= 1
            if self.break_in_timer <= 0:
                self.finish_break_in()
            return

        if not self.path:
            self.generate_path()

        if self.path_index < len(self.path):
            target_x, target_y = self.path[self.path_index]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < self.speed:
                self.x, self.y = target_x, target_y
                self.path_index += 1
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        if self.path_index >= len(self.path):
            self.generate_path()

    def generate_path(self):
        start_x = int(self.x // (self.grid_size + self.road_width)) * (self.grid_size + self.road_width) + self.road_width // 2
        start_y = int(self.y // (self.grid_size + self.road_width)) * (self.grid_size + self.road_width) + self.road_width // 2
        end_x = random.randint(0, self.width // (self.grid_size + self.road_width)) * (self.grid_size + self.road_width) + self.road_width // 2
        end_y = random.randint(0, self.height // (self.grid_size + self.road_width)) * (self.grid_size + self.road_width) + self.road_width // 2
        
        self.path = [(start_x, start_y), (end_x, start_y), (end_x, end_y)]
        self.path_index = 0

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))
        pygame.draw.rect(screen, RED, (self.x, self.y - 5, self.size, 3))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 5, self.size * (self.health / 100), 3))
        if self.breaking_in:
            pygame.draw.circle(screen, YELLOW, (int(self.x + self.size/2), int(self.y + self.size/2)), 5)

    def attempt_crime(self, buildings, civilians):
        if self.type == "criminal" and not self.in_jail and not self.committed_crime and not self.in_building and not self.breaking_in:
            self.crime_timer -= 1
            if self.crime_timer <= 0:
                target = random.choice(buildings + civilians)
                if isinstance(target, House) and target.has_downstairs:
                    print("A criminal is attempting to break into a house!")
                    self.breaking_in = True
                    self.break_in_timer = 180  # 3 seconds to break in
                    self.x, self.y = target.rect.x, target.rect.y
                    self.in_building = target
                elif isinstance(target, Building) and target.type == "normal":
                    print("A building was burglarized!")
                    self.in_building = target
                    self.x, self.y = target.get_random_interior_position()
                    self.building_timer = 180  # 3 seconds in the building
                    self.game_state.total_burglaries += 1
                elif not isinstance(target, Building):
                    print("A civilian was mugged!")
                    self.game_state.total_muggings += 1
                self.committed_crime = True
                self.crime_timer = random.randint(300, 600)

    def finish_break_in(self):
        self.breaking_in = False
        if self.in_building.attempt_break_in():
            print("Break-in successful!")
            self.x, self.y = self.in_building.get_random_interior_position()
            self.building_timer = 180
            self.game_state.total_burglaries += 1
        else:
            print("Break-in failed!")
            self.in_building = None
            self.committed_crime = False

    def generate_dialog(self):
        if self.type == "criminal":
            return ["I'm just minding my own business...", "Nothing to see here, move along."]
        elif self.type == "police":
            return ["Keep the peace, citizen.", "Report any suspicious activity."]
        else:  # civilian
            return ["Nice weather we're having.", "Have you heard about the new restaurant in town?"]