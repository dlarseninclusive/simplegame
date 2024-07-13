import pygame
from constants import *
from entities import Player
from environment import Village, IndoorScene

class Game:
    def __init__(self):
        self.player = Player()
        self.village = Village()
        self.indoor_scenes = [IndoorScene() for _ in range(len(self.village.buildings))]
        self.current_scene = "village"
        self.current_building = None
        self.near_entrance = False
        self.show_instructions = True  # Instructions on by default

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

            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            
            if self.current_scene == "village":
                self.player.move(dx, dy, self.village.buildings)
                self.village.update(self.player)
                self.check_near_entrance()
                if keys[pygame.K_RETURN]:
                    self.player.attack(self.village.monsters)
            else:
                self.player.move(dx, dy, [])  # No buildings in indoor scenes
                self.indoor_scenes[self.current_building].update(self.player)
                self.check_near_exit()
                if keys[pygame.K_RETURN]:
                    self.player.attack(self.indoor_scenes[self.current_building].monsters)

            self.player.update()
            self.draw()

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        return False  # Indicate that the game has ended

    def check_near_entrance(self):
        self.near_entrance = False
        for building in self.village.buildings:
            if building.entrance.colliderect(self.player.rect):
                self.near_entrance = True
                break

    def check_near_exit(self):
        exit_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 10, 40, 10)
        self.near_entrance = exit_rect.colliderect(self.player.rect)

    def try_enter_exit_building(self):
        if self.current_scene == "village":
            for i, building in enumerate(self.village.buildings):
                if building.entrance.colliderect(self.player.rect):
                    self.current_scene = "indoor"
                    self.current_building = i
                    self.player.rect.midbottom = (WIDTH // 2, HEIGHT - 20)
                    return
        else:
            exit_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 10, 40, 10)
            if exit_rect.colliderect(self.player.rect):
                self.current_scene = "village"
                building = list(self.village.buildings)[self.current_building]
                self.player.rect.midbottom = building.entrance.midtop
                return

    def draw(self):
        screen.fill(BLACK)
        if self.current_scene == "village":
            self.village.draw(screen)
        else:
            self.indoor_scenes[self.current_building].draw(screen)
        screen.blit(self.player.image, self.player.rect)
        self.player.draw_health_bar(screen)

        if self.near_entrance:
            text = font.render("Press SPACE to enter/exit", True, YELLOW)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

        if self.show_instructions:
            self.draw_instructions()

    def draw_instructions(self):
        instructions = [
            "Game Instructions:",
            "- Use arrow keys to move",
            "- Press SPACE near green rectangles to enter/exit buildings",
            "- Press ENTER to attack nearby monsters",
            "- Avoid or defeat monsters to survive",
            "- Green: Zombies (slow)",
            "- Red: Trackers (fast)",
            "- Purple: Vampires (inside houses)",
            "- Dark Orange: Bats (medium speed)",
            "- Press 'I' to toggle instructions",
            "- Press 'ESC' to exit the game"
        ]
        
        instruction_surface = pygame.Surface((WIDTH, HEIGHT))
        instruction_surface.set_alpha(200)
        instruction_surface.fill(BLACK)
        screen.blit(instruction_surface, (0, 0))

        for i, line in enumerate(instructions):
            text = small_font.render(line, True, WHITE)
            screen.blit(text, (20, 20 + i * 30))