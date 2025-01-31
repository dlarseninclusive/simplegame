import pygame
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

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Shattered Expanse - Updated Features")

    clock = pygame.time.Clock()

    # Create objects
    player = Player(400, 300)
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

    # NPCs with more advanced AI and different types
    npcs = [
        NPC(500, 200, faction="Automatons", group_id=1, enemy_type="scout"),
        NPC(1200, 600, faction="Scavengers", group_id=2, enemy_type="warrior"),
        NPC(1500, 1300, faction="Scavengers", group_id=2, enemy_type="heavy"),
        NPC(800, 800, faction="Automatons", group_id=1, enemy_type="ranged"),
        NPC(2000, 2000, faction="Automatons", group_id=3, enemy_type="boss"),
    ]

    building_system = BuildingSystem()
    crafting_system = CraftingSystem()

    # 3) Pathfinding grid, scaled up for 4000x4000
    # If each cell is 40px, we have 100x100 grid
    pathfinder = GridPathfinder(width=100, height=100, cell_size=40)
    pathfinder.set_obstacles(environment.obstacles)

    ui_manager = UIManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    game_menu = GameMenu(SCREEN_WIDTH, SCREEN_HEIGHT)

    build_mode = False
    show_menu = False
    day_cycle = 0.0
    heat_stroke_threshold = 12.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # Day/Night
        day_cycle += 0.5 * dt
        if day_cycle >= 24.0:
            day_cycle -= 24.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    build_mode = not build_mode
                if event.key == pygame.K_ESCAPE:
                    show_menu = not show_menu
                if event.key == pygame.K_c:
                    crafting_system.open_crafting_menu(player)
                # 4) Attack key: space bar => attempt to attack NPCs
                if event.key == pygame.K_SPACE:
                    player.attempt_attack(npcs, dt, combat_effects)

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

        if not show_menu:
            keys = pygame.key.get_pressed()

            # Player
            player.handle_input(dt)
            player.update(dt, environment.obstacles, npcs, day_cycle, heat_stroke_threshold)

            # 5) Press E to collect resources
            if keys[pygame.K_e]:
                for node in resource_nodes:
                    if not node.collected and player.rect.colliderect(node.rect):
                        node.collected = True
                        player.collect_resource(node)
                        quest_system.check_item_collection(player, node.resource_type)

            # NPC updates
            # Remove dead NPCs from the list if health <= 0
            for npc in npcs:
                npc.update(dt, environment.obstacles, player, pathfinder)
            npcs = [n for n in npcs if n.health > 0]

            # Factions & Quests
            quest_system.update_quests(player)

            # 6) Resource respawning
            for node in resource_nodes:
                node.update(dt)  # Check if respawn timer is ready

            # Camera
            camera.update(player.rect.centerx, player.rect.centery)

        # RENDER
        if 6 <= day_cycle < 18:
            background_color = (210, 180, 140)
        else:
            background_color = (80, 60, 60)

        screen.fill(background_color)

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

        # Buildings with more variety and strategic placement
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

        # NPCs with health bars
        for npc in npcs:
            nx = npc.rect.x - camera.offset_x
            ny = npc.rect.y - camera.offset_y
            
            # Draw the sprite
            screen.blit(npc.sprite, (nx, ny))
            
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
        ui_manager.draw_minimap(screen, player, npcs, environment.obstacles, camera, building_system, lore_system)

        if show_menu:
            game_menu.draw_menu(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
