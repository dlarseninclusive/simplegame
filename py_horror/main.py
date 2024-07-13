import pygame
import sys
import random

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BROWN = (165, 42, 42)
YELLOW = (255, 255, 0)

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Village Horror")
clock = pygame.time.Clock()

# Font setup
font = pygame.font.Font(None, 36)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.speed = 5
        self.health = 100
        self.inventory = []

    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        self.rect.clamp_ip(screen.get_rect())

class Monster(pygame.sprite.Sprite):
    def __init__(self, x, y, monster_type):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.type = monster_type
        self.speed = random.randint(1, 3)

    def update(self, player):
        if self.type == "outdoor":
            dx = player.rect.x - self.rect.x
            dy = player.rect.y - self.rect.y
            dist = (dx**2 + dy**2)**0.5
            if dist != 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
        elif self.type == "indoor":
            # Indoor monsters stay in place until player is close
            if self.rect.colliderect(player.rect.inflate(100, 100)):
                dx = player.rect.x - self.rect.x
                dy = player.rect.y - self.rect.y
                dist = (dx**2 + dy**2)**0.5
                if dist != 0:
                    self.rect.x += (dx / dist) * self.speed
                    self.rect.y += (dy / dist) * self.speed

class Building(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.entrance = pygame.Rect(x + width // 2 - 20, y + height - 10, 40, 10)

class Village:
    def __init__(self):
        self.buildings = pygame.sprite.Group()
        self.outdoor_monsters = pygame.sprite.Group()
        self.setup_village()

    def setup_village(self):
        # Create some buildings
        buildings = [
            (50, 50, 100, 100),
            (200, 100, 150, 120),
            (400, 50, 120, 100),
            (600, 100, 100, 100),
            (100, 300, 200, 150),
            (400, 300, 180, 130),
        ]
        for building in buildings:
            self.buildings.add(Building(*building))

        # Add outdoor monsters
        for _ in range(5):
            monster = Monster(random.randint(0, WIDTH), random.randint(0, HEIGHT), "outdoor")
            self.outdoor_monsters.add(monster)

    def draw(self, screen):
        for building in self.buildings:
            screen.blit(building.image, building.rect)
            pygame.draw.rect(screen, GREEN, building.entrance)
        self.outdoor_monsters.draw(screen)

    def update(self, player):
        self.outdoor_monsters.update(player)

class IndoorScene:
    def __init__(self):
        self.monsters = pygame.sprite.Group()
        self.setup_room()

    def setup_room(self):
        # Add indoor monsters
        for _ in range(random.randint(1, 3)):
            monster = Monster(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50), "indoor")
            self.monsters.add(monster)

    def draw(self, screen):
        screen.fill(BLACK)
        pygame.draw.rect(screen, GREEN, (WIDTH // 2 - 20, HEIGHT - 10, 40, 10))  # Exit
        self.monsters.draw(screen)

    def update(self, player):
        self.monsters.update(player)

class Game:
    def __init__(self):
        self.player = Player()
        self.village = Village()
        self.indoor_scenes = [IndoorScene() for _ in range(len(self.village.buildings))]
        self.current_scene = "village"
        self.current_building = None
        self.near_entrance = False

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.try_enter_exit_building()

            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            self.player.move(dx, dy)

            if self.current_scene == "village":
                self.village.update(self.player)
                self.check_near_entrance()
            else:
                self.indoor_scenes[self.current_building].update(self.player)
                self.check_near_exit()

            self.draw()

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def check_near_entrance(self):
        self.near_entrance = False
        for building in self.village.buildings:
            if building.entrance.collidepoint(self.player.rect.midbottom):
                self.near_entrance = True
                break

    def check_near_exit(self):
        exit_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 10, 40, 10)
        self.near_entrance = exit_rect.collidepoint(self.player.rect.midbottom)

    def try_enter_exit_building(self):
        if self.current_scene == "village":
            for i, building in enumerate(self.village.buildings):
                if building.entrance.collidepoint(self.player.rect.midbottom):
                    self.current_scene = "indoor"
                    self.current_building = i
                    self.player.rect.midbottom = (WIDTH // 2, HEIGHT - 20)
                    break
        else:
            exit_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 10, 40, 10)
            if exit_rect.collidepoint(self.player.rect.midbottom):
                self.current_scene = "village"
                building = list(self.village.buildings)[self.current_building]
                self.player.rect.midbottom = building.entrance.midtop

    def draw(self):
        screen.fill(BLACK)
        if self.current_scene == "village":
            self.village.draw(screen)
        else:
            self.indoor_scenes[self.current_building].draw(screen)
        screen.blit(self.player.image, self.player.rect)

        # Draw instruction text
        if self.near_entrance:
            text = font.render("Press SPACE to enter/exit", True, YELLOW)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

if __name__ == "__main__":
    game = Game()
    game.run()