import pygame
import random
import math

pygame.init()

width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Blacksmith's Sword Generator")

# Colors
BLACK = (0, 0, 0)
BLADE_COLORS = [(192, 192, 192), (160, 160, 160), (128, 128, 128), (224, 224, 224)]
HANDLE_COLORS = [(139, 69, 19), (101, 67, 33), (85, 57, 28), (32, 32, 32), (48, 48, 48), (64, 64, 64)]
GUARD_COLORS = [(218, 165, 32), (184, 134, 11), (205, 127, 50)]
BOLSTER_COLORS = [(255, 215, 0), (218, 165, 32), (205, 127, 50)]
OUTLINE_COLOR = (20, 20, 20)

# Font setup
font = pygame.font.Font(None, 24)

def generate_background():
    background = pygame.Surface((width, height))
    background.fill((50, 30, 20))  # Dark brown background
    pygame.draw.rect(background, (100, 60, 20), (50, 400, 700, 200))  # Wooden floor
    pygame.draw.rect(background, (80, 80, 80), (100, 100, 200, 200))  # Forge
    pygame.draw.rect(background, (120, 80, 40), (500, 150, 200, 250))  # Workbench
    pygame.draw.rect(background, (60, 60, 60), (550, 200, 100, 20))  # Hammer
    pygame.draw.polygon(background, (80, 80, 80), [(680, 250), (700, 270), (660, 270)])  # Anvil
    return background

def smooth_points(points, smoothness=0.2):
    smoothed = []
    for i in range(len(points)):
        prev = points[i-1]
        curr = points[i]
        next = points[(i+1) % len(points)]
        smoothed_x = curr[0] + smoothness * (prev[0] + next[0] - 2 * curr[0])
        smoothed_y = curr[1] + smoothness * (prev[1] + next[1] - 2 * curr[1])
        smoothed.append((smoothed_x, smoothed_y))
    return smoothed

def generate_sword():
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

    # Guard points
    guard_points = [
        (-guard_width//2, blade_length),
        (guard_width//2, blade_length),
        (guard_width//2, blade_length + 15),
        (-guard_width//2, blade_length + 15),
    ]

    # Bolster
    bolster_style = random.choice(["european", "japanese", "chinese"])
    if bolster_style == "european":
        bolster_points = generate_european_bolster(blade_width, blade_length + 15)
    elif bolster_style == "japanese":
        bolster_points = generate_japanese_bolster(blade_width, blade_length + 15)
    else:
        bolster_points = generate_chinese_bolster(blade_width, blade_length + 15)

    # Improved handle points
    handle_start = blade_length + 15 + blade_width * 0.5
    handle_segments = random.randint(5, 7)
    handle_points = []
    for i in range(handle_segments):
        y = handle_start + (handle_length * i // handle_segments)
        left_x = -blade_width//3 + random.randint(-2, 2)
        right_x = blade_width//3 + random.randint(-2, 2)
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
        "Style": bolster_style.capitalize(),
        "Damage": damage,
        "Speed": speed,
        "DPS": dps,
        "Durability": durability,
        "Value": value
    }

    return blade_points, guard_points, bolster_points, handle_points, grip_details, pommel_points, stats

# ... [keep the bolster generation functions as they were] ...

def scale_and_center_weapon(points_list, scale_factor=1):
    all_points = [p for points in points_list for p in points]
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)
    
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    
    scaled_points_list = []
    for points in points_list:
        scaled_points = [((x - center_x) * scale_factor + width // 2, 
                          (y - center_y) * scale_factor + height // 2) for x, y in points]
        scaled_points_list.append(scaled_points)
    
    return scaled_points_list

def draw_polygon_aa(surface, color, points):
    pygame.draw.polygon(surface, color, points)
    pygame.draw.aalines(surface, color, True, points)

def draw_sword(surface, blade, guard, bolster, handle, grip_details, pommel):
    parts = [
        (blade, random.choice(BLADE_COLORS)),
        (guard, random.choice(GUARD_COLORS)),
        (bolster, random.choice(BOLSTER_COLORS)),
        (handle, random.choice(HANDLE_COLORS)),
        (pommel, random.choice(GUARD_COLORS))
    ]
    
    # Draw filled polygons with anti-aliasing
    for points, color in parts:
        draw_polygon_aa(surface, color, points)
    
    # Draw grip details
    grip_color = (max(parts[3][1][0] - 20, 0), max(parts[3][1][1] - 20, 0), max(parts[3][1][2] - 20, 0))
    for i in range(0, len(grip_details), 2):
        pygame.draw.line(surface, grip_color, grip_details[i], grip_details[i+1], 1)
    
    # Draw outlines
    for points, _ in parts:
        pygame.draw.aalines(surface, OUTLINE_COLOR, True, points)

def draw_stats(surface, stats):
    y = 10
    for stat, value in stats.items():
        text = font.render(f"{stat}: {value}", True, (255, 255, 255))
        surface.blit(text, (10, y))
        y += 30

# Main game loop
running = True
background = generate_background()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                screen.blit(background, (0, 0))
                blade, guard, bolster, handle, grip_details, pommel, stats = generate_sword()
                scaled_parts = scale_and_center_weapon([blade, guard, bolster, handle, grip_details, pommel], 0.7)
                draw_sword(screen, *scaled_parts)
                draw_stats(screen, stats)
                pygame.display.flip()

    if pygame.time.get_ticks() < 100:
        screen.blit(background, (0, 0))
        blade, guard, bolster, handle, grip_details, pommel, stats = generate_sword()
        scaled_parts = scale_and_center_weapon([blade, guard, bolster, handle, grip_details, pommel], 0.7)
        draw_sword(screen, *scaled_parts)
        draw_stats(screen, stats)
        pygame.display.flip()

pygame.quit()