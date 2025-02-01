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
        
        # Damage log for tracking recent damage events
        self.damage_log = []
        self.max_damage_log_entries = 5
        self.damage_log_duration = 3.0  # seconds

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

        # Draw damage log
        self.draw_damage_log(screen, x_offset, y_offset + 90)

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

        # Draw inventory
        self.draw_inventory(screen, player)

    def draw_inventory(self, screen, player):
        """Draw a detailed inventory display"""
        inventory_font = pygame.font.Font(None, 24)
        y_offset = self.screen_height - 150  # Bottom of screen
        x_offset = 10
        
        # Inventory title
        title = inventory_font.render("Inventory:", True, (255, 255, 255))
        screen.blit(title, (x_offset, y_offset))
        
        # Render inventory items
        for i, (item, quantity) in enumerate(player.inventory.items()):
            item_text = inventory_font.render(f"{item.capitalize()}: {quantity}", True, (200, 200, 200))
            screen.blit(item_text, (x_offset, y_offset + 30 + i * 25))

    def log_damage(self, damage, source):
        """Log a damage event"""
        current_time = pygame.time.get_ticks() / 1000.0
        self.damage_log.append({
            'damage': damage,
            'source': source,
            'time': current_time
        })
        
        # Trim log if it gets too long
        if len(self.damage_log) > self.max_damage_log_entries:
            self.damage_log.pop(0)

    def draw_damage_log(self, screen, x, y):
        """Draw recent damage events"""
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Remove old entries
        self.damage_log = [
            entry for entry in self.damage_log 
            if current_time - entry['time'] < self.damage_log_duration
        ]
        
        # Draw remaining entries
        for i, entry in enumerate(self.damage_log):
            color = (255, 0, 0) if entry['damage'] > 0 else (0, 255, 0)
            damage_text = f"{entry['source']}: {entry['damage']:.1f}"
            damage_surf = self.font.render(damage_text, True, color)
            screen.blit(damage_surf, (x, y + i * 15))

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
        for faction, buildings in cities.items():
            for city in buildings:
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
    Simple game menu class for pausing and displaying options.
    """
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 24)

    def draw_menu(self, screen):
        menu_surface = pygame.Surface((self.screen_width, self.screen_height))
        menu_surface.set_alpha(128)  # Semi-transparent
        menu_surface.fill((0, 0, 0))
        screen.blit(menu_surface, (0, 0))

        title_text = self.font.render("Game Menu", True, (255, 255, 255))
        screen.blit(title_text, (self.screen_width // 2 - title_text.get_width() // 2, 50))

        # Comprehensive controls list
        controls = [
            "Movement:",
            "W/A/S/D - Move Up/Left/Down/Right",
            "",
            "Combat & Interaction:",
            "SPACE - Attack",
            "E - Collect Resources",
            "",
            "Building & Construction:",
            "B - Toggle Build Mode",
            "1-6 - Select Building Type",
            "Left Click - Place Building",
            "Right Click - Reclaim Building",
            "U - Upgrade Structure",
            "H - Repair Structure",
            "",
            "Inventory & Crafting:",
            "C - Open Crafting Menu",
            "",
            "Game Management:",
            "ESC - Open/Close Menu",
            "",
            "Press ESC to return to game"
        ]

        for i, line in enumerate(controls):
            if line:
                # Differentiate between section headers and control descriptions
                if line.endswith(':'):
                    text_color = (255, 215, 0)  # Gold for headers
                    font = self.font
                else:
                    text_color = (200, 200, 200)  # Gray for descriptions
                    font = self.small_font
            else:
                # Skip empty lines
                continue

            control_text = font.render(line, True, text_color)
            screen.blit(control_text, (
                self.screen_width // 2 - control_text.get_width() // 2, 
                150 + i * 25
            ))

        pygame.display.flip()
