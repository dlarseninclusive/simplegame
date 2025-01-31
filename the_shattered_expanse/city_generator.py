import pygame
import random
import math

class CityGenerator:
    """
    Generates detailed city structures for different factions.
    Provides methods to create city buildings, territories, roads, and visual representations.
    """
    def __init__(self, world_width=4000, world_height=4000):
        self.world_width = world_width
        self.world_height = world_height
        
        # Building type configurations
        self.building_types = {
            "Automatons": {
                "types": ["generator", "storage", "workshop", "defense_tower", "research_lab", "power_station"],
                "color": (100, 100, 255),  # Blue-ish
                "size_range": (40, 100),
                "npc_types": ["scout", "ranged", "heavy"],
                "resource_bias": {"scrap": 0.5, "artifact": 0.3, "water": 0.2}
            },
            "Scavengers": {
                "types": ["shelter", "workshop", "trading_post", "watchtower", "storage", "repair_bay"],
                "color": (255, 150, 50),   # Orange-ish
                "size_range": (30, 90),
                "npc_types": ["warrior", "trader", "scout"],
                "resource_bias": {"scrap": 0.4, "food": 0.3, "water": 0.3}
            },
            "Cog Preachers": {
                "types": ["shrine", "library", "workshop", "meditation_center", "research_station", "archive"],
                "color": (150, 50, 150),   # Purple-ish
                "size_range": (50, 110),
                "npc_types": ["scholar", "priest", "guardian"],
                "resource_bias": {"artifact": 0.5, "scrap": 0.3, "water": 0.2}
            }
        }
        
        # Road configuration
        self.road_color = (100, 100, 100)  # Gray roads
        self.road_width = 20
        
        # City layout parameters
        self.city_layout_params = {
            "Automatons": {
                "grid_spacing": 60,
                "building_density": 0.7,
                "defense_priority": 0.3
            },
            "Scavengers": {
                "grid_spacing": 50,
                "building_density": 0.6,
                "defense_priority": 0.2
            },
            "Cog Preachers": {
                "grid_spacing": 70,
                "building_density": 0.5,
                "defense_priority": 0.1
            }
        }

    def generate_city_buildings(self, faction_name):
        """
        Create a collection of buildings for a specific faction with strategic placement.
        
        :param faction_name: Name of the faction to generate buildings for
        :return: pygame.sprite.Group of city buildings
        """
        buildings = pygame.sprite.Group()
        faction_config = self.building_types.get(faction_name, {})
        layout_params = self.city_layout_params.get(faction_name, {})
        
        if not faction_config or not layout_params:
            return buildings

        # City center location (from factions.py)
        city_data = {
            "Automatons": (self.world_width - 300, self.world_height - 300),
            "Scavengers": (100, 100),
            "Cog Preachers": (self.world_width // 2 - 125, self.world_height // 2 - 125)
        }
        
        city_center = city_data.get(faction_name, (0, 0))
        grid_spacing = layout_params.get('grid_spacing', 50)
        building_density = layout_params.get('building_density', 0.6)
        defense_priority = layout_params.get('defense_priority', 0.2)
        
        # Generate grid-based city layout
        grid_width = int(math.sqrt(len(faction_config['types']) * 10))
        grid_height = grid_width
        
        for x in range(grid_width):
            for y in range(grid_height):
                # Probabilistic building placement
                if random.random() < building_density:
                    # Calculate grid-based position
                    bx = city_center[0] + (x - grid_width//2) * grid_spacing
                    by = city_center[1] + (y - grid_height//2) * grid_spacing
                    
                    # Weighted building type selection
                    if random.random() < defense_priority and 'defense_tower' in faction_config['types']:
                        building_type = 'defense_tower'
                    else:
                        building_type = random.choice(faction_config['types'])
                    
                    # Randomize building size
                    min_size, max_size = faction_config["size_range"]
                    building_size = random.randint(min_size, max_size)
                    
                    # Create building sprite
                    building_sprite = pygame.Surface((building_size, building_size), pygame.SRCALPHA)
                    building_color = faction_config["color"]
                    
                    # Specialized building rendering
                    if building_type == "defense_tower":
                        pygame.draw.rect(building_sprite, building_color, 
                                         (0, 0, building_size, building_size))
                        pygame.draw.rect(building_sprite, (255, 0, 0), 
                                         (building_size//4, 0, building_size//2, building_size), 2)
                    elif building_type == "trading_post":
                        pygame.draw.circle(building_sprite, building_color, 
                                           (building_size//2, building_size//2), building_size//2)
                        pygame.draw.circle(building_sprite, (0, 255, 0), 
                                           (building_size//2, building_size//2), building_size//3, 2)
                    else:
                        building_sprite.fill(building_color)
                    
                    # Create sprite
                    building = pygame.sprite.Sprite()
                    building.image = building_sprite
                    building.rect = building_sprite.get_rect(topleft=(bx, by))
                    building.type = building_type
                    
                    buildings.add(building)
        
        return buildings

    def generate_city_npcs(self, faction_name, num_npcs=20):
        """
        Generate NPCs for a specific faction's city.
        
        :param faction_name: Name of the faction
        :param num_npcs: Number of NPCs to generate
        :return: List of NPCs
        """
        from npc import NPC  # Import here to avoid circular import
        
        faction_config = self.building_types.get(faction_name, {})
        city_data = {
            "Automatons": (self.world_width - 300, self.world_height - 300),
            "Scavengers": (100, 100),
            "Cog Preachers": (self.world_width // 2 - 125, self.world_height // 2 - 125)
        }
        
        city_center = city_data.get(faction_name, (0, 0))
        npcs = []
        
        for _ in range(num_npcs):
            # Randomize NPC position within city bounds
            nx = city_center[0] + random.randint(-250, 250)
            ny = city_center[1] + random.randint(-250, 250)
            
            # Select NPC type based on faction
            npc_type = random.choice(faction_config.get('npc_types', ['warrior']))
            
            npc = NPC(nx, ny, faction=faction_name, group_id=1, enemy_type=npc_type)
            npcs.append(npc)
        
        return npcs

    def generate_city_resources(self, faction_name):
        """
        Generate resource nodes specific to a faction's city.
        
        :param faction_name: Name of the faction
        :return: List of resource nodes
        """
        from resource import ResourceNode
        
        faction_config = self.building_types.get(faction_name, {})
        city_data = {
            "Automatons": (self.world_width - 300, self.world_height - 300),
            "Scavengers": (100, 100),
            "Cog Preachers": (self.world_width // 2 - 125, self.world_height // 2 - 125)
        }
        
        city_center = city_data.get(faction_name, (0, 0))
        resources = []
        
        # Generate resources based on faction's resource bias
        resource_bias = faction_config.get('resource_bias', {})
        for resource, bias in resource_bias.items():
            num_nodes = int(10 * bias)  # Scale number of nodes by bias
            for _ in range(num_nodes):
                rx = city_center[0] + random.randint(-250, 250)
                ry = city_center[1] + random.randint(-250, 250)
                
                resource_node = ResourceNode(rx, ry, 40, 40, resource)
                resources.append(resource_node)
        
        return resources

    def generate_city_territories(self, factions_data):
        """
        Generate territories for each faction based on their city location.
        
        :param factions_data: Dictionary of faction data from Factions class
        :return: Dictionary of faction territories
        """
        territories = {}
        
        for faction, data in factions_data.items():
            city = data.get('city', {})
            location = city.get('location', (0, 0))
            size = city.get('size', (500, 500))
            
            # Create territory around city center
            territory = (
                location[0] - size[0]//2, 
                location[1] - size[1]//2, 
                size[0] * 2, 
                size[1] * 2
            )
            
            territories[faction] = territory
        
        return territories

    def generate_inter_city_roads(self, factions_data):
        """
        Generate roads connecting different faction cities.
        
        :param factions_data: Dictionary of faction data from Factions class
        :return: List of road segments
        """
        roads = []
        city_locations = [
            data['city']['location'] for data in factions_data.values()
        ]
        
        # Connect all cities with roads
        for i in range(len(city_locations)):
            for j in range(i+1, len(city_locations)):
                start = city_locations[i]
                end = city_locations[j]
                roads.append((start, end))
        
        return roads

    def generate_city_internal_roads(self, faction_name, buildings):
        """
        Generate internal roads within a city connecting buildings.
        
        :param faction_name: Name of the faction
        :param buildings: Sprite group of buildings in the city
        :return: List of road segments
        """
        roads = []
        building_list = list(buildings)
        
        # Connect buildings with roads
        for i in range(len(building_list)):
            for j in range(i+1, len(building_list)):
                b1, b2 = building_list[i], building_list[j]
                roads.append((b1.rect.center, b2.rect.center))
        
        return roads

    def draw_roads(self, screen, roads, camera_offset):
        """
        Draw roads on the screen.
        
        :param screen: Pygame screen surface
        :param roads: List of road segments
        :param camera_offset: Camera offset for world rendering
        """
        for start, end in roads:
            start_x = start[0] - camera_offset[0]
            start_y = start[1] - camera_offset[1]
            end_x = end[0] - camera_offset[0]
            end_y = end[1] - camera_offset[1]
            
            pygame.draw.line(screen, self.road_color, 
                             (start_x, start_y), 
                             (end_x, end_y), 
                             self.road_width)
