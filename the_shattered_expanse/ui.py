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
        self.show_equipment = False
        self.show_minimap = True
        self.show_backpack = False  # New line
        self.show_detailed_ui = False
        self.show_lore_log = False  # New flag for lore log
        
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

        # Draw backpack
        self.draw_backpack(screen, player)

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

        # Minimal info always displayed
        basic_text = self.font.render(
            f"HP: {player.health}/{player.max_health}", True, (255,255,255))
        screen.blit(basic_text, (x_offset, y_offset+35))

        # Detailed faction rep
        if self.show_detailed_ui:
            rep_text = self.font.render(
                f"Automatons:{player.faction_rep['Automatons']}  "
                f"Scavengers:{player.faction_rep['Scavengers']}  "
                f"Cog:{player.faction_rep['Cog Preachers']}",
                True, (255,255,255))
            screen.blit(rep_text, (x_offset, y_offset+50))

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

        # Draw inventory and equipment
        self.draw_inventory(screen, player)
        self.draw_equipment(screen, player)

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

    def draw_equipment(self, screen, player):
        """Draw equipment slots and equipped items"""
        if not self.show_equipment:
            return
            
        # Equipment panel on right side
        panel_width = 200
        panel_x = self.screen_width - panel_width
        pygame.draw.rect(screen, (40, 40, 40), 
                    (panel_x, 0, panel_width, self.screen_height))
        pygame.draw.rect(screen, (100, 100, 100), 
                    (panel_x, 0, panel_width, self.screen_height), 2)

        # Title
        title = self.font.render("Equipment (TAB to hide)", True, (255, 255, 255))
        screen.blit(title, (panel_x + 10, 10))

        # Draw equipment slots
        slot_size = 40
        slot_padding = 10
        slots_start_y = 40

        for i, (slot_name, item) in enumerate(player.equipment.slots.items()):
            slot_x = panel_x + 10
            slot_y = slots_start_y + (slot_size + slot_padding) * i
            
            # Draw slot background
            pygame.draw.rect(screen, (60, 60, 60), 
                       (slot_x, slot_y, slot_size, slot_size))
            pygame.draw.rect(screen, (120, 120, 120), 
                       (slot_x, slot_y, slot_size, slot_size), 1)
            
            # Draw slot label with hotkey
            label = self.font.render(f"{slot_name.capitalize()} (F{i+1})", True, (200, 200, 200))
            screen.blit(label, (slot_x + slot_size + 10, slot_y + slot_size//2 - 8))
            
            # Draw equipped item name if any
            if item:
                item_name = self.font.render(item.name, True, (255, 255, 255))
                screen.blit(item_name, (slot_x + slot_size + 80, slot_y + slot_size//2 - 8))

        # Draw total armor value at bottom
        armor_text = self.font.render(f"Total Armor: {player.equipment.get_total_armor()}", 
                                True, (200, 200, 200))
        screen.blit(armor_text, (panel_x + 10, self.screen_height - 30))

    def toggle_equipment_display(self):
        """Toggle the visibility of the equipment panel"""
        self.show_equipment = not self.show_equipment

    def toggle_minimap(self):
        """Toggle minimap visibility"""
        self.show_minimap = not self.show_minimap

    def toggle_backpack_display(self):
        """Toggle backpack visibility"""
        self.show_backpack = not self.show_backpack

    def draw_backpack(self, screen, player):
        """Draw backpack contents"""
        if not self.show_backpack:
            return
            
        # Backpack panel on left side
        panel_width = 200
        panel_height = 400
        panel_x = 10
        panel_y = 150
        
        # Draw panel background
        pygame.draw.rect(screen, (40, 40, 40), 
                        (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, (100, 100, 100), 
                        (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Title
        title = self.font.render("Backpack (I to hide)", True, (255, 255, 255))
        screen.blit(title, (panel_x + 10, panel_y + 10))
        
        # Draw items
        item_y = panel_y + 40
        for item, quantity in player.backpack.items:
            item_text = self.font.render(f"{item.name} x{quantity}", True, (255, 255, 255))
            screen.blit(item_text, (panel_x + 10, item_y))
            item_y += 25

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
        """
        if not self.show_minimap:
            return

        map_width = 150
        map_height = 150
        minimap_x = self.screen_width - map_width - 10
        minimap_y = 10
        
        # Create minimap surface
        minimap_surface = pygame.Surface((map_width, map_height))
        minimap_surface.fill((20, 20, 20))  # Dark gray background
        
        # Calculate scale factor (assuming 4000x4000 world size)
        scale_factor = map_width / 4000
        
        # Draw obstacles (white)
        for obs in obstacles:
            mini_rect = pygame.Rect(
                obs.x * scale_factor,
                obs.y * scale_factor,
                obs.width * scale_factor,
                obs.height * scale_factor
            )
            pygame.draw.rect(minimap_surface, (200, 200, 200), mini_rect)
        
        # Draw buildings (blue)
        if building_system and hasattr(building_system, 'structures'):
            for structure in building_system.structures:
                mini_rect = pygame.Rect(
                    structure.x * scale_factor,
                    structure.y * scale_factor,
                    structure.width * scale_factor,
                    structure.height * scale_factor
                )
                pygame.draw.rect(minimap_surface, (0, 100, 255), mini_rect)
        
        # Draw NPCs (red)
        for npc in npcs:
            mini_pos = (
                int(npc.rect.centerx * scale_factor),
                int(npc.rect.centery * scale_factor)
            )
            pygame.draw.circle(minimap_surface, (255, 0, 0), mini_pos, 2)
        
        # Draw lore fragments (yellow)
        if lore_system and hasattr(lore_system, 'fragments'):
            for fragment in lore_system.fragments:
                mini_pos = (
                    int(fragment.rect.centerx * scale_factor),
                    int(fragment.rect.centery * scale_factor)
                )
                pygame.draw.circle(minimap_surface, (255, 255, 0), mini_pos, 2)
        
        # Draw player (green)
        player_pos = (
            int(player.rect.centerx * scale_factor),
            int(player.rect.centery * scale_factor)
        )
        pygame.draw.circle(minimap_surface, (0, 255, 0), player_pos, 3)
        
        # Draw border
        pygame.draw.rect(minimap_surface, (255, 255, 255), 
                        (0, 0, map_width, map_height), 1)
        
        # Blit minimap to screen
        screen.blit(minimap_surface, (minimap_x, minimap_y))

    def draw_lore_log(self, screen, lore_system):
        """
        Draw a panel displaying discovered lore fragments.
        """
        panel_width = 400
        panel_height = 300
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2
        
        # Draw panel background and border
        pygame.draw.rect(screen, (0, 0, 0), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, (255, 255, 255), (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Title
        title = self.font.render("Lore Log", True, (255, 255, 255))
        screen.blit(title, (panel_x + 10, panel_y + 10))
        
        # List discovered lore
        y_offset = panel_y + 40
        for fragment in lore_system.discovered_fragments:
            lore_text = self.font.render(fragment.text, True, (200, 200, 200))
            screen.blit(lore_text, (panel_x + 10, y_offset))
            y_offset += 25

    def draw_npc_dialog(self, screen, dialog_text, font_size=24):
        """
        Draw a dialog box for NPC interactions at the bottom of the screen.
        """
        # Create a semi-transparent dialog box
        dialog_surface = pygame.Surface((self.screen_width, 150), pygame.SRCALPHA)
        dialog_surface.fill((0, 0, 0, 128))  # Semi-transparent black
        
        # Position at bottom of screen
        screen_height = screen.get_height()
        screen.blit(dialog_surface, (0, screen_height - 150))
        
        # Render dialog text
        dialog_font = pygame.font.Font(None, font_size)
        text_surface = dialog_font.render(dialog_text, True, (255, 255, 255))
        
        # Center the text in the dialog box
        text_rect = text_surface.get_rect(center=(self.screen_width//2, screen_height - 75))
        screen.blit(text_surface, text_rect)

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
            "F - Interact with NPCs",
            "",
            "Building & Construction:",
            "B - Toggle Build Mode",
            "1-6 - Select Building Type",
            "Left Click - Place Building",
            "Right Click - Reclaim Building",
            "U - Upgrade Structure",
            "H - Repair Structure",
            "",
            "Equipment & Inventory:",
            "TAB - Toggle Equipment Panel",
            "I - Toggle Backpack",
            "F1-F6 - Toggle Equipment Slots",
            "C - Open Crafting Menu",
            "",
            "Interface:",
            "M - Toggle Minimap",
            "I - Toggle Backpack",
            "ESC - Open/Close Menu",
            "",
            "Faction & Quests:",
            "Check Faction Reputation in HUD",
            "Complete Quests by Collecting Items",
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

class TabbedMenu:
    def __init__(self, rect, tabs, font):
        """
        rect: pygame.Rect defining the area for the menu.
        tabs: list of dicts, each with 'label' and 'content' (a Surface)
        font: pygame font for rendering tab labels.
        """
        self.rect = rect
        self.tabs = tabs
        self.font = font
        self.active_tab = 0
        self.button_height = 30
        self._create_button_rects()

    def _create_button_rects(self):
        # Divide the top area of the menu into equal button regions.
        num_tabs = len(self.tabs)
        button_width = self.rect.width // num_tabs
        for i, tab in enumerate(self.tabs):
            tab['button_rect'] = pygame.Rect(self.rect.x + i * button_width,
                                              self.rect.y,
                                              button_width,
                                              self.button_height)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, tab in enumerate(self.tabs):
                if tab['button_rect'].collidepoint(event.pos):
                    self.active_tab = i

    def draw(self, screen):
        # Draw the tab buttons.
        for i, tab in enumerate(self.tabs):
            color = (255, 255, 0) if i == self.active_tab else (200, 200, 200)
            pygame.draw.rect(screen, color, tab['button_rect'])
            label_surf = self.font.render(tab['label'], True, (0, 0, 0))
            label_rect = label_surf.get_rect(center=tab['button_rect'].center)
            screen.blit(label_surf, label_rect)
        # Draw active tab's content in the rest of the menu area.
        content_area = pygame.Rect(self.rect.x,
                                   self.rect.y + self.button_height,
                                   self.rect.width,
                                   self.rect.height - self.button_height)
        pygame.draw.rect(screen, (50, 50, 50), content_area)
        # Assume each tab's 'content' is a pre-rendered Surface.
        active_content = self.tabs[self.active_tab].get('content')
        if active_content:
            screen.blit(active_content, (content_area.x + 10, content_area.y + 10))
