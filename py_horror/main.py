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
PURPLE = (128, 0, 128)
DARK_ORANGE = (255, 140, 0)

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Village Horror")
clock = pygame.time.Clock()

# Font setup
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

class Entity(pygame.sprite.Sprite):
    def __init__(self, color, x, y, width, height, speed, max_health):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.max_health = max_health
        self.health = max_health

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x, self.rect.y - 10, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y - 10, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

class Player(Entity):
    def __init__(self):
        super().__init__(WHITE, WIDTH // 2, HEIGHT // 2, 20, 20, 5, 100)
        self.attack_cooldown = 0
        self.attack_range = 50
        self.attack_damage = 20

    def move(self, dx, dy, buildings):
        new_x = self.rect.x + dx * self.speed
        new_y = self.rect.y + dy * self.speed

        # Check x-axis movement
        self.rect.x = new_x
        collided = False
        for building in buildings:
            if self.rect.colliderect(building.rect) and not building.entrance.colliderect(self.rect):
                collided = True
                if dx > 0:  # Moving right
                    self.rect.right = building.rect.left
                elif dx < 0:  # Moving left
                    self.rect.left = building.rect.right
        if not collided:
            self.rect.x = new_x

        # Check y-axis movement
        self.rect.y = new_y
        collided = False
        for building in buildings:
            if self.rect.colliderect(building.rect) and not building.entrance.colliderect(self.rect):
                collided = True
                if dy > 0:  # Moving down
                    self.rect.bottom = building.rect.top
                elif dy < 0:  # Moving up
                    self.rect.top = building.rect.bottom
        if not collided:
            self.rect.y = new_y

        # Keep player within screen bounds
        self.rect.clamp_ip(screen.get_rect())

    def attack(self, monsters):
        if self.attack_cooldown == 0:
            for monster in monsters:
                if monster.rect.colliderect(self.rect.inflate(self.attack_range, self.attack_range)):
                    monster.take_damage(self.attack_damage)
            self.attack_cooldown = 30  # Set cooldown to 30 frames (0.5 seconds at 60 FPS)

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

class Monster(Entity):
    def __init__(self, monster_type, x, y):
        if monster_type == "zombie":
            super().__init__(GREEN, x, y, 30, 30, 0.5, 50)
        elif monster_type == "tracker":
            super().__init__(RED, x, y, 30, 30, 1, 30)
        elif monster_type == "vampire":
            super().__init__(PURPLE, x, y, 30, 30, 0.75, 80)
        elif monster_type == "bat":
            super().__init__(DARK_ORANGE, x, y, 20, 20, 1.5, 20)
        self.type = monster_type

    def update(self, player):
        dx = player.rect.x - self.rect.x
        dy = player.rect.y - self.rect.y
        dist = (dx**2 + dy**2)**0.5
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

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
        self.monsters = pygame.sprite.Group()
        self.setup_village()

    def setup_village(self):
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

        for _ in range(5):
            self.monsters.add(Monster("zombie", random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        for _ in range(2):
            self.monsters.add(Monster("tracker", random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        for _ in range(3):
            self.monsters.add(Monster("bat", random.randint(0, WIDTH), random.randint(0, HEIGHT)))

    def draw(self, screen):
        for building in self.buildings:
            screen.blit(building.image, building.rect)
            pygame.draw.rect(screen, GREEN, building.entrance)
        for monster in self.monsters:
            screen.blit(monster.image, monster.rect)
            monster.draw_health_bar(screen)

    def update(self, player):
        self.monsters.update(player)

class IndoorScene:
    def __init__(self):
        self.monsters = pygame.sprite.Group()
        self.setup_room()

    def setup_room(self):
        self.monsters.add(Monster("vampire", random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)))
        for _ in range(3):
            self.monsters.add(Monster("bat", random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)))

    def draw(self, screen):
        screen.fill(BLACK)
        pygame.draw.rect(screen, GREEN, (WIDTH // 2 - 20, HEIGHT - 10, 40, 10))  # Exit
        for monster in self.monsters:
            screen.blit(monster.image, monster.rect)
            monster.draw_health_bar(screen)

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
        sys.exit()

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

if __name__ == "__main__":
    game = Game()
    game.run()