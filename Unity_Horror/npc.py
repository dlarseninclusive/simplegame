import pygame
from settings import GREEN

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, name):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.name = name
        self.dialogue = [
            f"Hello, I'm {name}. Welcome to our town!",
            "We've been having some strange occurrences lately...",
            "Can you help us investigate?",
            "Be careful out there!"
        ]
        self.current_dialogue = 0

    def talk(self):
        text = self.dialogue[self.current_dialogue]
        self.current_dialogue = (self.current_dialogue + 1) % len(self.dialogue)
        return text
