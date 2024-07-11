import pygame
import random
from player import Player
from npc import NPC
from buildings import Building, Jail, Hospital
from game_state import GameState
from rendering import draw_roads, show_dialog
from quest_system import Quest, available_quests
from utils import distance, find_valid_spawn

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 1024, 768
GRID_SIZE = 80  # Size of each grid cell
ROAD_WIDTH = 35  # Width of the road
PLAYER_SIZE = 35  # Size of the player
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("City Simulation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
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
game_state = GameState()

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

# Create player
player_x, player_y = WIDTH // 2, HEIGHT // 2
player = Player(player_x, player_y, player_sprite)

# Create buildings, ensuring none spawn at the player's initial position
buildings = []
grid_positions = [(x, y) for x in range(0, WIDTH, GRID_SIZE + ROAD_WIDTH) for y in range(0, HEIGHT, GRID_SIZE + ROAD_WIDTH)]
random.shuffle(grid_positions)

for _ in range(12):
    if not grid_positions:
        break
    x, y = grid_positions.pop()
    if (x <= player_x <= x + GRID_SIZE and y <= player_y <= y + GRID_SIZE):
        continue
    image = random.choice(house_images)
    new_building = Building(x + ROAD_WIDTH, y + ROAD_WIDTH, GRID_SIZE, GRID_SIZE, image)
    buildings.append(new_building)

# Create jail and hospital at specific positions on the grid
jail = Jail(WIDTH - GRID_SIZE - ROAD_WIDTH, ROAD_WIDTH, GRID_SIZE, GRID_SIZE, jail_image)
hospital = Hospital(ROAD_WIDTH, HEIGHT - GRID_SIZE - ROAD_WIDTH, GRID_SIZE, GRID_SIZE, hospital_image)
buildings.append(jail)
buildings.append(hospital)

# Create NPCs
num_criminals = 8
num_police = 8
num_civilians = 15
criminals = [NPC(*find_valid_spawn(buildings, WIDTH, HEIGHT, PLAYER_SIZE), criminal_sprite, "criminal", GRID_SIZE, ROAD_WIDTH, WIDTH, HEIGHT, game_state) for _ in range(num_criminals)]
police = [NPC(*find_valid_spawn(buildings, WIDTH, HEIGHT, PLAYER_SIZE), police_sprite, "police", GRID_SIZE, ROAD_WIDTH, WIDTH, HEIGHT, game_state) for _ in range(num_police)]
civilians = [NPC(*find_valid_spawn(buildings, WIDTH, HEIGHT, PLAYER_SIZE), civilian_sprite, "civilian", GRID_SIZE, ROAD_WIDTH, WIDTH, HEIGHT, game_state) for _ in range(num_civilians)]

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
                npc.x, npc.y = find_valid_spawn(buildings, WIDTH, HEIGHT, PLAYER_SIZE)
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
                        game_state.criminals_caught += 1
                        criminal.committed_crime = False
                    break

    for npc in criminals + police + civilians:
        if distance(player, npc) < 30:
            if player.alignment == "good" and npc.type == "criminal":
                npc.health -= 1
            elif player.alignment == "evil" and npc.type != "criminal":
                npc.health -= 1

    screen.fill(LIGHT_GRAY)
    
    draw_roads(screen, WIDTH, HEIGHT, GRID_SIZE, ROAD_WIDTH, ROAD_COLOR)

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

    muggings_text = font.render(f"Muggings: {game_state.total_muggings}", True, BLACK)
    burglaries_text = font.render(f"Burglaries: {game_state.total_burglaries}", True, BLACK)
    caught_text = font.render(f"Caught: {game_state.criminals_caught}", True, BLACK)
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
