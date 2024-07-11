import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 1024, 768
GRID_SIZE = 80  # Size of each grid cell
ROAD_WIDTH = 35  # Width of the road
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("City Simulation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ROAD_COLOR = (50, 50, 50)
TEXT_BACKGROUND_COLOR = (200, 200, 200, 150)  # Gray background with transparency

# Load sprites and scale them
sprite_size = (45, 45)  # New size for the sprites
player_sprite = pygame.transform.scale(pygame.image.load('player.png'), sprite_size)
criminal_sprite = pygame.transform.scale(pygame.image.load('criminal.png'), sprite_size)
police_sprite = pygame.transform.scale(pygame.image.load('police.png'), sprite_size)
civilian_sprite = pygame.transform.scale(pygame.image.load('civilian.png'), sprite_size)

# Load building images
house_images = [
    pygame.transform.scale(pygame.image.load('house1.png'), (GRID_SIZE, GRID_SIZE)),
    pygame.transform.scale(pygame.image.load('house2.png'), (GRID_SIZE, GRID_SIZE)),
    pygame.transform.scale(pygame.image.load('house3.png'), (GRID_SIZE, GRID_SIZE)),
]
hospital_image = pygame.transform.scale(pygame.image.load('hospital.png'), (GRID_SIZE, GRID_SIZE))
jail_image = pygame.transform.scale(pygame.image.load('jail.png'), (GRID_SIZE, GRID_SIZE))

# Game state
total_muggings = 0
total_burglaries = 0
criminals_caught = 0

# Instructions text
instructions_text = [
    "Instructions:",
    "Arrow keys to move",
    "G to change alignment to good",
    "E to change alignment to evil",
    "Space to interact",
    "I to toggle instructions",
    "ESC to exit"
]

# Player
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 35
        self.speed = 5
        self.sprite = player_sprite
        self.health = 100
        self.karma = 0
        self.alignment = "neutral"
        self.current_quest = None

    def move(self, dx, dy, buildings):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        new_rect = pygame.Rect(new_x, new_y, self.size, self.size)
        if not any(building.is_colliding(new_rect) for building in buildings):
            self.x = max(0, min(new_x, WIDTH - self.size))
            self.y = max(0, min(new_y, HEIGHT - self.size))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, self.size, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, self.size * (self.health / 100), 5))

    def change_alignment(self, alignment):
        self.alignment = alignment

    def interact(self, npcs, buildings):
        for npc in npcs:
            if distance(self, npc) < 50:
                return npc
        for building in buildings:
            if building.rect.collidepoint(self.x, self.y):
                return building
        return None

# NPCs
class NPC:
    def __init__(self, x, y, sprite, npc_type):
        self.x = x
        self.y = y
        self.size = 35
        self.speed = 2
        self.sprite = sprite
        self.type = npc_type
        self.direction = random.choice(["up", "down", "left", "right"])
        self.move_timer = 0
        self.in_jail = False
        self.jail_timer = 600
        self.crime_timer = random.randint(300, 600)
        self.health = 100
        self.committed_crime = False
        self.in_building = None
        self.building_timer = 0
        self.cooldown_timer = 0  # Cooldown timer for healing
        self.path = []
        self.path_index = 0
        self.dialog = self.generate_dialog()

    def move(self, buildings, hospital):
        if self.in_jail or self.in_building:
            return

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if not self.path:
            self.generate_path()

        if self.path_index < len(self.path):
            target_x, target_y = self.path[self.path_index]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < self.speed:
                self.x, self.y = target_x, target_y
                self.path_index += 1
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        if self.path_index >= len(self.path):
            self.generate_path()

    def generate_path(self):
        start_x = int(self.x // (GRID_SIZE + ROAD_WIDTH)) * (GRID_SIZE + ROAD_WIDTH) + ROAD_WIDTH // 2
        start_y = int(self.y // (GRID_SIZE + ROAD_WIDTH)) * (GRID_SIZE + ROAD_WIDTH) + ROAD_WIDTH // 2
        end_x = random.randint(0, WIDTH // (GRID_SIZE + ROAD_WIDTH)) * (GRID_SIZE + ROAD_WIDTH) + ROAD_WIDTH // 2
        end_y = random.randint(0, HEIGHT // (GRID_SIZE + ROAD_WIDTH)) * (GRID_SIZE + ROAD_WIDTH) + ROAD_WIDTH // 2
        
        self.path = [(start_x, start_y), (end_x, start_y), (end_x, end_y)]
        self.path_index = 0

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))
        pygame.draw.rect(screen, RED, (self.x, self.y - 5, self.size, 3))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 5, self.size * (self.health / 100), 3))

    def attempt_crime(self, buildings, civilians):
        global total_muggings, total_burglaries
        if self.type == "criminal" and not self.in_jail and not self.committed_crime and not self.in_building:
            self.crime_timer -= 1
            if self.crime_timer <= 0:
                target = random.choice(buildings + civilians)
                if isinstance(target, Building) and target.type == "normal":
                    print("A building was burglarized!")
                    self.in_building = target
                    self.x, self.y = target.get_random_interior_position()
                    self.building_timer = 180  # 3 seconds in the building
                    total_burglaries += 1
                elif not isinstance(target, Building):
                    print("A civilian was mugged!")
                    total_muggings += 1
                self.committed_crime = True
                self.crime_timer = random.randint(300, 600)

    def generate_dialog(self):
        if self.type == "criminal":
            return ["I'm just minding my own business...", "Nothing to see here, move along."]
        elif self.type == "police":
            return ["Keep the peace, citizen.", "Report any suspicious activity."]
        else:  # civilian
            return ["Nice weather we're having.", "Have you heard about the new restaurant in town?"]

def distance(obj1, obj2):
    return math.sqrt((obj1.x - obj2.x)**2 + (obj1.y - obj2.y)**2)

# Buildings
class Building:
    def __init__(self, x, y, width, height, image, building_type="normal"):
        self.rect = pygame.Rect(x, y, width, height)
        self.image = image
        self.type = building_type
        self.wall_thickness = 5

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def is_colliding(self, rect):
        if self.rect.colliderect(rect):
            inner_rect = pygame.Rect(self.rect.left + self.wall_thickness, 
                                     self.rect.top + self.wall_thickness,
                                     self.rect.width - 2 * self.wall_thickness,
                                     self.rect.height - 2 * self.wall_thickness)
            return not inner_rect.colliderect(rect)
        return False

    def get_random_interior_position(self):
        return (random.randint(self.rect.left + self.wall_thickness, self.rect.right - self.wall_thickness),
                random.randint(self.rect.top + self.wall_thickness, self.rect.bottom - self.wall_thickness))

    def get_exit_position(self):
        return (self.rect.centerx, self.rect.centery)

# Jail
class Jail(Building):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, jail_image, "jail")

# Hospital
class Hospital(Building):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, hospital_image, "hospital")

# Function to generate non-overlapping buildings on a grid
def create_buildings_grid(num_buildings):
    buildings = []
    grid_positions = [(x, y) for x in range(0, WIDTH, GRID_SIZE + ROAD_WIDTH) for y in range(0, HEIGHT, GRID_SIZE + ROAD_WIDTH)]
    random.shuffle(grid_positions)
    
    for _ in range(num_buildings):
        if not grid_positions:
            break
        x, y = grid_positions.pop()
        image = random.choice(house_images)
        new_building = Building(x + ROAD_WIDTH, y + ROAD_WIDTH, GRID_SIZE, GRID_SIZE, image)
        buildings.append(new_building)
    
    return buildings

# Create buildings
buildings = create_buildings_grid(12)

# Create jail and hospital at specific positions on the grid
jail = Jail(WIDTH - GRID_SIZE - ROAD_WIDTH, ROAD_WIDTH, GRID_SIZE, GRID_SIZE)
hospital = Hospital(ROAD_WIDTH, HEIGHT - GRID_SIZE - ROAD_WIDTH, GRID_SIZE, GRID_SIZE)
buildings.append(jail)
buildings.append(hospital)

# Function to find a valid spawn position
def find_valid_spawn(buildings):
    while True:
        x = random.randint(0, WIDTH - 20)
        y = random.randint(0, HEIGHT - 20)
        rect = pygame.Rect(x, y, 35, 35)
        if not any(building.is_colliding(rect) for building in buildings):
            return x, y

# Create player
player = Player(WIDTH // 2, HEIGHT // 2)

# Create NPCs
num_criminals = 8
num_police = 8
num_civilians = 15
criminals = [NPC(*find_valid_spawn(buildings), criminal_sprite, "criminal") for _ in range(num_criminals)]
police = [NPC(*find_valid_spawn(buildings), police_sprite, "police") for _ in range(num_police)]
civilians = [NPC(*find_valid_spawn(buildings), civilian_sprite, "civilian") for _ in range(num_civilians)]

# Adding roads to the map
def draw_roads():
    for i in range(0, WIDTH, GRID_SIZE + ROAD_WIDTH):
        pygame.draw.rect(screen, ROAD_COLOR, (i, 0, ROAD_WIDTH, HEIGHT))  # Vertical roads
    for j in range(0, HEIGHT, GRID_SIZE + ROAD_WIDTH):
        pygame.draw.rect(screen, ROAD_COLOR, (0, j, WIDTH, ROAD_WIDTH))  # Horizontal roads

# Dialog system
def show_dialog(screen, text, x, y):
    font = pygame.font.Font(None, 24)
    dialog_surface = pygame.Surface((300, 100))
    dialog_surface.fill(WHITE)
    dialog_surface.set_alpha(200)
    screen.blit(dialog_surface, (x, y))
    
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if font.size(' '.join(current_line))[0] > 280:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, BLACK)
        screen.blit(text_surface, (x + 10, y + 10 + i * 30))

# Quest system
class Quest:
    def __init__(self, description, target_type, target_count):
        self.description = description
        self.target_type = target_type
        self.target_count = target_count
        self.current_count = 0

    def update(self, event_type):
        if event_type == self.target_type:
            self.current_count += 1
            return self.current_count >= self.target_count
        return False

# Create a list of available quests
available_quests = [
    Quest("Catch 3 criminals", "criminal_caught", 3),
    Quest("Help 5 civilians", "civilian_helped", 5),
    Quest("Patrol the city (visit 10 buildings)", "building_visited", 10)
]

# Game loop
running = True
clock = pygame.time.Clock()
show_instructions = True
current_dialog = None
dialog_timer = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                player.change_alignment("good")
            elif event.key == pygame.K_e:
                player.change_alignment("evil")
            elif event.key == pygame.K_i:
                show_instructions = not show_instructions
            elif event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                interacted_object = player.interact(criminals + police + civilians, buildings)
                if isinstance(interacted_object, NPC):
                    current_dialog = random.choice(interacted_object.dialog)
                    dialog_timer = 180  # Show dialog for 3 seconds

    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
    dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
    player.move(dx, dy, buildings)

    for npc in criminals + police + civilians:
        if npc.in_jail:
            npc.jail_timer -= 1
            if npc.jail_timer <= 0:
                npc.in_jail = False
                npc.jail_timer = 600
                npc.health = 100
                npc.committed_crime = False
                npc.x, npc.y = find_valid_spawn(buildings)
        else:
            npc.move(buildings, hospital)
            if npc.type == "criminal":
                npc.attempt_crime(buildings, civilians)
            
            if hospital.rect.collidepoint(npc.x, npc.y):
                npc.health = min(npc.health + 1, 100)
                if npc.health == 100:
                    npc.x, npc.y = hospital.get_exit_position()
                    npc.cooldown_timer = 300  # 5 seconds cooldown

            if npc.health <= 0:
                npc.health = 100
                npc.x, npc.y = hospital.get_exit_position()
                npc.cooldown_timer = 300  # 5 seconds cooldown

    for criminal in criminals:
        if criminal.committed_crime and not criminal.in_building:
            for police_officer in police:
                if distance(criminal, police_officer) < 30:
                    criminal.health -= 2
                    if criminal.health <= 0:
                        criminal.in_jail = True
                        criminal.x, criminal.y = jail.get_random_interior_position()
                        criminals_caught += 1
                        criminal.committed_crime = False
                    break

    for npc in criminals + police + civilians:
        if distance(player, npc) < 30:
            if player.alignment == "good" and npc.type == "criminal":
                npc.health -= 1
            elif player.alignment == "evil" and npc.type != "criminal":
                npc.health -= 1

    screen.fill(LIGHT_GRAY)
    
    draw_roads()

    for building in buildings:
        building.draw(screen)

    for npc in criminals + police + civilians:
        if not npc.in_building:
            npc.draw(screen)

    player.draw(screen)

    font = pygame.font.Font(None, 24)

    # Draw text background
    text_background_rect = pygame.Surface((200, 150))
    text_background_rect.set_alpha(150)  # Transparency level
    text_background_rect.fill(TEXT_BACKGROUND_COLOR)
    screen.blit(text_background_rect, (5, 5))

    muggings_text = font.render(f"Muggings: {total_muggings}", True, BLACK)
    burglaries_text = font.render(f"Burglaries: {total_burglaries}", True, BLACK)
    caught_text = font.render(f"Caught: {criminals_caught}", True, BLACK)
    karma_text = font.render(f"Karma: {player.karma:.1f}", True, BLACK)
    alignment_text = font.render(f"Alignment: {player.alignment}", True, BLACK)
    screen.blit(muggings_text, (10, 10))
    screen.blit(burglaries_text, (10, 40))
    screen.blit(caught_text, (10, 70))
    screen.blit(karma_text, (10, 100))
    screen.blit(alignment_text, (10, 130))

    # Show dialog if available
    if current_dialog and dialog_timer > 0:
        show_dialog(screen, current_dialog, player.x + 50, player.y - 50)
        dialog_timer -= 1
    else:
        current_dialog = None

    # Show instructions if toggled
    if show_instructions:
        instructions_background = pygame.Surface((300, 200))
        instructions_background.fill(WHITE)
        instructions_background.set_alpha(200)
        screen.blit(instructions_background, (WIDTH - 310, 10))
        for i, line in enumerate(instructions_text):
            instruction_text = font.render(line, True, BLACK)
            screen.blit(instruction_text, (WIDTH - 300, 20 + i * 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
