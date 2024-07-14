import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("City-State Prototype")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# City class
class City:
    def __init__(self, name):
        self.name = name
        self.districts = []
        self.crime_rate = 0
        self.police_effectiveness = 0.5

    def update(self):
        total_crime = sum(district.crime_rate for district in self.districts)
        self.crime_rate = total_crime / len(self.districts) if self.districts else 0
        
        for district in self.districts:
            district.update(self.police_effectiveness)

# District class
class District:
    def __init__(self, name, x, y, width, height):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.crime_rate = random.uniform(0, 1)
        self.color = self.get_color()

    def update(self, police_effectiveness):
        crime_change = random.uniform(-0.1, 0.1) - (self.crime_rate * police_effectiveness * 0.1)
        self.crime_rate = max(0, min(1, self.crime_rate + crime_change))
        self.color = self.get_color()

    def get_color(self):
        r = int(self.crime_rate * 255)
        g = int((1 - self.crime_rate) * 255)
        return (r, g, 0)

# Create city and districts
city = City("Neon Harbor")
district_width, district_height = 150, 150
districts = [
    District("Downtown", 100, 100, district_width, district_height),
    District("Industrial Zone", 300, 100, district_width, district_height),
    District("Residential Area", 100, 300, district_width, district_height),
    District("Commerce District", 300, 300, district_width, district_height)
]
city.districts = districts

# Font setup
font = pygame.font.Font(None, 24)

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update city
    city.update()

    # Clear the screen
    screen.fill(WHITE)

    # Draw districts
    for district in city.districts:
        pygame.draw.rect(screen, district.color, district.rect)
        name_text = font.render(district.name, True, BLACK)
        screen.blit(name_text, (district.rect.x + 5, district.rect.y + 5))
        crime_text = font.render(f"Crime: {district.crime_rate:.2f}", True, BLACK)
        screen.blit(crime_text, (district.rect.x + 5, district.rect.y + 25))

    # Display city information
    city_info = font.render(f"{city.name} - Overall Crime Rate: {city.crime_rate:.2f}", True, BLACK)
    screen.blit(city_info, (10, 10))

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()