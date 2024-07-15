from environment.indoor_scene import IndoorScene
from entities.monsters import BossMonster
from constants import *
from utils.sprite_loader import boss_sprite

class MansionScene(IndoorScene):
    def __init__(self):
        super().__init__()
        self.boss = None
        self.setup_mansion()

    def setup_mansion(self):
        # Add boss
        self.boss = BossMonster(WIDTH // 2, HEIGHT // 2)
        self.monsters.add(self.boss)

        # Add more furniture and decorations specific to the mansion
        # (You can add more complex setup here)

    def update(self, player):
        super().update(player)
        # Add any mansion-specific update logic here

    def draw(self, screen, camera_x, camera_y):
        super().draw(screen, camera_x, camera_y)
        # Add any mansion-specific drawing here
        mansion_text = font.render("Mansion", True, RED)
        screen.blit(mansion_text, (WIDTH // 2 - mansion_text.get_width() // 2, 20))