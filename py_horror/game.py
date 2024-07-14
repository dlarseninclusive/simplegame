import pygame
import random
from constants import *
from game_objects import Player, Monster, BossMonster, Coin, Building, CoinCollectEffect, MagicMissile
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
        self.show_minimap = False
        self.camera_x = 0
        self.camera_y = 0
        self.effects = pygame.sprite.Group()
        self.magic_missiles = pygame.sprite.Group()

        # Shader effect setup
        self.shader_surface = pygame.Surface((WIDTH, HEIGHT))
        self.shader_surface.set_alpha(50)
        self.rain_drops = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(100)]

        # Lightning effect setup
        self.lightning_active = False
        self.lightning_start_time = 0
        self.lightning_duration = 0
        self.next_lightning_time = pygame.time.get_ticks() + random.randint(15 * 1000, 30 * 1000)

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
                    elif event.key == pygame.K_m:
                        self.show_minimap = not self.show_minimap
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_left_click(event.pos)
                    elif event.button == 3:  # Right mouse button
                        self.handle_right_click(event.pos)

            self.update()
            
            if self.current_scene == "village":
                self.update_shader_effects()
            
            self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        return False

    def update(self):
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]

        if self.current_scene == "village":
            if self.player.target_pos:
                dx = self.player.target_pos[0] - self.player.rect.centerx
                dy = self.player.target_pos[1] - self.player.rect.centery
                distance = (dx**2 + dy**2)**0.5
                if distance < self.player.speed:
                    self.player.rect.center = self.player.target_pos
                    self.player.target_pos = None
                else:
                    dx = dx / distance * self.player.speed
                    dy = dy / distance * self.player.speed
            else:
                dx *= self.player.speed
                dy *= self.player.speed

            new_rect = self.player.rect.move(dx, dy)
            can_move = True
            for building in self.village.buildings:
                if building.collide_with_player(new_rect):
                    can_move = False
                    break
            if can_move:
                self.player.rect = new_rect
            else:
                self.player.target_pos = None  # Reset target position if we can't move there

            self.village.update(self.player)
            self.check_near_entrance()
            if keys[pygame.K_RETURN]:
                self.player_attack()

            coins_collected = pygame.sprite.spritecollide(self.player, self.village.coins, True)
            for coin in coins_collected:
                effect = self.player.collect_coin(coin)
                self.effects.add(effect)

            self.update_magic_missiles(self.village.monsters)

        elif self.current_scene == "mansion":
            self.player.move(dx, dy, [])
            self.mansion_scene.update(self.player)
            self.check_near_exit()
            if keys[pygame.K_RETURN]:
                self.player_attack()

            coins_collected = pygame.sprite.spritecollide(self.player, self.mansion_scene.coins, True)
            for coin in coins_collected:
                effect = self.player.collect_coin(coin)
                self.effects.add(effect)

            self.update_magic_missiles(self.mansion_scene.monsters)

        else:  # Indoor scene
            current_indoor = self.indoor_scenes[self.current_building]
            self.player.move(dx, dy, [])
            current_indoor.update(self.player)
            self.check_near_exit()
            if keys[pygame.K_RETURN]:
                self.player_attack()

            coins_collected = pygame.sprite.spritecollide(self.player, current_indoor.coins, True)
            for coin in coins_collected:
                effect = self.player.collect_coin(coin)
                self.effects.add(effect)

            self.update_magic_missiles(current_indoor.monsters)

        self.player.update()
        self.effects.update()
        self.magic_missiles.update()
        self.update_camera()

    def handle_left_click(self, pos):
        if self.current_scene == "village":
            target_x = pos[0] + self.camera_x
            target_y = pos[1] + self.camera_y
            self.player.set_target((target_x, target_y))
        else:
            self.player.set_target(pos)

    def handle_right_click(self, pos):
        if self.current_scene == "village":
            target_x = pos[0] + self.camera_x
            target_y = pos[1] + self.camera_y
            target_pos = (target_x, target_y)
        else:
            target_pos = pos

        magic_missile = self.player.fire_magic_missile(target_pos)
        if magic_missile:
            self.magic_missiles.add(magic_missile)

    def update_magic_missiles(self, monsters):
        for missile in self.magic_missiles:
            hit_monsters = pygame.sprite.spritecollide(missile, monsters, False)
            for monster in hit_monsters:
                monster.health -= missile.damage
                print(f"Magic missile hit {monster.__class__.__name__} for {missile.damage} damage")
                if monster.health <= 0:
                    self.remove_monster(monster)
                missile.kill()
                break

    def player_attack(self):
        if self.current_scene == "village":
            monsters = self.village.monsters
            coins = self.village.coins
        elif self.current_scene == "mansion":
            monsters = self.mansion_scene.monsters
            coins = self.mansion_scene.coins
        else:
            monsters = self.indoor_scenes[self.current_building].monsters
            coins = self.indoor_scenes[self.current_building].coins

        self.player.attack(monsters)
        
        for monster in list(monsters):  # Create a copy of the list to safely remove items
            if monster.health <= 0:
                self.remove_monster(monster)
        
        print(f"Current number of coins in scene: {len(coins)}")  # Debug print

    def remove_monster(self, monster):
        if self.current_scene == "village":
            monsters = self.village.monsters
            coins = self.village.coins
        elif self.current_scene == "mansion":
            monsters = self.mansion_scene.monsters
            coins = self.mansion_scene.coins
        else:
            monsters = self.indoor_scenes[self.current_building].monsters
            coins = self.indoor_scenes[self.current_building].coins

        monsters.remove(monster)
        dropped_coin = monster.drop_coin()
        if dropped_coin:
            coins.add(dropped_coin)
            print(f"Coin dropped at position: {dropped_coin.rect.center}")  # Debug print
        else:
            print("Monster defeated but no coin dropped")  # Debug print
        print(f"Monster removed. Remaining monsters: {len(monsters)}")  # Debug print

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
            self.player.rect.midbottom = (WIDTH // 2, HEIGHT - 50)  # Adjusted position
        elif (self.current_scene == "indoor" or self.current_scene == "mansion") and self.near_entrance:
            self.current_scene = "village"
            self.player.rect.center = self.current_building.entrance.center
            self.current_building = None

    def update_shader_effects(self):
        # Update rain
        for i, (x, y) in enumerate(self.rain_drops):
            y += 5
            if y > HEIGHT:
                y = random.randint(-10, 0)
                x = random.randint(0, WIDTH)
            self.rain_drops[i] = (x, y)

        # Update lightning
        current_time = pygame.time.get_ticks()
        if self.lightning_active:
            if current_time - self.lightning_start_time >= self.lightning_duration:
                self.lightning_active = False
                self.next_lightning_time = current_time + random.randint(15 * 1000, 30 * 1000)
        else:
            if current_time >= self.next_lightning_time:
                self.lightning_active = True
                self.lightning_start_time = current_time
                self.lightning_duration = random.randint(250, 750)

    def draw(self):
        self.screen.fill(BLACK)
        if self.current_scene == "village":
            self.village.draw(self.screen, self.camera_x, self.camera_y)
            self.draw_shader_effects()
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

        for effect in self.effects:
            if self.current_scene == "village":
                effect_screen_x = effect.rect.x - self.camera_x
                effect_screen_y = effect.rect.y - self.camera_y
            else:
                effect_screen_x = effect.rect.x
                effect_screen_y = effect.rect.y
            self.screen.blit(effect.image, (effect_screen_x, effect_screen_y))

        for missile in self.magic_missiles:
            if self.current_scene == "village":
                missile_screen_x = missile.rect.x - self.camera_x
                missile_screen_y = missile.rect.y - self.camera_y
            else:
                missile_screen_x = missile.rect.x
                missile_screen_y = missile.rect.y
            self.screen.blit(missile.image, (missile_screen_x, missile_screen_y))

        if self.near_entrance:
            text = font.render("Press SPACE to enter/exit", True, YELLOW)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

        coin_text = font.render(f"Coins: {self.player.coins}", True, YELLOW)
        self.screen.blit(coin_text, (10, 10))

        if self.show_instructions:
            self.draw_instructions()

        if self.show_minimap:
            self.draw_minimap()

    def draw_shader_effects(self):
        self.shader_surface.fill((105, 128, 180))  # Fill with a blue-ish color

        # Draw rain
        for x, y in self.rain_drops:
            pygame.draw.line(self.shader_surface, (200, 200, 200), (x, y), (x, y + 5))

        # Apply lightning effect
        if self.lightning_active:
            lightning_surface = pygame.Surface((WIDTH, HEIGHT))
            lightning_surface.fill((255, 255, 255))  # White flash
            lightning_surface.set_alpha(100)  # Semi-transparent
            self.screen.blit(lightning_surface, (0, 0))

        # Apply the shader
        self.screen.blit(self.shader_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Darken buildings
        for building in self.village.buildings:
            dark_surface = pygame.Surface((building.rect.width, building.rect.height))
            dark_surface.fill((0, 0, 0))
            dark_surface.set_alpha(0)  # Adjust this value to make buildings darker or lighter
            self.screen.blit(dark_surface, (building.rect.x - self.camera_x, building.rect.y - self.camera_y))

    def draw_instructions(self):
        instructions = [
            "Game Instructions:",
            "- Use arrow keys to move",
            "- Left-click to move to pointer",
            "- Right-click to fire magic missile",
            "- Press SPACE near green rectangles to enter/exit buildings",
            "- Press ENTER to attack nearby monsters",
            "- Collect coins dropped by defeated monsters",
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

        for building in self.village.buildings:
            minimap_x = int(building.rect.x * scale_x)
            minimap_y = int(building.rect.y * scale_y)
            minimap_width = max(3, int(building.rect.width * scale_x))
            minimap_height = max(3, int(building.rect.height * scale_y))
            pygame.draw.rect(minimap_surface, WHITE, (minimap_x, minimap_y, minimap_width, minimap_height))

        player_x = int(self.player.rect.centerx * scale_x)
        player_y = int(self.player.rect.centery * scale_y)
        pygame.draw.circle(minimap_surface, RED, (player_x, player_y), 2)

        self.screen.blit(minimap_surface, (WIDTH - minimap_size - 10, 10))

if __name__ == "__main__":
    game = Game()
    game.run()
