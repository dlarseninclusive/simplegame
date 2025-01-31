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

        # Resources
        resource_text = (f"Scrap:{player.inventory['scrap']} "
                         f"Water:{player.inventory['water']} "
                         f"Food:{player.inventory['food']} "
                         f"Wood:{player.inventory['wood']} "
                         f"Artifact:{player.inventory['artifact']}")
        res_surf = self.font.render(resource_text, True, (255,255,255))
        screen.blit(res_surf, (x_offset, y_offset+50))

        # Build mode
        if build_mode:
            build_surf = self.font.render("BUILD MODE (Shift=Turret)", True, (255,255,0))
            screen.blit(build_surf, (x_offset, y_offset+65))

        # Show time-of-day
        time_surf = self.font.render(f"Time: {day_cycle:.1f}h", True, (255,255,255))
        screen.blit(time_surf, (x_offset, y_offset+80))

    def draw_minimap(self, screen, player, npcs, obstacles, camera, building_system):
        """
        A simple top-right corner minimap. We just scale down by some factor.
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

        text = self.font.render("Game Paused - ESC to Resume", True, (255, 255, 255))
        screen.blit(text, (self.width//2 - text.get_width()//2,
                           self.height//2 - text.get_height()//2))
