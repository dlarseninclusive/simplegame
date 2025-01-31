import pygame

class Structure:
    """
    A placed structure in the game world (e.g., wall, turret).
    """
    def __init__(self, x, y, width, height, structure_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.structure_type = structure_type
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.upgrade_cost = {"scrap": 5, "artifact": 1}
        self.repair_cost = {"scrap": 1}
        
        # Power system attributes
        self.power_required = 0
        self.power_received = 0
        self.power_grid_id = None  # Structures on same grid share power
        self.power_range = 100  # How far power can transmit
        
        # Structure-specific attributes
        if structure_type == "Storage":
            self.capacity = 100 * self.level
            self.stored = 0
            self.power_required = 2
        elif structure_type == "Generator":
            self.power_output = 10 * self.level
            self.active = True
            self.power_required = 0  # Generators don't need power
        elif structure_type == "Collector":
            self.collection_rate = 1 * self.level
            self.collection_timer = 0
            self.power_required = 3
        elif structure_type == "Workshop":
            self.production_speed = 1 * self.level
            self.current_project = None
            self.power_required = 5
        elif structure_type == "Advanced Turret":
            self.power_required = 4
            
    def upgrade(self, player):
        """Upgrade structure to next level if player has resources"""
        scaled_cost = {k: v * self.level for k, v in self.upgrade_cost.items()}
        
        # Check if player has enough resources
        for resource, amount in scaled_cost.items():
            if player.inventory.get(resource, 0) < amount:
                return False
                
        # Deduct resources and upgrade
        for resource, amount in scaled_cost.items():
            player.inventory[resource] -= amount
            
        self.level += 1
        self.max_health *= 1.5
        self.health = self.max_health
        
        # Upgrade structure-specific attributes
        if self.structure_type == "Storage":
            self.capacity = 100 * self.level
        elif self.structure_type == "Generator":
            self.power_output = 10 * self.level
        elif self.structure_type == "Collector":
            self.collection_rate = 1 * self.level
        elif self.structure_type == "Workshop":
            self.production_speed = 1 * self.level
        
        return True
        
    def repair(self, player):
        """Repair structure if player has resources"""
        if self.health >= self.max_health:
            return False
            
        missing_health = self.max_health - self.health
        repair_amount = min(missing_health, 20)  # Repair in chunks of 20
        
        # Calculate resource cost based on repair amount
        scaled_cost = {k: max(1, int(v * (repair_amount / self.max_health))) 
                      for k, v in self.repair_cost.items()}
        
        # Check if player has enough resources
        for resource, amount in scaled_cost.items():
            if player.inventory.get(resource, 0) < amount:
                return False
                
        # Deduct resources and repair
        for resource, amount in scaled_cost.items():
            player.inventory[resource] -= amount
            
        self.health = min(self.max_health, self.health + repair_amount)
        return True

class BuildingSystem:
    """
    Allows player to place or reclaim structures if they have enough resources.
    """
    def __init__(self):
        self.structures = []
        # Basic structure costs
        self.basic_wall_cost = {"scrap": 2}
        self.advanced_turret_cost = {"scrap": 5, "artifact": 1}
        # New structure costs
        self.storage_cost = {"scrap": 3, "wood": 2}
        self.workshop_cost = {"scrap": 4, "wood": 3, "artifact": 1}
        self.collector_cost = {"scrap": 2, "wood": 1}
        self.generator_cost = {"scrap": 5, "artifact": 2}
        
        # Power grid tracking
        self.next_grid_id = 0

    def attempt_placement(self, player, environment, world_x, world_y):
        pressed = pygame.key.get_pressed()
        
        # Structure selection with number keys
        if pressed[pygame.K_1]:  # Basic wall
            if self.check_resources(player, self.basic_wall_cost):
                self.place_structure("Wall", 40, 40, world_x, world_y, environment)
                self.deduct_resources(player, self.basic_wall_cost)
                
        elif pressed[pygame.K_2]:  # Advanced turret
            if self.check_resources(player, self.advanced_turret_cost):
                self.place_structure("Advanced Turret", 40, 40, world_x, world_y, environment)
                self.deduct_resources(player, self.advanced_turret_cost)
                
        elif pressed[pygame.K_3]:  # Storage
            if self.check_resources(player, self.storage_cost):
                self.place_structure("Storage", 60, 60, world_x, world_y, environment)
                self.deduct_resources(player, self.storage_cost)
                
        elif pressed[pygame.K_4]:  # Workshop
            if self.check_resources(player, self.workshop_cost):
                self.place_structure("Workshop", 80, 80, world_x, world_y, environment)
                self.deduct_resources(player, self.workshop_cost)
                
        elif pressed[pygame.K_5]:  # Resource Collector
            if self.check_resources(player, self.collector_cost):
                self.place_structure("Collector", 40, 40, world_x, world_y, environment)
                self.deduct_resources(player, self.collector_cost)
                
        elif pressed[pygame.K_6]:  # Generator
            if self.check_resources(player, self.generator_cost):
                self.place_structure("Generator", 50, 50, world_x, world_y, environment)
                self.deduct_resources(player, self.generator_cost)

        # 1) Reclaim if 'R' is pressed while overlapping a structure
        if pressed[pygame.K_r]:
            self.attempt_reclaim(player, environment)

    def attempt_reclaim(self, player, environment):
        """
        If the player overlaps any structure, remove it and refund resources.
        Simple approach: refund half the cost, or 1:1 if you prefer.
        """
        reclaimed_list = []
        px, py = player.rect.centerx, player.rect.centery

        # We'll check which structure's rect overlaps the player's center
        for s in self.structures:
            srect = pygame.Rect(s.x, s.y, s.width, s.height)
            if srect.collidepoint(px, py):
                # Found a structure we can reclaim
                reclaimed_list.append(s)

        for s in reclaimed_list:
            self.structures.remove(s)
            srect = pygame.Rect(s.x, s.y, s.width, s.height)
            if srect in environment.obstacles:
                environment.obstacles.remove(srect)

            # Refund resources based on structure type
            # If it's a wall, refund basic_wall_cost
            if s.structure_type == "Wall":
                cost = self.basic_wall_cost
            else:
                cost = self.advanced_turret_cost

            # For simplicity, give 100% back. Or use 50% if you want partial.
            for rtype, amt in cost.items():
                player.inventory[rtype] += amt

    def place_structure(self, structure_type, w, h, x, y, environment):
        new_structure = Structure(x, y, w, h, structure_type)
        self.structures.append(new_structure)
        environment.obstacles.append(pygame.Rect(x, y, w, h))

    def check_resources(self, player, cost_dict):
        for rtype, needed in cost_dict.items():
            if player.inventory.get(rtype, 0) < needed:
                return False
        return True

    def deduct_resources(self, player, cost_dict):
        for rtype, needed in cost_dict.items():
            player.inventory[rtype] -= needed
            
    def update_structures(self, dt, player):
        """Update all structures' production and status"""
        # First, update power grids
        self.update_power_grids()
        
        for structure in self.structures:
            # Only operate if structure has power (or is a generator)
            if structure.power_received >= structure.power_required or structure.structure_type == "Generator":
                if structure.structure_type == "Collector":
                    structure.collection_timer += dt
                    if structure.collection_timer >= 5.0:  # Collect every 5 seconds
                        structure.collection_timer = 0
                        # Add resources to player inventory based on collection rate
                        collected = structure.collection_rate
                        player.inventory["scrap"] = player.inventory.get("scrap", 0) + collected
                        
                elif structure.structure_type == "Generator":
                    if structure.active:
                        # Power distribution handled in update_power_grids
                        pass
                        
                elif structure.structure_type == "Workshop":
                    if structure.current_project:
                        # Could implement crafting progress here
                        pass
                    
    def attempt_upgrade(self, player, world_x, world_y):
        """Try to upgrade structure player is standing on"""
        for structure in self.structures:
            if pygame.Rect(structure.x, structure.y, 
                         structure.width, structure.height).collidepoint(world_x, world_y):
                return structure.upgrade(player)
        return False
        
    def attempt_repair(self, player, world_x, world_y):
        """Try to repair structure player is standing on"""
        for structure in self.structures:
            if pygame.Rect(structure.x, structure.y, 
                         structure.width, structure.height).collidepoint(world_x, world_y):
                return structure.repair(player)
        return False
        
    def update_power_grids(self):
        """Update power distribution across all structures"""
        # Reset power received
        for structure in self.structures:
            structure.power_received = 0
            structure.power_grid_id = None
            
        # Assign grid IDs to connected structures
        for structure in self.structures:
            if structure.power_grid_id is None:
                self._flood_fill_power_grid(structure, self.next_grid_id)
                self.next_grid_id += 1
                
        # Calculate and distribute power within each grid
        grid_powers = {}  # grid_id -> (total_output, total_required)
        
        # Sum up power generation and requirements
        for structure in self.structures:
            grid_id = structure.power_grid_id
            if grid_id not in grid_powers:
                grid_powers[grid_id] = [0, 0]  # [output, required]
                
            if structure.structure_type == "Generator" and structure.active:
                grid_powers[grid_id][0] += structure.power_output
            grid_powers[grid_id][1] += structure.power_required
            
        # Distribute available power
        for structure in self.structures:
            grid_id = structure.power_grid_id
            output, required = grid_powers[grid_id]
            
            if required > 0:
                # Distribute power proportionally if not enough for everyone
                power_ratio = min(1.0, output / required)
                structure.power_received = structure.power_required * power_ratio
                
    def _flood_fill_power_grid(self, start_structure, grid_id):
        """Recursively assign grid_id to all connected structures"""
        if start_structure.power_grid_id is not None:
            return
            
        start_structure.power_grid_id = grid_id
        
        # Find all structures in range
        for structure in self.structures:
            if structure.power_grid_id is None:
                dx = structure.x - start_structure.x
                dy = structure.y - start_structure.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= start_structure.power_range:
                    self._flood_fill_power_grid(structure, grid_id)
