import pygame
from constants import *
from entities.player import Player
from environment.village import Village
from ui.hud import HUD

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Village Horror")
        self.clock = pygame.time.Clock()
        self.player = Player()
        self.village = Village()
        self.hud = HUD()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    target_x = mouse_pos[0] + self.player.camera_x
                    target_y = mouse_pos[1] + self.player.camera_y
                    self.player.set_target((target_x, target_y))
        return True

    def update(self):
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        
        self.player.move(dx, dy, self.village.buildings)
        self.village.update(self.player)

        # Check for coin collisions
        coins_collected = pygame.sprite.spritecollide(self.player, self.village.coins, False)
        for coin in coins_collected:
            self.player.collect_coin(coin)

    def draw(self):
        self.screen.fill(BLACK)
        self.village.draw(self.screen, self.player.camera_x, self.player.camera_y)
        self.player.draw(self.screen)
        self.hud.draw(self.screen, self.player)
        self.hud.draw_instructions(self.screen)