import pygame
import random

class Building:
    def __init__(self, x, y, width, height, image, building_type="normal"):
        self.rect = pygame.Rect(x, y, width, height)
        self.image = image
        self.type = building_type
        self.wall_thickness = 5

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def is_colliding(self, rect):
        if self.rect.colliderect(rect):
            inner_rect = pygame.Rect(self.rect.left + self.wall_thickness, 
                                     self.rect.top + self.wall_thickness,
                                     self.rect.width - 2 * self.wall_thickness,
                                     self.rect.height - 2 * self.wall_thickness)
            return not inner_rect.colliderect(rect)
        return False

    def get_random_interior_position(self):
        return (random.randint(self.rect.left + self.wall_thickness, self.rect.right - self.wall_thickness),
                random.randint(self.rect.top + self.wall_thickness, self.rect.bottom - self.wall_thickness))

    def get_exit_position(self):
        return (self.rect.centerx, self.rect.centery)

class House(Building):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height, image, "house")
        self.has_downstairs = random.choice([True, False])
        self.downstairs_locked = random.choice([True, False]) if self.has_downstairs else False

    def attempt_break_in(self):
        if not self.has_downstairs:
            return False
        if not self.downstairs_locked:
            return True
        # 50% chance of successfully picking the lock
        return random.random() < 0.5

class Jail(Building):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height, image, "jail")

class Hospital(Building):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height, image, "hospital")