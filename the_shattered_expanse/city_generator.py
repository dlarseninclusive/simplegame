import pygame
import random

class CityGenerator:
    """
    Generates detailed city structures for different factions.
    Provides methods to create city buildings, territories, and visual representations.
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
