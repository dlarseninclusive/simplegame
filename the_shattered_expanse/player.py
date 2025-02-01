import pygame
from combat_effects import DamageNumber, HitFlash, AttackAnimation
from data import generate_loot  # Add loot generation import

class Player:
    """
    Player with movement, collisions, health regen, thirst, hunger, 
    heat stroke, inventory, faction rep, attack ability.
    """
    def __init__(self, x, y, weapon_type="knife"):
        from sprites import create_weapon_sprite, WEAPON_TYPES
        from data import EQUIPMENT_DATA
        from item import Item

        self.width = 32
        self.height = 32
        self.speed = 200
        self.rect = pygame.Rect(x, y, self.width, self.height)

        self.vx = 0
        self.vy = 0

        # Weapon
        self.weapon_type = weapon_type
        self.weapon_sprite = create_weapon_sprite(weapon_type)
        self.weapon_damage_multiplier = WEAPON_TYPES[weapon_type]['damage_multiplier']

        # Stats
        self.max_health = 100
        self.health = 100

        self.max_thirst = 100
        self.thirst = 100

        self.max_hunger = 100
        self.hunger = 100

        # Health Regeneration Rate
        self.health_regen_rate = 2.0  # e.g., 2 HP per second if conditions met

        # Starting inventory: enough to build a small base
        self.inventory = {
            "scrap": 50,    # Enough for several structures
            "water": 10,
            "food": 10,
            "artifact": 5,  # For advanced structures
            "wood": 20     # For new building types
        }

        # Backpack initialization
        self.backpack = Backpack(max_slots=20)

        # Equipment system
        self.equipment = EquipmentManager()

        # Add some starting equipment
        starter_sword = Item("Rusty Sword", "weapon", 
                           EQUIPMENT_DATA["rusty_sword"]["stats"])
        starter_armor = Item("Scrap Metal Armor", "chest", 
                           EQUIPMENT_DATA["scrap_armor"]["stats"])
        
        self.equipment.equip_item(starter_sword)
        self.equipment.equip_item(starter_armor)

        # Faction reputation
        self.faction_rep = {
            "Automatons": 0,
            "Scavengers": 0,
            "Cog Preachers": 0
        }

        # For a simple melee attack, define range and damage
        self.attack_range = 50
        self.attack_damage = 50

    def handle_input(self, dt):
        """Handle keyboard input for player movement"""
        keys = pygame.key.get_pressed()
        
        # Movement handling
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
        
        # Use stockpiled resources when primary supply runs out
        if self.thirst <= 0 and self.inventory.get('water', 0) > 0:
            water_to_use = min(self.inventory['water'], 10)  # Use up to 10 water at a time
            self.inventory['water'] -= water_to_use
            self.thirst += water_to_use * 10  # Each water restores 10 thirst
        
        if self.hunger <= 0 and self.inventory.get('food', 0) > 0:
            food_to_use = min(self.inventory['food'], 5)  # Use up to 5 food at a time
            self.inventory['food'] -= food_to_use
            self.hunger += food_to_use * 20  # Each food restores 20 hunger
        
        # Health damage if resources are completely depleted
        if self.thirst <= 0:
            self.health -= 2 * dt
        
        if self.hunger <= 0:
            self.health -= 1 * dt
        
        # Ensure thirst and hunger don't go negative
        self.thirst = max(0, self.thirst)
        self.hunger = max(0, self.hunger)

        # Heat stroke around midday
        if abs(day_cycle - heat_stroke_threshold) < 1.0:
            if self.thirst < 50:
                self.health -= 5 * dt

        # Collisions with hostile NPCs
        for npc in npcs:
            if self.rect.colliderect(npc.rect) and npc.hostile:
                self.health -= 10 * dt

        # Health regeneration if thirst/hunger above certain thresholds
        if self.health < self.max_health:
            if self.thirst > 50 and self.hunger > 50:
                self.health += self.health_regen_rate * dt
                if self.health > self.max_health:
                    self.health = self.max_health

        if self.health < 0:
            self.health = 0

    def attempt_attack(self, npcs, dt, combat_effects=None, ui_manager=None):
        attacked = False
        for npc in npcs:
            dist_x = npc.rect.centerx - self.rect.centerx
            dist_y = npc.rect.centery - self.rect.centery
            dist = (dist_x**2 + dist_y**2) ** 0.5
            if dist <= self.attack_range:
                # Deal damage with weapon multiplier
                damage = self.attack_damage * self.weapon_damage_multiplier
                npc.health -= damage
                attacked = True
                
                # Add visual effects if combat_effects system exists
                if combat_effects:
                    # Damage number
                    combat_effects.add(DamageNumber(
                        npc.rect.centerx, npc.rect.top, 
                        damage
                    ))
                    # Hit flash
                    combat_effects.add(HitFlash(
                        self.rect.centerx, self.rect.centery,
                        50  # Adjust size as needed
                    ))
                    # Attack animation with weapon
                    combat_effects.add(AttackAnimation(
                        self.rect, npc.rect, self.weapon_sprite
                    ))
                
                # Log damage in UI
                if ui_manager:
                    ui_manager.log_damage(damage, f"Player to {npc.__class__.__name__}")
                
                # Handle NPC death and loot drops
                if npc.health <= 0:
                    if ui_manager:
                        ui_manager.log_damage(0, f"Defeated {npc.enemy_type}")
                    
                    # Generate and add loot
                    loot = generate_loot(npc.enemy_type)
                    
                    for item, quantity in loot:
                        if isinstance(item, str):
                            # Resource item
                            if item not in self.inventory:
                                self.inventory[item] = 0
                            self.inventory[item] += quantity
                            if ui_manager:
                                ui_manager.log_damage(0, f"+ {quantity} {item}")
                        else:
                            # Equipment item
                            success, message = self.backpack.add_item(item, quantity)
                            if ui_manager:
                                ui_manager.log_damage(0, f"+ {item.name}")
                                if not success:
                                    ui_manager.log_damage(0, message)
                    
                    # Faction reputation effects
                    if npc.faction == "Scavengers":
                        self.change_faction_rep("Scavengers", -10)

    def change_faction_rep(self, faction_name, amount):
        """
        Change reputation with a specific faction
        Args:
            faction_name (str): Name of the faction
            amount (int): Amount to change reputation by (positive or negative)
        """
        if faction_name in self.faction_rep:
            self.faction_rep[faction_name] = max(-100, min(100, self.faction_rep[faction_name] + amount))

    def toggle_equipment_slot(self, slot_name):
        """
        Toggle equipment in a specific slot (equip/unequip)
        Args:
            slot_name (str): Name of the slot to toggle ("weapon", "chest", "head", "legs", "feet", "offhand")
        Returns:
            Item or None: The unequipped item if one was removed, None if slot was empty
        """
        if slot_name in self.equipment.slots:
            return self.equipment.unequip_item(slot_name)
        return None

    def collect_resource(self, resource_node):
        """Collect resources from a node"""
        rtype = resource_node.resource_type
        amount = 1  # Default amount if not specified
        
        # Initialize inventory key if it doesn't exist
        if rtype not in self.inventory:
            self.inventory[rtype] = 0
        
        self.inventory[rtype] += amount
        
        # Handle consumable effects
        if rtype == "water":
            self.thirst = min(self.thirst + 20, self.max_thirst)
        elif rtype == "food":
            self.hunger = min(self.hunger + 30, self.max_hunger)

class EquipmentManager:
    def __init__(self):
        self.slots = {
            "weapon": None,
            "chest": None,
            "head": None,
            "legs": None,
            "feet": None,
            "offhand": None
        }

    def equip_item(self, item):
        """Equip an item to its appropriate slot"""
        if item.type in self.slots:
            self.slots[item.type] = item
        else:
            raise ValueError(f"Invalid equipment type: {item.type}")

    def unequip_item(self, slot):
        """Unequip an item from a specific slot"""
        if slot in self.slots:
            item = self.slots[slot]
            self.slots[slot] = None
            return item
        else:
            raise ValueError(f"Invalid equipment slot: {slot}")

    def get_total_armor(self):
        """Calculate total armor from equipped items"""
        return sum(
            item.get_stat('armor', 0) 
            for item in self.slots.values() 
            if item is not None
        )

    def get_speed_multiplier(self):
        """Calculate speed multiplier from equipped items"""
        speed_multipliers = [
            item.get_stat('speed', 1.0) 
            for item in self.slots.values() 
            if item is not None
        ]
        
        # Multiply all speed multipliers
        total_multiplier = 1.0
        for multiplier in speed_multipliers:
            total_multiplier *= multiplier
        
        return total_multiplier

class Backpack:
    def __init__(self, max_slots=20):
        self.max_slots = max_slots
        self.items = []  # List of (item, quantity) tuples
        
    def add_item(self, item, quantity=1):
        """Try to add an item to the backpack"""
        if len(self.items) >= self.max_slots:
            return False, "Backpack is full!"
            
        # Check if item already exists
        for i, (existing_item, qty) in enumerate(self.items):
            if existing_item.name == item.name:
                self.items[i] = (existing_item, qty + quantity)
                return True, "Added to existing stack"
                
        # Add new item
        self.items.append((item, quantity))
        return True, "Item added"
        
    def remove_item(self, item_name, quantity=1):
        """Remove an item from the backpack"""
        for i, (item, qty) in enumerate(self.items):
            if item.name == item_name:
                if qty <= quantity:
                    self.items.pop(i)
                else:
                    self.items[i] = (item, qty - quantity)
                return True
        return False

