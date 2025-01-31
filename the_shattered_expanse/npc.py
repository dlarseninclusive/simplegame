# npc.py

import pygame
import random

class NPC:
    """
    Basic NPC that can wander, chase the player if hostile,
    or use pathfinding. Group ID can allow group behavior.
    """
    def __init__(self, x, y, faction="Scavengers", group_id=None, enemy_type="warrior"):
        self.enemy_type = enemy_type
        stats = ENEMY_STATS[enemy_type]
        
        self.width = stats["size"]
        self.height = stats["size"]
        self.speed = stats["speed"]
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.faction = faction
        self.hostile = True
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

    def update(self, dt, obstacles, player, pathfinder=None):
        """
        Decide what behavior to use each frame:
        - If player is near and we're hostile, chase or pathfind to them.
        - Otherwise, wander around randomly.
        """
        dist_to_player = ((self.rect.centerx - player.rect.centerx)**2 +
                          (self.rect.centery - player.rect.centery)**2)**0.5

        # If we're close enough to see the player and are hostile
        if dist_to_player < 200 and self.hostile:
            if pathfinder is not None:
                # Use pathfinding-based approach
                self.follow_path(dt, obstacles, player, pathfinder)
            else:
                # Fallback to direct chase 
                self.chase_player(dt, obstacles, player)
        else:
            # If the player is far, just wander
            self.wander(dt, obstacles)

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
