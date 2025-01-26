import pygame

RESOURCE_DATA = {
    "scrap": {
        "display_name": "Scrap Metal",
        "value": 1,
        "description": "Rusted metal bits for forging or trading."
    },
    "water": {
        "display_name": "Fresh Water",
        "value": 2,
        "thirst_recovery": 30,
        "description": "Essential for survival."
    },
    "food": {
        "display_name": "Dried Rations",
        "value": 3,
        "hunger_recovery": 20,
        "description": "Basic sustenance."
    },
    "artifact": {
        "display_name": "Ancient Artifact",
        "value": 10,
        "description": "Relic from the Architects."
    }
}

class ResourceNode:
    """
    Collectible resource node with respawn logic.
    """
    def __init__(self, x, y, width, height, resource_type):
        self.rect = pygame.Rect(x, y, width, height)
        self.resource_type = resource_type
        self.collected = False

        # 1) Respawn timer
        self.respawn_time = 30.0  # seconds
        self.current_timer = 0.0

    @property
    def data(self):
        return RESOURCE_DATA.get(self.resource_type, {})

    def update(self, dt):
        """
        If collected, increment the timer. Once it hits respawn_time, reset.
        """
        if self.collected:
            self.current_timer += dt
            if self.current_timer >= self.respawn_time:
                self.collected = False
                self.current_timer = 0.0
