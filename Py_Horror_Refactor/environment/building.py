import pygame

class Building(pygame.sprite.Sprite):
    def __init__(self, pos, sprite):
        super().__init__()
        self.image = sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        entrance_width = 100  # Increased from 50 to 100
        entrance_height = 20  # Increased from 12 to 20
        self.entrance = pygame.Rect(self.rect.centerx - entrance_width // 2, 
                                    self.rect.bottom - entrance_height, 
                                    entrance_width, entrance_height)

    def collide_with_player(self, player_rect):
        return self.rect.colliderect(player_rect) and not self.entrance.colliderect(player_rect)
        
class MansionBuilding(Building):
    def __init__(self, pos, sprite):
        super().__init__(pos, sprite)
        # Add any mansion-specific attributes or methods here