import pygame
from camera import Camera
from player import Player
from environment import Environment
from resource import ResourceNode
from npc import NPC
from building import BuildingSystem
from crafting import CraftingSystem
from factions import Factions
from quests import QuestSystem
from ui import UIManager, GameMenu
from pathfinding import GridPathfinder

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

    # NPCs with more advanced AI
    npcs = [
        NPC(500, 200, faction="Automatons", group_id=1),
        NPC(1200, 600, faction="Scavengers", group_id=2),
        NPC(1500, 1300, faction="Scavengers", group_id=2),
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
                    player.attempt_attack(npcs, dt)

            # Build placement
            if build_mode and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    wx = mx + camera.offset_x
                    wy = my + camera.offset_y
                    building_system.attempt_placement(player, environment, wx, wy)

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

        # Buildings
        for bld in building_system.structures:
            bx = bld.x - camera.offset_x
            by = bld.y - camera.offset_y
            pygame.draw.rect(screen, (139, 69, 19), (bx, by, bld.width, bld.height))

        # NPCs
        for npc in npcs:
            nx = npc.rect.x - camera.offset_x
            ny = npc.rect.y - camera.offset_y
            pygame.draw.rect(screen, (100, 100, 100), (nx, ny, npc.rect.width, npc.rect.height))

        # Player
        px = player.rect.x - camera.offset_x
        py = player.rect.y - camera.offset_y
        pygame.draw.rect(screen, (178, 34, 34), (px, py, player.rect.width, player.rect.height))

        ui_manager.draw_hud(screen, player, factions, build_mode, day_cycle)
        ui_manager.draw_minimap(screen, player, npcs, environment.obstacles, camera)

        if show_menu:
            game_menu.draw_menu(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
