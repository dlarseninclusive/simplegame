import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Echoes of the Abyss: Convergence Prototype")

# Set up the world size (larger than the display)
WORLD_WIDTH, WORLD_HEIGHT = 1600, 1200

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)  # Additional color for distinct scenes
ORANGE = (255, 165, 0)  # Additional color for distinct scenes

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
        self.target_pos = None

    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        # Keep character within world boundaries
        self.rect.x = max(0, min(self.rect.x, WORLD_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, WORLD_HEIGHT - self.rect.height))

    def update(self):
        # Move toward the target position if set
        if self.target_pos:
            dx = self.target_pos[0] - self.rect.centerx
            dy = self.target_pos[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > self.speed:
                dx, dy = dx / dist, dy / dist
                self.move(dx, dy)
            else:
                self.target_pos = None  # Reached target

    def attack(self):
        return pygame.Rect(self.rect.centerx - 15, self.rect.centery - 15, 30, 30)

    def draw_health_bar(self, surface, camera):
        bar_width = 30
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, fill, bar_height)
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

    def draw_health_bar(self, surface, camera):
        bar_width = 20
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.x - camera.camera.x, self.rect.y - 10 - camera.camera.y, fill, bar_height)
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

# Door class for scene transitions
class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, target_scene):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.target_scene = target_scene

# Camera class
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Offset the entity's position by the camera's top-left position
        return entity.rect.move(-self.camera.x, -self.camera.y)

    def update(self, target):
        x = target.rect.centerx - WIDTH // 2
        y = target.rect.centery - HEIGHT // 2

        # Clamp camera to the boundaries of the world
        x = max(0, min(x, self.width - WIDTH))
        y = max(0, min(y, self.height - HEIGHT))

        self.camera = pygame.Rect(x, y, self.width, self.height)

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
        self.mission = "Collect 3 items and defeat 5 enemies"
        self.items_collected = 0
        self.enemies_defeated = 0
        self.scene = "town"
        self.dialog_text = ""
        self.dialog_active = False
        self.current_npc = None
        self.continue_button_rect = None  # Button for continuing dialog
        self.exit_button_rect = None  # Button for exiting dialog
        self.scenes = {
            "town": {
                "background_color": ORANGE,
                "npcs": pygame.sprite.Group(),
                "enemies": pygame.sprite.Group(),  # No enemies in town
                "items": pygame.sprite.Group(),  # Items if needed
                "doors": pygame.sprite.Group()
            },
            "dungeon": {
                "background_color": PURPLE,
                "npcs": pygame.sprite.Group(),
                "enemies": pygame.sprite.Group(),
                "items": pygame.sprite.Group(),
                "doors": pygame.sprite.Group()
            }
        }
        self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
        self.setup_scenes()
        self.load_scene()

    def setup_scenes(self):
        # Set up the town scene
        town_scene = self.scenes["town"]

        # Add NPCs and doors if they don't already exist
        if not town_scene["npcs"]:
            for _ in range(3):
                npc = NPC(random.randint(0, WORLD_WIDTH - 40), random.randint(0, WORLD_HEIGHT - 40), f"Villager {_+1}")
                town_scene["npcs"].add(npc)

        if not town_scene["doors"]:
            town_door = Door(WORLD_WIDTH - 100, WORLD_HEIGHT // 2, "dungeon")
            town_scene["doors"].add(town_door)

        # Set up the dungeon scene
        dungeon_scene = self.scenes["dungeon"]

        # Add enemies, items, and doors if they don't already exist
        if not dungeon_scene["enemies"]:
            for _ in range(5):
                enemy = Enemy(random.randint(0, WORLD_WIDTH - 20), random.randint(0, WORLD_HEIGHT - 20))
                dungeon_scene["enemies"].add(enemy)

        if not dungeon_scene["items"]:
            for _ in range(3):
                item = Item(random.randint(0, WORLD_WIDTH - 15), random.randint(0, WORLD_HEIGHT - 15), "health")
                dungeon_scene["items"].add(item)

        if not dungeon_scene["doors"]:
            dungeon_door = Door(100, WORLD_HEIGHT // 2, "town")
            dungeon_scene["doors"].add(dungeon_door)

    def load_scene(self):
        # Clear all sprites except characters
        for sprite in self.all_sprites:
            if not isinstance(sprite, Character):
                sprite.kill()

        # Always add characters to all_sprites
        for char in self.characters:
            self.all_sprites.add(char)

        # Load the current scene
        current_scene = self.scenes[self.scene]

        # Re-add scene-specific sprites
        self.all_sprites.add(current_scene["npcs"])
        self.all_sprites.add(current_scene["enemies"])
        self.all_sprites.add(current_scene["items"])
        self.all_sprites.add(current_scene["doors"])

    def switch_character(self):
        self.active_char_index = (self.active_char_index + 1) % len(self.characters)

    def get_active_character(self):
        return self.characters[self.active_char_index]

    def change_scene(self, target_scene):
        # Change scene to the target scene
        self.scene = target_scene
        self.load_scene()

    def update(self, mouse_pos):
        active_character = self.get_active_character()

        if not self.dialog_active:
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            active_character.move(dx, dy)

            # Character movement toward mouse click
            if pygame.mouse.get_pressed()[0]:  # Left mouse button
                active_character.target_pos = (mouse_pos[0] + self.camera.camera.x, mouse_pos[1] + self.camera.camera.y)

            active_character.update()

            # Update camera to follow the active character
            self.camera.update(active_character)

            # Enemy movement
            if self.scene == "dungeon":
                for enemy in self.scenes[self.scene]["enemies"]:
                    enemy.update(active_character)

                collected_items = pygame.sprite.spritecollide(active_character, self.scenes[self.scene]["items"], True)
                for item in collected_items:
                    active_character.inventory.append(item.type)
                    self.items_collected += 1

                if keys[pygame.K_SPACE]:
                    attack_rect = active_character.attack()
                    defeated_enemies = [e for e in self.scenes[self.scene]["enemies"] if attack_rect.colliderect(e.rect)]
                    for enemy in defeated_enemies:
                        enemy.health -= 10
                        if enemy.health <= 0:
                            enemy.kill()
                            self.enemies_defeated += 1

                if self.items_collected >= 3 and self.enemies_defeated >= 5:
                    self.mission = "Mission Complete! Press R to restart."

            # NPC interaction
            for npc in self.scenes[self.scene]["npcs"]:
                if active_character.rect.colliderect(npc.rect) and not self.dialog_active:
                    self.dialog_text = npc.talk()
                    self.dialog_active = True
                    self.current_npc = npc
                    break

            # Door interaction
            for door in self.scenes[self.scene]["doors"]:
                if active_character.rect.colliderect(door.rect):
                    self.show_door_instructions(door)

    def show_door_instructions(self, door):
        instructions_text = font.render("Press E to enter", True, WHITE)
        screen.blit(instructions_text, (door.rect.x - 20 - self.camera.camera.x, door.rect.y - 30 - self.camera.camera.y))

    def draw(self, screen):
        # Set background color based on the current scene
        current_scene = self.scenes[self.scene]
        screen.fill(current_scene["background_color"])

        # Draw all sprites with camera offset
        for sprite in self.all_sprites:
            screen.blit(sprite.image, self.camera.apply(sprite))

        for character in self.characters:
            character.draw_health_bar(screen, self.camera)

        for enemy in self.scenes[self.scene]["enemies"]:
            enemy.draw_health_bar(screen, self.camera)

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
        pygame.draw.rect(screen, YELLOW, (char.rect.x - 2 - self.camera.camera.x, char.rect.y - 2 - self.camera.camera.y, char.rect.width + 4, char.rect.height + 4), 2)

        # Draw dialog box
        self.continue_button_rect = None
        self.exit_button_rect = None
        if self.dialog_active:
            dialog_box = pygame.Surface((WIDTH - 100, 100))
            dialog_box.fill(WHITE)
            dialog_box.set_alpha(200)
            screen.blit(dialog_box, (50, HEIGHT - 150))
            dialog_text = dialog_font.render(self.dialog_text, True, BLACK)
            screen.blit(dialog_text, (60, HEIGHT - 140))

            # Draw continue button
            self.continue_button_rect = pygame.Rect(WIDTH - 250, HEIGHT - 100, 100, 40)
            pygame.draw.rect(screen, BLUE, self.continue_button_rect)
            continue_button_text = dialog_font.render("Continue", True, WHITE)
            screen.blit(continue_button_text, (WIDTH - 235, HEIGHT - 90))

            # Draw exit button
            self.exit_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 100, 100, 40)
            pygame.draw.rect(screen, RED, self.exit_button_rect)
            exit_button_text = dialog_font.render("Exit", True, WHITE)
            screen.blit(exit_button_text, (WIDTH - 130, HEIGHT - 90))

    def handle_dialog_continue(self):
        if self.dialog_active and self.current_npc:
            self.dialog_text = self.current_npc.talk()

    def handle_dialog_exit(self):
        self.dialog_active = False
        self.current_npc = None

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
                    game_state = GameState()  # Resets the entire game state
                elif event.key == pygame.K_e:
                    # Check for door interaction
                    for door in game_state.scenes[game_state.scene]["doors"]:
                        if game_state.get_active_character().rect.colliderect(door.rect):
                            game_state.change_scene(door.target_scene)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if game_state.continue_button_rect and game_state.continue_button_rect.collidepoint(event.pos):
                        game_state.handle_dialog_continue()
                    if game_state.exit_button_rect and game_state.exit_button_rect.collidepoint(event.pos):
                        game_state.handle_dialog_exit()

        game_state.update(mouse_pos)
        game_state.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
