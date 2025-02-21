import pygame
import random
import math
from npc import NPC  # Import NPC class
from resource import ResourceNode  # Import ResourceNode class

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

    def generate_city_buildings(self, faction_name, environment):
        """
        Create a collection of buildings for a specific faction with strategic placement.
        
        :param faction_name: Name of the faction to generate buildings for
        :param environment: Environment object to check for collisions
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
                    
                    # Randomize building size
                    min_size, max_size = faction_config["size_range"]
                    building_size = random.randint(min_size, max_size)
                    
                    # Create building sprite
                    building_sprite = pygame.Surface((building_size, building_size), pygame.SRCALPHA)
                    building_color = faction_config["color"]
                    
                    # Check for collisions with existing buildings
                    new_building_rect = pygame.Rect(bx, by, building_size, building_size)
                    if any(new_building_rect.colliderect(b.rect) for b in buildings):
                        continue  # Skip if there's a collision
                    
                    # Specialized building rendering
                    if 'defense_tower' in faction_config['types'] and random.random() < defense_priority:
                        building_type = 'defense_tower'
                        pygame.draw.rect(building_sprite, building_color, 
                                         (0, 0, building_size, building_size))
                        pygame.draw.rect(building_sprite, (255, 0, 0), 
                                         (building_size//4, 0, building_size//2, building_size), 2)
                    elif 'trading_post' in faction_config['types']:
                        building_type = 'trading_post'
                        pygame.draw.circle(building_sprite, building_color, 
                                           (building_size//2, building_size//2), building_size//2)
                        pygame.draw.circle(building_sprite, (0, 255, 0), 
                                           (building_size//2, building_size//2), building_size//3, 2)
                    else:
                        building_type = random.choice(faction_config['types'])
                        building_sprite.fill(building_color)
                    
                    # Create sprite
                    building = pygame.sprite.Sprite()
                    building.image = building_sprite
                    building.rect = new_building_rect
                    building.type = building_type
                    
                    building.is_shop = True
                    building.sign_text = f"{faction_name} Shop"
                    door_width = int(new_building_rect.width * 0.4)
                    door_height = 10
                    building.door_rect = pygame.Rect(
                        new_building_rect.x + (new_building_rect.width - door_width) // 2,
                        new_building_rect.y + new_building_rect.height - door_height,
                        door_width,
                        door_height
                    )
                    building.interior_map = self.generate_interior_map(building)
                    
                    buildings.add(building)
                    environment.add_obstacle(bx, by, building_size, building_size)  # Add to environment obstacles
        
        return buildings

    def generate_city_npcs(self, faction_name):
        """
        Generate NPCs for a specific faction.
        
        :param faction_name: Name of the faction to generate NPCs for
        :return: List of NPCs
        """
        npcs = []
        faction_config = self.building_types.get(faction_name, {})
        
        if not faction_config:
            return npcs

        npc_types = faction_config.get("npc_types", [])
        for _ in range(random.randint(5, 15)):  # Random number of NPCs per city
            npc_type = random.choice(npc_types)
            # If the faction is meant to have vendors, randomly choose some NPCs as shopkeepers.
            is_vendor = random.random() < 0.3
            npc = NPC(random.randint(0, self.world_width), random.randint(0, self.world_height),
                      faction=faction_name, enemy_type=npc_type)
            if is_vendor:
                npc.is_shopkeeper = True
                npc.hostile = False
            npcs.append(npc)
        
        return npcs

    def generate_interior_map(self, building, environment=None):
        """
        Generate and return an interior map for a building.
        This could be a new Surface or a new Environment instance.
        For example, create a simple room with a basement staircase.
        """
        # Create a smaller interior room (300x200) with a black background
        interior = pygame.Surface((300, 200))
        interior.fill((0, 0, 0))  # black background

        # Define interior walls (in the interior's local coordinate space)
        building.interior_walls = [
            pygame.Rect(0, 0, 300, 10),    # Top wall
            pygame.Rect(0, 0, 10, 200),    # Left wall
            pygame.Rect(290, 0, 10, 200),  # Right wall
            pygame.Rect(0, 190, 300, 10)   # Bottom wall
        ]

        # Add interior walls to environment obstacles if environment is provided
        if environment is not None:
            for wall in building.interior_walls:
                environment.add_obstacle(wall.x, wall.y, wall.width, wall.height)

        # Also define a specific 'interior_door_rect' near the bottom
        # so we know exactly where to place the player when they enter.
        building.interior_door_rect = pygame.Rect(
            130, 180,   # X, Y inside the 300x200 interior
            40,  20     # width, height
        )

        return interior
    
    def generate_city_resources(self, faction_name):
        """
        Generate resources for a specific faction.
        
        :param faction_name: Name of the faction to generate resources for
        :return: List of resource nodes
        """
        resources = []
        faction_config = self.building_types.get(faction_name, {})
        
        if not faction_config:
            return resources

        resource_bias = faction_config.get("resource_bias", {})
        for resource_type, bias in resource_bias.items():
            if random.random() < bias:
                x = random.randint(0, self.world_width)
                y = random.randint(0, self.world_height)
                resources.append(ResourceNode(x, y, 40, 40, resource_type))
        
        return resources

    def generate_roads(self, city_centers):
        """
        Generate road segments connecting city centers with pathfinding and terrain consideration.
        
        :param city_centers: List of city center coordinates
        :return: List of road segments with waypoints
        """
        roads = []
        
        # Use A* pathfinding to create road paths
        for i in range(len(city_centers) - 1):
            start = city_centers[i]
            end = city_centers[i+1]
            
            # Add some randomness and terrain-following behavior
            road_segment = self._create_road_segment(start, end)
            roads.append(road_segment)
        
        return roads

    def _create_road_segment(self, start, end, max_deviation=100):
        """
        Create a road segment between two points with some natural curvature.
        
        :param start: Starting point coordinates
        :param end: Ending point coordinates
        :param max_deviation: Maximum allowed deviation from straight line
        :return: List of waypoints forming the road
        """
        road_points = [start]
        
        # Add intermediate points with some randomness
        mid_x = (start[0] + end[0]) / 2 + random.randint(-max_deviation, max_deviation)
        mid_y = (start[1] + end[1]) / 2 + random.randint(-max_deviation, max_deviation)
        
        # Create a curved road segment with 2-3 intermediate points
        road_points.extend([
            (mid_x, start[1]),  # First waypoint
            (mid_x, mid_y),     # Middle waypoint
            (end[0], mid_y),    # Third waypoint
            end
        ])
        
        return road_points
