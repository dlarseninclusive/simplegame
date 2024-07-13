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
        self.downstairs = None
        if self.has_downstairs:
            self.downstairs = pygame.Rect(x, y + height, width, height)

    def draw(self, screen):
        super().draw(screen)
        if self.has_downstairs:
            pygame.draw.rect(screen, (100, 100, 100), self.downstairs)  # Draw downstairs in dark gray

    def attempt_break_in(self):
        if not self.has_downstairs:
            return False
        if not self.downstairs_locked:
            return True
        # 50% chance of successfully picking the lock
        return random.random() < 0.5

    def enter_downstairs(self, entity):
        if self.has_downstairs:
            entity.x = self.downstairs.centerx
            entity.y = self.downstairs.centery

    def exit_downstairs(self, entity):
        entity.x = self.rect.centerx
        entity.y = self.rect.bottom - self.wall_thickness

class Jail(Building):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height, image, "jail")

class Hospital(Building):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height, image, "hospital")