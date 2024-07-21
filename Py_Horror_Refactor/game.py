import pygame
import math
from constants import *
from entities.player import Player
from environment.village import Village
from environment.indoor_scene import IndoorScene
from environment.mansion_scene import MansionScene
from environment.graveyard_scene import GraveyardScene
from environment.building import Building, MansionBuilding
from ui.hud import HUD
from entities.magic_missile import MagicMissile

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Village Horror")
        self.clock = pygame.time.Clock()
        self.reset_game()

    def reset_game(self):
        self.player = Player()
        self.player.health = self.player.max_health
        self.scenes = {
            'village': Village(),
            'indoor': IndoorScene(),
            'mansion': MansionScene(),
            'graveyard': GraveyardScene()
        }
        self.current_scene = 'village'
        self.hud = HUD()
        self.magic_missiles = pygame.sprite.Group()

    def run(self):
        running = True
        while running:
            if self.player.health <= 0:
                restart = self.game_over_screen()
                if restart:
                    self.reset_game()
                else:
                    running = False
                    break
            
            running = self.handle_events()
            if not running:
                break

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
                elif event.key == pygame.K_SPACE:
                    print("Space key pressed - attempting scene transition")
                    self.try_scene_transition()
                elif event.key == pygame.K_RETURN:
                    self.player.attack(self.scenes[self.current_scene].monsters)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    target_x = mouse_pos[0] + self.player.camera_x
                    target_y = mouse_pos[1] + self.player.camera_y
                    self.player.set_target((target_x, target_y))
                elif event.button == 3:  # Right mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    target_x = mouse_pos[0] + self.player.camera_x
                    target_y = mouse_pos[1] + self.player.camera_y
                    self.fire_magic_missile((target_x, target_y))
        return True

    def update(self):
        self.player.update()
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]

        current_scene = self.scenes[self.current_scene]
        self.player.move(dx, dy, current_scene.buildings if hasattr(current_scene, 'buildings') else [])
        self.player.update()
        current_scene.update(self.player)

        if self.player.target_pos:
            dx = self.player.target_pos[0] - self.player.rect.centerx
            dy = self.player.target_pos[1] - self.player.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            if distance > self.player.speed:
                dx = dx / distance * self.player.speed
                dy = dy / distance * self.player.speed
                self.player.move(dx, dy, current_scene.buildings if hasattr(current_scene, 'buildings') else [])
            else:
                self.player.rect.center = self.player.target_pos
                self.player.target_pos = None

        self.magic_missiles.update()
        for missile in self.magic_missiles:
            for monster in current_scene.monsters:
                if pygame.sprite.collide_rect(missile, monster):
                    monster.health -= missile.damage
                    missile.kill()
                    if monster.health <= 0:
                        coin = monster.drop_coin()
                        if coin:
                            current_scene.coins.add(coin)
                        monster.kill()

        coins_collected = pygame.sprite.spritecollide(self.player, current_scene.coins, True)
        for coin in coins_collected:
            self.player.collect_coin(coin)

        for monster in current_scene.monsters:
            if monster.rect.colliderect(self.player.rect):
                monster.attack(self.player)

    def draw(self):
        self.screen.fill(BLACK)
        current_scene = self.scenes[self.current_scene]
        current_scene.draw(self.screen, self.player.camera_x, self.player.camera_y)
        self.player.draw(self.screen)
        self.magic_missiles.draw(self.screen)
        self.hud.draw(self.screen, self.player, self.current_scene)
        self.hud.draw_instructions(self.screen)

    def try_scene_transition(self):
        print(f"Attempting scene transition. Current scene: {self.current_scene}")
        print(f"Player position: {self.player.rect.center}")

        if self.current_scene == 'village':
            for building in self.scenes['village'].buildings:
                if building.entrance.colliderect(self.player.rect):
                    if isinstance(building, MansionBuilding):
                        self.current_scene = 'mansion'
                    else:
                        self.current_scene = 'indoor'
                    self.player.reset_position(WIDTH // 2, HEIGHT - 50)
                    print(f"Entered building. New scene: {self.current_scene}")
                    return
            graveyard_entrance = getattr(self.scenes['village'], 'graveyard_entrance', None)
            if graveyard_entrance and graveyard_entrance.colliderect(self.player.rect):
                self.current_scene = 'graveyard'
                self.player.reset_position(WIDTH // 2, HEIGHT - 50)
                print("Entered graveyard")
                return
        elif self.current_scene in ['indoor', 'mansion', 'graveyard']:
            print("In a building or graveyard, checking for exit")
            exit_rect = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 20, 50, 20)
            print(f"Exit rect: {exit_rect}")
            print(f"Player rect: {self.player.rect}")
            if self.player.rect.colliderect(exit_rect):
                print("Player is in exit area, transitioning to village")
                self.current_scene = 'village'
                self.player.reset_position(MAP_WIDTH // 2, MAP_HEIGHT // 2)
            else:
                print("Player is not in exit area")

        print(f"After transition attempt, current scene is: {self.current_scene}")

    def fire_magic_missile(self, target_pos):
        missile = self.player.fire_magic_missile(target_pos)
        if missile:
            self.magic_missiles.add(missile)

    def game_over_screen(self):
        self.screen.fill(BLACK)
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', True, RED)
        text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2 - 50))
        self.screen.blit(text, text_rect)

        font = pygame.font.Font(None, 36)
        text = font.render('Press R to Restart or Q to Quit', True, WHITE)
        text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2 + 50))
        self.screen.blit(text, text_rect)

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return True
                    elif event.key == pygame.K_q:
                        return False
            
            pygame.time.wait(100)

        return False

if __name__ == "__main__":
    game = Game()
    game.run()
