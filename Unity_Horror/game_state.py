import pygame
import random
import math
from character import Character
from enemy import Enemy
from item import Item
from npc import NPC
from door import Door
from building import Building
from camera import Camera
from settings import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, ORANGE, PURPLE, WHITE, YELLOW, RED

class GameState:
    def __init__(self, font, dialog_font):
        self.font = font
        self.dialog_font = dialog_font

        # Set up the display
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Echoes of the Abyss: Convergence Prototype")

        self.characters = [
            Character(WIDTH // 4, HEIGHT // 2, WHITE, 5),
            Character(WIDTH // 2, HEIGHT // 2, (0, 0, 255), 3),  # Blue color
            Character(3 * WIDTH // 4, HEIGHT // 2, (0, 255, 0), 4)  # Green color
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
        self.continue_button_rect = None
        self.exit_button_rect = None
        self.interaction_cooldown = 0
        self.scenes = {
            "town": {
                "background_color": ORANGE,
                "npcs": pygame.sprite.Group(),
                "enemies": pygame.sprite.Group(),
                "items": pygame.sprite.Group(),
                "doors": pygame.sprite.Group(),
                "buildings": pygame.sprite.Group()
            },
            "dungeon": {
                "background_color": PURPLE,
                "npcs": pygame.sprite.Group(),
                "enemies": pygame.sprite.Group(),
                "items": pygame.sprite.Group(),
                "doors": pygame.sprite.Group(),
                "buildings": pygame.sprite.Group()
            }
        }
        self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
        self.setup_scenes()
        self.load_scene()
        self.load_scene_state()

    def setup_scenes(self):
        # Set up the town scene
        town_scene = self.scenes["town"]
        if len(town_scene["npcs"]) == 0:
            for _ in range(3):
                npc = NPC(random.randint(0, WORLD_WIDTH - 40), random.randint(0, WORLD_HEIGHT - 40), f"Villager {_+1}")
                town_scene["npcs"].add(npc)
        if len(town_scene["doors"]) == 0:
            town_door = Door(WORLD_WIDTH - 100, WORLD_HEIGHT // 2, "dungeon")
            town_scene["doors"].add(town_door)

        # Set up the dungeon scene
        dungeon_scene = self.scenes["dungeon"]
        if len(dungeon_scene["enemies"]) == 0:
            for _ in range(5):
                enemy = Enemy(random.randint(0, WORLD_WIDTH - 20), random.randint(0, WORLD_HEIGHT - 20))
                dungeon_scene["enemies"].add(enemy)
        if len(dungeon_scene["items"]) == 0:
            for _ in range(3):
                item = Item(random.randint(0, WORLD_WIDTH - 15), random.randint(0, WORLD_HEIGHT - 15), "health")
                dungeon_scene["items"].add(item)
        if len(dungeon_scene["doors"]) == 0:
            dungeon_door = Door(100, WORLD_HEIGHT // 2, "town")
            dungeon_scene["doors"].add(dungeon_door)

        # Add buildings to both scenes
        self.scenes["town"]["buildings"] = self.create_buildings_for_scene("town")
        self.scenes["dungeon"]["buildings"] = self.create_buildings_for_scene("dungeon")

    def create_buildings_for_scene(self, scene_name):
        buildings = pygame.sprite.Group()
        if scene_name == "town":
            buildings.add(Building(100, 100, 200, 150, (139, 69, 19)))  # Brown building
            buildings.add(Building(400, 200, 180, 120, (169, 169, 169)))  # Gray building
            buildings.add(Building(700, 300, 250, 200, (205, 133, 63)))  # Peru colored building
        elif scene_name == "dungeon":
            buildings.add(Building(200, 200, 100, 100, (64, 64, 64)))  # Dark gray obstacle
            buildings.add(Building(500, 400, 150, 80, (128, 128, 128)))  # Light gray obstacle
            buildings.add(Building(800, 100, 120, 120, (47, 79, 79)))  # Dark slate gray obstacle
        return buildings

    def load_scene(self):
        for sprite in self.all_sprites:
            if not isinstance(sprite, Character):
                sprite.kill()
        for char in self.characters:
            self.all_sprites.add(char)
        current_scene = self.scenes[self.scene]
        self.all_sprites.add(current_scene["npcs"])
        self.all_sprites.add(current_scene["enemies"])
        self.all_sprites.add(current_scene["items"])
        self.all_sprites.add(current_scene["doors"])
        self.all_sprites.add(current_scene["buildings"])

    def switch_character(self):
        self.active_char_index = (self.active_char_index + 1) % len(self.characters)

    def get_active_character(self):
        return self.characters[self.active_char_index]

    def change_scene(self, target_scene):
        self.save_scene_state()
        self.scene = target_scene
        self.load_scene()
        self.load_scene_state()

    def save_scene_state(self):
        current_scene = self.scenes[self.scene]
        current_scene["saved_state"] = {
            "npcs": [(npc.rect.topleft, npc.current_dialogue) for npc in current_scene["npcs"]],
            "enemies": [(enemy.rect.topleft, enemy.health) for enemy in current_scene["enemies"]],
            "items": [item.rect.topleft for item in current_scene["items"]],
            "buildings": [building.rect.topleft for building in current_scene["buildings"]]
        }

    def load_scene_state(self):
        current_scene = self.scenes[self.scene]
        if "saved_state" in current_scene:
            saved_state = current_scene["saved_state"]

            for npc, (pos, dialogue) in zip(current_scene["npcs"], saved_state["npcs"]):
                npc.rect.topleft = pos
                npc.current_dialogue = dialogue

            for enemy, (pos, health) in zip(current_scene["enemies"], saved_state["enemies"]):
                enemy.rect.topleft = pos
                enemy.health = health

            for item, pos in zip(current_scene["items"], saved_state["items"]):
                item.rect.topleft = pos

            for building, pos in zip(current_scene["buildings"], saved_state["buildings"]):
                building.rect.topleft = pos

    def update(self):
        active_character = self.get_active_character()

        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1

        if not self.dialog_active:
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]

            self.move_character(active_character, dx * active_character.speed, dy * active_character.speed)

            active_character.update()

            self.camera.update(active_character)

            if self.scene == "dungeon":
                for enemy in self.scenes[self.scene]["enemies"]:
                    enemy.update(active_character)

                collected_items = pygame.sprite.spritecollide(active_character, self.scenes[self.scene]["items"], True)
                for item in collected_items:
                    active_character.inventory.append(item.type)
                    self.items_collected += 1

                defeated_enemies = []  # Initialize as an empty list
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

            for npc in self.scenes[self.scene]["npcs"]:
                if (
                    active_character.rect.colliderect(npc.rect)
                    and not self.dialog_active
                    and self.interaction_cooldown == 0
                ):
                    self.dialog_text = npc.talk()
                    self.dialog_active = True
                    self.current_npc = npc
                    break

            for door in self.scenes[self.scene]["doors"]:
                if active_character.rect.colliderect(door.rect):
                    self.show_door_instructions(door)

    def move_character(self, character, dx, dy):
        original_pos = character.rect.topleft
        character.move(dx, dy)
        if self.check_collision(character):
            character.rect.topleft = original_pos

    def check_collision(self, character):
        return pygame.sprite.spritecollideany(character, self.scenes[self.scene]["buildings"])

    def show_door_instructions(self, door):
        instructions_text = self.font.render("Press E to enter", True, WHITE)
        self.screen.blit(instructions_text, (door.rect.x - 20 - self.camera.camera.x, door.rect.y - 30 - self.camera.camera.y))

    def draw(self, screen):
        current_scene = self.scenes[self.scene]
        screen.fill(current_scene["background_color"])

        for sprite in self.all_sprites:
            screen.blit(sprite.image, self.camera.apply(sprite))

        for character in self.characters:
            character.draw_health_bar(screen, self.camera)

        for enemy in self.scenes[self.scene]["enemies"]:
            enemy.draw_health_bar(screen, self.camera)

        health_text = self.font.render(f"Health: {self.get_active_character().health}", True, WHITE)
        screen.blit(health_text, (10, 10))

        inventory_text = self.font.render(f"Inventory: {len(self.get_active_character().inventory)}", True, WHITE)
        screen.blit(inventory_text, (10, 50))

        mission_text = self.font.render(self.mission, True, WHITE)
        screen.blit(mission_text, (WIDTH // 2 - mission_text.get_width() // 2, 10))

        scene_text = self.font.render(f"Scene: {self.scene.capitalize()}", True, WHITE)
        screen.blit(scene_text, (WIDTH - scene_text.get_width() - 10, 10))

        char = self.get_active_character()
        pygame.draw.rect(screen, YELLOW, (char.rect.x - 2 - self.camera.camera.x, char.rect.y - 2 - self.camera.camera.y, char.rect.width + 4, char.rect.height + 4), 2)

        self.continue_button_rect = None
        self.exit_button_rect = None
        if self.dialog_active:
            dialog_box = pygame.Surface((WIDTH - 100, 100))
            dialog_box.fill(WHITE)
            dialog_box.set_alpha(200)
            screen.blit(dialog_box, (50, HEIGHT - 150))
            dialog_text = self.dialog_font.render(self.dialog_text, True, (0, 0, 0))
            screen.blit(dialog_text, (60, HEIGHT - 140))

            self.continue_button_rect = pygame.Rect(WIDTH - 250, HEIGHT - 100, 100, 40)
            pygame.draw.rect(screen, (0, 0, 255), self.continue_button_rect)
            continue_button_text = self.dialog_font.render("Continue", True, WHITE)
            screen.blit(continue_button_text, (WIDTH - 235, HEIGHT - 90))

            self.exit_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 100, 100, 40)
            pygame.draw.rect(screen, RED, self.exit_button_rect)
            exit_button_text = self.dialog_font.render("Exit", True, WHITE)
            screen.blit(exit_button_text, (WIDTH - 130, HEIGHT - 90))

    def handle_dialog_continue(self):
        if self.dialog_active and self.current_npc:
            self.dialog_text = self.current_npc.talk()

    def handle_dialog_exit(self):
        if self.dialog_active:
            self.move_character_away_from_npc()
            self.dialog_active = False
            self.current_npc = None

    def move_character_away_from_npc(self):
        active_character = self.get_active_character()
        if self.current_npc:
            dx = active_character.rect.x - self.current_npc.rect.x
            dy = active_character.rect.y - self.current_npc.rect.y
            distance = math.hypot(dx, dy)

            if distance < 30:
                move_x = 0
                move_y = 0
                move_distance = 10
                if abs(dx) > abs(dy):
                    move_x = move_distance if dx > 0 else -move_distance
                else:
                    move_y = move_distance if dy > 0 else -move_distance
                self.move_character(active_character, move_x, move_y)

            active_character.target_pos = None
            self.interaction_cooldown = 30
