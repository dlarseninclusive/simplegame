import pygame
import random
from camera import Camera
from player import Player
from environment import Environment
from lore import LoreSystem
from resource import ResourceNode
from npc import NPC
from building import BuildingSystem
from crafting import CraftingSystem
from factions import Factions
from quests import QuestSystem
from ui import UIManager, GameMenu
from pathfinding import GridPathfinder
from sprites import create_player_sprite
from combat_effects import DamageNumber, HitFlash, AttackAnimation
from city_generator import CityGenerator
from jail import Jail
from character_classes import Warrior, Mage, Thief
from slave_system import Slave

# Globals for building transitions
current_building = None

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

def enter_building(building, player, npcs):
    """
    Simple function to handle entering a building.
    Can be expanded to show interior, trigger dialogue, etc.
    """
    global current_state, current_interior, exit_door, current_building
    # Switch to interior state
    current_state = "interior"
    current_interior = building.interior_map  # interior already generated
    current_building = building
    
    # Set current_building for player
    player.current_building = building
    
    # Set current_building for NPCs in the interior
    for npc in npcs:
        npc.current_building = building
    # Instead of centering, spawn at the building's interior_door_rect if present
    if hasattr(building, "interior_door_rect"):
        # The interior door rect is in the interior's local (0..300, 0..200) coordinates.
        # We'll offset it so the player spawns exactly there on-screen.
        door_x = (SCREEN_WIDTH - building.interior_map.get_width()) // 2 + building.interior_door_rect.x
        door_y = (SCREEN_HEIGHT - building.interior_map.get_height()) // 2 + building.interior_door_rect.y
        # Spawn the player slightly away from the door (e.g. 10 pixels upward)
        player.rect.midbottom = (door_x + building.interior_door_rect.width//2,
                                 door_y + building.interior_door_rect.height - 10)
        # Initialize an exit delay timer (in seconds) to prevent immediate exit
        player.exit_delay = 1.0
    else:
        # Fallback if no interior_door_rect
        player.rect.topleft = (
            (SCREEN_WIDTH - player.rect.width) // 2,
            (SCREEN_HEIGHT - player.rect.height) // 2
        )
    exit_door = building.door_rect.copy()  # Save the door for exit
    print(f"Entering {building.type} interior")
    if getattr(building, "is_shop", False):
        print("Merchant: Welcome, valued customer!")

def main():
    pygame.init()
    global current_building
    global current_interior
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Shattered Expanse - Updated Features")

    clock = pygame.time.Clock()

    # Game state
    global current_state, current_interior, game_paused
    current_state = "exterior"  # "exterior" or "interior"
    current_interior = None
    game_paused = False
    show_tabbed_menu = False

    # Create objects
    player = Player(2000, 2000)
    combat_effects = pygame.sprite.Group()
    
    # 1) Bigger world: 4000x4000
    camera = Camera(
        world_width=4000,
        world_height=4000,
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT
    )

    environment = Environment()
    # Example obstacles
    environment.add_obstacle(100, 100, 100, 50)
    environment.add_obstacle(800, 400, 60, 120)
    environment.add_obstacle(2200, 1200, 200, 200)
    environment.add_obstacle(3300, 2000, 150, 150)

    # Initialize Lore System
    lore_system = LoreSystem()
    lore_system.generate_world_fragments(4000, 4000)

    # 2) Resource nodes, now bigger spread across the world
    resource_nodes = [
        ResourceNode(200, 200, 40, 40, "scrap"),
        ResourceNode(600, 450, 40, 40, "water"),
        ResourceNode(1300, 700, 40, 40, "food"),
        ResourceNode(1800, 1800, 40, 40, "artifact"),
        ResourceNode(300, 600, 40, 40, "scrap"),
        ResourceNode(2500, 500, 40, 40, "scrap"),
        ResourceNode(1500, 2200, 40, 40, "water"),
        ResourceNode(3400, 1000, 40, 40, "food"),
        ResourceNode(3900, 3900, 40, 40, "artifact"),
    ]

    # Factions & Quests
    factions = Factions()
    quest_system = QuestSystem()
    quest_system.add_quest("GatherScrap",
        description="Scavengers want 5 scrap for an alliance offer.",
        faction="Scavengers",
        target_item="scrap",
        target_count=5
    )

    # Initialize new systems
    jail_system = Jail()
    # Optional: Initialize player with a specific character class
    player.character_class = Warrior().name

    # Initialize TabbedMenu
    tab_font = pygame.font.Font(None, 24)
    
    # Create surfaces for each tab's content
    lore_surface = pygame.Surface((400, 270))
    lore_surface.fill((30, 30, 30))
    
    # Render lore fragments onto the surface
    lore_y_offset = 10
    for fragment in lore_system.discovered_fragments:
        fragment_text = pygame.font.Font(None, 20).render(fragment.text, True, (200, 200, 200))
        lore_surface.blit(fragment_text, (10, lore_y_offset))
        lore_y_offset += 25
    
    faction_surface = pygame.Surface((400, 270))
    faction_surface.fill((30, 30, 30))
    
    # Render faction information
    faction_text = pygame.font.Font(None, 20).render("Faction Reputation:", True, (255, 255, 255))
    faction_surface.blit(faction_text, (10, 10))
    
    faction_y_offset = 40
    for faction, rep in player.faction_rep.items():
        rep_text = pygame.font.Font(None, 20).render(f"{faction}: {rep}", True, (200, 200, 200))
        faction_surface.blit(rep_text, (10, faction_y_offset))
        faction_y_offset += 25
    
    # Create backpack surface
    backpack_surface = pygame.Surface((400, 270))
    backpack_surface.fill((30, 30, 30))
    
    # Render backpack contents
    backpack_y_offset = 10
    backpack_font = pygame.font.Font(None, 20)
    backpack_surface.blit(
        backpack_font.render("Backpack Contents:", True, (255, 255, 255)), 
        (10, backpack_y_offset)
    )
    backpack_y_offset += 30
    
    for item, quantity in player.backpack.items:
        item_text = backpack_font.render(f"{item.name} x{quantity}", True, (200, 200, 200))
        backpack_surface.blit(item_text, (10, backpack_y_offset))
        backpack_y_offset += 25
        
    # Create equipment surface
    equipment_surface = pygame.Surface((400, 270))
    equipment_surface.fill((30, 30, 30))
    equipment_font = pygame.font.Font(None, 20)
    y_offset = 10
    title = equipment_font.render("Equipment", True, (255, 255, 255))
    equipment_surface.blit(title, (10, y_offset))
    y_offset += 30
    for slot, item in player.equipment.slots.items():
        text = f"{slot.capitalize()}: {item.name if item else 'Empty'}"
        eq_text = equipment_font.render(text, True, (200, 200, 200))
        equipment_surface.blit(eq_text, (10, y_offset))
        y_offset += 25
    
    tabs = [
        {'label': 'Lore Log', 'content': lore_surface},
        {'label': 'Faction Info', 'content': faction_surface},
        {'label': 'Backpack', 'content': backpack_surface},
        {'label': 'Equipment', 'content': equipment_surface},
    ]
    
    tabbed_menu_rect = pygame.Rect(200, 150, 400, 300)
    from ui import TabbedMenu  # Import TabbedMenu from ui module
    tabbed_menu = TabbedMenu(tabbed_menu_rect, tabs, tab_font)

    # City Generator
    city_generator = CityGenerator()

    # Tabbed menu toggle flag
    show_tabbed_menu = False

    # Generate cities for each faction
    city_buildings = {}
    city_npcs = {}
    city_resources = {}
    for faction in ["Automatons", "Scavengers", "Cog Preachers"]:
        city_buildings[faction] = city_generator.generate_city_buildings(faction, environment)  # Pass environment
        city_npcs[faction] = city_generator.generate_city_npcs(faction)
        city_resources[faction] = city_generator.generate_city_resources(faction)

    # Combine all NPCs
    npcs = []
    for faction_npcs in city_npcs.values():
        npcs.extend(faction_npcs)

    # Combine all resource nodes
    resource_nodes = []
    for faction_resources in city_resources.values():
        resource_nodes.extend(faction_resources)

    building_system = BuildingSystem()
    crafting_system = CraftingSystem()

    # 3) Pathfinding grid, scaled up for 4000x4000
    # If each cell is 40px, we have 100x100 grid
    pathfinder = GridPathfinder(width=100, height=100, cell_size=40)
    pathfinder.set_obstacles(environment.obstacles)

    ui_manager = UIManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    game_menu = GameMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    from ui import TabbedMenu  # Add import for TabbedMenu

    build_mode = False
    show_menu = False
    day_cycle = 0.0
    heat_stroke_threshold = 12.0

    current_dialog = None
    dialog_timer = 0
    DIALOG_DURATION = 3.0  # seconds dialog stays on screen

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # Pause check: if game is paused, set dt to 0
        if show_menu:
            dt = 0

        # Day/Night
        day_cycle += 0.5 * dt
        if day_cycle >= 24.0:
            day_cycle -= 24.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Forward events to TabbedMenu
            tabbed_menu.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    build_mode = not build_mode
                if event.key == pygame.K_ESCAPE:
                    show_menu = not show_menu
                if event.key == pygame.K_c:
                    crafting_system.open_crafting_menu(player)
                # Removed equipment toggle on Tab for TabbedMenu
                if event.key == pygame.K_m:  # Add minimap toggle
                    ui_manager.toggle_minimap()
                if event.key == pygame.K_i:  # Toggle backpack
                    ui_manager.toggle_backpack_display()
                if event.key == pygame.K_TAB:  # Toggle tabbed menu
                    tabbed_menu.toggle_pause()
                    show_tabbed_menu = not show_tabbed_menu
                    game_paused = tabbed_menu.is_game_paused
                # Equipment hotkeys
                if pygame.K_F1 <= event.key <= pygame.K_F6:
                    slot_index = event.key - pygame.K_F1
                    slots = list(player.equipment.slots.keys())
                    if slot_index < len(slots):
                        player.toggle_equipment_slot(slots[slot_index])
                # 4) Attack key: space bar => attempt to attack NPCs
                if event.key == pygame.K_SPACE:
                    player.attempt_attack(npcs, dt, combat_effects, ui_manager)
                
                # NPC Interaction
                if event.key == pygame.K_f:
                    for npc in npcs:
                        # Check if player is close to NPC
                        dist = ((player.rect.centerx - npc.rect.centerx)**2 + 
                                (player.rect.centery - npc.rect.centery)**2)**0.5
                        if dist < 100:  # Interaction range
                            current_dialog = npc.interact(player)
                            dialog_timer = DIALOG_DURATION
                            break  # Interact with only one NPC at a time
            
                # Example: Commit a crime when 'C' is pressed
                if event.key == pygame.K_c:
                    player.commit_crime("theft", 5)

                # Example: Change character class when 'L' is pressed (cycle or set a new class)
                if event.key == pygame.K_l:
                    player.character_class = "Mage"  # Or cycle through available classes

            # Building controls
            if build_mode:
                # Get current mouse position for preview/placement
                mx, my = pygame.mouse.get_pos()
                wx = mx + camera.offset_x
                wy = my + camera.offset_y
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        building_system.attempt_placement(player, environment, wx, wy)
                    elif event.button == 3:  # Right click
                        building_system.attempt_reclaim(player, environment)
                        
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u:  # Upgrade
                        building_system.attempt_upgrade(player, wx, wy)
                    elif event.key == pygame.K_h:  # Repair
                        building_system.attempt_repair(player, wx, wy)
                
                # Update building system
                building_system.update_structures(dt, player)

            # Equipment toggle hotkeys (moved outside build_mode check)
            if event.type == pygame.KEYDOWN:
                if pygame.K_F1 <= event.key <= pygame.K_F6:
                    slot_index = event.key - pygame.K_F1
                    slots = list(player.equipment.slots.keys())
                    if slot_index < len(slots):
                        player.toggle_equipment_slot(slots[slot_index])

        if not show_menu and not game_paused:
            keys = pygame.key.get_pressed()

            # Player
            player.old_pos = player.rect.topleft  # store where the player was
            player.handle_input(dt)
            player.update(dt, environment.obstacles, npcs, day_cycle, heat_stroke_threshold)

            # Only check building doors if we're in the "exterior" state
            if current_state == "exterior" and keys[pygame.K_e]:
                door_entered = False
                # Check both placed structures and city-generated buildings
                for building_list in [building_system.structures] + list(city_buildings.values()):
                    for building in building_list:
                        if hasattr(building, 'door_rect'):
                            # Compare world coordinates directly with inflated door rect
                            if player.rect.colliderect(building.door_rect.inflate(10, 10)):
                                print(f"Collision detected with building door: {building.type}")
                                enter_building(building, player, npcs)
                                door_entered = True
                                break
                    if door_entered:
                        break
                # Only if no door was entered, process resource collection.
                if not door_entered:
                    for node in resource_nodes:
                        if not node.collected and player.rect.colliderect(node.rect):
                            node.collected = True
                            player.collect_resource(node)
                            quest_system.check_item_collection(player, node.resource_type)

            # Generate roads between city centers
            city_centers = [
                (camera.world_width - 300, camera.world_height - 300),  # Automatons
                (100, 100),  # Scavengers
                (camera.world_width // 2 - 125, camera.world_height // 2 - 125)  # Cog Preachers
            ]
            city_roads = city_generator.generate_roads(city_centers)

            # NPC updates
            # Remove dead NPCs from the list if health <= 0
            for npc in npcs:
                npc.update(dt, environment.obstacles, player, pathfinder, city_roads)
            npcs = [n for n in npcs if n.health > 0]

            # Render roads in the rendering section
            if current_state == "exterior":
                for road in city_roads:
                    for i in range(len(road) - 1):
                        start = road[i]
                        end = road[i+1]
                        start_x = start[0] - camera.offset_x
                        start_y = start[1] - camera.offset_y
                        end_x = end[0] - camera.offset_x
                        end_y = end[1] - camera.offset_y
                        
                        # Draw road with varying width and slight randomness
                        road_width = random.randint(15, 25)  # Varied road width
                        pygame.draw.line(screen, (100, 100, 100), (start_x, start_y), (end_x, end_y), road_width)
                        
                        # Optional: Add road edge highlights
                        edge_color = (120, 120, 120)
                        pygame.draw.line(screen, edge_color, (start_x, start_y), (end_x, end_y), 2)

            # Factions & Quests
            quest_system.update_quests(player)

            # 6) Resource respawning
            for node in resource_nodes:
                node.update(dt)  # Check if respawn timer is ready

            # Lore fragment discovery
            for fragment in lore_system.fragments[:]:
                if player.rect.colliderect(fragment.rect):
                    lore_system.discovered_fragments.append(fragment)
                    lore_system.fragments.remove(fragment)
                    print(f"Discovered lore: {fragment.text}")
                    # Optional: Add a UI notification or sound effect here

            # Camera updates only in exterior state
            if current_state == "exterior":
                camera.update(player.rect.centerx, player.rect.centery)

        # Clear screen with appropriate background
        if current_state == "exterior":
            if 6 <= day_cycle < 18:
                background_color = (210, 180, 140)
            else:
                background_color = (80, 60, 60)
        else:
            background_color = (50, 50, 50)  # Interior background
        screen.fill(background_color)

        # Render exterior elements
        if current_state == "exterior":
            # Obstacles
            for obs in environment.obstacles:
                ox = obs.x - camera.offset_x
                oy = obs.y - camera.offset_y
                pygame.draw.rect(screen, (0, 128, 0), (ox, oy, obs.width, obs.height))
    
            # Resource nodes
            for node in resource_nodes:
                if not node.collected:
                    nx = node.rect.x - camera.offset_x
                    ny = node.rect.y - camera.offset_y
                    color = (30, 144, 255)
                    if node.resource_type == "water":
                        color = (0, 191, 255)
                    elif node.resource_type == "food":
                        color = (50, 205, 50)
                    elif node.resource_type == "artifact":
                        color = (186, 85, 211)
                    pygame.draw.rect(screen, color, (nx, ny, node.rect.width, node.rect.height))

            # Render city buildings for each faction
            for faction, buildings in city_buildings.items():
                for building in buildings:
                    bx = building.rect.x - camera.offset_x
                    by = building.rect.y - camera.offset_y
                    screen.blit(building.image, (bx, by))
                    
                    if hasattr(building, 'sign_text') and building.sign_text:
                        sign_font = pygame.font.Font(None, 16)
                        sign_surf = sign_font.render(building.sign_text, True, (255, 255, 255))
                        screen.blit(sign_surf, (bx, by - 20))
                    
                    if hasattr(building, 'door_rect'):
                        door_rect = building.door_rect.copy()
                        door_rect.x -= camera.offset_x
                        door_rect.y -= camera.offset_y
                        pygame.draw.rect(screen, (255, 0, 0), 
                                         (door_rect.x, door_rect.y,
                                          door_rect.width,
                                          door_rect.height), 2)
                        if player.rect.colliderect(door_rect):
                            font = pygame.font.Font(None, 24)
                            prompt = font.render("E", True, (255, 255, 255))
                            screen.blit(prompt, (door_rect.centerx - prompt.get_width()//2, door_rect.top - 25))

            # Existing building system rendering
            building_types = [
                "Generator", "Storage", "Workshop", "Collector", 
                "Turret", "Wall", "Research Station", "Repair Bay", 
                "Communication Tower", "Power Relay"
            ]
        
            for bld in building_system.structures:
                bx = bld.x - camera.offset_x
                by = bld.y - camera.offset_y
            
                # Enhanced building color scheme
                building_colors = {
                    "Generator": (255, 140, 0),      # Orange
                    "Storage": (139, 69, 19),        # Brown
                    "Workshop": (105, 105, 105),     # Gray
                    "Collector": (46, 139, 87),      # Sea green
                    "Turret": (178, 34, 34),         # Firebrick red
                    "Wall": (112, 128, 144),         # Slate gray
                    "Research Station": (70, 130, 180),  # Steel blue
                    "Repair Bay": (32, 178, 170),    # Light sea green
                    "Communication Tower": (75, 0, 130),  # Indigo
                    "Power Relay": (255, 215, 0)     # Gold
                }
            
                color = building_colors.get(bld.structure_type, (139, 69, 19))
            
                # Different shapes or rendering for special buildings
                if bld.structure_type == "Communication Tower":
                    # Render as a taller, thinner structure
                    pygame.draw.rect(screen, color, (bx, by, bld.width//2, bld.height*1.5))
                elif bld.structure_type == "Turret":
                    # Render as a circular/octagonal shape
                    pygame.draw.polygon(screen, color, [
                        (bx, by+bld.height//2),
                        (bx+bld.width//2, by),
                        (bx+bld.width, by+bld.height//2),
                        (bx+bld.width, by+bld.height),
                        (bx, by+bld.height)
                    ])
                else:
                    pygame.draw.rect(screen, color, (bx, by, bld.width, bld.height))
                
                # Health bar (red to green)
                health_percent = bld.health / bld.max_health
                health_width = bld.width * health_percent
                health_color = (int(255 * (1 - health_percent)), int(255 * health_percent), 0)
                pygame.draw.rect(screen, health_color, (bx, by - 5, health_width, 3))
                
                # Power indicator
                if bld.power_required > 0:
                    power_percent = bld.power_received / bld.power_required
                    power_width = bld.width * power_percent
                    pygame.draw.rect(screen, (0, 191, 255), (bx, by - 9, power_width, 3))
                    
                # Level indicator
                if bld.level > 1:
                    font = pygame.font.Font(None, 20)
                    level_text = font.render(f"L{bld.level}", True, (255, 255, 255))
                    screen.blit(level_text, (bx + bld.width - 20, by + bld.height - 20))

        # Render interior elements
        elif current_state == "interior":
            if current_interior:
                # Center the interior map on screen
                interior_w, interior_h = current_interior.get_size()
                x = (SCREEN_WIDTH - interior_w) // 2
                y = (SCREEN_HEIGHT - interior_h) // 2
                screen.blit(current_interior, (x, y))
                
                # Check collision with interior walls (if defined)
                if current_building and hasattr(current_building, 'interior_walls'):
                    for wall in current_building.interior_walls:
                        wall_rect = wall.copy()
                        wall_rect.x += x
                        wall_rect.y += y
                
                        if player.rect.colliderect(wall_rect):
                            # Determine the direction of collision more precisely
                            overlap_left = wall_rect.right - player.rect.left
                            overlap_right = player.rect.right - wall_rect.left
                            overlap_top = wall_rect.bottom - player.rect.top
                            overlap_bottom = player.rect.bottom - wall_rect.top

                            # Find the smallest overlap
                            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

                            # Move player out based on the smallest overlap
                            if min_overlap == overlap_left:
                                player.rect.left = wall_rect.right
                            elif min_overlap == overlap_right:
                                player.rect.right = wall_rect.left
                            elif min_overlap == overlap_top:
                                player.rect.top = wall_rect.bottom
                            else:  # overlap_bottom
                                player.rect.bottom = wall_rect.top

                        # Similar collision resolution for NPCs
                        for npc in npcs:
                            if npc.rect.colliderect(wall_rect):
                                overlap_left = wall_rect.right - npc.rect.left
                                overlap_right = npc.rect.right - wall_rect.left
                                overlap_top = wall_rect.bottom - npc.rect.top
                                overlap_bottom = npc.rect.bottom - wall_rect.top

                                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

                                if min_overlap == overlap_left:
                                    npc.rect.left = wall_rect.right
                                elif min_overlap == overlap_right:
                                    npc.rect.right = wall_rect.left
                                elif min_overlap == overlap_top:
                                    npc.rect.top = wall_rect.bottom
                                else:  # overlap_bottom
                                    npc.rect.bottom = wall_rect.top

                # Define the exit door relative to the interior map
                exit_door_rect = pygame.Rect(
                    x + current_building.interior_door_rect.x,
                    y + current_building.interior_door_rect.y,
                    current_building.interior_door_rect.width,
                    current_building.interior_door_rect.height
                )
                pygame.draw.rect(screen, (200, 200, 0), exit_door_rect)
                
                # Draw the player without subtracting any camera offset
                screen.blit(create_player_sprite(), player.rect)
                
                # Update exit delay timer if present
                if hasattr(player, "exit_delay") and player.exit_delay > 0:
                    player.exit_delay -= dt
                else:
                    # Now check for exit door collision only if the delay has elapsed
                    if player.rect.colliderect(exit_door_rect):
                        if pygame.key.get_pressed()[pygame.K_e]:
                            current_state = "exterior"
                            current_interior = None
                            if current_building is not None:
                                # Place the player back at the building's exterior door (or another safe spot)
                                player.rect.midbottom = (current_building.door_rect.centerx,
                                                        current_building.door_rect.top - 5)
                                
                                # Reset current_building for player and NPCs
                                player.current_building = None
                                for npc in npcs:
                                    npc.current_building = None
                            
                            current_building = None
                            camera.update(player.rect.centerx, player.rect.centery)
                            print("Exiting interior back to world.")

        if current_state == "exterior":
            # Obstacles
            for obs in environment.obstacles:
                ox = obs.x - camera.offset_x
                oy = obs.y - camera.offset_y
                pygame.draw.rect(screen, (0, 128, 0), (ox, oy, obs.width, obs.height))

        if current_state == "exterior":
            # Resource nodes
            for node in resource_nodes:
                if not node.collected:
                    nx = node.rect.x - camera.offset_x
                    ny = node.rect.y - camera.offset_y
                    color = (30, 144, 255)
                    if node.resource_type == "water":
                        color = (0, 191, 255)
                    elif node.resource_type == "food":
                        color = (50, 205, 50)
                    elif node.resource_type == "artifact":
                        color = (186, 85, 211)
                    pygame.draw.rect(screen, color, (nx, ny, node.rect.width, node.rect.height))

            # Render city buildings for each faction
            for faction, buildings in city_buildings.items():
                for building in buildings:
                    bx = building.rect.x - camera.offset_x
                    by = building.rect.y - camera.offset_y
                    screen.blit(building.image, (bx, by))
                    
                    if hasattr(building, 'sign_text') and building.sign_text:
                        sign_font = pygame.font.Font(None, 16)
                        sign_surf = sign_font.render(building.sign_text, True, (255, 255, 255))
                        screen.blit(sign_surf, (bx, by - 20))
                    
                    if hasattr(building, 'door_rect'):
                        door_rect = building.door_rect.copy()
                        door_rect.x -= camera.offset_x
                        door_rect.y -= camera.offset_y
                        pygame.draw.rect(screen, (255, 0, 0), 
                                         (door_rect.x, door_rect.y,
                                          door_rect.width,
                                          door_rect.height), 2)
                        if player.rect.colliderect(door_rect):
                            font = pygame.font.Font(None, 24)
                            prompt = font.render("E", True, (255, 255, 255))
                            screen.blit(prompt, (door_rect.centerx - prompt.get_width()//2, door_rect.top - 25))

        # Existing building system rendering
        building_types = [
            "Generator", "Storage", "Workshop", "Collector", 
            "Turret", "Wall", "Research Station", "Repair Bay", 
            "Communication Tower", "Power Relay"
        ]
    
        for bld in building_system.structures:
            bx = bld.x - camera.offset_x
            by = bld.y - camera.offset_y
        
            # Enhanced building color scheme
            building_colors = {
                "Generator": (255, 140, 0),      # Orange
                "Storage": (139, 69, 19),        # Brown
                "Workshop": (105, 105, 105),     # Gray
                "Collector": (46, 139, 87),      # Sea green
                "Turret": (178, 34, 34),         # Firebrick red
                "Wall": (112, 128, 144),         # Slate gray
                "Research Station": (70, 130, 180),  # Steel blue
                "Repair Bay": (32, 178, 170),    # Light sea green
                "Communication Tower": (75, 0, 130),  # Indigo
                "Power Relay": (255, 215, 0)     # Gold
            }
        
            color = building_colors.get(bld.structure_type, (139, 69, 19))
        
            # Different shapes or rendering for special buildings
            if bld.structure_type == "Communication Tower":
                # Render as a taller, thinner structure
                pygame.draw.rect(screen, color, (bx, by, bld.width//2, bld.height*1.5))
            elif bld.structure_type == "Turret":
                # Render as a circular/octagonal shape
                pygame.draw.polygon(screen, color, [
                    (bx, by+bld.height//2),
                    (bx+bld.width//2, by),
                    (bx+bld.width, by+bld.height//2),
                    (bx+bld.width, by+bld.height),
                    (bx, by+bld.height)
                ])
            else:
                pygame.draw.rect(screen, color, (bx, by, bld.width, bld.height))
            
            # Health bar (red to green)
            health_percent = bld.health / bld.max_health
            health_width = bld.width * health_percent
            health_color = (int(255 * (1 - health_percent)), int(255 * health_percent), 0)
            pygame.draw.rect(screen, health_color, (bx, by - 5, health_width, 3))
            
            # Power indicator
            if bld.power_required > 0:
                power_percent = bld.power_received / bld.power_required
                power_width = bld.width * power_percent
                pygame.draw.rect(screen, (0, 191, 255), (bx, by - 9, power_width, 3))
                
            # Level indicator
            if bld.level > 1:
                font = pygame.font.Font(None, 20)
                level_text = font.render(f"L{bld.level}", True, (255, 255, 255))
                screen.blit(level_text, (bx + bld.width - 20, by + bld.height - 20))
        
        # Duplicate interior rendering block removed

        # NPCs with health bars
        for npc in npcs:
            nx = npc.rect.x - camera.offset_x
            ny = npc.rect.y - camera.offset_y
            
            # Draw the sprite
            screen.blit(npc.sprite, (nx, ny))
            
            # Draw faction markers
            npc.draw_faction_marker(screen, (camera.offset_x, camera.offset_y))
            
            # Health bar
            health_percent = npc.health / npc.max_health
            health_width = npc.width * health_percent
            health_color = (int(255 * (1 - health_percent)), int(255 * health_percent), 0)
            pygame.draw.rect(screen, health_color, (nx, ny - 5, health_width, 3))

        # Player with sprite
        px = player.rect.x - camera.offset_x
        py = player.rect.y - camera.offset_y
        player_sprite = create_player_sprite()
        screen.blit(player_sprite, (px, py))
        
        # Update and draw combat effects
        for effect in list(combat_effects):
            if isinstance(effect, (DamageNumber, HitFlash)):
                if not effect.update(dt):
                    combat_effects.remove(effect)
            elif isinstance(effect, AttackAnimation):
                if effect.update(dt):
                    effect.draw(screen, (camera.offset_x, camera.offset_y))
                else:
                    combat_effects.remove(effect)
        
        # Dialog rendering
        if current_dialog and dialog_timer > 0:
            ui_manager.draw_npc_dialog(screen, current_dialog)
            dialog_timer -= dt
            if dialog_timer <= 0:
                current_dialog = None
        
        # Build mode cursor and power grid visualization
        if build_mode:
            mx, my = pygame.mouse.get_pos()
            wx = mx + camera.offset_x
            wy = my + camera.offset_y
            
            # Draw power connections between structures
            for s1 in building_system.structures:
                if s1.power_grid_id is not None:
                    s1x = s1.x + s1.width/2 - camera.offset_x
                    s1y = s1.y + s1.height/2 - camera.offset_y
                    for s2 in building_system.structures:
                        if (s2.power_grid_id == s1.power_grid_id and 
                            s2 != s1):
                            s2x = s2.x + s2.width/2 - camera.offset_x
                            s2y = s2.y + s2.height/2 - camera.offset_y
                            pygame.draw.line(screen, (0, 191, 255), 
                                          (s1x, s1y), (s2x, s2y), 1)
            
            # Building placement preview
            preview_size = (40, 40)  # default size
            if pygame.key.get_pressed()[pygame.K_1]: 
                preview_size = (40, 40)  # Wall
            elif pygame.key.get_pressed()[pygame.K_2]:
                preview_size = (40, 40)  # Turret
            elif pygame.key.get_pressed()[pygame.K_3]:
                preview_size = (60, 60)  # Storage
            elif pygame.key.get_pressed()[pygame.K_4]:
                preview_size = (80, 80)  # Workshop
            elif pygame.key.get_pressed()[pygame.K_5]:
                preview_size = (40, 40)  # Collector
            elif pygame.key.get_pressed()[pygame.K_6]:
                preview_size = (50, 50)  # Generator
                
            pygame.draw.rect(screen, (255, 255, 0), 
                           (mx - preview_size[0]//2, my - preview_size[1]//2, 
                            preview_size[0], preview_size[1]), 2)
            # Display current structure type
            if pygame.key.get_pressed()[pygame.K_1]: text = "Wall"
            elif pygame.key.get_pressed()[pygame.K_2]: text = "Turret"
            elif pygame.key.get_pressed()[pygame.K_3]: text = "Storage"
            elif pygame.key.get_pressed()[pygame.K_4]: text = "Workshop"
            elif pygame.key.get_pressed()[pygame.K_5]: text = "Collector"
            elif pygame.key.get_pressed()[pygame.K_6]: text = "Generator"
            else: text = "Select 1-6"
            font = pygame.font.Font(None, 24)
            text_surface = font.render(text, True, (255, 255, 0))
            screen.blit(text_surface, (mx+25, my-10))

        ui_manager.draw_hud(screen, player, factions, build_mode, day_cycle)
        ui_manager.draw_minimap(screen, player, npcs, environment.obstacles, camera, building_system, lore_system, city_buildings)  # Pass city_buildings

        if ui_manager.show_lore_log:
            ui_manager.draw_lore_log(screen, lore_system)

        if show_menu:
            game_menu.draw_menu(screen)
        
        # Update lore tab content
        lore_surface.fill((30, 30, 30))  # Clear the surface
        y_offset = 10
        for fragment in lore_system.discovered_fragments:
            lore_text = tab_font.render(fragment.text, True, (200, 200, 200))
            lore_surface.blit(lore_text, (10, y_offset))
            y_offset += 25

        # Update faction info tab
        faction_surface.fill((30, 30, 30))
        y_offset = 10
        rep_text = tab_font.render(f"Automatons: {player.faction_rep.get('Automatons',0)}", True, (200,200,200))
        faction_surface.blit(rep_text, (10, y_offset))
        y_offset += 25
        rep_text = tab_font.render(f"Scavengers: {player.faction_rep.get('Scavengers',0)}", True, (200,200,200))
        faction_surface.blit(rep_text, (10, y_offset))
        y_offset += 25
        rep_text = tab_font.render(f"Cog Preachers: {player.faction_rep.get('Cog Preachers',0)}", True, (200,200,200))
        faction_surface.blit(rep_text, (10, y_offset))

        # Update backpack tab
        backpack_surface.fill((30, 30, 30))
        y_offset = 10
        for item, quantity in player.backpack.items:
            backpack_text = tab_font.render(f"{item.name} x{quantity}", True, (200, 200, 200))
            backpack_surface.blit(backpack_text, (10, y_offset))
            y_offset += 25

        # Draw TabbedMenu only if flag is true
        if show_tabbed_menu:
            tabbed_menu.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
