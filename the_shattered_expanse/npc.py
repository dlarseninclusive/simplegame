# npc.py

import pygame
import random
from sprites import ENEMY_STATS, create_enemy_sprite

class NPC:
    """
    Basic NPC that can wander, chase the player if hostile,
    or use pathfinding. Group ID can allow group behavior.
    """
    def interact(self, player):
        """
        Interact with the player, generating context-specific dialogue
        """
        # Basic relationship determination
        dist = ((player.rect.centerx - self.rect.centerx)**2 + 
                (player.rect.centery - self.rect.centery)**2)**0.5
        
        # Determine basic relationship status
        if dist < 50:
            status = "friendly"
        elif dist < 100:
            status = "neutral"
        else:
            status = "hostile"
        
        # Generate a basic dialogue with more flavor
        dialogues = {
            "Scavengers": [
                f"Scavenger says: We're always looking for resources. Our relationship is {status}.",
                f"Scavenger mutters: Survival is tough out here. Feeling {status} today.",
                f"Scavenger nods: Trade might be possible if you're {status}."
            ],
            "Automatons": [
                f"Automaton beeps: Efficiency protocols detect {status} interaction.",
                f"Automaton chirps: Calculating social parameters. Current status: {status}.",
                f"Automaton whirrs: Interaction mode: {status}."
            ],
            "Cog Preachers": [
                f"Cog Preacher intones: The machine spirit sees you as {status}.",
                f"Cog Preacher whispers: Our paths cross under divine machinery.",
                f"Cog Preacher declares: Your standing is {status} in the eyes of the Cog."
            ]
        }
        
        # Randomly select a dialogue for the faction
        faction_dialogues = dialogues.get(self.faction, dialogues["Scavengers"])
        return random.choice(faction_dialogues)
    def __init__(self, x, y, faction="Scavengers", group_id=None, enemy_type="warrior", spawn_region="south"):
        self.spawn_region = spawn_region
        self.enemy_type = enemy_type
        
        # Ensure enemy_type exists in ENEMY_STATS
        if enemy_type not in ENEMY_STATS:
            # Fallback to a default type if not found
            enemy_type = "warrior"
        
        stats = ENEMY_STATS[enemy_type]
        
        # Use a default size if not specified
        self.width = stats.get("size", 32)
        self.height = stats.get("size", 32)
        self.speed = stats["speed"]
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.faction = faction
        
        # Store original position for collision reverts
        self.old_pos = (x, y)
        
        # Store original position for collision reverts
        self.old_pos = (x, y)
        
        # Flag for shopkeepers
        self.is_shopkeeper = enemy_type == "merchant"
        
        # Shopkeepers are not hostile
        self.hostile = not self.is_shopkeeper and stats.get("hostile", True)
        
        self.group_id = group_id

        self.move_cooldown = 0
        self.vx = 0
        self.vy = 0

        # Use enemy stats for health
        self.health = stats["health"]
        self.max_health = stats["health"]
        self.damage = stats["damage"]
        
        # Create sprite
        self.sprite = create_enemy_sprite(enemy_type)

        # For pathfinding
        self.path = []            # list of (gx, gy) cells from A* 
        self.current_path_index = 0

    def draw_faction_marker(self, screen, camera_offset):
        """Draw a distinctive marker above the NPC to indicate their faction."""
        marker_color = {
            "Automatons": (0, 255, 255),   # Cyan
            "Scavengers": (0, 255, 0),     # Green
            "Cog Preachers": (255, 0, 255) # Magenta
        }.get(self.faction, (255, 255, 255))  # Default white
        
        marker_style = {
            "Automatons": lambda s, x: pygame.draw.line(s, marker_color,
                (x.rect.left - camera_offset[0], x.rect.top - camera_offset[1] - 5),
                (x.rect.right - camera_offset[0], x.rect.top - camera_offset[1] - 5), 2),
            "Scavengers": lambda s, x: pygame.draw.line(s, marker_color,
                (x.rect.centerx - camera_offset[0], x.rect.top - camera_offset[1] - 10),
                (x.rect.centerx - camera_offset[0], x.rect.bottom - camera_offset[1] + 10), 2),
            "Cog Preachers": lambda s, x: (
                pygame.draw.line(s, marker_color,
                    (x.rect.left - camera_offset[0], x.rect.top - camera_offset[1]),
                    (x.rect.right - camera_offset[0], x.rect.bottom - camera_offset[1]), 2),
                pygame.draw.line(s, marker_color,
                    (x.rect.right - camera_offset[0], x.rect.top - camera_offset[1]),
                    (x.rect.left - camera_offset[0], x.rect.bottom - camera_offset[1]), 2)
            )
        }
        
        marker_func = marker_style.get(self.faction, lambda s, x: None)
        marker_func(screen, self)

    def choose_behavior(self, dt, obstacles, player, pathfinder, city_roads=None):
        """
        Decide NPC behavior based on faction and road network.
        """
        # Scavengers can freely wander
        if self.faction == "Scavengers":
            self.wander(dt, obstacles)
            return

        # Other factions use road network for movement
        if city_roads and not self.path:
            # Choose a random road segment
            road = random.choice(city_roads)
            
            # Convert world coordinates to grid coordinates
            start_gx, start_gy = pathfinder.world_to_grid(self.rect.centerx, self.rect.centery)
            
            # Choose a random destination on the road
            dest = random.choice(road[1:])  # Skip first point to avoid starting point
            dest_gx, dest_gy = pathfinder.world_to_grid(dest[0], dest[1])
            
            # Find path using A*
            self.path = pathfinder.find_path(start_gx, start_gy, dest_gx, dest_gy)
            self.current_path_index = 0

        # Use existing path-following logic
        if self.path:
            self.follow_path(dt, obstacles, player, pathfinder)
        else:
            # Fallback to existing behavior
            dist_to_player = ((self.rect.centerx - player.rect.centerx)**2 +
                              (self.rect.centery - player.rect.centery)**2)**0.5

            if dist_to_player < 200 and self.hostile:
                self.chase_player(dt, obstacles, player)
            else:
                self.wander(dt, obstacles)

    def update(self, dt, obstacles, player, pathfinder=None, city_roads=None):
        """
        Decide what behavior to use each frame:
        - If player is near and we're hostile, chase or pathfind to them.
        - Otherwise, wander around randomly.
        """
        # Before moving, remember last position
        self.old_pos = self.rect.topleft
        
        self.choose_behavior(dt, obstacles, player, pathfinder, city_roads)

    def chase_player(self, dt, obstacles, player):
        """
        A direct chase approach without pathfinding:
        Move in a straight line toward the player's position.
        """
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = (dx**2 + dy**2) ** 0.5
        if dist != 0:
            dx /= dist
            dy /= dist

        # Move
        self.rect.x += int(dx * self.speed * dt)
        self.rect.y += int(dy * self.speed * dt)

        # Check collisions with obstacles
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if dx > 0:
                    self.rect.right = obs.left
                elif dx < 0:
                    self.rect.left = obs.right
                if dy > 0:
                    self.rect.bottom = obs.top
                elif dy < 0:
                    self.rect.top = obs.bottom

    def follow_path(self, dt, obstacles, player, pathfinder):
        """
        Use pathfinder (A*) to find a path to the player's position,
        and move step-by-step along that path.
        """
        # Convert our NPC center & player center to grid coords
        npc_gx, npc_gy = pathfinder.world_to_grid(self.rect.centerx, self.rect.centery)
        ply_gx, ply_gy = pathfinder.world_to_grid(player.rect.centerx, player.rect.centery)

        # If we need a new path (either we have no path or we finished it)
        if not self.path or self.current_path_index >= len(self.path):
            self.path = pathfinder.find_path(npc_gx, npc_gy, ply_gx, ply_gy)
            self.current_path_index = 0

        # Follow the path if it exists
        if self.path:
            target_cell = self.path[self.current_path_index]
            world_x, world_y = pathfinder.grid_to_world(target_cell[0], target_cell[1])

            # Move toward that cell
            dx = world_x - self.rect.centerx
            dy = world_y - self.rect.centery
            dist = (dx**2 + dy**2)**0.5
            if dist > 2:  # If not close enough to the cell center
                dx /= dist
                dy /= dist
                self.rect.x += int(dx * self.speed * dt)
                self.rect.y += int(dy * self.speed * dt)
            else:
                # Arrived at this cell, move to the next
                self.current_path_index += 1

        # Check collisions with obstacles
        for obs in obstacles:
            if self.rect.colliderect(obs):
                # Basic collision resolution
                pass

    def wander(self, dt, obstacles):
        """
        Choose random directions at intervals, 
        then move that way until cooldown expires.
        """
        self.move_cooldown -= dt
        if self.move_cooldown <= 0:
            self.vx = random.randint(-1, 1) * self.speed
            self.vy = random.randint(-1, 1) * self.speed
            self.move_cooldown = random.uniform(1, 3)

        # Move
        self.rect.x += int(self.vx * dt)
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if self.vx > 0:
                    self.rect.right = obs.left
                elif self.vx < 0:
                    self.rect.left = obs.right

        self.rect.y += int(self.vy * dt)
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if self.vy > 0:
                    self.rect.bottom = obs.top
                elif self.vy < 0:
                    self.rect.top = obs.bottom
