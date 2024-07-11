import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple RPG")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Font
font = pygame.font.Font(None, 36)

class Character:
    def __init__(self, name, health, attack, x, y, color):
        self.name = name
        self.health = health
        self.attack = attack
        self.x = x
        self.y = y
        self.color = color

    def is_alive(self):
        return self.health > 0

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), 20)
        name_text = font.render(self.name, True, BLACK)
        surface.blit(name_text, (self.x - 30, self.y - 50))

class Player(Character):
    def __init__(self, name):
        super().__init__(name, health=100, attack=10, x=WIDTH//2, y=HEIGHT//2, color=BLUE)

class Enemy(Character):
    def __init__(self, name, health, attack, x, y):
        super().__init__(name, health, attack, x, y, color=RED)

def draw_health_bars(surface, player, enemy):
    pygame.draw.rect(surface, RED, (50, 50, 200, 20))
    pygame.draw.rect(surface, GREEN, (50, 50, 200 * (player.health / 100), 20))
    
    pygame.draw.rect(surface, RED, (WIDTH - 250, 50, 200, 20))
    pygame.draw.rect(surface, GREEN, (WIDTH - 250, 50, 200 * (enemy.health / 100), 20))

def combat(player, enemy):
    clock = pygame.time.Clock()
    combat_active = True

    while combat_active and player.is_alive() and enemy.is_alive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:  # Attack
                    enemy.health -= player.attack
                    if enemy.is_alive():
                        player.health -= enemy.attack
                elif event.key == pygame.K_r:  # Run
                    if random.random() < 0.5:
                        combat_active = False
                    else:
                        player.health -= enemy.attack

        screen.fill(WHITE)
        player.draw(screen)
        enemy.draw(screen)
        draw_health_bars(screen, player, enemy)

        pygame.display.flip()
        clock.tick(60)

    return player.is_alive()

def main():
    player = Player("Hero")
    enemy = Enemy("Goblin", health=50, attack=5, x=WIDTH-100, y=HEIGHT-100)
    
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if combat(player, enemy):
                        enemy = Enemy("Goblin", health=50, attack=5, x=random.randint(100, WIDTH-100), y=random.randint(100, HEIGHT-100))
                    else:
                        running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.x -= 5
        if keys[pygame.K_RIGHT]:
            player.x += 5
        if keys[pygame.K_UP]:
            player.y -= 5
        if keys[pygame.K_DOWN]:
            player.y += 5

        screen.fill(WHITE)
        player.draw(screen)
        enemy.draw(screen)

        instructions = font.render("Use arrow keys to move. Press SPACE to initiate combat.", True, BLACK)
        screen.blit(instructions, (10, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()