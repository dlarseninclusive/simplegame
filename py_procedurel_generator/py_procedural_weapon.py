import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Blacksmith's Weapon Generator")

# Colors
BLACK = (0, 0, 0)
BLADE_COLORS = [(192, 192, 192), (160, 160, 160), (128, 128, 128), (224, 224, 224)]
HANDLE_COLORS = [(139, 69, 19), (101, 67, 33), (85, 57, 28), (32, 32, 32), (48, 48, 48), (64, 64, 64)]
GUARD_COLORS = [(218, 165, 32), (184, 134, 11), (205, 127, 50)]
BOLSTER_COLORS = [(255, 215, 0), (218, 165, 32), (205, 127, 50)]
OUTLINE_COLOR = (20, 20, 20)
BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (150, 150, 150)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Font setup
font = pygame.font.Font(None, 24)

class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False

    def draw(self, surface):
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BUTTON_TEXT_COLOR, self.rect, 2)
        text_surface = font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return self.action()
        return None

def generate_background():
    """Generate the background surface."""
    background = pygame.Surface((width, height))
    background.fill((50, 30, 20))  # Dark brown background
    pygame.draw.rect(background, (100, 60, 20), (50, 400, 700, 200))  # Wooden floor
    pygame.draw.rect(background, (80, 80, 80), (100, 100, 200, 200))  # Forge
    pygame.draw.rect(background, (120, 80, 40), (500, 150, 200, 250))  # Workbench
    pygame.draw.rect(background, (60, 60, 60), (550, 200, 100, 20))  # Hammer
    pygame.draw.polygon(background, (80, 80, 80), [(680, 250), (700, 270), (660, 270)])  # Anvil
    return background

def smooth_points(points, smoothness=0.2):
    """Smooth the points of a polygon."""
    smoothed = []
    for i in range(len(points)):
        prev = points[i-1]
        curr = points[i]
        next = points[(i+1) % len(points)]
        smoothed_x = curr[0] + smoothness * (prev[0] + next[0] - 2 * curr[0])
        smoothed_y = curr[1] + smoothness * (prev[1] + next[1] - 2 * curr[1])
        smoothed.append((smoothed_x, smoothed_y))
    return smoothed

def generate_european_bolster(blade_width, y_position):
    """Generate the points for a European-style bolster."""
    width = blade_width * 1.5
    height = blade_width * 0.5
    return [
        (-width/2, y_position),
        (width/2, y_position),
        (width/2, y_position + height),
        (-width/2, y_position + height)
    ]

def generate_japanese_bolster(blade_width, y_position):
    """Generate the points for a Japanese-style bolster."""
    width = blade_width * 1.2
    height = blade_width * 0.3
    return [
        (-width/2, y_position),
        (width/2, y_position),
        (blade_width/2, y_position + height),
        (-blade_width/2, y_position + height)
    ]

def generate_chinese_bolster(blade_width, y_position):
    """Generate the points for a Chinese-style bolster."""
    width = blade_width * 1.8
    height = blade_width * 0.4
    return [
        (-width/2, y_position),
        (width/2, y_position),
        (width/3, y_position + height),
        (-width/3, y_position + height)
    ]

def generate_sword():
    """Generate a sword."""
    blade_length = random.randint(300, 400)
    blade_width = random.randint(20, 30)
    guard_width = random.randint(60, 80)
    handle_length = random.randint(80, 100)

    # Improved blade points
    blade_points = [
        (0, 0),  # Tip
        (-blade_width//4, blade_length//4),
        (-blade_width//2, blade_length//2),
        (-blade_width//2, blade_length),
        (blade_width//2, blade_length),
        (blade_width//2, blade_length//2),
        (blade_width//4, blade_length//4),
    ]

    # Add randomness to blade edge
    for i in range(1, len(blade_points) - 1):
        x, y = blade_points[i]
        blade_points[i] = (x + random.randint(-3, 3), y + random.randint(-5, 5))

    blade_points = smooth_points(blade_points)

    # Guard points (now connected to the blade)
    guard_points = [
        (-blade_width//2, blade_length),  # Connect to left side of blade
        (-guard_width//2, blade_length),
        (-guard_width//2, blade_length + 15),
        (guard_width//2, blade_length + 15),
        (guard_width//2, blade_length),
        (blade_width//2, blade_length),  # Connect to right side of blade
    ]

    # Bolster
    bolster_style = random.choice(["european", "japanese", "chinese"])
    if bolster_style == "european":
        bolster_points = generate_european_bolster(blade_width, blade_length + 15)
    elif bolster_style == "japanese":
        bolster_points = generate_japanese_bolster(blade_width, blade_length + 15)
    else:
        bolster_points = generate_chinese_bolster(blade_width, blade_length + 15)

    # Improved handle points (now connected to the bolster)
    handle_start = blade_length + 15 + max([point[1] for point in bolster_points]) - blade_length  # Align handle start to bolster
    handle_segments = random.randint(5, 7)
    handle_points = [(-blade_width//3, handle_start), (blade_width//3, handle_start)]  # Start at blade width
    for i in range(1, handle_segments):
        y = handle_start + (handle_length * i // handle_segments)
        left_x = -blade_width//4 + random.randint(-2, 2)
        right_x = blade_width//4 + random.randint(-2, 2)
        handle_points.extend([(left_x, y), (right_x, y)])
    
    # Add grip details
    grip_details = []
    for i in range(1, handle_segments):
        y = handle_start + (handle_length * i // handle_segments) - handle_length // (2 * handle_segments)
        left_x = -blade_width//4 + random.randint(-1, 1)
        right_x = blade_width//4 + random.randint(-1, 1)
        grip_details.extend([(left_x, y), (right_x, y)])

    handle_points.extend([
        (blade_width//3, handle_start + handle_length),
        (-blade_width//3, handle_start + handle_length)
    ])

    handle_points = smooth_points(handle_points)

    # Pommel points
    pommel_radius = blade_width // 2
    pommel_center = (0, handle_start + handle_length + pommel_radius)
    pommel_points = [
        (pommel_center[0] + pommel_radius * math.cos(angle),
         pommel_center[1] + pommel_radius * math.sin(angle))
        for angle in [math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4]
    ]

    # Generate stats
    damage = random.randint(10, 20)
    speed = round(20 - damage * 0.5 + random.uniform(-1, 1), 1)
    durability = random.randint(50, 100)
    dps = round(damage * speed / 10, 1)
    value = int((damage * 50 + speed * 30 + durability * 20 + dps * 100) * random.uniform(0.8, 1.2))

    stats = {
        "Type": "Sword",
        "Style": bolster_style.capitalize(),
        "Damage": damage,
        "Speed": speed,
        "DPS": dps,
        "Durability": durability,
        "Value": value
    }

    return blade_points, guard_points, bolster_points, handle_points, grip_details, pommel_points, stats

def generate_bow():
    """Generate a bow."""
    bow_length = random.randint(300, 400)
    bow_width = random.randint(10, 20)
    
    # Basic bow shape
    bow_points = [
        (-bow_width//2, -bow_length//2),
        (bow_width//2, -bow_length//2),
        (bow_width//2, bow_length//2),
        (-bow_width//2, bow_length//2)
    ]
    
    # String
    string_points = [
        (0, -bow_length//2),
        (bow_width//2, 0),
        (0, bow_length//2)
    ]
    
    # Generate stats
    damage = random.randint(8, 15)
    speed = random.randint(15, 25)
    durability = random.randint(40, 80)
    dps = round(damage * speed / 10, 1)
    value = int((damage * 50 + speed * 30 + durability * 20 + dps * 100) * random.uniform(0.8, 1.2))

    stats = {
        "Type": "Bow",
        "Damage": damage,
        "Speed": speed,
        "DPS": dps,
        "Durability": durability,
        "Value": value
    }

    return [bow_points, string_points], stats

def generate_mace():
    """Generate a mace."""
    handle_length = random.randint(200, 300)
    handle_width = random.randint(10, 20)
    head_radius = random.randint(30, 50)
    
    # Handle
    handle_points = [
        (-handle_width//2, 0),
        (handle_width//2, 0),
        (handle_width//2, handle_length),
        (-handle_width//2, handle_length)
    ]
    
    # Head
    head_points = [
        (head_radius * math.cos(angle) + random.randint(-5, 5),
         head_radius * math.sin(angle) + random.randint(-5, 5) + handle_length)
        for angle in [i * 2 * math.pi / 8 for i in range(8)]
    ]
    
    # Generate stats
    damage = random.randint(12, 22)
    speed = random.randint(8, 15)
    durability = random.randint(60, 120)
    dps = round(damage * speed / 10, 1)
    value = int((damage * 50 + speed * 30 + durability * 20 + dps * 100) * random.uniform(0.8, 1.2))

    stats = {
        "Type": "Mace",
        "Damage": damage,
        "Speed": speed,
        "DPS": dps,
        "Durability": durability,
        "Value": value
    }

    return [handle_points, head_points], stats

def scale_and_center_weapon(points_list, scale_factor=1):
    """Scale and center the points of a weapon."""
    print(f"Scaling points: {points_list}")
    all_points = [p for points in points_list for p in points]
    if not all_points:
        print("Debug: No points found.")
        return points_list

    valid_points = [p for p in all_points if isinstance(p, tuple) and len(p) == 2]
    if not valid_points:
        print("Debug: No valid points found.")
        return points_list
    
    min_x = min(p[0] for p in valid_points)
    max_x = max(p[0] for p in valid_points)
    min_y = min(p[1] for p in valid_points)
    max_y = max(p[1] for p in valid_points)
    
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    
    scaled_points_list = []
    for points in points_list:
        scaled_points = [((x - center_x) * scale_factor + width // 2, 
                          (y - center_y) * scale_factor + height // 2) for x, y in points]
        scaled_points_list.append(scaled_points)
    
    print(f"Scaled points: {scaled_points_list}")
    return scaled_points_list

def draw_polygon_aa(surface, color, points):
    """Draw a polygon with anti-aliasing."""
    pygame.draw.polygon(surface, color, points)
    pygame.draw.aalines(surface, color, True, points)

def draw_weapon(surface, weapon_parts, weapon_type):
    """Draw a weapon."""
    print(f"Drawing {weapon_type}")
    print(f"Weapon parts: {weapon_parts}")

    if weapon_type == "Sword":
        if len(weapon_parts) == 6:
            blade, guard, bolster, handle, grip_details, pommel = weapon_parts
            parts = [
                (blade, random.choice(BLADE_COLORS)),
                (guard, random.choice(GUARD_COLORS)),
                (bolster, random.choice(BOLSTER_COLORS)),
                (handle, random.choice(HANDLE_COLORS)),
                (pommel, random.choice(GUARD_COLORS))
            ]
            
            for points, color in parts:
                print(f"Drawing part: {points}")
                draw_polygon_aa(surface, color, points)
            
            grip_color = (max(parts[3][1][0] - 20, 0), max(parts[3][1][1] - 20, 0), max(parts[3][1][2] - 20, 0))
            for i in range(0, len(grip_details), 2):
                pygame
            for i in range(0, len(grip_details), 2):
                pygame.draw.line(surface, grip_color, grip_details[i], grip_details[i+1], 2)

        else:
            print("Error: Invalid sword parts.")

    elif weapon_type == "Bow":
        if len(weapon_parts) == 2:
            bow, string = weapon_parts
            pygame.draw.polygon(surface, (150, 75, 0), bow)  # Brown color for bow
            pygame.draw.aalines(surface, (150, 75, 0), True, bow)
            pygame.draw.lines(surface, (255, 255, 255), False, string, 2)  # White color for string
        else:
            print("Error: Invalid bow parts.")

    elif weapon_type == "Mace":
        if len(weapon_parts) == 2:
            handle, head = weapon_parts
            pygame.draw.polygon(surface, (150, 75, 0), handle)  # Brown color for handle
            pygame.draw.aalines(surface, (150, 75, 0), True, handle)
            pygame.draw.polygon(surface, (100, 100, 100), head)  # Gray color for head
            pygame.draw.aalines(surface, (100, 100, 100), True, head)
        else:
            print("Error: Invalid mace parts.")

    else:
        print("Error: Unknown weapon type.")

def draw_stats(surface, stats):
    """Draw the stats of the current weapon on the screen."""
    stat_font = pygame.font.Font(None, 24)
    stat_color = (255, 255, 255)
    stat_x, stat_y = 10, 10

    for stat, value in stats.items():
        stat_text = stat_font.render(f"{stat}: {value}", True, stat_color)
        surface.blit(stat_text, (stat_x, stat_y))
        stat_y += 30

def main():
    clock = pygame.time.Clock()
    running = True

    background = generate_background()
    buttons = [
        Button(10, 10, 100, 50, "Generate Sword", lambda: generate_sword()),
        Button(120, 10, 100, 50, "Generate Bow", lambda: generate_bow()),
        Button(230, 10, 100, 50, "Generate Mace", lambda: generate_mace())
    ]

    current_weapon = None
    current_stats = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    action = button.handle_event(event)
                    if action:
                        current_weapon, current_stats = action
                        current_weapon = scale_and_center_weapon(current_weapon, 0.5)

        screen.blit(background, (0, 0))

        for button in buttons:
            button.draw(screen)

        if current_weapon:
            draw_weapon(screen, current_weapon, current_stats["Type"])
            draw_stats(screen, current_stats)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()