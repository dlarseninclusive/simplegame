import pygame
from constants import *
from entities import Player
from environment import Village, IndoorScene, MansionScene

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.player = Player()
        self.village = Village()
        self.indoor_scenes = {building: IndoorScene(building) for building in self.village.buildings if building != self.village.mansion}
        self.mansion_scene = MansionScene(self.village.mansion)
        self.current_scene = "village"
        self.current_building = None
        self.near_entrance = False
        self.show_instructions = True
        self.show_minimap = False  # New attribute for minimap toggle
        self.spawn_timer = 0
        self.spawn_interval = 5 * FPS  # Spawn coins every 5 seconds

        self.camera_x = 0
        self.camera_y = 0

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.try_enter_exit_building()
                    elif event.key == pygame.K_i:
                        self.show_instructions = not self.show_instructions
                    elif event.key == pygame.K_m:  # New key handler for minimap toggle
                        self.show_minimap = not self.show_minimap
                    elif event.key == pygame.K_d:  # Debug mode toggle
                        self.debug_mode = not self.debug_mode
                        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")

            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            
            if self.current_scene == "village":
                self.player.move(dx, dy, self.village.buildings)
                self.village.update(self.player)
                self.check_near_entrance()
                if keys[pygame.K_RETURN]:
                    self.player.attack(self.village.monsters)
                
                self.spawn_timer += 1
                if self.spawn_timer >= self.spawn_interval:
                    self.village.spawn_coin()
                    self.spawn_timer = 0

                coins_collected = pygame.sprite.spritecollide(self.player, self.village.coins, True)
                for coin in coins_collected:
                    self.player.collect_coin(coin)

            elif self.current_scene == "mansion":
                self.player.move(dx, dy, [])
                self.mansion_scene.update(self.player)
                self.check_near_exit()
                if keys[pygame.K_RETURN]:
                    self.player.attack(self.mansion_scene.monsters)

                coins_collected = pygame.sprite.spritecollide(self.player, self.mansion_scene.coins, True)
                for coin in coins_collected:
                    self.player.collect_coin(coin)

            else:  # Indoor scene
                current_indoor = self.indoor_scenes[self.current_building]
                self.player.move(dx, dy, [])
                current_indoor.update(self.player)
                self.check_near_exit()
                if keys[pygame.K_RETURN]:
                    self.player.attack(current_indoor.monsters)

                coins_collected = pygame.sprite.spritecollide(self.player, current_indoor.coins, True)
                for coin in coins_collected:
                    self.player.collect_coin(coin)

            self.player.update()
            self.update_camera()
            self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        return False

    def update_camera(self):
        self.camera_x = max(0, min(self.player.rect.centerx - WIDTH // 2, MAP_WIDTH - WIDTH))
        self.camera_y = max(0, min(self.player.rect.centery - HEIGHT // 2, MAP_HEIGHT - HEIGHT))

    def check_near_entrance(self):
        self.near_entrance = False
        for building in self.village.buildings:
            if building.entrance.colliderect(self.player.rect):
                self.near_entrance = True
                self.current_building = building
                break

    def check_near_exit(self):
        exit_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 20, 40, 20)
        self.near_entrance = exit_rect.colliderect(self.player.rect)

    def try_enter_exit_building(self):
        if self.current_scene == "village" and self.near_entrance:
            if self.current_building == self.village.mansion:
                self.current_scene = "mansion"
            else:
                self.current_scene = "indoor"
            self.player.rect.midbottom = (WIDTH // 2, HEIGHT - 40)
        elif (self.current_scene == "indoor" or self.current_scene == "mansion") and self.near_entrance:
            self.current_scene = "village"
            self.player.rect.center = self.current_building.entrance.center
            self.current_building = None

    def draw(self):
        self.screen.fill(BLACK)
        if self.current_scene == "village":
            self.village.draw(self.screen, self.camera_x, self.camera_y)
        elif self.current_scene == "mansion":
            self.mansion_scene.draw(self.screen, 0, 0)
        else:
            self.indoor_scenes[self.current_building].draw(self.screen, 0, 0)
        
        if self.current_scene == "village":
            player_screen_x = self.player.rect.x - self.camera_x
            player_screen_y = self.player.rect.y - self.camera_y
        else:
            player_screen_x = self.player.rect.x
            player_screen_y = self.player.rect.y
        self.screen.blit(self.player.image, (player_screen_x, player_screen_y))
        self.player.draw_health_bar(self.screen, self.camera_x if self.current_scene == "village" else 0, 
                                    self.camera_y if self.current_scene == "village" else 0)

        if self.near_entrance:
            text = font.render("Press SPACE to enter/exit", True, YELLOW)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

        coin_text = font.render(f"Coins: {self.player.coins}", True, YELLOW)
        self.screen.blit(coin_text, (10, 10))

        if self.show_instructions:
            self.draw_instructions()

        if self.show_minimap:
            self.draw_minimap()

    def draw_instructions(self):
        instructions = [
            "Game Instructions:",
            "- Use arrow keys to move",
            "- Press SPACE near green rectangles to enter/exit buildings",
            "- Press ENTER to attack nearby monsters",
            "- Collect coins to buy upgrades",
            "- Defeat the boss monster in the mansion",
            "- Press 'I' to toggle instructions",
            "- Press 'M' to toggle minimap",
            "- Press 'ESC' to exit the game"
        ]
        
        instruction_surface = pygame.Surface((WIDTH, HEIGHT))
        instruction_surface.set_alpha(200)
        instruction_surface.fill(BLACK)
        self.screen.blit(instruction_surface, (0, 0))

        for i, line in enumerate(instructions):
            text = small_font.render(line, True, WHITE)
            self.screen.blit(text, (20, 20 + i * 30))

    def draw_minimap(self):
        minimap_size = 150
        minimap_surface = pygame.Surface((minimap_size, minimap_size))
        minimap_surface.fill(BLACK)
        minimap_surface.set_alpha(200)

        scale_x = minimap_size / MAP_WIDTH
        scale_y = minimap_size / MAP_HEIGHT

        # Draw buildings
        for building in self.village.buildings:
            minimap_x = int(building.rect.x * scale_x)
            minimap_y = int(building.rect.y * scale_y)
            minimap_width = max(3, int(building.rect.width * scale_x))
            minimap_height = max(3, int(building.rect.height * scale_y))
            pygame.draw.rect(minimap_surface, WHITE, (minimap_x, minimap_y, minimap_width, minimap_height))

        # Draw player
        player_x = int(self.player.rect.centerx * scale_x)
        player_y = int(self.player.rect.centery * scale_y)
        pygame.draw.circle(minimap_surface, RED, (player_x, player_y), 2)

        self.screen.blit(minimap_surface, (WIDTH - minimap_size - 10, 10))