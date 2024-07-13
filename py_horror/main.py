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

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Horror Mansion")
clock = pygame.time.Clock()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
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
        self.image = pygame.Surface((40, 40))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.type = monster_type
        self.speed = random.randint(1, 3)

    def update(self, player):
        if self.type == "ghost":
            # Ghost movement logic
            pass
        elif self.type == "zombie":
            # Zombie movement logic
            dx = player.rect.x - self.rect.x
            dy = player.rect.y - self.rect.y
            dist = (dx**2 + dy**2)**0.5
            if dist != 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed

class Scene:
    def __init__(self):
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill(BLACK)
        self.monsters = pygame.sprite.Group()
        self.items = pygame.sprite.Group()

    def add_monster(self, monster):
        self.monsters.add(monster)

    def update(self, player):
        self.monsters.update(player)

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        self.monsters.draw(screen)
        self.items.draw(screen)

class Game:
    def __init__(self):
        self.player = Player()
        self.current_scene = 0
        self.scenes = [Scene() for _ in range(5)]  # Create 5 scenes
        self.setup_scenes()

    def setup_scenes(self):
        # Add monsters and items to each scene
        for scene in self.scenes:
            for _ in range(random.randint(1, 3)):
                monster = Monster(random.randint(0, WIDTH), random.randint(0, HEIGHT), 
                                  random.choice(["ghost", "zombie"]))
                scene.add_monster(monster)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            self.player.move(dx, dy)

            current_scene = self.scenes[self.current_scene]
            current_scene.update(self.player)

            screen.fill(BLACK)
            current_scene.draw(screen)
            screen.blit(self.player.image, self.player.rect)

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()