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
        self.is_shop = False
        self.sign_text = ""
        self.door_rect = pygame.Rect(x, y, 0, 0)  # default; to be updated by city_generator
        
        # Power system attributes
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.upgrade_cost = {"scrap": 5, "artifact": 1}
        self.repair_cost = {"scrap": 1}
        
        # New attributes for shop and door
        self.door_rect = pygame.Rect(x, y, 0, 0)  # will be set later by city_generator
        self.sign_text = ""
        self.is_shop = False
        
        # Power system attributes
        self.power_required = 0
        self.power_received = 0
        self.power_grid_id = None  # Structures on same grid share power
        self.power_range = 100  # How far power can transmit
        
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
    Enhanced with more building types and strategic placement logic.
    """
    def __init__(self):
        self.structures = []
        
        # Predefined building costs and requirements
        self.building_costs = {
            "Generator": {"scrap": 50, "artifact": 1},
            "Storage": {"scrap": 30, "wood": 20},
            "Workshop": {"scrap": 75, "artifact": 2},
            "Collector": {"scrap": 25, "water": 10},
            "Turret": {"scrap": 40, "artifact": 1},
            "Wall": {"scrap": 20},
            "Research Station": {"scrap": 100, "artifact": 3},
            "Repair Bay": {"scrap": 60, "water": 20},
            "Communication Tower": {"scrap": 80, "artifact": 2},
            "Power Relay": {"scrap": 45, "artifact": 1}
        }
        
        # Add power grid timer
        self.power_grid_timer = 0
        
        # Strategic placement zones
        self.strategic_zones = {
            "south": (0, 4000, 2500, 4000),     # Southern region
            "north": (0, 4000, 0, 1500),        # Northern region
            "east": (2500, 4000, 0, 4000),      # Eastern region
            "west": (0, 1500, 0, 4000)          # Western region
        }
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
        # Get structure size first
        size = (40, 40)  # default size
        structure_type = None
        cost = None
        
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_1]:
            structure_type = "Wall"
            cost = self.basic_wall_cost
            size = (40, 40)
        elif pressed[pygame.K_2]:
            structure_type = "Advanced Turret"
            cost = self.advanced_turret_cost
            size = (40, 40)
        elif pressed[pygame.K_3]:
            structure_type = "Storage"
            cost = self.storage_cost
            size = (60, 60)
        elif pressed[pygame.K_4]:
            structure_type = "Workshop"
            cost = self.workshop_cost
            size = (80, 80)
        elif pressed[pygame.K_5]:
            structure_type = "Collector"
            cost = self.collector_cost
            size = (40, 40)
        elif pressed[pygame.K_6]:
            structure_type = "Generator"
            cost = self.generator_cost
            size = (50, 50)
            
        # Adjust position to center the structure on the mouse
        world_x -= size[0] // 2
        world_y -= size[1] // 2
        
        # Debug output
        print(f"\nAttempting placement at ({world_x}, {world_y})")
        print(f"Player inventory: {player.inventory}")
        
        # Get the current key states
        pressed = pygame.key.get_pressed()
        

        if structure_type and cost:
            print(f"Attempting to place {structure_type}")
            if self.check_resources(player, cost):
                if self.place_structure(structure_type, size[0], size[1], world_x, world_y, environment):
                    self.deduct_resources(player, cost)
                    print(f"Successfully placed {structure_type}")
            else:
                print(f"Not enough resources for {structure_type}. Need: {cost}")

        # 1) Reclaim if 'R' is pressed while overlapping a structure
        if pressed[pygame.K_r]:
            self.attempt_reclaim(player, environment)

    def attempt_reclaim(self, player, environment):
        """
        If the player overlaps any structure, remove it and refund resources.
        Improved to check player's entire rect for overlap.
        """
        reclaimed_list = []

        # Check which structure's rect overlaps the player's rect
        for s in self.structures:
            srect = pygame.Rect(s.x, s.y, s.width, s.height)
            if srect.colliderect(player.rect):
                # Found a structure we can reclaim
                reclaimed_list.append(s)

        for s in reclaimed_list:
            # Remove from structures list
            self.structures.remove(s)
            
            # Remove from environment obstacles
            obs_rect = pygame.Rect(s.x, s.y, s.width, s.height)
            if obs_rect in environment.obstacles:
                environment.obstacles.remove(obs_rect)

            # Determine cost based on structure type
            cost_map = {
                "Wall": self.basic_wall_cost,
                "Advanced Turret": self.advanced_turret_cost,
                "Storage": self.storage_cost,
                "Workshop": self.workshop_cost,
                "Collector": self.collector_cost,
                "Generator": self.generator_cost
            }

            # Get the cost, defaulting to an empty dict if not found
            cost = cost_map.get(s.structure_type, {})

            # Refund resources (full refund)
            for rtype, amt in cost.items():
                player.inventory[rtype] = player.inventory.get(rtype, 0) + amt

            print(f"Reclaimed {s.structure_type} structure")

    def place_structure(self, structure_type, w, h, x, y, environment):
        print(f"Placing {structure_type} at ({x}, {y})")
        
        # Check if position is valid
        new_rect = pygame.Rect(x, y, w, h)
        
        # Check for overlapping structures
        for structure in self.structures:
            if pygame.Rect(structure.x, structure.y, 
                         structure.width, structure.height).colliderect(new_rect):
                print(f"Cannot place: overlaps existing structure")
                return False
                
        # Check if within world bounds (4000x4000 world)
        if x < 0 or y < 0 or x + w > 4000 or y + h > 4000:
            print(f"Cannot place: outside world bounds")
            return False
            
        new_structure = Structure(x, y, w, h, structure_type)
        self.structures.append(new_structure)
        environment.obstacles.append(new_rect)
        print(f"Successfully placed {structure_type}")
        return True

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
        # Update power grids only once per second
        self.power_grid_timer += dt
        if self.power_grid_timer >= 1.0:
            self.update_power_grids()
            self.power_grid_timer = 0
        
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
