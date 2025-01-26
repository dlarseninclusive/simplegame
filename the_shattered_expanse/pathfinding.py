# pathfinding.py

import heapq
import pygame

class GridPathfinder:
    """
    A simple grid-based A* pathfinder to navigate around obstacles.
    cell_size controls how big each grid cell is in the actual world.
    For a 2000x2000 world, if cell_size=40, we get a 50x50 grid.
    """
    def __init__(self, width, height, cell_size=40):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = [[0 for _ in range(height)] for _ in range(width)]

    def set_obstacles(self, obstacles):
        """
        Mark grid cells as blocked if they intersect any obstacle.
        """
        for x in range(self.width):
            for y in range(self.height):
                world_x, world_y = self.grid_to_world(x, y)
                cell_rect = pygame.Rect(world_x, world_y, self.cell_size, self.cell_size)
                for obs in obstacles:
                    if cell_rect.colliderect(obs):
                        self.grid[x][y] = 1  # blocked
                        break

    def world_to_grid(self, wx, wy):
        gx = int(wx // self.cell_size)
        gy = int(wy // self.cell_size)
        return gx, gy

    def grid_to_world(self, gx, gy):
        wx = gx * self.cell_size + self.cell_size//2
        wy = gy * self.cell_size + self.cell_size//2
        return wx, wy

    def find_path(self, start_x, start_y, goal_x, goal_y):
        """
        A* search from (start_x, start_y) to (goal_x, goal_y) in grid coords.
        Returns a list of (gx,gy) cells for the path.
        """
        if not self.is_valid_cell(start_x, start_y) or not self.is_valid_cell(goal_x, goal_y):
            return []

        open_set = []
        heapq.heappush(open_set, (0, (start_x, start_y)))
        came_from = {}
        g_score = {(start_x, start_y): 0}

        while open_set:
            current_f, current = heapq.heappop(open_set)
            if current == (goal_x, goal_y):
                return self.reconstruct_path(came_from, current)

            cx, cy = current
            for neighbor in self.get_neighbors(cx, cy):
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, (goal_x, goal_y))
                    heapq.heappush(open_set, (f_score, neighbor))
                    came_from[neighbor] = current

        return []

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def get_neighbors(self, gx, gy):
        neighbors = []
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = gx+dx, gy+dy
            if self.is_valid_cell(nx, ny):
                neighbors.append((nx, ny))
        return neighbors

    def is_valid_cell(self, gx, gy):
        if gx < 0 or gy < 0 or gx >= self.width or gy >= self.height:
            return False
        return self.grid[gx][gy] == 0

    def heuristic(self, a, b):
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
