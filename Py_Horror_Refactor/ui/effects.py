import pygame
from constants import YELLOW

class CoinCollectEffect(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((50, 20), pygame.SRCALPHA)
        self.font = pygame.font.Font(None, 20)
        self.text = self.font.render("+1 Coin", True, YELLOW)
        self.image.blit(self.text, (0, 0))
        self.rect = self.image.get_rect(center=pos)
        self.timer = 60  # Effect lasts for 60 frames (1 second at 60 FPS)

    def update(self):
        self.rect.y -= 1
        self.timer -= 1
        if self.timer <= 0:
            self.kill()