import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Echoes of the Abyss: Convergence Prototype")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Fonts
font = pygame.font.Font(None, 36)
dialog_font = pygame.font.Font(None, 24)

# Character class
class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.max_health = 100
        self.health = self.max_health
        self.inventory = []

    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        self.rect.clamp_ip(screen.get_rect())

    def attack(self):
        return pygame.Rect(self.rect.centerx - 15, self.rect.centery - 15, 30, 30)

    def draw_health_bar(self, surface):
        bar_width = 30
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x, self.rect.y - 10, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y - 10, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = random.randint(1, 3)
        self.max_health = 50
        self.health = self.max_health

    def update(self, target):
        dx = target.rect.x - self.rect.x
        dy = target.rect.y - self.rect.y
        dist = max(abs(dx), abs(dy))
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

    def draw_health_bar(self, surface):
        bar_width = 20
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x, self.rect.y - 10, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y - 10, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

# Item class
class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.type = item_type

# NPC class
class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, name):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.name = name
        self.dialogue = [
            f"Hello, I'm {name}. Welcome to our town!",
            "We've been having some strange occurrences lately...",
            "Can you help us investigate?",
            "Be careful out there!"
        ]
        self.current_dialogue = 0

    def talk(self):
        text = self.dialogue[self.current_dialogue]
        self.current_dialogue = (self.current_dialogue + 1) % len(self.dialogue)
        return text

# Game state
class GameState:
    def __init__(self):
        self.characters = [
            Character(WIDTH // 4, HEIGHT // 2, WHITE, 5),
            Character(WIDTH // 2, HEIGHT // 2, BLUE, 3),
            Character(3 * WIDTH // 4, HEIGHT // 2, GREEN, 4)
        ]
        self.active_char_index = 0
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.mission = "Collect 3 items and defeat 5 enemies"
        self.items_collected = 0
        self.enemies_defeated = 0
        self.scene = "town"
        self.dialog_text = ""
        self.dialog_active = False
        self.current_npc = None
        self.scenes = {
            "town": {
                "npcs": pygame.sprite.Group(),
                "enemies": pygame.sprite.Group(),
                "items": pygame.sprite.Group()
            },
            "dungeon": {
                "npcs": pygame.sprite.Group(),
                "enemies": pygame.sprite.Group(),
                "items": pygame.sprite.Group()
            }
        }
        self.setup_scenes()
        self.load_scene()

    def setup_scenes(self):
        # Set up the town scene
        town_scene = self.scenes["town"]
        for _ in range(3):
            npc = NPC(random.randint(0, WIDTH), random.randint(0, HEIGHT), f"Villager {_+1}")
            town_scene["npcs"].add(npc)

        # Set up the dungeon scene
        dungeon_scene = self.scenes["dungeon"]
        for _ in range(5):
            enemy = Enemy(random.randint(0, WIDTH), random.randint(0, HEIGHT))
            dungeon_scene["enemies"].add(enemy)
        for _ in range(3):
            item = Item(random.randint(0, WIDTH), random.randint(0, HEIGHT), "health")
            dungeon_scene["items"].add(item)

    def load_scene(self):
        # Clear existing sprites except characters
        for sprite in self.all_sprites:
            if not isinstance(sprite, Character):
                sprite.kill()

        # Always add characters to all_sprites
        for char in self.characters:
            self.all_sprites.add(char)

        # Load the current scene
        current_scene = self.scenes[self.scene]
        
        self.npcs.empty()
        self.enemies.empty()
        self.items.empty()
        
        for npc in current_scene["npcs"]:
            self.all_sprites.add(npc)
            self.npcs.add(npc)

        for enemy in current_scene["enemies"]:
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

        for item in current_scene["items"]:
            self.all_sprites.add(item)
            self.items.add(item)

    def switch_character(self):
        self.active_char_index = (self.active_char_index + 1) % len(self.characters)

    def get_active_character(self):
        return self.characters[self.active_char_index]

    def change_scene(self):
        # Switch scenes while preserving the current state
        self.scene = "dungeon" if self.scene == "town" else "town"
        self.load_scene()

    def update(self, mouse_pos):
        if not self.dialog_active:
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            self.get_active_character().move(dx, dy)

            # Mouse movement
            char = self.get_active_character()
            if pygame.mouse.get_pressed()[0]:  # Left mouse button
                char.rect.center = mouse_pos

            if self.scene == "dungeon":
                for enemy in self.enemies:
                    enemy.update(self.get_active_character())

                collected_items = pygame.sprite.spritecollide(self.get_active_character(), self.items, True)
                for item in collected_items:
                    self.get_active_character().inventory.append(item.type)
                    self.items_collected += 1

                if keys[pygame.K_SPACE]:
                    attack_rect = self.get_active_character().attack()
                    defeated_enemies = [e for e in self.enemies if attack_rect.colliderect(e.rect)]
                    for enemy in defeated_enemies:
                        enemy.health -= 10
                        if enemy.health <= 0:
                            enemy.kill()
                            self.enemies_defeated += 1

                if self.items_collected >= 3 and self.enemies_defeated >= 5:
                    self.mission = "Mission Complete! Press R to restart."

            # NPC interaction
            for npc in self.npcs:
                if char.rect.colliderect(npc.rect) and not self.dialog_active:
                    self.dialog_text = npc.talk()
                    self.dialog_active = True
                    self.current_npc = npc
                    break

    def draw(self, screen):
        screen.fill(BLACK)
        self.all_sprites.draw(screen)

        for character in self.characters:
            character.draw_health_bar(screen)

        for enemy in self.enemies:
            enemy.draw_health_bar(screen)

        # Draw UI
        health_text = font.render(f"Health: {self.get_active_character().health}", True, WHITE)
        screen.blit(health_text, (10, 10))

        inventory_text = font.render(f"Inventory: {len(self.get_active_character().inventory)}", True, WHITE)
        screen.blit(inventory_text, (10, 50))

        mission_text = font.render(self.mission, True, WHITE)
        screen.blit(mission_text, (WIDTH // 2 - mission_text.get_width() // 2, 10))

        scene_text = font.render(f"Scene: {self.scene.capitalize()}", True, WHITE)
        screen.blit(scene_text, (WIDTH - scene_text.get_width() - 10, 10))

        # Draw character indicator
        char = self.get_active_character()
        pygame.draw.rect(screen, YELLOW, (char.rect.x - 2, char.rect.y - 2, char.rect.width + 4, char.rect.height + 4), 2)

        # Draw dialog box
        button_rect = None
        if self.dialog_active:
            dialog_box = pygame.Surface((WIDTH - 100, 100))
            dialog_box.fill(WHITE)
            dialog_box.set_alpha(200)
            screen.blit(dialog_box, (50, HEIGHT - 150))
            dialog_text = dialog_font.render(self.dialog_text, True, BLACK)
            screen.blit(dialog_text, (60, HEIGHT - 140))
            exit_text = dialog_font.render("Press SPACE to exit, ENTER to continue", True, BLACK)
            screen.blit(exit_text, (60, HEIGHT - 80))

            # Draw exit button
            button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 100, 100, 40)
            pygame.draw.rect(screen, RED, button_rect)
            button_text = dialog_font.render("Exit", True, WHITE)
            screen.blit(button_text, (WIDTH - 130, HEIGHT - 90))

        return button_rect  # Return the button rectangle for click detection

# Game loop
def main():
    clock = pygame.time.Clock()
    game_state = GameState()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    game_state.switch_character()
                elif event.key == pygame.K_r:
                    game_state = GameState()
                elif event.key == pygame.K_c:
                    game_state.change_scene()
                elif event.key == pygame.K_SPACE:
                    if game_state.dialog_active:
                        # Exit dialog if active
                        game_state.dialog_active = False
                        game_state.current_npc = None
                elif event.key == pygame.K_RETURN:
                    if game_state.dialog_active and game_state.current_npc:
                        # Continue dialog if active
                        game_state.dialog_text = game_state.current_npc.talk()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Right mouse button
                    game_state.change_scene()

                # Handle dialog exit button click
                button_rect = game_state.draw(screen)
                if button_rect and button_rect.collidepoint(event.pos):
                    game_state.dialog_active = False
                    game_state.current_npc = None

        game_state.update(mouse_pos)
        game_state.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
