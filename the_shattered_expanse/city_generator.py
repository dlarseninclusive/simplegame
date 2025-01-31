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
                "types": ["generator", "storage", "workshop", "defense_tower"],
                "color": (100, 100, 255),  # Blue-ish
                "size_range": (40, 80)
            },
            "Scavengers": {
                "types": ["shelter", "workshop", "trading_post", "watchtower"],
                "color": (255, 150, 50),   # Orange-ish
                "size_range": (30, 70)
            },
            "Cog Preachers": {
                "types": ["shrine", "library", "workshop", "meditation_center"],
                "color": (150, 50, 150),   # Purple-ish
                "size_range": (50, 90)
            }
        }
        
        # Road configuration
        self.road_color = (100, 100, 100)  # Gray roads
        self.road_width = 20

    def generate_city_buildings(self, faction_name):
        """
        Create a collection of buildings for a specific faction.
        
        :param faction_name: Name of the faction to generate buildings for
        :return: pygame.sprite.Group of city buildings
        """
        buildings = pygame.sprite.Group()
        faction_config = self.building_types.get(faction_name, {})
        
        if not faction_config:
            return buildings

        # City center location (from factions.py)
        city_data = {
            "Automatons": (self.world_width - 300, self.world_height - 300),
            "Scavengers": (100, 100),
            "Cog Preachers": (self.world_width // 2 - 125, self.world_height // 2 - 125)
        }
        
        city_center = city_data.get(faction_name, (0, 0))
        
        # Generate 10-15 buildings per city
        num_buildings = random.randint(10, 15)
        
        for _ in range(num_buildings):
            # Randomize building position within city bounds
            bx = city_center[0] + random.randint(-200, 200)
            by = city_center[1] + random.randint(-200, 200)
            
            # Randomize building size and type
            building_type = random.choice(faction_config["types"])
            min_size, max_size = faction_config["size_range"]
            building_size = random.randint(min_size, max_size)
            
            # Create building sprite
            building_sprite = pygame.Surface((building_size, building_size))
            building_sprite.fill(faction_config["color"])
            
            # Create building sprite with slight variation
            if building_type == "defense_tower":
                pygame.draw.rect(building_sprite, (255, 0, 0), 
                                 (building_size//4, 0, building_size//2, building_size), 2)
            elif building_type == "trading_post":
                pygame.draw.circle(building_sprite, (0, 255, 0), 
                                   (building_size//2, building_size//2), building_size//3, 2)
            
            # Create sprite
            building = pygame.sprite.Sprite()
            building.image = building_sprite
            building.rect = building_sprite.get_rect(topleft=(bx, by))
            building.type = building_type
            
            buildings.add(building)
        
        return buildings

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
