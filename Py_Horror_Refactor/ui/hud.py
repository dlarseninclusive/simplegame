import pygame
from constants import *

class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def draw(self, surface, player):
        self.draw_health_bar(surface, player.health, player.max_health)
        self.draw_coin_counter(surface, player.coins)
        # Add more HUD elements as needed

    def draw_health_bar(self, surface, health, max_health):
        bar_width = 200
        bar_height = 20
        fill = (health / max_health) * bar_width
        outline_rect = pygame.Rect(10, 10, bar_width, bar_height)
        fill_rect = pygame.Rect(10, 10, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

    def draw_coin_counter(self, surface, coins):
        coin_text = self.font.render(f"Coins: {coins}", True, YELLOW)
        surface.blit(coin_text, (10, 40))

    def draw_instructions(self, surface):
        instructions = [
            "Arrow keys: Move",
            "SPACE: Enter/Exit buildings",
            "ENTER: Attack",
            "ESC: Quit game"
        ]
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            surface.blit(text, (10, HEIGHT - 100 + i * 20))