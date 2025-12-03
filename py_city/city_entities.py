"""
City Entities - Vehicles, Animals, and Special Buildings for Py City

GTA-lite expansion featuring:
- Vehicles (cars, trucks, buses) on roads
- Animals (dogs, cats, pigeons)
- Special buildings (jail, courthouse, hospital, police station)
- Enterable buildings with interiors
- Crime investigation system (clues, evidence)
"""

import random
import math
import pygame
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable
from enum import Enum, auto


# =============================================================================
# VEHICLES
# =============================================================================

class VehicleType(Enum):
    """Types of vehicles in the city."""
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    POLICE_CAR = "police_car"
    AMBULANCE = "ambulance"
    TAXI = "taxi"


@dataclass
class Vehicle:
    """A vehicle that travels on roads."""
    x: float
    y: float
    vehicle_type: VehicleType
    direction: Tuple[float, float]  # Normalized direction vector
    speed: float = 2.0
    width: int = 40
    height: int = 20
    color: Tuple[int, int, int] = (100, 100, 100)

    # State
    waiting: bool = False
    wait_timer: float = 0.0
    honking: bool = False

    # Path following
    path: List[Tuple[float, float]] = field(default_factory=list)
    path_index: int = 0

    def __post_init__(self):
        """Set color based on vehicle type."""
        type_colors = {
            VehicleType.CAR: [(180, 50, 50), (50, 50, 180), (50, 150, 50),
                             (180, 180, 50), (100, 100, 100), (200, 200, 200)],
            VehicleType.TRUCK: [(80, 80, 80), (100, 80, 60), (60, 80, 100)],
            VehicleType.BUS: [(200, 150, 50), (50, 100, 150)],
            VehicleType.POLICE_CAR: [(30, 30, 30)],  # Black with lights
            VehicleType.AMBULANCE: [(255, 255, 255)],  # White with cross
            VehicleType.TAXI: [(255, 200, 50)],  # Yellow
        }
        colors = type_colors.get(self.vehicle_type, [(100, 100, 100)])
        self.color = random.choice(colors)

        # Size varies by type
        if self.vehicle_type == VehicleType.BUS:
            self.width = 70
            self.height = 25
            self.speed = 1.5
        elif self.vehicle_type == VehicleType.TRUCK:
            self.width = 50
            self.height = 22
            self.speed = 1.8
        elif self.vehicle_type == VehicleType.POLICE_CAR:
            self.speed = 3.0  # Faster

    def update(self, dt: float, road_network: 'RoadNetwork' = None):
        """Update vehicle position with lane-based movement."""
        if self.waiting:
            self.wait_timer -= dt
            if self.wait_timer <= 0:
                self.waiting = False
            return

        # Move along path
        if self.path and self.path_index < len(self.path):
            target_x, target_y = self.path[self.path_index]

            # Calculate direction to target
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 20:  # Reached waypoint (increased threshold for smooth turning)
                self.path_index += 1
                if self.path_index >= len(self.path):
                    # Generate new path
                    if road_network:
                        self.path = road_network.get_random_path(self.x, self.y, length=8)
                        self.path_index = 0
            else:
                # Update direction (smooth turning)
                new_dir = (dx / dist, dy / dist)
                # Blend old and new direction for smooth turns
                blend = 0.1  # Turn speed
                self.direction = (
                    self.direction[0] * (1 - blend) + new_dir[0] * blend,
                    self.direction[1] * (1 - blend) + new_dir[1] * blend
                )
                # Renormalize
                dir_len = math.sqrt(self.direction[0]**2 + self.direction[1]**2)
                if dir_len > 0:
                    self.direction = (self.direction[0] / dir_len, self.direction[1] / dir_len)

                # Apply lane offset - stay on right side of road
                lane_offset = 12
                perp_x = -self.direction[1]
                perp_y = self.direction[0]

                # Calculate target position with lane offset
                lane_target_x = target_x + perp_x * lane_offset
                lane_target_y = target_y + perp_y * lane_offset

                # Move toward lane-adjusted target
                adj_dx = lane_target_x - self.x
                adj_dy = lane_target_y - self.y
                adj_dist = math.sqrt(adj_dx * adj_dx + adj_dy * adj_dy)
                if adj_dist > 0:
                    move_dir = (adj_dx / adj_dist, adj_dy / adj_dist)
                    self.x += move_dir[0] * self.speed * dt * 60
                    self.y += move_dir[1] * self.speed * dt * 60
        elif road_network:
            # No path - get one
            self.path = road_network.get_random_path(self.x, self.y, length=8)
            self.path_index = 0

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw the vehicle with improved top-down graphics."""
        screen_x, screen_y = camera.apply(self.x, self.y)

        # Skip if off screen
        if (screen_x < -self.width or screen_x > camera.screen_width + self.width or
            screen_y < -self.height or screen_y > camera.screen_height + self.height):
            return

        # Determine if moving horizontally or vertically based on direction
        horizontal = abs(self.direction[0]) > abs(self.direction[1])
        facing_right = self.direction[0] > 0
        facing_down = self.direction[1] > 0

        # Swap width/height based on orientation
        if horizontal:
            w, h = self.width, self.height
        else:
            w, h = self.height, self.width

        cx, cy = int(screen_x), int(screen_y)

        # Shadow
        shadow_offset = 2
        pygame.draw.rect(screen, (30, 30, 30),
                        (cx - w // 2 + shadow_offset, cy - h // 2 + shadow_offset, w, h),
                        border_radius=4)

        # Main body
        body_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        pygame.draw.rect(screen, self.color, body_rect, border_radius=4)

        # Darker shade for depth
        shade_color = (max(0, self.color[0] - 40),
                      max(0, self.color[1] - 40),
                      max(0, self.color[2] - 40))

        # Roof/cabin (smaller rectangle in center)
        cabin_margin = 4
        if self.vehicle_type != VehicleType.TRUCK:
            cabin_rect = pygame.Rect(cx - w // 2 + cabin_margin, cy - h // 2 + cabin_margin,
                                    w - cabin_margin * 2, h - cabin_margin * 2)
            pygame.draw.rect(screen, shade_color, cabin_rect, border_radius=2)

        # Windows (glass color)
        glass_color = (100, 150, 200)
        if self.vehicle_type in [VehicleType.CAR, VehicleType.TAXI, VehicleType.POLICE_CAR]:
            # Front and rear windshield
            if horizontal:
                # Front window
                front_offset = w // 3 if facing_right else -w // 3
                pygame.draw.rect(screen, glass_color,
                               (cx + front_offset - 4, cy - h // 4, 6, h // 2), border_radius=1)
                # Rear window
                pygame.draw.rect(screen, glass_color,
                               (cx - front_offset - 2, cy - h // 4, 6, h // 2), border_radius=1)
            else:
                # Vertical orientation
                front_offset = h // 3 if facing_down else -h // 3
                pygame.draw.rect(screen, glass_color,
                               (cx - w // 4, cy + front_offset - 3, w // 2, 5), border_radius=1)
                pygame.draw.rect(screen, glass_color,
                               (cx - w // 4, cy - front_offset - 2, w // 2, 5), border_radius=1)

        # Wheels (4 corners)
        wheel_color = (20, 20, 20)
        wheel_w, wheel_h = (6, 3) if horizontal else (3, 6)
        offsets = [(-w//2 + 3, -h//2), (-w//2 + 3, h//2 - wheel_h),
                   (w//2 - wheel_w - 3, -h//2), (w//2 - wheel_w - 3, h//2 - wheel_h)]
        for ox, oy in offsets:
            pygame.draw.rect(screen, wheel_color, (cx + ox, cy + oy, wheel_w, wheel_h))

        # Type-specific details
        if self.vehicle_type == VehicleType.POLICE_CAR:
            # Light bar on top
            light_time = pygame.time.get_ticks()
            left_color = (255, 0, 0) if (light_time // 150) % 2 == 0 else (100, 0, 0)
            right_color = (0, 0, 255) if (light_time // 150) % 2 == 1 else (0, 0, 100)
            pygame.draw.rect(screen, left_color, (cx - 8, cy - 3, 6, 6), border_radius=1)
            pygame.draw.rect(screen, right_color, (cx + 2, cy - 3, 6, 6), border_radius=1)

        elif self.vehicle_type == VehicleType.AMBULANCE:
            # Red cross on white
            pygame.draw.rect(screen, (255, 255, 255), (cx - 8, cy - 8, 16, 16))
            pygame.draw.rect(screen, (255, 0, 0), (cx - 2, cy - 6, 4, 12))
            pygame.draw.rect(screen, (255, 0, 0), (cx - 6, cy - 2, 12, 4))

        elif self.vehicle_type == VehicleType.TAXI:
            # Taxi sign on roof
            pygame.draw.rect(screen, (255, 220, 100), (cx - 6, cy - 4, 12, 8), border_radius=2)
            pygame.draw.rect(screen, (0, 0, 0), (cx - 6, cy - 4, 12, 8), 1, border_radius=2)

        elif self.vehicle_type == VehicleType.BUS:
            # Multiple windows along sides
            for i in range(4):
                if horizontal:
                    pygame.draw.rect(screen, glass_color,
                                   (cx - w//2 + 8 + i * 14, cy - 3, 10, 6), border_radius=1)
                else:
                    pygame.draw.rect(screen, glass_color,
                                   (cx - 3, cy - h//2 + 8 + i * 14, 6, 10), border_radius=1)

        elif self.vehicle_type == VehicleType.TRUCK:
            # Cargo area (darker)
            cargo_color = (60, 60, 70)
            if horizontal:
                cargo_x = cx - w//4 if facing_right else cx - w//2
                pygame.draw.rect(screen, cargo_color,
                               (cargo_x, cy - h//2 + 2, w//2, h - 4), border_radius=2)
            else:
                cargo_y = cy - h//4 if facing_down else cy - h//2
                pygame.draw.rect(screen, cargo_color,
                               (cx - w//2 + 2, cargo_y, w - 4, h//2), border_radius=2)

        # Headlights (front)
        headlight_color = (255, 255, 200)
        if horizontal:
            front_x = cx + (w//2 - 3 if facing_right else -w//2 + 1)
            pygame.draw.circle(screen, headlight_color, (front_x, cy - h//4), 2)
            pygame.draw.circle(screen, headlight_color, (front_x, cy + h//4), 2)
        else:
            front_y = cy + (h//2 - 3 if facing_down else -h//2 + 1)
            pygame.draw.circle(screen, headlight_color, (cx - w//4, front_y), 2)
            pygame.draw.circle(screen, headlight_color, (cx + w//4, front_y), 2)

        # Taillights (rear) - red
        taillight_color = (200, 50, 50)
        if horizontal:
            rear_x = cx + (-w//2 + 1 if facing_right else w//2 - 3)
            pygame.draw.circle(screen, taillight_color, (rear_x, cy - h//4), 2)
            pygame.draw.circle(screen, taillight_color, (rear_x, cy + h//4), 2)
        else:
            rear_y = cy + (-h//2 + 1 if facing_down else h//2 - 3)
            pygame.draw.circle(screen, taillight_color, (cx - w//4, rear_y), 2)
            pygame.draw.circle(screen, taillight_color, (cx + w//4, rear_y), 2)


class VehicleManager:
    """Manages all vehicles in the city."""

    def __init__(self, world_width: int, world_height: int, road_network: 'RoadNetwork' = None):
        self.world_width = world_width
        self.world_height = world_height
        self.road_network = road_network
        self.vehicles: List[Vehicle] = []
        self.max_vehicles = 15

    def spawn_vehicles(self, road_segments: List[Tuple[int, int, int, int]]):
        """Spawn initial vehicles on road segments."""
        for _ in range(self.max_vehicles):
            if road_segments and self.road_network:
                # Pick random road segment
                x1, y1, x2, y2 = random.choice(road_segments)
                t = random.random()
                x = x1 + t * (x2 - x1)
                y = y1 + t * (y2 - y1)

                # Direction along road
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx * dx + dy * dy)
                if length > 0:
                    direction = (dx / length, dy / length)
                else:
                    direction = (1, 0)

                # Offset to right side of road for lane separation
                lane_offset = 12  # Half road width to stay in lane
                perp_x = -direction[1]  # Perpendicular vector
                perp_y = direction[0]
                x += perp_x * lane_offset
                y += perp_y * lane_offset

                # Random vehicle type (weighted)
                vtype = random.choices(
                    [VehicleType.CAR, VehicleType.TAXI, VehicleType.TRUCK,
                     VehicleType.BUS, VehicleType.POLICE_CAR],
                    weights=[60, 15, 10, 8, 7]
                )[0]

                vehicle = Vehicle(x=x, y=y, vehicle_type=vtype, direction=direction)

                # Assign initial path
                initial_path = self.road_network.get_random_path(x, y, length=8)
                if initial_path:
                    vehicle.path = initial_path
                    vehicle.path_index = 0

                self.vehicles.append(vehicle)

    def update(self, dt: float):
        """Update all vehicles."""
        for vehicle in self.vehicles:
            vehicle.update(dt, self.road_network)

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw all vehicles."""
        for vehicle in self.vehicles:
            vehicle.draw(screen, camera)


# =============================================================================
# ANIMALS
# =============================================================================

class AnimalType(Enum):
    """Types of animals in the city."""
    DOG = "dog"
    CAT = "cat"
    PIGEON = "pigeon"
    RAT = "rat"


@dataclass
class Animal:
    """An animal that wanders the city."""
    x: float
    y: float
    animal_type: AnimalType
    size: int = 15
    speed: float = 1.0
    color: Tuple[int, int, int] = (100, 80, 60)

    # State
    state: str = "idle"  # idle, walking, running, fleeing
    state_timer: float = 0.0
    direction: Tuple[float, float] = (0, 0)

    # Behavior
    flee_from: Optional[Tuple[float, float]] = None
    follow_target: Optional[any] = None  # For dogs following owner

    def __post_init__(self):
        """Set properties based on animal type."""
        type_props = {
            AnimalType.DOG: {
                "colors": [(139, 90, 43), (80, 50, 30), (200, 180, 160), (50, 50, 50)],
                "size": 20,
                "speed": 2.0,
            },
            AnimalType.CAT: {
                "colors": [(100, 100, 100), (200, 150, 100), (50, 50, 50), (255, 255, 255)],
                "size": 15,
                "speed": 2.5,
            },
            AnimalType.PIGEON: {
                "colors": [(120, 120, 140), (100, 100, 120)],
                "size": 10,
                "speed": 1.5,
            },
            AnimalType.RAT: {
                "colors": [(80, 70, 60), (60, 55, 50)],
                "size": 8,
                "speed": 3.0,
            },
        }
        props = type_props.get(self.animal_type, {})
        self.color = random.choice(props.get("colors", [(100, 80, 60)]))
        self.size = props.get("size", 15)
        self.speed = props.get("speed", 1.0)
        self.state_timer = random.uniform(1.0, 5.0)

    def update(self, dt: float, player_x: float = 0, player_y: float = 0):
        """Update animal behavior."""
        self.state_timer -= dt

        # Check for nearby threats (player too close)
        dx = player_x - self.x
        dy = player_y - self.y
        dist_to_player = math.sqrt(dx * dx + dy * dy)

        # Flee behavior
        if dist_to_player < 80 and self.animal_type in [AnimalType.PIGEON, AnimalType.CAT, AnimalType.RAT]:
            self.state = "fleeing"
            if dist_to_player > 0:
                self.direction = (-dx / dist_to_player, -dy / dist_to_player)
            self.state_timer = 2.0

        # State machine
        if self.state == "idle":
            if self.state_timer <= 0:
                # Transition to walking
                self.state = "walking"
                angle = random.uniform(0, 2 * math.pi)
                self.direction = (math.cos(angle), math.sin(angle))
                self.state_timer = random.uniform(2.0, 6.0)

        elif self.state == "walking":
            # Move in direction
            self.x += self.direction[0] * self.speed * dt * 60
            self.y += self.direction[1] * self.speed * dt * 60

            if self.state_timer <= 0:
                self.state = "idle"
                self.state_timer = random.uniform(1.0, 4.0)

        elif self.state == "fleeing":
            # Move faster away from threat
            self.x += self.direction[0] * self.speed * 2 * dt * 60
            self.y += self.direction[1] * self.speed * 2 * dt * 60

            if self.state_timer <= 0:
                self.state = "idle"
                self.state_timer = random.uniform(2.0, 5.0)

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw the animal with improved pixel-art style graphics."""
        screen_x, screen_y = camera.apply(self.x, self.y)

        # Skip if off screen
        if (screen_x < -self.size or screen_x > camera.screen_width + self.size or
            screen_y < -self.size or screen_y > camera.screen_height + self.size):
            return

        cx, cy = int(screen_x), int(screen_y)

        # Determine facing direction
        facing_right = self.direction[0] >= 0
        facing_down = self.direction[1] > 0.3
        facing_up = self.direction[1] < -0.3

        # Darker shade for outlines/details
        dark_color = (max(0, self.color[0] - 50),
                     max(0, self.color[1] - 50),
                     max(0, self.color[2] - 50))

        if self.animal_type == AnimalType.DOG:
            # Shadow
            pygame.draw.ellipse(screen, (30, 30, 30, 100),
                              (cx - 8 + 1, cy - 4 + 1, 16, 10))
            # Body (oval, horizontal orientation)
            pygame.draw.ellipse(screen, self.color, (cx - 8, cy - 4, 16, 10))
            pygame.draw.ellipse(screen, dark_color, (cx - 8, cy - 4, 16, 10), 1)

            # Head (circle, offset by direction)
            head_offset_x = 7 if facing_right else -7
            head_x = cx + head_offset_x
            pygame.draw.circle(screen, self.color, (head_x, cy - 2), 5)
            pygame.draw.circle(screen, dark_color, (head_x, cy - 2), 5, 1)

            # Ears (small triangles on head)
            ear_x = head_x + (2 if facing_right else -2)
            pygame.draw.polygon(screen, dark_color, [
                (ear_x - 3, cy - 6), (ear_x - 1, cy - 2), (ear_x - 5, cy - 3)
            ])
            pygame.draw.polygon(screen, dark_color, [
                (ear_x + 1, cy - 6), (ear_x + 3, cy - 2), (ear_x - 1, cy - 3)
            ])

            # Eye
            eye_x = head_x + (2 if facing_right else -2)
            pygame.draw.circle(screen, (0, 0, 0), (eye_x, cy - 3), 1)

            # Tail (wagging based on time)
            tail_wag = math.sin(pygame.time.get_ticks() / 100) * 3
            tail_x = cx + (-9 if facing_right else 9)
            pygame.draw.line(screen, dark_color, (tail_x, cy),
                           (tail_x + (-4 if facing_right else 4), cy - 4 + int(tail_wag)), 2)

            # Legs (4 small rectangles)
            leg_color = dark_color
            pygame.draw.rect(screen, leg_color, (cx - 6, cy + 3, 2, 4))
            pygame.draw.rect(screen, leg_color, (cx - 2, cy + 3, 2, 4))
            pygame.draw.rect(screen, leg_color, (cx + 2, cy + 3, 2, 4))
            pygame.draw.rect(screen, leg_color, (cx + 5, cy + 3, 2, 4))

        elif self.animal_type == AnimalType.CAT:
            # Shadow
            pygame.draw.ellipse(screen, (30, 30, 30, 100),
                              (cx - 6 + 1, cy - 3 + 1, 12, 8))
            # Body (smaller, sleeker than dog)
            pygame.draw.ellipse(screen, self.color, (cx - 6, cy - 3, 12, 8))
            pygame.draw.ellipse(screen, dark_color, (cx - 6, cy - 3, 12, 8), 1)

            # Head
            head_offset_x = 5 if facing_right else -5
            head_x = cx + head_offset_x
            pygame.draw.circle(screen, self.color, (head_x, cy - 1), 4)
            pygame.draw.circle(screen, dark_color, (head_x, cy - 1), 4, 1)

            # Pointed ears
            ear_base = head_x
            pygame.draw.polygon(screen, self.color, [
                (ear_base - 3, cy - 4), (ear_base - 4, cy - 8), (ear_base - 1, cy - 3)
            ])
            pygame.draw.polygon(screen, self.color, [
                (ear_base + 1, cy - 4), (ear_base + 2, cy - 8), (ear_base + 4, cy - 3)
            ])
            # Ear outlines
            pygame.draw.polygon(screen, dark_color, [
                (ear_base - 3, cy - 4), (ear_base - 4, cy - 8), (ear_base - 1, cy - 3)
            ], 1)
            pygame.draw.polygon(screen, dark_color, [
                (ear_base + 1, cy - 4), (ear_base + 2, cy - 8), (ear_base + 4, cy - 3)
            ], 1)

            # Eyes (almond shaped for cats)
            eye_x = head_x + (1 if facing_right else -1)
            pygame.draw.ellipse(screen, (200, 200, 50), (eye_x - 2, cy - 2, 3, 2))
            pygame.draw.circle(screen, (0, 0, 0), (eye_x, cy - 1), 1)

            # Tail (curved)
            tail_x = cx + (-7 if facing_right else 7)
            tail_curve = math.sin(pygame.time.get_ticks() / 200) * 2
            points = [(tail_x, cy), (tail_x + (-3 if facing_right else 3), cy - 4),
                     (tail_x + (-2 if facing_right else 2) + int(tail_curve), cy - 8)]
            pygame.draw.lines(screen, dark_color, False, points, 2)

            # Legs
            pygame.draw.rect(screen, dark_color, (cx - 4, cy + 2, 2, 3))
            pygame.draw.rect(screen, dark_color, (cx + 2, cy + 2, 2, 3))

        elif self.animal_type == AnimalType.PIGEON:
            # Shadow
            pygame.draw.ellipse(screen, (30, 30, 30, 100),
                              (cx - 5 + 1, cy - 3 + 1, 10, 6))
            # Body (round)
            pygame.draw.ellipse(screen, self.color, (cx - 5, cy - 3, 10, 7))

            # Wing pattern
            wing_color = (self.color[0] - 20, self.color[1] - 20, self.color[2] - 10)
            pygame.draw.ellipse(screen, wing_color, (cx - 3, cy - 2, 6, 4))

            # Head (small circle)
            head_x = cx + (4 if facing_right else -4)
            pygame.draw.circle(screen, self.color, (head_x, cy - 2), 3)

            # Eye
            pygame.draw.circle(screen, (200, 100, 0), (head_x + (1 if facing_right else -1), cy - 3), 1)

            # Beak (orange triangle)
            beak_x = head_x + (3 if facing_right else -3)
            pygame.draw.polygon(screen, (220, 150, 50), [
                (beak_x, cy - 2),
                (beak_x + (3 if facing_right else -3), cy - 1),
                (beak_x, cy)
            ])

            # Iridescent neck patch (green/purple shimmer)
            neck_color = (100, 50, 120) if (pygame.time.get_ticks() // 500) % 2 else (50, 100, 80)
            pygame.draw.ellipse(screen, neck_color, (head_x - 2, cy, 4, 3))

            # Feet (orange)
            pygame.draw.line(screen, (220, 150, 50), (cx - 2, cy + 3), (cx - 3, cy + 5), 1)
            pygame.draw.line(screen, (220, 150, 50), (cx + 1, cy + 3), (cx + 2, cy + 5), 1)

        elif self.animal_type == AnimalType.RAT:
            # Shadow
            pygame.draw.ellipse(screen, (30, 30, 30, 100),
                              (cx - 4 + 1, cy - 2 + 1, 8, 5))
            # Body (small, elongated)
            pygame.draw.ellipse(screen, self.color, (cx - 4, cy - 2, 8, 5))

            # Head (pointed)
            head_x = cx + (4 if facing_right else -4)
            pygame.draw.ellipse(screen, self.color, (head_x - 2, cy - 2, 5, 4))

            # Ears (round, prominent)
            ear_color = (180, 140, 140)
            pygame.draw.circle(screen, ear_color, (head_x - 1, cy - 3), 2)
            pygame.draw.circle(screen, ear_color, (head_x + 1, cy - 3), 2)

            # Eye (beady)
            pygame.draw.circle(screen, (0, 0, 0), (head_x + (1 if facing_right else -1), cy - 1), 1)

            # Nose (pink)
            nose_x = head_x + (3 if facing_right else -3)
            pygame.draw.circle(screen, (200, 150, 150), (nose_x, cy), 1)

            # Whiskers
            pygame.draw.line(screen, (150, 150, 150), (nose_x, cy - 1),
                           (nose_x + (3 if facing_right else -3), cy - 2), 1)
            pygame.draw.line(screen, (150, 150, 150), (nose_x, cy + 1),
                           (nose_x + (3 if facing_right else -3), cy + 2), 1)

            # Tail (long, thin, curved)
            tail_x = cx + (-5 if facing_right else 5)
            tail_curve = math.sin(pygame.time.get_ticks() / 150) * 2
            pygame.draw.line(screen, (180, 140, 140), (tail_x, cy),
                           (tail_x + (-8 if facing_right else 8), cy + int(tail_curve)), 1)
            pygame.draw.line(screen, (180, 140, 140),
                           (tail_x + (-8 if facing_right else 8), cy + int(tail_curve)),
                           (tail_x + (-12 if facing_right else 12), cy - 2 + int(tail_curve)), 1)


class AnimalManager:
    """Manages all animals in the city."""

    def __init__(self, world_width: int, world_height: int):
        self.world_width = world_width
        self.world_height = world_height
        self.animals: List[Animal] = []
        self.building_rects: List[pygame.Rect] = []  # For collision avoidance

    def set_building_rects(self, rects: List[pygame.Rect]):
        """Set building rectangles for collision avoidance."""
        self.building_rects = rects

    def _is_in_building(self, x: float, y: float) -> bool:
        """Check if position is inside a building."""
        for rect in self.building_rects:
            if rect.collidepoint(x, y):
                return True
        return False

    def spawn_animals(self, sidewalk_nodes: List, count: int = 20):
        """Spawn animals on sidewalks only (not in buildings)."""
        spawned = 0
        attempts = 0
        max_attempts = count * 10

        while spawned < count and attempts < max_attempts:
            attempts += 1

            if sidewalk_nodes:
                node = random.choice(sidewalk_nodes)
                # Stay close to sidewalk center
                x = node.x + random.randint(-15, 15)
                y = node.y + random.randint(-15, 15)
            else:
                x = random.randint(0, self.world_width)
                y = random.randint(0, self.world_height)

            # Skip if inside building
            if self._is_in_building(x, y):
                continue

            # Weighted animal types
            animal_type = random.choices(
                [AnimalType.PIGEON, AnimalType.DOG, AnimalType.CAT, AnimalType.RAT],
                weights=[40, 25, 25, 10]
            )[0]

            animal = Animal(x=x, y=y, animal_type=animal_type)
            self.animals.append(animal)
            spawned += 1

    def update(self, dt: float, player_x: float, player_y: float):
        """Update all animals with building collision avoidance."""
        for animal in self.animals:
            # Store old position
            old_x, old_y = animal.x, animal.y

            animal.update(dt, player_x, player_y)

            # Check if animal moved into a building
            if self._is_in_building(animal.x, animal.y):
                # Revert position and change direction
                animal.x, animal.y = old_x, old_y
                # Reverse direction
                animal.direction = (-animal.direction[0], -animal.direction[1])
                animal.state = "idle"
                animal.state_timer = random.uniform(0.5, 1.5)

            # Keep in bounds (wraparound)
            animal.x = animal.x % self.world_width
            animal.y = animal.y % self.world_height

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw all animals."""
        for animal in self.animals:
            animal.draw(screen, camera)


# =============================================================================
# SPECIAL BUILDINGS
# =============================================================================

class SpecialBuildingType(Enum):
    """Types of special buildings."""
    JAIL = "jail"
    COURTHOUSE = "courthouse"
    HOSPITAL = "hospital"
    POLICE_STATION = "police_station"
    BANK = "bank"
    BAR = "bar"
    APARTMENT = "apartment"
    SHOP = "shop"


@dataclass
class SpecialBuilding:
    """A special building that can be entered."""
    x: float
    y: float
    width: int
    height: int
    building_type: SpecialBuildingType
    name: str = ""

    # Visual
    color: Tuple[int, int, int] = (100, 100, 100)
    door_x: float = 0
    door_y: float = 0

    # Interaction
    enterable: bool = True
    occupied_by: List[str] = field(default_factory=list)  # NPCs inside

    # Crime investigation
    has_clue: bool = False
    clue_type: str = ""
    clue_discovered: bool = False

    def __post_init__(self):
        """Initialize based on building type."""
        type_props = {
            SpecialBuildingType.JAIL: {
                "color": (60, 60, 70),
                "name": "City Jail",
            },
            SpecialBuildingType.COURTHOUSE: {
                "color": (180, 170, 150),
                "name": "Courthouse",
            },
            SpecialBuildingType.HOSPITAL: {
                "color": (255, 255, 255),
                "name": "City Hospital",
            },
            SpecialBuildingType.POLICE_STATION: {
                "color": (50, 50, 120),
                "name": "Police Station",
            },
            SpecialBuildingType.BANK: {
                "color": (150, 140, 130),
                "name": "First National Bank",
            },
            SpecialBuildingType.BAR: {
                "color": (100, 60, 40),
                "name": "The Rusty Nail",
            },
            SpecialBuildingType.APARTMENT: {
                "color": (140, 100, 80),
                "name": "Apartments",
            },
            SpecialBuildingType.SHOP: {
                "color": (120, 120, 100),
                "name": "Corner Store",
            },
        }
        props = type_props.get(self.building_type, {})
        self.color = props.get("color", (100, 100, 100))
        if not self.name:
            self.name = props.get("name", "Building")

        # Door at bottom center
        self.door_x = self.x + self.width // 2
        self.door_y = self.y + self.height

    def is_near_door(self, px: float, py: float, radius: float = 30) -> bool:
        """Check if position is near the door."""
        dx = px - self.door_x
        dy = py - self.door_y
        return math.sqrt(dx * dx + dy * dy) < radius

    def draw(self, screen: pygame.Surface, camera: 'Camera', highlight: bool = False):
        """Draw the special building."""
        screen_x, screen_y = camera.apply(self.x, self.y)

        # Skip if off screen
        if (screen_x < -self.width or screen_x > camera.screen_width + self.width or
            screen_y < -self.height or screen_y > camera.screen_height + self.height):
            return

        rect = pygame.Rect(screen_x, screen_y, self.width, self.height)

        # Building body
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, (50, 50, 50), rect, 2)

        # Type-specific decorations
        if self.building_type == SpecialBuildingType.JAIL:
            # Barred windows
            for i in range(3):
                wx = screen_x + 20 + i * 30
                wy = screen_y + 20
                pygame.draw.rect(screen, (40, 40, 40), (wx, wy, 20, 30))
                for j in range(4):
                    pygame.draw.line(screen, (80, 80, 80),
                                   (wx + 5 + j * 4, wy), (wx + 5 + j * 4, wy + 30), 1)

        elif self.building_type == SpecialBuildingType.COURTHOUSE:
            # Columns
            for i in range(4):
                cx = screen_x + 15 + i * 25
                pygame.draw.rect(screen, (200, 190, 170), (cx, screen_y + 30, 10, self.height - 40))
            # Pediment (triangle top)
            pygame.draw.polygon(screen, (170, 160, 140), [
                (screen_x, screen_y + 25),
                (screen_x + self.width, screen_y + 25),
                (screen_x + self.width // 2, screen_y)
            ])

        elif self.building_type == SpecialBuildingType.HOSPITAL:
            # Red cross
            cx, cy = screen_x + self.width // 2, screen_y + 30
            pygame.draw.rect(screen, (255, 0, 0), (cx - 15, cy - 5, 30, 10))
            pygame.draw.rect(screen, (255, 0, 0), (cx - 5, cy - 15, 10, 30))

        elif self.building_type == SpecialBuildingType.POLICE_STATION:
            # Badge symbol
            pygame.draw.circle(screen, (200, 180, 50),
                             (int(screen_x + self.width // 2), int(screen_y + 25)), 15)
            pygame.draw.polygon(screen, (200, 180, 50), [
                (screen_x + self.width // 2, screen_y + 45),
                (screen_x + self.width // 2 - 10, screen_y + 35),
                (screen_x + self.width // 2 + 10, screen_y + 35),
            ])

        # Door
        door_screen_x, door_screen_y = camera.apply(self.door_x, self.door_y)
        door_color = (60, 40, 30) if not highlight else (100, 80, 60)
        pygame.draw.rect(screen, door_color,
                        (door_screen_x - 12, door_screen_y - 25, 24, 25))

        # Name label
        if highlight:
            font = pygame.font.Font(None, 20)
            label = font.render(self.name, True, (255, 255, 255))
            label_rect = label.get_rect(centerx=screen_x + self.width // 2, y=screen_y - 20)
            # Background
            bg_rect = label_rect.inflate(10, 4)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            screen.blit(label, label_rect)

        # Clue indicator
        if self.has_clue and not self.clue_discovered:
            pygame.draw.circle(screen, (255, 200, 50),
                             (int(screen_x + self.width - 10), int(screen_y + 10)), 5)


class SpecialBuildingManager:
    """Manages special buildings in the city."""

    def __init__(self, world_width: int, world_height: int):
        self.world_width = world_width
        self.world_height = world_height
        self.buildings: List[SpecialBuilding] = []

    def create_special_buildings(self, block_positions: List[Tuple[int, int, int, int]]):
        """Create special buildings at specific blocks."""
        if len(block_positions) < 6:
            return

        # Select blocks for special buildings
        selected = random.sample(block_positions, min(6, len(block_positions)))

        building_types = [
            SpecialBuildingType.JAIL,
            SpecialBuildingType.COURTHOUSE,
            SpecialBuildingType.POLICE_STATION,
            SpecialBuildingType.HOSPITAL,
            SpecialBuildingType.BANK,
            SpecialBuildingType.BAR,
        ]

        for i, (x, y, w, h) in enumerate(selected):
            if i < len(building_types):
                building = SpecialBuilding(
                    x=x + 10,
                    y=y + 10,
                    width=w - 20,
                    height=h - 20,
                    building_type=building_types[i]
                )
                self.buildings.append(building)

    def get_building_near(self, x: float, y: float, radius: float = 50) -> Optional[SpecialBuilding]:
        """Get a special building near the given position."""
        for building in self.buildings:
            if building.is_near_door(x, y, radius):
                return building
        return None

    def draw(self, screen: pygame.Surface, camera: 'Camera', player_x: float, player_y: float):
        """Draw all special buildings."""
        for building in self.buildings:
            highlight = building.is_near_door(player_x, player_y)
            building.draw(screen, camera, highlight)


# =============================================================================
# CRIME INVESTIGATION
# =============================================================================

class ClueType(Enum):
    """Types of clues for crime investigation."""
    WITNESS = "witness"
    FOOTPRINT = "footprint"
    WEAPON = "weapon"
    DOCUMENT = "document"
    BLOOD = "blood"
    FINGERPRINT = "fingerprint"


@dataclass
class Clue:
    """A clue in a crime investigation."""
    x: float
    y: float
    clue_type: ClueType
    description: str
    discovered: bool = False
    linked_crime_id: Optional[str] = None

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw clue indicator if not discovered."""
        if self.discovered:
            return

        screen_x, screen_y = camera.apply(self.x, self.y)

        # Subtle sparkle effect
        pulse = abs(math.sin(pygame.time.get_ticks() / 300)) * 0.5 + 0.5
        color = (int(255 * pulse), int(200 * pulse), int(50 * pulse))
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), 5)
        pygame.draw.circle(screen, (255, 255, 200), (int(screen_x), int(screen_y)), 2)


@dataclass
class CrimeCase:
    """A crime case to investigate."""
    case_id: str
    crime_type: str  # "murder", "robbery", "assault"
    description: str
    clues: List[Clue] = field(default_factory=list)
    solved: bool = False
    suspect_id: Optional[str] = None

    # Progress
    clues_found: int = 0
    clues_required: int = 3


class InvestigationManager:
    """Manages crime investigations."""

    def __init__(self):
        self.active_cases: List[CrimeCase] = []
        self.solved_cases: List[CrimeCase] = []
        self.clues_in_world: List[Clue] = []

    def create_case(self, crime_type: str, world_width: int, world_height: int) -> CrimeCase:
        """Create a new crime case with clues."""
        case = CrimeCase(
            case_id=f"case_{len(self.active_cases) + len(self.solved_cases)}",
            crime_type=crime_type,
            description=self._generate_description(crime_type),
            clues_required=3
        )

        # Generate clues
        clue_types = list(ClueType)
        for i in range(case.clues_required):
            clue = Clue(
                x=random.randint(100, world_width - 100),
                y=random.randint(100, world_height - 100),
                clue_type=random.choice(clue_types),
                description=self._generate_clue_description(crime_type),
                linked_crime_id=case.case_id
            )
            case.clues.append(clue)
            self.clues_in_world.append(clue)

        self.active_cases.append(case)
        return case

    def _generate_description(self, crime_type: str) -> str:
        """Generate case description."""
        descriptions = {
            "murder": "A body was found in the alley. Find evidence to identify the killer.",
            "robbery": "The bank was hit last night. Track down the perpetrator.",
            "assault": "A citizen was attacked. Find witnesses and evidence.",
        }
        return descriptions.get(crime_type, "Investigate the crime scene.")

    def _generate_clue_description(self, crime_type: str) -> str:
        """Generate clue description."""
        clues = [
            "A torn piece of fabric caught on a fence.",
            "Footprints leading away from the scene.",
            "A dropped wallet with no ID.",
            "Security camera footage available.",
            "A witness saw someone fleeing.",
            "Blood droplets forming a trail.",
            "A discarded weapon nearby.",
            "Financial records showing motive.",
        ]
        return random.choice(clues)

    def check_clue_discovery(self, player_x: float, player_y: float, radius: float = 30) -> Optional[Clue]:
        """Check if player discovered a clue."""
        for clue in self.clues_in_world:
            if clue.discovered:
                continue

            dx = player_x - clue.x
            dy = player_y - clue.y
            if math.sqrt(dx * dx + dy * dy) < radius:
                clue.discovered = True

                # Update case progress
                for case in self.active_cases:
                    if case.case_id == clue.linked_crime_id:
                        case.clues_found += 1
                        if case.clues_found >= case.clues_required:
                            self._solve_case(case)
                        break

                return clue

        return None

    def _solve_case(self, case: CrimeCase):
        """Mark a case as solved."""
        case.solved = True
        self.active_cases.remove(case)
        self.solved_cases.append(case)

    def draw_clues(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw all undiscovered clues."""
        for clue in self.clues_in_world:
            clue.draw(screen, camera)


# =============================================================================
# BUILDING INTERIORS
# =============================================================================

class InteriorType(Enum):
    """Types of room/furniture arrangements."""
    OFFICE = "office"
    JAIL_CELL = "jail_cell"
    COURTROOM = "courtroom"
    HOSPITAL_ROOM = "hospital_room"
    SHOP_FLOOR = "shop_floor"
    BAR_ROOM = "bar_room"
    LIVING_ROOM = "living_room"
    BANK_LOBBY = "bank_lobby"


@dataclass
class Furniture:
    """A piece of furniture in a building interior."""
    x: float
    y: float
    width: int
    height: int
    furniture_type: str  # desk, chair, bed, counter, etc.
    color: Tuple[int, int, int] = (100, 80, 60)
    interactable: bool = False
    interaction_message: str = ""

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """Draw the furniture piece."""
        rect = pygame.Rect(int(self.x) + offset_x, int(self.y) + offset_y,
                          self.width, self.height)
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, (50, 40, 30), rect, 1)

        # Type-specific details
        if self.furniture_type == "desk":
            # Drawer handles
            pygame.draw.rect(screen, (70, 60, 50),
                           (rect.x + 5, rect.centery - 2, 15, 4))
        elif self.furniture_type == "chair":
            # Chair back
            pygame.draw.rect(screen, (max(0, self.color[0] - 20),
                                     max(0, self.color[1] - 20),
                                     max(0, self.color[2] - 20)),
                           (rect.x + 2, rect.y - 8, rect.width - 4, 10))
        elif self.furniture_type == "bed":
            # Pillow
            pygame.draw.rect(screen, (220, 220, 200),
                           (rect.x + 5, rect.y + 5, 20, 15))
            # Blanket
            pygame.draw.rect(screen, (100, 100, 150),
                           (rect.x + 5, rect.y + 25, rect.width - 10, rect.height - 30))
        elif self.furniture_type == "counter":
            # Counter surface highlight
            pygame.draw.rect(screen, (min(255, self.color[0] + 20),
                                     min(255, self.color[1] + 20),
                                     min(255, self.color[2] + 20)),
                           (rect.x, rect.y, rect.width, 5))
        elif self.furniture_type == "shelf":
            # Shelf items
            for i in range(3):
                item_color = random.choice([(150, 50, 50), (50, 150, 50), (50, 50, 150)])
                pygame.draw.rect(screen, item_color,
                               (rect.x + 5 + i * 15, rect.y + 5, 10, 15))
        elif self.furniture_type == "toilet":
            pygame.draw.ellipse(screen, (230, 230, 230), rect)
            pygame.draw.ellipse(screen, (100, 100, 100), rect, 1)
        elif self.furniture_type == "sink":
            pygame.draw.rect(screen, (200, 200, 200), rect)
            pygame.draw.ellipse(screen, (150, 150, 150),
                              (rect.x + 5, rect.y + 5, rect.width - 10, rect.height - 10))


@dataclass
class BuildingInterior:
    """The interior of a building."""
    width: int
    height: int
    interior_type: InteriorType
    floor_color: Tuple[int, int, int] = (80, 70, 60)
    wall_color: Tuple[int, int, int] = (150, 140, 130)
    furniture: List[Furniture] = field(default_factory=list)

    # Door position (for exiting)
    exit_x: float = 0
    exit_y: float = 0

    # NPCs in the building
    npcs: List[any] = field(default_factory=list)

    def __post_init__(self):
        """Generate interior layout based on type."""
        self._generate_layout()
        self._generate_npcs()
        # Exit door at bottom center
        self.exit_x = self.width // 2
        self.exit_y = self.height - 10

    def _generate_npcs(self):
        """Generate NPCs based on interior type. Imported here to avoid circular import."""
        # Import here to use InteriorNPC (defined later in file)
        # This is filled in by InteriorManager when creating the interior
        pass

    def _generate_layout(self):
        """Generate furniture layout based on interior type."""
        self.furniture = []

        if self.interior_type == InteriorType.OFFICE:
            self.floor_color = (100, 90, 80)
            self.wall_color = (180, 175, 165)
            # Desk
            self.furniture.append(Furniture(
                x=self.width // 2 - 40, y=self.height // 3,
                width=80, height=40, furniture_type="desk",
                color=(120, 80, 50)
            ))
            # Chair behind desk
            self.furniture.append(Furniture(
                x=self.width // 2 - 15, y=self.height // 3 - 30,
                width=30, height=25, furniture_type="chair",
                color=(60, 50, 40)
            ))
            # Filing cabinet
            self.furniture.append(Furniture(
                x=30, y=30,
                width=40, height=60, furniture_type="shelf",
                color=(80, 80, 90)
            ))

        elif self.interior_type == InteriorType.JAIL_CELL:
            self.floor_color = (70, 70, 75)
            self.wall_color = (100, 100, 105)
            # Bunk bed
            self.furniture.append(Furniture(
                x=30, y=self.height // 2 - 30,
                width=60, height=50, furniture_type="bed",
                color=(80, 80, 80)
            ))
            # Toilet
            self.furniture.append(Furniture(
                x=self.width - 60, y=self.height - 80,
                width=30, height=35, furniture_type="toilet",
                color=(200, 200, 200)
            ))
            # Sink
            self.furniture.append(Furniture(
                x=self.width - 60, y=self.height - 130,
                width=25, height=20, furniture_type="sink",
                color=(180, 180, 180)
            ))

        elif self.interior_type == InteriorType.COURTROOM:
            self.floor_color = (120, 100, 70)
            self.wall_color = (160, 140, 100)
            # Judge's bench
            self.furniture.append(Furniture(
                x=self.width // 2 - 50, y=40,
                width=100, height=30, furniture_type="counter",
                color=(100, 60, 30)
            ))
            # Witness stand
            self.furniture.append(Furniture(
                x=self.width // 4, y=100,
                width=40, height=40, furniture_type="desk",
                color=(90, 55, 25)
            ))
            # Jury box (benches)
            for i in range(2):
                self.furniture.append(Furniture(
                    x=self.width - 100, y=100 + i * 50,
                    width=80, height=30, furniture_type="counter",
                    color=(80, 50, 20)
                ))

        elif self.interior_type == InteriorType.HOSPITAL_ROOM:
            self.floor_color = (200, 200, 200)
            self.wall_color = (220, 220, 220)
            # Hospital bed
            self.furniture.append(Furniture(
                x=self.width // 2 - 30, y=self.height // 3,
                width=60, height=90, furniture_type="bed",
                color=(200, 200, 200)
            ))
            # Medical equipment cart
            self.furniture.append(Furniture(
                x=self.width - 70, y=self.height // 3,
                width=40, height=50, furniture_type="shelf",
                color=(150, 150, 160)
            ))

        elif self.interior_type == InteriorType.BAR_ROOM:
            self.floor_color = (60, 50, 40)
            self.wall_color = (100, 80, 60)
            # Bar counter
            self.furniture.append(Furniture(
                x=30, y=60,
                width=self.width - 60, height=25, furniture_type="counter",
                color=(80, 50, 30)
            ))
            # Bar stools
            for i in range(4):
                self.furniture.append(Furniture(
                    x=60 + i * 50, y=100,
                    width=20, height=20, furniture_type="chair",
                    color=(50, 35, 20)
                ))
            # Tables
            for i in range(2):
                self.furniture.append(Furniture(
                    x=50 + i * 120, y=self.height - 100,
                    width=50, height=50, furniture_type="desk",
                    color=(70, 45, 25)
                ))

        elif self.interior_type == InteriorType.SHOP_FLOOR:
            self.floor_color = (150, 140, 130)
            self.wall_color = (180, 170, 160)
            # Checkout counter
            self.furniture.append(Furniture(
                x=30, y=self.height - 80,
                width=60, height=30, furniture_type="counter",
                color=(100, 80, 60)
            ))
            # Shelves
            for i in range(3):
                self.furniture.append(Furniture(
                    x=30 + i * 70, y=40,
                    width=50, height=100, furniture_type="shelf",
                    color=(120, 100, 80)
                ))

        elif self.interior_type == InteriorType.BANK_LOBBY:
            self.floor_color = (180, 170, 150)
            self.wall_color = (200, 190, 170)
            # Teller counters
            for i in range(3):
                self.furniture.append(Furniture(
                    x=40 + i * 80, y=50,
                    width=60, height=25, furniture_type="counter",
                    color=(100, 80, 60)
                ))
            # Waiting area chairs
            for i in range(4):
                self.furniture.append(Furniture(
                    x=50 + i * 50, y=self.height - 80,
                    width=25, height=25, furniture_type="chair",
                    color=(60, 50, 40)
                ))

        elif self.interior_type == InteriorType.LIVING_ROOM:
            self.floor_color = (140, 120, 100)
            self.wall_color = (180, 170, 150)
            # Couch
            self.furniture.append(Furniture(
                x=self.width // 2 - 50, y=self.height // 2,
                width=100, height=40, furniture_type="counter",
                color=(80, 60, 100)
            ))
            # Coffee table
            self.furniture.append(Furniture(
                x=self.width // 2 - 30, y=self.height // 2 + 55,
                width=60, height=30, furniture_type="desk",
                color=(100, 70, 40)
            ))
            # TV stand
            self.furniture.append(Furniture(
                x=self.width // 2 - 40, y=40,
                width=80, height=20, furniture_type="shelf",
                color=(50, 50, 50)
            ))

    def get_collision_rects(self) -> List[pygame.Rect]:
        """Get collision rectangles for furniture."""
        return [pygame.Rect(f.x, f.y, f.width, f.height) for f in self.furniture]

    def is_near_exit(self, x: float, y: float, radius: float = 30) -> bool:
        """Check if position is near the exit."""
        dx = x - self.exit_x
        dy = y - self.exit_y
        return math.sqrt(dx * dx + dy * dy) < radius

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """Draw the building interior."""
        # Floor
        floor_rect = pygame.Rect(offset_x, offset_y, self.width, self.height)
        pygame.draw.rect(screen, self.floor_color, floor_rect)

        # Walls (border)
        pygame.draw.rect(screen, self.wall_color, floor_rect, 8)
        pygame.draw.rect(screen, (50, 50, 50), floor_rect, 2)

        # Draw furniture
        for furniture in self.furniture:
            furniture.draw(screen, offset_x, offset_y)

        # Exit door
        exit_screen_x = int(self.exit_x) + offset_x
        exit_screen_y = int(self.exit_y) + offset_y
        pygame.draw.rect(screen, (80, 60, 40),
                        (exit_screen_x - 20, exit_screen_y - 5, 40, 15))
        # "EXIT" text
        font = pygame.font.Font(None, 16)
        exit_text = font.render("EXIT", True, (255, 200, 200))
        screen.blit(exit_text, (exit_screen_x - 15, exit_screen_y - 3))


class InteriorManager:
    """Manages building interiors and transitions."""

    # Map building types to interior types
    BUILDING_TO_INTERIOR = {
        SpecialBuildingType.JAIL: InteriorType.JAIL_CELL,
        SpecialBuildingType.COURTHOUSE: InteriorType.COURTROOM,
        SpecialBuildingType.HOSPITAL: InteriorType.HOSPITAL_ROOM,
        SpecialBuildingType.POLICE_STATION: InteriorType.OFFICE,
        SpecialBuildingType.BANK: InteriorType.BANK_LOBBY,
        SpecialBuildingType.BAR: InteriorType.BAR_ROOM,
        SpecialBuildingType.APARTMENT: InteriorType.LIVING_ROOM,
        SpecialBuildingType.SHOP: InteriorType.SHOP_FLOOR,
    }

    # Map interior types to NPC roles that spawn there
    # NOTE: This is set as None and populated in __init__ to avoid forward reference issues
    INTERIOR_TO_NPCS = None

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_interior: Optional[BuildingInterior] = None
        self.current_building: Optional[SpecialBuilding] = None
        self.is_inside = False

        # Player position within interior
        self.interior_player_x = 0
        self.interior_player_y = 0

        # Interior dimensions (scaled to fit screen)
        self.interior_width = int(screen_width * 0.7)
        self.interior_height = int(screen_height * 0.7)
        self.interior_offset_x = (screen_width - self.interior_width) // 2
        self.interior_offset_y = (screen_height - self.interior_height) // 2

        # NPC interaction
        self.nearby_npc: Optional[InteriorNPC] = None
        self.dialogue_active: bool = False
        self.current_dialogue: str = ""
        self.dialogue_timer: float = 0.0

    def _spawn_interior_npcs(self, interior: BuildingInterior) -> List:
        """Spawn NPCs for an interior based on its type."""
        # Import is done late to avoid circular reference - InteriorNPC is defined later in file
        # Define the mapping here to access InteriorNPCRole which is defined after this class
        interior_to_npcs = {
            InteriorType.OFFICE: ["OFFICER", "CLERK"],
            InteriorType.JAIL_CELL: ["PRISONER", "GUARD"],
            InteriorType.COURTROOM: ["JUDGE", "GUARD"],
            InteriorType.HOSPITAL_ROOM: ["DOCTOR", "NURSE"],
            InteriorType.BANK_LOBBY: ["BANKER", "GUARD"],
            InteriorType.BAR_ROOM: ["BARTENDER", "PATRON", "PATRON"],
            InteriorType.LIVING_ROOM: ["PATRON"],
            InteriorType.SHOP_FLOOR: ["SHOPKEEPER"],
        }
        npcs = []
        role_names = interior_to_npcs.get(interior.interior_type, [])

        # NPC spawn positions based on interior type
        spawn_positions = {
            InteriorType.OFFICE: [(interior.width // 2, interior.height // 3 - 40)],
            InteriorType.JAIL_CELL: [(50, interior.height // 2), (interior.width - 50, interior.height // 2)],
            InteriorType.COURTROOM: [(interior.width // 2, 80), (interior.width - 50, 150)],
            InteriorType.HOSPITAL_ROOM: [(interior.width - 50, interior.height // 3), (interior.width - 80, interior.height // 2)],
            InteriorType.BANK_LOBBY: [(interior.width // 2, 80), (interior.width - 50, 150)],
            InteriorType.BAR_ROOM: [(60, 80), (150, interior.height - 70), (200, interior.height - 70)],
            InteriorType.LIVING_ROOM: [(interior.width // 2 + 50, interior.height // 2)],
            InteriorType.SHOP_FLOOR: [(50, interior.height - 60)],
        }

        positions = spawn_positions.get(interior.interior_type, [(100, 100)])

        for i, role_name in enumerate(role_names):
            if i < len(positions):
                x, y = positions[i]
            else:
                # Random position if not enough predefined
                x = random.randint(50, interior.width - 50)
                y = random.randint(50, interior.height - 100)

            # Convert string role name to enum (InteriorNPCRole defined after this class)
            # We use a simple dict lookup since the enum isn't available here
            role_map = {
                "BARTENDER": "bartender", "CLERK": "clerk", "OFFICER": "officer",
                "JUDGE": "judge", "DOCTOR": "doctor", "NURSE": "nurse",
                "PRISONER": "prisoner", "BANKER": "banker", "SHOPKEEPER": "shopkeeper",
                "PATRON": "patron", "GUARD": "guard"
            }
            role_value = role_map.get(role_name, "patron")

            # Create a simple NPC dict that will be converted to InteriorNPC later
            # For now, store as tuple (x, y, role_value) and convert in enter_building
            npcs.append((x, y, role_value))

        return npcs

    def enter_building(self, building: SpecialBuilding) -> bool:
        """Enter a building, creating its interior."""
        if not building.enterable:
            return False

        interior_type = self.BUILDING_TO_INTERIOR.get(
            building.building_type,
            InteriorType.OFFICE
        )

        self.current_interior = BuildingInterior(
            width=self.interior_width,
            height=self.interior_height,
            interior_type=interior_type
        )

        # Spawn NPCs for this interior (returns tuples, convert to InteriorNPC)
        npc_data = self._spawn_interior_npcs(self.current_interior)
        self.current_interior.npcs = []
        for x, y, role_value in npc_data:
            # InteriorNPCRole is defined after this class, access by value
            try:
                role = InteriorNPCRole(role_value)
            except (ValueError, NameError):
                # Fallback - create with a default role
                role = InteriorNPCRole.PATRON
            npc = InteriorNPC(x=x, y=y, role=role)
            self.current_interior.npcs.append(npc)

        self.current_building = building
        self.is_inside = True

        # Place player near entrance
        self.interior_player_x = self.interior_width // 2
        self.interior_player_y = self.interior_height - 50

        # Reset interaction state
        self.nearby_npc = None
        self.dialogue_active = False
        self.current_dialogue = ""

        return True

    def exit_building(self) -> Tuple[float, float]:
        """Exit the current building. Returns the door position to place player."""
        if not self.is_inside or not self.current_building:
            return (0, 0)

        door_x = self.current_building.door_x
        door_y = self.current_building.door_y + 30  # Slightly below door
        self.current_interior = None
        self.current_building = None
        self.is_inside = False

        return (door_x, door_y)

    def update(self, keys_pressed: dict, dt: float) -> str:
        """Update interior state. Returns action string."""
        if not self.is_inside or not self.current_interior:
            return ""

        # Update dialogue timer
        if self.dialogue_active:
            self.dialogue_timer -= dt
            if self.dialogue_timer <= 0:
                self.dialogue_active = False
                self.current_dialogue = ""

        # Movement
        speed = 150 * dt
        dx, dy = 0, 0

        if keys_pressed.get(pygame.K_LEFT) or keys_pressed.get(pygame.K_a):
            dx = -speed
        if keys_pressed.get(pygame.K_RIGHT) or keys_pressed.get(pygame.K_d):
            dx = speed
        if keys_pressed.get(pygame.K_UP) or keys_pressed.get(pygame.K_w):
            dy = -speed
        if keys_pressed.get(pygame.K_DOWN) or keys_pressed.get(pygame.K_s):
            dy = speed

        # Apply movement with collision
        new_x = self.interior_player_x + dx
        new_y = self.interior_player_y + dy

        # Check furniture collision
        player_rect = pygame.Rect(new_x - 10, new_y - 10, 20, 20)
        collision = False
        for furniture in self.current_interior.furniture:
            furn_rect = pygame.Rect(furniture.x, furniture.y,
                                   furniture.width, furniture.height)
            if player_rect.colliderect(furn_rect):
                collision = True
                break

        if not collision:
            # Keep within bounds
            self.interior_player_x = max(20, min(self.interior_width - 20, new_x))
            self.interior_player_y = max(20, min(self.interior_height - 20, new_y))

        # Check for nearby NPCs
        self.nearby_npc = None
        for npc in self.current_interior.npcs:
            dist = math.sqrt((self.interior_player_x - npc.x) ** 2 +
                           (self.interior_player_y - npc.y) ** 2)
            if dist < 40:
                self.nearby_npc = npc
                break

        # Check exit
        if self.current_interior.is_near_exit(
            self.interior_player_x, self.interior_player_y
        ):
            return "near_exit"

        # Check for nearby NPC
        if self.nearby_npc:
            return "near_npc"

        return ""

    def interact_with_npc(self, quest_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Interact with nearby NPC. Returns (npc_name, dialogue) or (None, None)."""
        if not self.nearby_npc:
            return None, None

        npc = self.nearby_npc
        dialogue = npc.get_dialogue(quest_id)
        npc.talked_to = True

        # Show dialogue
        self.dialogue_active = True
        self.current_dialogue = dialogue
        self.dialogue_timer = 4.0

        return npc.name, dialogue

    def get_current_building_type(self) -> Optional[str]:
        """Get the current building type as a string."""
        if self.current_building:
            return self.current_building.building_type.value
        return None

    def draw(self, screen: pygame.Surface):
        """Draw the interior and player."""
        if not self.is_inside or not self.current_interior:
            return

        # Dim background
        dim_surface = pygame.Surface((self.screen_width, self.screen_height))
        dim_surface.fill((0, 0, 0))
        dim_surface.set_alpha(150)
        screen.blit(dim_surface, (0, 0))

        # Draw interior
        self.current_interior.draw(screen, self.interior_offset_x, self.interior_offset_y)

        # Draw NPCs
        for npc in self.current_interior.npcs:
            is_nearby = (npc == self.nearby_npc)
            npc.draw(screen, self.interior_offset_x, self.interior_offset_y, highlight=is_nearby)

        # Draw player
        player_screen_x = int(self.interior_player_x) + self.interior_offset_x
        player_screen_y = int(self.interior_player_y) + self.interior_offset_y

        # Simple player representation
        pygame.draw.circle(screen, (100, 100, 200), (player_screen_x, player_screen_y), 10)
        pygame.draw.circle(screen, (50, 50, 150), (player_screen_x, player_screen_y), 10, 2)

        # Building name header
        if self.current_building:
            font = pygame.font.Font(None, 32)
            name_text = font.render(self.current_building.name, True, (255, 255, 255))
            name_rect = name_text.get_rect(centerx=self.screen_width // 2, y=20)
            # Background
            bg_rect = name_rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(screen, (100, 100, 100), bg_rect, 2)
            screen.blit(name_text, name_rect)

        # Exit prompt if near exit
        if self.current_interior.is_near_exit(
            self.interior_player_x, self.interior_player_y
        ):
            font = pygame.font.Font(None, 24)
            prompt = font.render("Press E to Exit", True, (255, 255, 100))
            prompt_rect = prompt.get_rect(centerx=self.screen_width // 2,
                                         y=self.screen_height - 50)
            screen.blit(prompt, prompt_rect)

        # NPC interaction prompt
        elif self.nearby_npc and not self.dialogue_active:
            font = pygame.font.Font(None, 24)
            prompt = font.render(f"Press E to talk to {self.nearby_npc.name}", True, (255, 255, 100))
            prompt_rect = prompt.get_rect(centerx=self.screen_width // 2,
                                         y=self.screen_height - 50)
            screen.blit(prompt, prompt_rect)

        # Draw dialogue box if active
        if self.dialogue_active and self.current_dialogue:
            self._draw_dialogue_box(screen)

    def _draw_dialogue_box(self, screen: pygame.Surface):
        """Draw the NPC dialogue box."""
        # Dialogue box dimensions
        box_width = int(self.screen_width * 0.6)
        box_height = 80
        box_x = (self.screen_width - box_width) // 2
        box_y = self.screen_height - 120

        # Background
        pygame.draw.rect(screen, (20, 20, 30), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (100, 100, 120), (box_x, box_y, box_width, box_height), 2)

        # NPC name
        if self.nearby_npc:
            font_name = pygame.font.Font(None, 24)
            name_surf = font_name.render(self.nearby_npc.name, True, (200, 200, 100))
            screen.blit(name_surf, (box_x + 10, box_y + 8))

        # Dialogue text (wrap if needed)
        font_text = pygame.font.Font(None, 22)
        words = self.current_dialogue.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font_text.size(test_line)[0] < box_width - 20:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)

        # Draw lines
        for i, line in enumerate(lines[:3]):  # Max 3 lines
            line_surf = font_text.render(line, True, (220, 220, 220))
            screen.blit(line_surf, (box_x + 10, box_y + 30 + i * 18))


# =============================================================================
# ROAD NETWORK (for vehicle pathfinding)
# =============================================================================

@dataclass(eq=False)
class RoadNode:
    """A node in the road network."""
    x: float
    y: float
    connections: List['RoadNode'] = field(default_factory=list)

    def __hash__(self):
        """Hash by position (unique identifier)."""
        return hash((self.x, self.y))

    def __eq__(self, other):
        """Equality by position."""
        if not isinstance(other, RoadNode):
            return False
        return self.x == other.x and self.y == other.y


class RoadNetwork:
    """Network of roads for vehicle navigation."""

    def __init__(self):
        self.nodes: List[RoadNode] = []
        self.segments: List[Tuple[int, int, int, int]] = []

    def build_from_grid(self, world_width: int, world_height: int,
                        block_width: int, block_height: int, road_width: int):
        """Build road network from city grid."""
        # Create nodes at intersections
        cols = world_width // (block_width + road_width)
        rows = world_height // (block_height + road_width)

        node_grid = {}

        for row in range(rows + 1):
            for col in range(cols + 1):
                x = col * (block_width + road_width) + road_width // 2
                y = row * (block_height + road_width) + road_width // 2
                node = RoadNode(x=x, y=y)
                self.nodes.append(node)
                node_grid[(col, row)] = node

        # Connect adjacent nodes
        for row in range(rows + 1):
            for col in range(cols + 1):
                node = node_grid.get((col, row))
                if not node:
                    continue

                # Connect to right neighbor
                right = node_grid.get((col + 1, row))
                if right:
                    node.connections.append(right)
                    right.connections.append(node)
                    self.segments.append((int(node.x), int(node.y), int(right.x), int(right.y)))

                # Connect to bottom neighbor
                bottom = node_grid.get((col, row + 1))
                if bottom:
                    node.connections.append(bottom)
                    bottom.connections.append(node)
                    self.segments.append((int(node.x), int(node.y), int(bottom.x), int(bottom.y)))

    def get_nearest_node(self, x: float, y: float) -> Optional[RoadNode]:
        """Get the nearest road node to a position."""
        nearest = None
        min_dist = float('inf')

        for node in self.nodes:
            dx = node.x - x
            dy = node.y - y
            dist = dx * dx + dy * dy
            if dist < min_dist:
                min_dist = dist
                nearest = node

        return nearest

    def get_random_path(self, start_x: float, start_y: float, length: int = 5) -> List[Tuple[float, float]]:
        """Get a random path starting from near the given position."""
        start_node = self.get_nearest_node(start_x, start_y)
        if not start_node:
            return []

        path = [(start_node.x, start_node.y)]
        current = start_node
        visited = {start_node}

        for _ in range(length):
            # Get unvisited connections
            options = [n for n in current.connections if n not in visited]
            if not options:
                # Dead end, allow revisiting
                options = current.connections

            if options:
                next_node = random.choice(options)
                path.append((next_node.x, next_node.y))
                visited.add(next_node)
                current = next_node

        return path


# =============================================================================
# INTERIOR NPCs
# =============================================================================

class InteriorNPCRole(Enum):
    """Roles for NPCs inside buildings."""
    BARTENDER = "bartender"
    CLERK = "clerk"
    OFFICER = "officer"
    JUDGE = "judge"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PRISONER = "prisoner"
    BANKER = "banker"
    SHOPKEEPER = "shopkeeper"
    PATRON = "patron"
    GUARD = "guard"


@dataclass
class InteriorNPC:
    """An NPC inside a building."""
    x: float
    y: float
    role: InteriorNPCRole
    name: str = ""

    # Appearance
    color: Tuple[int, int, int] = (100, 100, 150)
    size: int = 16
    facing: str = "down"  # up, down, left, right

    # Dialogue
    dialogue_lines: List[str] = field(default_factory=list)
    quest_dialogue: Dict[str, str] = field(default_factory=dict)  # quest_id -> dialogue
    talked_to: bool = False

    # Behavior
    stationary: bool = True
    patrol_points: List[Tuple[float, float]] = field(default_factory=list)
    current_patrol_index: int = 0

    # Quest related
    gives_quest: Optional[str] = None
    required_for_quest: Optional[str] = None

    def __post_init__(self):
        """Initialize based on role."""
        role_props = {
            InteriorNPCRole.BARTENDER: {
                "color": (80, 60, 50),
                "name": "Bartender",
                "dialogue_lines": [
                    "What'll it be?",
                    "We don't get many strangers here.",
                    "You look like you've seen things... terrible things.",
                    "The back room? Nobody goes back there anymore."
                ]
            },
            InteriorNPCRole.CLERK: {
                "color": (100, 100, 120),
                "name": "Clerk",
                "dialogue_lines": [
                    "How can I help you today?",
                    "Please take a number.",
                    "The files you're looking for... they were moved."
                ]
            },
            InteriorNPCRole.OFFICER: {
                "color": (50, 50, 100),
                "name": "Officer",
                "dialogue_lines": [
                    "Stay out of trouble, citizen.",
                    "We've had reports of strange activity.",
                    "If you see anything suspicious, report it immediately.",
                    "The case? It's... complicated."
                ]
            },
            InteriorNPCRole.JUDGE: {
                "color": (30, 30, 30),
                "name": "Judge",
                "dialogue_lines": [
                    "Order in the court!",
                    "Justice will be served.",
                    "The evidence is... troubling."
                ]
            },
            InteriorNPCRole.DOCTOR: {
                "color": (200, 200, 200),
                "name": "Doctor",
                "dialogue_lines": [
                    "How are you feeling?",
                    "The injuries I've seen lately... unnatural.",
                    "Rest is the best medicine. If only we could rest."
                ]
            },
            InteriorNPCRole.NURSE: {
                "color": (200, 180, 180),
                "name": "Nurse",
                "dialogue_lines": [
                    "The doctor will see you shortly.",
                    "Have you been taking your medication?",
                    "Room 4 is... off limits now."
                ]
            },
            InteriorNPCRole.PRISONER: {
                "color": (150, 100, 50),
                "name": "Prisoner",
                "dialogue_lines": [
                    "I didn't do it, I swear!",
                    "They put me here for asking questions.",
                    "The guards... they're not who they seem."
                ]
            },
            InteriorNPCRole.BANKER: {
                "color": (80, 80, 100),
                "name": "Banker",
                "dialogue_lines": [
                    "Your account balance is... concerning.",
                    "We've noticed some unusual transactions.",
                    "The vault? Only authorized personnel."
                ]
            },
            InteriorNPCRole.SHOPKEEPER: {
                "color": (100, 80, 60),
                "name": "Shopkeeper",
                "dialogue_lines": [
                    "Looking for something specific?",
                    "That item? Haven't had it in stock for years.",
                    "The back shelf has... special items."
                ]
            },
            InteriorNPCRole.PATRON: {
                "color": (120, 100, 80),
                "name": "Patron",
                "dialogue_lines": [
                    "...",
                    "Leave me alone.",
                    "I've seen things. You wouldn't understand."
                ]
            },
            InteriorNPCRole.GUARD: {
                "color": (60, 60, 80),
                "name": "Guard",
                "dialogue_lines": [
                    "Move along.",
                    "This area is restricted.",
                    "You don't have clearance for that."
                ]
            },
        }

        props = role_props.get(self.role, {})
        if not self.name:
            self.name = props.get("name", "NPC")
        self.color = props.get("color", self.color)
        if not self.dialogue_lines:
            self.dialogue_lines = props.get("dialogue_lines", ["..."])

    def get_dialogue(self, quest_id: Optional[str] = None) -> str:
        """Get dialogue line, prioritizing quest dialogue."""
        if quest_id and quest_id in self.quest_dialogue:
            return self.quest_dialogue[quest_id]
        return random.choice(self.dialogue_lines) if self.dialogue_lines else "..."

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0,
             highlight: bool = False):
        """Draw the interior NPC."""
        sx = int(self.x) + offset_x
        sy = int(self.y) + offset_y

        # Body
        body_rect = pygame.Rect(sx - self.size // 2, sy - self.size // 2,
                               self.size, self.size)
        pygame.draw.rect(screen, self.color, body_rect, border_radius=3)

        # Highlight if nearby
        if highlight:
            pygame.draw.rect(screen, (255, 255, 100), body_rect, 2, border_radius=3)

        # Head
        head_color = (min(255, self.color[0] + 50),
                     min(255, self.color[1] + 50),
                     min(255, self.color[2] + 30))
        pygame.draw.circle(screen, head_color, (sx, sy - self.size // 2 - 5), 6)

        # Eyes based on facing
        eye_color = (50, 50, 50)
        if self.facing == "down":
            pygame.draw.circle(screen, eye_color, (sx - 2, sy - self.size // 2 - 5), 1)
            pygame.draw.circle(screen, eye_color, (sx + 2, sy - self.size // 2 - 5), 1)
        elif self.facing == "up":
            pass  # Eyes not visible
        elif self.facing == "left":
            pygame.draw.circle(screen, eye_color, (sx - 3, sy - self.size // 2 - 5), 1)
        elif self.facing == "right":
            pygame.draw.circle(screen, eye_color, (sx + 3, sy - self.size // 2 - 5), 1)

        # Role-specific details
        if self.role == InteriorNPCRole.OFFICER:
            # Badge
            pygame.draw.circle(screen, (200, 180, 50), (sx - 5, sy - 3), 3)
        elif self.role == InteriorNPCRole.DOCTOR:
            # Stethoscope hint
            pygame.draw.arc(screen, (100, 100, 100),
                          (sx - 5, sy - 2, 10, 8), 0, 3.14, 1)
        elif self.role == InteriorNPCRole.JUDGE:
            # Robe indication (wider body)
            pygame.draw.rect(screen, (20, 20, 20),
                           (sx - self.size // 2 - 2, sy - 2, self.size + 4, 8))
        elif self.role == InteriorNPCRole.PRISONER:
            # Stripes
            for i in range(3):
                pygame.draw.line(screen, (100, 100, 100),
                               (sx - self.size // 2 + 2, sy - self.size // 2 + 4 + i * 5),
                               (sx + self.size // 2 - 2, sy - self.size // 2 + 4 + i * 5), 1)


# =============================================================================
# QUEST SYSTEM
# =============================================================================

class QuestStatus(Enum):
    """Status of a quest."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestObjectiveType(Enum):
    """Types of quest objectives."""
    TALK_TO_NPC = "talk_to_npc"
    VISIT_BUILDING = "visit_building"
    COLLECT_ITEM = "collect_item"
    DELIVER_ITEM = "deliver_item"
    ARREST_CRIMINAL = "arrest_criminal"
    INVESTIGATE_CLUE = "investigate_clue"
    CHASE_VEHICLE = "chase_vehicle"
    ENTER_VEHICLE = "enter_vehicle"


@dataclass
class QuestObjective:
    """A single objective within a quest."""
    objective_type: QuestObjectiveType
    description: str
    target_id: str  # NPC name, building type, item id, etc.
    completed: bool = False
    narrator_line_on_complete: str = ""

    # Optional requirements
    required_building: Optional[str] = None  # Must be in this building type
    required_item: Optional[str] = None  # Must have this item


@dataclass
class Quest:
    """A quest with multiple objectives."""
    quest_id: str
    title: str
    description: str
    objectives: List[QuestObjective]
    status: QuestStatus = QuestStatus.NOT_STARTED

    # Rewards
    karma_reward: int = 0
    item_rewards: List[str] = field(default_factory=list)

    # Narrator integration
    narrator_start_line: str = ""
    narrator_complete_line: str = ""
    narrator_fail_line: str = ""

    # Quest chain
    prerequisite_quest: Optional[str] = None
    next_quest: Optional[str] = None

    def get_current_objective(self) -> Optional[QuestObjective]:
        """Get the first incomplete objective."""
        for obj in self.objectives:
            if not obj.completed:
                return obj
        return None

    def is_complete(self) -> bool:
        """Check if all objectives are complete."""
        return all(obj.completed for obj in self.objectives)

    def complete_objective(self, objective_type: QuestObjectiveType, target_id: str) -> Tuple[bool, str]:
        """Try to complete an objective. Returns (success, narrator_line)."""
        current = self.get_current_objective()
        if current and current.objective_type == objective_type and current.target_id == target_id:
            current.completed = True
            narrator_line = current.narrator_line_on_complete

            # Check if quest is now complete
            if self.is_complete():
                self.status = QuestStatus.COMPLETED
                narrator_line = self.narrator_complete_line or narrator_line

            return True, narrator_line
        return False, ""


class QuestManager:
    """Manages all quests in the game."""

    def __init__(self):
        self.available_quests: Dict[str, Quest] = {}
        self.active_quests: Dict[str, Quest] = {}
        self.completed_quests: Dict[str, Quest] = {}
        self._create_starter_quests()

    def _create_starter_quests(self):
        """Create the initial starter quests."""
        # Quest 1: The Missing Report
        missing_report = Quest(
            quest_id="missing_report",
            title="The Missing Report",
            description="Officer Jenkins needs help finding a missing police report. Check the courthouse and bar for leads.",
            objectives=[
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Talk to Officer Jenkins at the Police Station",
                    target_id="Officer",
                    narrator_line_on_complete="The officer's eyes dart nervously. Something troubles him deeply.",
                    required_building="police_station"
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.VISIT_BUILDING,
                    description="Visit the Courthouse to search for records",
                    target_id="courthouse",
                    narrator_line_on_complete="The courthouse... so many secrets buried in its halls."
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Question the Bartender about the missing report",
                    target_id="Bartender",
                    narrator_line_on_complete="The bartender knows more than he's saying. They always do.",
                    required_building="bar"
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Return to Officer Jenkins with your findings",
                    target_id="Officer",
                    narrator_line_on_complete="",
                    required_building="police_station"
                ),
            ],
            narrator_start_line="A simple errand, they say. But nothing in this city is simple.",
            narrator_complete_line="The report is found, but the questions it raises... those may never be answered.",
            karma_reward=10,
            next_quest="strange_deliveries"
        )
        self.available_quests["missing_report"] = missing_report

        # Quest 2: Strange Deliveries
        strange_deliveries = Quest(
            quest_id="strange_deliveries",
            title="Strange Deliveries",
            description="The shopkeeper has noticed suspicious packages. Investigate the bank and hospital.",
            objectives=[
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Talk to the Shopkeeper about the deliveries",
                    target_id="Shopkeeper",
                    narrator_line_on_complete="Packages that arrive but never leave. How curious.",
                    required_building="shop"
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.VISIT_BUILDING,
                    description="Check the Bank for suspicious activity",
                    target_id="bank",
                    narrator_line_on_complete="The bank's vault holds more than money."
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Question the Doctor at the Hospital",
                    target_id="Doctor",
                    narrator_line_on_complete="The doctor's hands tremble. What has he witnessed?",
                    required_building="hospital"
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.INVESTIGATE_CLUE,
                    description="Find evidence of the deliveries",
                    target_id="delivery_manifest",
                    narrator_line_on_complete="The manifest reveals a pattern. A terrible pattern."
                ),
            ],
            narrator_start_line="Follow the packages, and you'll find the truth. Or the truth will find you.",
            narrator_complete_line="The delivery network exposed. But who ordered the shipments?",
            karma_reward=15,
            prerequisite_quest="missing_report",
            next_quest="the_prisoner"
        )
        self.available_quests["strange_deliveries"] = strange_deliveries

        # Quest 3: The Prisoner's Tale
        the_prisoner = Quest(
            quest_id="the_prisoner",
            title="The Prisoner's Tale",
            description="A prisoner in the jail claims to know the truth. But can you trust him?",
            objectives=[
                QuestObjective(
                    objective_type=QuestObjectiveType.VISIT_BUILDING,
                    description="Enter the Jail",
                    target_id="jail",
                    narrator_line_on_complete="The jail... where the guilty and innocent alike rot."
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Speak with the Prisoner",
                    target_id="Prisoner",
                    narrator_line_on_complete="His words are desperate. But desperation often births truth.",
                    required_building="jail"
                ),
                QuestObjective(
                    objective_type=QuestObjectiveType.TALK_TO_NPC,
                    description="Confront the Judge with the prisoner's claims",
                    target_id="Judge",
                    narrator_line_on_complete="The judge's face... did you see it? The mask slipped, just for a moment.",
                    required_building="courthouse"
                ),
            ],
            narrator_start_line="They say every prisoner claims innocence. But this one... this one might be telling the truth.",
            narrator_complete_line="The truth is revealed. But truth, in this city, is a dangerous thing to possess.",
            karma_reward=20,
            prerequisite_quest="strange_deliveries"
        )
        self.available_quests["the_prisoner"] = the_prisoner

    def start_quest(self, quest_id: str) -> Tuple[bool, str]:
        """Start a quest. Returns (success, narrator_line)."""
        if quest_id not in self.available_quests:
            return False, ""

        quest = self.available_quests[quest_id]

        # Check prerequisite
        if quest.prerequisite_quest and quest.prerequisite_quest not in self.completed_quests:
            return False, "You're not ready for this yet."

        # Move to active
        del self.available_quests[quest_id]
        self.active_quests[quest_id] = quest
        quest.status = QuestStatus.ACTIVE

        return True, quest.narrator_start_line

    def update_quest_progress(self, objective_type: QuestObjectiveType, target_id: str,
                              current_building: Optional[str] = None) -> List[Tuple[str, str]]:
        """Update quest progress. Returns list of (quest_id, narrator_line) for completed objectives."""
        results = []

        for quest_id, quest in list(self.active_quests.items()):
            current_obj = quest.get_current_objective()
            if not current_obj:
                continue

            # Check building requirement
            if current_obj.required_building and current_building != current_obj.required_building:
                continue

            success, narrator_line = quest.complete_objective(objective_type, target_id)
            if success:
                results.append((quest_id, narrator_line))

                # Check if quest completed
                if quest.status == QuestStatus.COMPLETED:
                    del self.active_quests[quest_id]
                    self.completed_quests[quest_id] = quest

                    # Unlock next quest
                    if quest.next_quest and quest.next_quest in self.available_quests:
                        # Next quest is now available
                        pass

        return results

    def get_active_quest_info(self) -> List[Tuple[str, str, str]]:
        """Get info about active quests. Returns list of (title, current_objective, quest_id)."""
        info = []
        for quest_id, quest in self.active_quests.items():
            current = quest.get_current_objective()
            if current:
                info.append((quest.title, current.description, quest_id))
        return info


# =============================================================================
# VEHICLE INTERACTION
# =============================================================================

class VehicleState(Enum):
    """State of a vehicle the player can interact with."""
    PARKED = "parked"
    DRIVING = "driving"
    PLAYER_DRIVING = "player_driving"
    CHASING = "chasing"
    FLEEING = "fleeing"


@dataclass
class InteractableVehicle(Vehicle):
    """A vehicle the player can enter and drive."""
    state: VehicleState = VehicleState.DRIVING
    owner: Optional[str] = None  # NPC id or None if unowned
    locked: bool = False
    fuel: float = 100.0
    damage: float = 0.0

    # Chase related
    chase_target: Optional[any] = None
    fleeing_from: Optional[any] = None

    # Stolen
    is_stolen: bool = False
    wanted_level: int = 0  # 0-5 stars

    def can_enter(self, player_karma: int) -> Tuple[bool, str]:
        """Check if player can enter this vehicle."""
        if self.state == VehicleState.PLAYER_DRIVING:
            return False, "You're already in this vehicle."

        if self.locked and self.owner:
            if player_karma < -20:
                return True, "The lock looks flimsy... you could break in."
            return False, "The vehicle is locked."

        if self.owner and self.state == VehicleState.DRIVING:
            return False, "Someone is driving this vehicle."

        return True, "Press E to enter."

    def enter(self, is_stealing: bool = False) -> str:
        """Player enters the vehicle."""
        self.state = VehicleState.PLAYER_DRIVING
        if is_stealing:
            self.is_stolen = True
            self.wanted_level = 1
            return "You break into the vehicle. Sirens might follow."
        return "You get in the vehicle."

    def exit(self) -> Tuple[float, float]:
        """Player exits. Returns position to place player."""
        self.state = VehicleState.PARKED
        # Exit to the left of the vehicle
        exit_x = self.x - self.width
        exit_y = self.y
        return exit_x, exit_y

    def start_chase(self, target) -> str:
        """Start chasing a target."""
        self.state = VehicleState.CHASING
        self.chase_target = target
        return "The chase is on!"

    def flee(self, threat) -> str:
        """Start fleeing from a threat."""
        self.state = VehicleState.FLEEING
        self.fleeing_from = threat
        return "Time to get out of here!"


class VehicleInteractionManager:
    """Manages player interaction with vehicles."""

    def __init__(self):
        self.player_vehicle: Optional[InteractableVehicle] = None
        self.nearby_vehicles: List[InteractableVehicle] = []
        self.chase_active: bool = False
        self.chase_target: Optional[InteractableVehicle] = None

        # Driving controls
        self.acceleration: float = 0.0
        self.steering: float = 0.0
        self.max_speed: float = 8.0
        self.current_speed: float = 0.0

    def find_nearby_vehicle(self, player_x: float, player_y: float,
                           vehicles: List[Vehicle], radius: float = 40) -> Optional[InteractableVehicle]:
        """Find a vehicle near the player."""
        for vehicle in vehicles:
            dx = vehicle.x - player_x
            dy = vehicle.y - player_y
            if math.sqrt(dx * dx + dy * dy) < radius:
                # Convert to interactable if needed
                if isinstance(vehicle, InteractableVehicle):
                    return vehicle
                else:
                    # Wrap regular vehicle
                    return InteractableVehicle(
                        x=vehicle.x, y=vehicle.y,
                        vehicle_type=vehicle.vehicle_type,
                        direction=vehicle.direction,
                        speed=vehicle.speed,
                        state=VehicleState.PARKED if not vehicle.path else VehicleState.DRIVING
                    )
        return None

    def enter_vehicle(self, vehicle: InteractableVehicle, player_karma: int) -> Tuple[bool, str]:
        """Try to enter a vehicle."""
        can_enter, message = vehicle.can_enter(player_karma)
        if not can_enter:
            return False, message

        is_stealing = vehicle.owner is not None and vehicle.locked
        result_message = vehicle.enter(is_stealing)
        self.player_vehicle = vehicle
        return True, result_message

    def exit_vehicle(self) -> Tuple[Optional[Tuple[float, float]], str]:
        """Exit current vehicle."""
        if not self.player_vehicle:
            return None, "You're not in a vehicle."

        exit_pos = self.player_vehicle.exit()
        self.player_vehicle = None
        self.current_speed = 0
        return exit_pos, "You exit the vehicle."

    def update_driving(self, keys_pressed: dict, dt: float) -> Tuple[float, float]:
        """Update vehicle when player is driving. Returns (dx, dy) movement."""
        if not self.player_vehicle:
            return 0, 0

        vehicle = self.player_vehicle

        # Acceleration
        if keys_pressed.get(pygame.K_UP) or keys_pressed.get(pygame.K_w):
            self.current_speed = min(self.max_speed, self.current_speed + 0.2)
        elif keys_pressed.get(pygame.K_DOWN) or keys_pressed.get(pygame.K_s):
            self.current_speed = max(-self.max_speed / 2, self.current_speed - 0.3)
        else:
            # Friction
            self.current_speed *= 0.95
            if abs(self.current_speed) < 0.1:
                self.current_speed = 0

        # Steering (only when moving)
        if abs(self.current_speed) > 0.5:
            turn_rate = 0.05 * (1 - abs(self.current_speed) / self.max_speed * 0.5)
            if keys_pressed.get(pygame.K_LEFT) or keys_pressed.get(pygame.K_a):
                angle = math.atan2(vehicle.direction[1], vehicle.direction[0])
                angle -= turn_rate
                vehicle.direction = (math.cos(angle), math.sin(angle))
            elif keys_pressed.get(pygame.K_RIGHT) or keys_pressed.get(pygame.K_d):
                angle = math.atan2(vehicle.direction[1], vehicle.direction[0])
                angle += turn_rate
                vehicle.direction = (math.cos(angle), math.sin(angle))

        # Apply movement
        dx = vehicle.direction[0] * self.current_speed * dt * 60
        dy = vehicle.direction[1] * self.current_speed * dt * 60

        vehicle.x += dx
        vehicle.y += dy

        # Consume fuel
        vehicle.fuel = max(0, vehicle.fuel - abs(self.current_speed) * 0.01)

        return dx, dy

    def start_chase(self, target_vehicle: InteractableVehicle) -> str:
        """Start a chase sequence."""
        if not self.player_vehicle:
            return "You need a vehicle to chase!"

        self.chase_active = True
        self.chase_target = target_vehicle
        target_vehicle.state = VehicleState.FLEEING
        target_vehicle.fleeing_from = self.player_vehicle

        return "The chase begins! Don't let them escape!"

    def update_chase(self, dt: float) -> Tuple[bool, str]:
        """Update chase logic. Returns (chase_ended, message)."""
        if not self.chase_active or not self.chase_target or not self.player_vehicle:
            return False, ""

        target = self.chase_target
        player_v = self.player_vehicle

        # Distance check
        dx = target.x - player_v.x
        dy = target.y - player_v.y
        distance = math.sqrt(dx * dx + dy * dy)

        # Catch check
        if distance < 30:
            self.chase_active = False
            target.state = VehicleState.PARKED
            return True, "Target apprehended!"

        # Escape check
        if distance > 500:
            self.chase_active = False
            return True, "The target escaped..."

        # Target AI - flee behavior
        flee_dir_x = -dx / distance if distance > 0 else random.choice([-1, 1])
        flee_dir_y = -dy / distance if distance > 0 else random.choice([-1, 1])

        # Add some randomness
        flee_dir_x += random.uniform(-0.3, 0.3)
        flee_dir_y += random.uniform(-0.3, 0.3)

        # Normalize
        flee_len = math.sqrt(flee_dir_x ** 2 + flee_dir_y ** 2)
        if flee_len > 0:
            target.direction = (flee_dir_x / flee_len, flee_dir_y / flee_len)

        # Move target
        target.x += target.direction[0] * target.speed * 1.2 * dt * 60
        target.y += target.direction[1] * target.speed * 1.2 * dt * 60

        return False, ""

    def is_driving(self) -> bool:
        """Check if player is currently driving."""
        return self.player_vehicle is not None


# =============================================================================
# PEDESTRIAN/TRAFFIC SEGREGATION
# =============================================================================

class TrafficZone(Enum):
    """Types of traffic zones."""
    ROAD = "road"
    SIDEWALK = "sidewalk"
    CROSSWALK = "crosswalk"
    INTERSECTION = "intersection"


@dataclass
class TrafficNode:
    """A node in the traffic network with zone information."""
    x: float
    y: float
    zone: TrafficZone
    connections: List['TrafficNode'] = field(default_factory=list)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, TrafficNode):
            return False
        return self.x == other.x and self.y == other.y


class TrafficManager:
    """Manages traffic flow and zone enforcement."""

    def __init__(self, city_config):
        self.config = city_config
        self.road_zones: List[pygame.Rect] = []
        self.sidewalk_zones: List[pygame.Rect] = []
        self.crosswalk_zones: List[pygame.Rect] = []

    def build_zones(self, city_map):
        """Build traffic zones from city map."""
        road_width = self.config.road_width
        sidewalk_width = self.config.sidewalk_width
        block_w = self.config.block_width
        block_h = self.config.block_height

        world_w = self.config.world_width
        world_h = self.config.world_height

        # Calculate grid
        cols = world_w // (block_w + road_width)
        rows = world_h // (block_h + road_width)

        for row in range(rows + 1):
            for col in range(cols + 1):
                # Intersection center
                int_x = col * (block_w + road_width)
                int_y = row * (block_h + road_width)

                # Horizontal road segment
                if col < cols:
                    road_rect = pygame.Rect(
                        int_x + sidewalk_width,
                        int_y + sidewalk_width,
                        block_w + road_width - sidewalk_width * 2,
                        road_width - sidewalk_width * 2
                    )
                    self.road_zones.append(road_rect)

                    # Sidewalks along horizontal road
                    top_sidewalk = pygame.Rect(
                        int_x, int_y,
                        block_w + road_width, sidewalk_width
                    )
                    bottom_sidewalk = pygame.Rect(
                        int_x, int_y + road_width - sidewalk_width,
                        block_w + road_width, sidewalk_width
                    )
                    self.sidewalk_zones.extend([top_sidewalk, bottom_sidewalk])

                # Vertical road segment
                if row < rows:
                    road_rect = pygame.Rect(
                        int_x + sidewalk_width,
                        int_y + sidewalk_width,
                        road_width - sidewalk_width * 2,
                        block_h + road_width - sidewalk_width * 2
                    )
                    self.road_zones.append(road_rect)

                    # Sidewalks along vertical road
                    left_sidewalk = pygame.Rect(
                        int_x, int_y,
                        sidewalk_width, block_h + road_width
                    )
                    right_sidewalk = pygame.Rect(
                        int_x + road_width - sidewalk_width, int_y,
                        sidewalk_width, block_h + road_width
                    )
                    self.sidewalk_zones.extend([left_sidewalk, right_sidewalk])

                # Crosswalks at intersections
                if col < cols and row < rows:
                    # Horizontal crosswalk
                    h_crosswalk = pygame.Rect(
                        int_x + road_width // 4,
                        int_y + road_width // 2 - 5,
                        road_width // 2, 10
                    )
                    # Vertical crosswalk
                    v_crosswalk = pygame.Rect(
                        int_x + road_width // 2 - 5,
                        int_y + road_width // 4,
                        10, road_width // 2
                    )
                    self.crosswalk_zones.extend([h_crosswalk, v_crosswalk])

    def get_zone(self, x: float, y: float) -> TrafficZone:
        """Get the traffic zone at a position."""
        point = (x, y)

        for rect in self.crosswalk_zones:
            if rect.collidepoint(point):
                return TrafficZone.CROSSWALK

        for rect in self.road_zones:
            if rect.collidepoint(point):
                return TrafficZone.ROAD

        for rect in self.sidewalk_zones:
            if rect.collidepoint(point):
                return TrafficZone.SIDEWALK

        return TrafficZone.SIDEWALK  # Default to sidewalk (buildings, etc.)

    def is_valid_for_pedestrian(self, x: float, y: float) -> bool:
        """Check if position is valid for pedestrians."""
        zone = self.get_zone(x, y)
        return zone in (TrafficZone.SIDEWALK, TrafficZone.CROSSWALK)

    def is_valid_for_vehicle(self, x: float, y: float) -> bool:
        """Check if position is valid for vehicles."""
        zone = self.get_zone(x, y)
        return zone in (TrafficZone.ROAD, TrafficZone.CROSSWALK, TrafficZone.INTERSECTION)

    def get_nearest_valid_position(self, x: float, y: float,
                                   for_pedestrian: bool = True) -> Tuple[float, float]:
        """Get the nearest valid position for entity type."""
        # Simple implementation - snap to nearest zone
        target_zones = self.sidewalk_zones if for_pedestrian else self.road_zones

        min_dist = float('inf')
        best_pos = (x, y)

        for rect in target_zones:
            # Center of zone
            cx = rect.centerx
            cy = rect.centery
            dist = (x - cx) ** 2 + (y - cy) ** 2
            if dist < min_dist:
                min_dist = dist
                # Clamp to inside rect
                best_pos = (
                    max(rect.left, min(rect.right, x)),
                    max(rect.top, min(rect.bottom, y))
                )

        return best_pos
