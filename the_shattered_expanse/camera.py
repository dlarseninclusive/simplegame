# camera.py

class Camera:
    """
    A simple camera to track the player in a large environment.
    """
    def __init__(self, world_width, world_height, screen_width, screen_height):
        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset_x = 0
        self.offset_y = 0

    def update(self, target_x, target_y):
        self.offset_x = target_x - self.screen_width // 2
        self.offset_y = target_y - self.screen_height // 2

        if self.offset_x < 0:
            self.offset_x = 0
        if self.offset_y < 0:
            self.offset_y = 0

        max_x = self.world_width - self.screen_width
        max_y = self.world_height - self.screen_height

        if self.offset_x > max_x:
            self.offset_x = max_x
        if self.offset_y > max_y:
            self.offset_y = max_y
