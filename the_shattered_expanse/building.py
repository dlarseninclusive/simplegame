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
        
        # Structure-specific attributes
        if structure_type == "Storage":
            self.capacity = 100 * self.level
            self.stored = 0
        elif structure_type == "Generator":
            self.power_output = 10 * self.level
            self.active = True
        elif structure_type == "Collector":
            self.collection_rate = 1 * self.level
            self.collection_timer = 0
        elif structure_type == "Workshop":
            self.production_speed = 1 * self.level
            self.current_project = None

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
