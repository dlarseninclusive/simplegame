# ui.py

import pygame

class UIManager:
    """
    Handles on-screen HUD elements like bars, text, and minimap rendering.
    """
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.SysFont(None, 20)
        
        # Separate status bar resources from inventory
        self.status_resources = {
            "scrap": 0,
            "water": 0,
            "food": 0,
            "wood": 0,
            "artifact": 0
        }

    def draw_hud(self, screen, player, factions, build_mode, day_cycle):
        # Health/Thirst/Hunger bars
        bar_width = 100
        x_offset = 10
        y_offset = 10

        # Health
        health_ratio = player.health / player.max_health
        pygame.draw.rect(screen, (255, 0, 0),
                         (x_offset, y_offset, int(bar_width*health_ratio), 8))
        pygame.draw.rect(screen, (255, 255, 255), (x_offset, y_offset, bar_width, 8), 1)

        # Thirst
        thirst_ratio = player.thirst / player.max_thirst
        pygame.draw.rect(screen, (0, 191, 255),
                         (x_offset, y_offset+10, int(bar_width*thirst_ratio), 8))
        pygame.draw.rect(screen, (255, 255, 255),
                         (x_offset, y_offset+10, bar_width, 8), 1)

        # Hunger
        hunger_ratio = player.hunger / player.max_hunger
        pygame.draw.rect(screen, (50, 205, 50),
                         (x_offset, y_offset+20, int(bar_width*hunger_ratio), 8))
        pygame.draw.rect(screen, (255, 255, 255),
                         (x_offset, y_offset+20, bar_width, 8), 1)

        # Faction Rep
        rep_text = self.font.render(
            f"Automatons:{player.faction_rep['Automatons']}  "
            f"Scavengers:{player.faction_rep['Scavengers']}  "
            f"Cog:{player.faction_rep['Cog Preachers']}",
            True, (255,255,255))
        screen.blit(rep_text, (x_offset, y_offset+35))

        # Update status resources (could be tied to a method that player calls)
        self.status_resources['scrap'] = min(player.inventory.get('scrap', 0), 50)
        self.status_resources['water'] = min(player.inventory.get('water', 0), 10)
        self.status_resources['food'] = min(player.inventory.get('food', 0), 10)
        self.status_resources['wood'] = min(player.inventory.get('wood', 0), 20)
        self.status_resources['artifact'] = min(player.inventory.get('artifact', 0), 5)

        # Resources
        resource_text = (f"Scrap:{self.status_resources['scrap']} "
                         f"Water:{self.status_resources['water']} "
                         f"Food:{self.status_resources['food']} "
                         f"Wood:{self.status_resources['wood']} "
                         f"Artifact:{self.status_resources['artifact']}")
        res_surf = self.font.render(resource_text, True, (255,255,255))
        screen.blit(res_surf, (x_offset, y_offset+50))

        # Build mode
        if build_mode:
            build_surf = self.font.render("BUILD MODE (1=Wall, 2=Turret, 3=Storage, 4=Workshop, 5=Collector, 6=Generator)", True, (255,255,0))
            screen.blit(build_surf, (x_offset, y_offset+65))

        # Show time-of-day
        time_surf = self.font.render(f"Time: {day_cycle:.1f}h", True, (255,255,255))
        screen.blit(time_surf, (x_offset, y_offset+80))

    def draw_minimap(self, screen, player, npcs, obstacles, camera, building_system, lore_system, cities):
        """
        A simple top-right corner minimap. We just scale down by some factor.
        Requires lore_system to be passed in to render lore fragments.
        """
        map_width = 150
        map_height = 150
        minimap_x = self.screen_width - map_width - 10
        minimap_y = 10
        pygame.draw.rect(screen, (20,20,20), (minimap_x, minimap_y, map_width, map_height))

        # scale factor for 4000x4000 world
        scale_x = map_width / 4000
        scale_y = map_height / 4000

        # Draw obstacles
        for obs in obstacles:
            ox = int(obs.x * scale_x)
            oy = int(obs.y * scale_y)
            ow = max(1, int(obs.width * scale_x))
            oh = max(1, int(obs.height * scale_y))
            pygame.draw.rect(
                screen, (0,128,0),
                (minimap_x+ox, minimap_y+oy, ow, oh)
            )

        # Draw cities
        for city in cities:
            cx = int(city.rect.x * scale_x)
            cy = int(city.rect.y * scale_y)
            cw = max(1, int(city.rect.width * scale_x))
            ch = max(1, int(city.rect.height * scale_y))
            pygame.draw.rect(screen, (255, 215, 0),  # Gold color for cities
                             (minimap_x+cx, minimap_y+cy, cw, ch))

        # Draw NPCs
        for npc in npcs:
            nx = int(npc.rect.x * scale_x)
            ny = int(npc.rect.y * scale_y)
            pygame.draw.rect(screen, (100,100,100),
                             (minimap_x+nx, minimap_y+ny, 2, 2))

        # Draw buildings
        for bld in building_system.structures:
            bx = int(bld.x * scale_x)
            by = int(bld.y * scale_y)
            bw = max(1, int(bld.width * scale_x))
            bh = max(1, int(bld.height * scale_y))
            
            # Different colors for different building types
            if bld.structure_type == "Generator":
                color = (255, 140, 0)  # Orange
            elif bld.structure_type == "Storage":
                color = (139, 69, 19)  # Brown
            elif bld.structure_type == "Workshop":
                color = (105, 105, 105)  # Gray
            elif bld.structure_type == "Collector":
                color = (46, 139, 87)  # Sea green
            else:
                color = (139, 69, 19)  # Default brown
                
            pygame.draw.rect(screen, color,
                           (minimap_x+bx, minimap_y+by, bw, bh))

        # Draw player
        px = int(player.rect.x * scale_x)
        py = int(player.rect.y * scale_y)
        pygame.draw.rect(screen, (200,0,0),
                         (minimap_x+px, minimap_y+py, 3, 3))

        # Render Lore Fragments
        if lore_system:
            for fragment in lore_system.fragments:
                fragment.render(screen, (camera.offset_x, camera.offset_y))

            # Check for Lore Fragment Discovery
            discovered_fragment = lore_system.discover_fragment(player)
            if discovered_fragment:
                lore_system.render_discovered_fragments(screen, self.font, (camera.offset_x, camera.offset_y))

class GameMenu:
    """
    A placeholder for a pause menu or in-game menu.
    """
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font = pygame.font.SysFont(None, 36)

    def draw_menu(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # semi-transparent dark
        screen.blit(overlay, (0,0))

        controls = [
            "Movement: WASD",
            "Build Mode: B",
            "Collect Resource: E",
            "Attack: Spacebar",
            "Crafting Menu: C",
            "Upgrade Structure: U (in build mode)",
            "Repair Structure: H (in build mode)",
            "Reclaim Structure: Right-Click (in build mode)",
            "Place Structures: 1-6 (in build mode)",
            "Pause/Resume: ESC"
        ]

        title = self.font.render("Game Paused - ESC to Resume", True, (255, 255, 255))
        screen.blit(title, (self.width//2 - title.get_width()//2, 100))

        for i, control in enumerate(controls):
            text = pygame.font.SysFont(None, 24).render(control, True, (200, 200, 200))
            screen.blit(text, (self.width//2 - text.get_width()//2, 200 + i*30))
