import pygame

# Define colors for different enemy types
ENEMY_COLORS = {
    "scout": (255, 165, 0),     # Orange
    "warrior": (255, 0, 0),     # Red
    "heavy": (139, 0, 0),       # Dark Red
    "ranged": (148, 0, 211),    # Purple
    "boss": (255, 215, 0)       # Gold
}

# Define enemy stats
ENEMY_STATS = {
    "scout": {
        "health": 50,
        "speed": 150,
        "damage": 5,
        "size": 25
    },
    "warrior": {
        "health": 100,
        "speed": 100,
        "damage": 15,
        "size": 32
    },
    "heavy": {
        "health": 200,
        "speed": 50,
        "damage": 25,
        "size": 40
    },
    "ranged": {
        "health": 75,
        "speed": 80,
        "damage": 10,
        "size": 28
    },
    "boss": {
        "health": 500,
        "speed": 60,
        "damage": 40,
        "size": 50
    }
}

def create_player_sprite():
    """Create a more detailed player sprite"""
    size = 32
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Main body (red)
    pygame.draw.circle(surface, (178, 34, 34), (size//2, size//2), size//2)
    
    # Armor details (darker red)
    pygame.draw.arc(surface, (139, 0, 0), (4, 4, size-8, size-8), 0, 3.14, 3)
    pygame.draw.arc(surface, (139, 0, 0), (4, 4, size-8, size-8), 3.14, 6.28, 3)
    
    # Center highlight (lighter red)
    pygame.draw.circle(surface, (205, 92, 92), (size//2, size//2), size//6)
    
    return surface

def create_enemy_sprite(enemy_type):
    """Create enemy sprite based on type"""
    stats = ENEMY_STATS[enemy_type]
    size = stats["size"]
    color = ENEMY_COLORS[enemy_type]
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    if enemy_type == "scout":
        # Triangle shape for scouts
        points = [(size//2, 0), (0, size), (size, size)]
        pygame.draw.polygon(surface, color, points)
        
    elif enemy_type == "warrior":
        # Square with details for warriors
        pygame.draw.rect(surface, color, (0, 0, size, size))
        pygame.draw.line(surface, (0, 0, 0), (0, size//2), (size, size//2), 2)
        
    elif enemy_type == "heavy":
        # Hexagon shape for heavy units
        points = [
            (size//4, 0), (3*size//4, 0),
            (size, size//2),
            (3*size//4, size), (size//4, size),
            (0, size//2)
        ]
        pygame.draw.polygon(surface, color, points)
        
    elif enemy_type == "ranged":
        # Diamond shape for ranged units
        points = [(size//2, 0), (size, size//2), (size//2, size), (0, size//2)]
        pygame.draw.polygon(surface, color, points)
        
    elif enemy_type == "boss":
        # Star shape for boss
        pygame.draw.circle(surface, color, (size//2, size//2), size//2)
        points = []
        for i in range(5):
            angle = i * 2 * 3.14159 / 5 - 3.14159 / 2
            points.append((
                size//2 + int(size//2 * 0.9 * pygame.math.cos(angle)),
                size//2 + int(size//2 * 0.9 * pygame.math.sin(angle))
            ))
        pygame.draw.polygon(surface, (255, 255, 0), points, 3)
    
    return surface
