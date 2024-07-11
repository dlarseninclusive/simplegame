import pygame

# Ensure colors are defined
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def draw_roads(screen, WIDTH, HEIGHT, GRID_SIZE, ROAD_WIDTH, ROAD_COLOR):
    for i in range(0, WIDTH, GRID_SIZE + ROAD_WIDTH):
        pygame.draw.rect(screen, ROAD_COLOR, (i, 0, ROAD_WIDTH, HEIGHT))  # Vertical roads
    for j in range(0, HEIGHT, GRID_SIZE + ROAD_WIDTH):
        pygame.draw.rect(screen, ROAD_COLOR, (0, j, WIDTH, ROAD_WIDTH))  # Horizontal roads

def show_dialog(screen, text, x, y):
    font = pygame.font.Font(None, 24)
    dialog_surface = pygame.Surface((300, 100))
    dialog_surface.fill(WHITE)
    dialog_surface.set_alpha(200)
    screen.blit(dialog_surface, (x, y))
    
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if font.size(' '.join(current_line))[0] > 280:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, BLACK)
        screen.blit(text_surface, (x + 10, y + 10 + i * 30))
