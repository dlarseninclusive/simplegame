import pygame
from resource import RESOURCE_DATA

class Player:
    """
    Player with movement, collisions, health regen, thirst, hunger, 
    heat stroke, inventory, faction rep, attack ability.
    """
    def __init__(self, x, y):
        self.width = 32
        self.height = 32
        self.speed = 200
        self.rect = pygame.Rect(x, y, self.width, self.height)

        self.vx = 0
        self.vy = 0

        # Stats
        self.max_health = 100
        self.health = 100

        self.max_thirst = 100
        self.thirst = 100

        self.max_hunger = 100
        self.hunger = 100

        # 1) Health Regeneration Rate
        self.health_regen_rate = 2.0  # e.g., 2 HP per second if conditions met

        # Starting inventory: enough to build a small base
        self.inventory = {
            "scrap": 50,    # Enough for several structures
            "water": 10,
            "food": 10,
            "artifact": 5,  # For advanced structures
            "wood": 20     # For new building types
        }

        self.faction_rep = {
            "Automatons": 0,
            "Scavengers": 0,
            "Cog Preachers": 0
        }

        # For a simple melee attack, define range and damage
        self.attack_range = 50
        self.attack_damage = 50

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        self.vx = 0
        self.vy = 0
        if keys[pygame.K_a]:
            self.vx = -self.speed
        if keys[pygame.K_d]:
            self.vx = self.speed
        if keys[pygame.K_w]:
            self.vy = -self.speed
        if keys[pygame.K_s]:
            self.vy = self.speed

        self.vx *= dt
        self.vy *= dt

    def update(self, dt, obstacles, npcs, day_cycle, heat_stroke_threshold):
        # Movement
        self.rect.x += self.vx
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if self.vx > 0:
                    self.rect.right = obs.left
                elif self.vx < 0:
                    self.rect.left = obs.right

        self.rect.y += self.vy
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if self.vy > 0:
                    self.rect.bottom = obs.top
                elif self.vy < 0:
                    self.rect.top = obs.bottom

        # Thirst & Hunger drain (reduced rates)
        self.thirst -= 1 * dt  # Was 5
        self.hunger -= 0.5 * dt  # Was 3
        if self.thirst < 0:
            self.thirst = 0
            self.health -= 2 * dt
        if self.hunger < 0:
            self.hunger = 0
            self.health -= 1 * dt

        # Heat stroke around midday
        if abs(day_cycle - heat_stroke_threshold) < 1.0:
            if self.thirst < 50:
                self.health -= 5 * dt

        # Collisions with hostile NPCs
        for npc in npcs:
            if self.rect.colliderect(npc.rect) and npc.hostile:
                self.health -= 10 * dt

        # 2) Health regeneration if thirst/hunger above certain thresholds
        if self.health < self.max_health:
            if self.thirst > 50 and self.hunger > 50:
                self.health += self.health_regen_rate * dt
                if self.health > self.max_health:
                    self.health = self.max_health

        if self.health < 0:
            self.health = 0

    def collect_resource(self, resource_node):
        rtype = resource_node.resource_type
        self.inventory[rtype] += 1

        data = resource_node.data
        thirst_recov = data.get("thirst_recovery", 0)
        hunger_recov = data.get("hunger_recovery", 0)

        self.thirst = min(self.thirst + thirst_recov, self.max_thirst)
        self.hunger = min(self.hunger + hunger_recov, self.max_hunger)

    def change_faction_rep(self, faction, amount):
        if faction in self.faction_rep:
            self.faction_rep[faction] += amount

    def attempt_attack(self, npcs, dt, combat_effects=None):
        """
        Melee attack with visual effects:
        - If an NPC is within attack_range, deal attack_damage to them.
        - Show damage numbers and hit effects
        """
        attacked = False
        for npc in npcs:
            dist_x = npc.rect.centerx - self.rect.centerx
            dist_y = npc.rect.centery - self.rect.centery
            dist = (dist_x**2 + dist_y**2) ** 0.5
            if dist <= self.attack_range:
                # Deal damage
                npc.health -= self.attack_damage
                attacked = True
                
                # Add visual effects if combat_effects system exists
                if combat_effects:
                    # Damage number
                    combat_effects.add(DamageNumber(
                        npc.rect.centerx, npc.rect.top, 
                        self.attack_damage
                    ))
                    # Hit flash
                    combat_effects.add(HitFlash(
                        npc.rect.centerx, npc.rect.centery,
                        npc.width * 1.5
                    ))
                    # Attack animation
                    combat_effects.add(AttackAnimation(
                        self.rect, npc.rect
                    ))
                
                # Faction reputation effects
                if npc.health <= 0 and npc.faction == "Scavengers":
                    self.change_faction_rep("Scavengers", -10)
