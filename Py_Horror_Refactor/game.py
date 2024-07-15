import pygame
from constants import *
from entities.player import Player
from environment.village import Village
from environment.indoor_scene import IndoorScene
from environment.mansion_scene import MansionScene
from environment.graveyard_scene import GraveyardScene
from ui.hud import HUD

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Village Horror")
        self.clock = pygame.time.Clock()
        self.player = Player()
        self.village = Village()
        self.indoor_scenes = {}  # To be populated
        self.mansion_scene = MansionScene()
        self.graveyard_scene = GraveyardScene()
        self.current_scene = "village"
        self.hud = HUD()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # Handle other key events here

            self.update()
            self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def update(self):
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        
        if self.current_scene == "village":
            self.player.move(dx, dy, self.village.buildings)
            self.village.update(self.player)
        elif self.current_scene == "indoor":
            self.player.move(dx, dy, [])
            self.indoor_scenes[self.current_building].update(self.player)
        elif self.current_scene == "mansion":
            self.player.move(dx, dy, [])
            self.mansion_scene.update(self.player)
        elif self.current_scene == "graveyard":
            self.player.move(dx, dy, [])
            self.graveyard_scene.update(self.player)

        self.player.update()

    def draw(self):
        self.screen.fill(BLACK)
        
        if self.current_scene == "village":
            self.village.draw(self.screen, self.player.camera_x, self.player.camera_y)
        elif self.current_scene == "indoor":
            self.indoor_scenes[self.current_building].draw(self.screen, 0, 0)
        elif self.current_scene == "mansion":
            self.mansion_scene.draw(self.screen, 0, 0)
        elif self.current_scene == "graveyard":
            self.graveyard_scene.draw(self.screen, 0, 0)

        # Draw player
        self.player.draw(self.screen)

        # Draw HUD
        self.hud.draw(self.screen, self.player)

        pygame.display.flip()