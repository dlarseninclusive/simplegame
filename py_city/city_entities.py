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
        # Exit door at bottom center
        self.exit_x = self.width // 2
        self.exit_y = self.height - 10

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
        self.current_building = building
        self.is_inside = True

        # Place player near entrance
        self.interior_player_x = self.interior_width // 2
        self.interior_player_y = self.interior_height - 50

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

        # Check exit
        if self.current_interior.is_near_exit(
            self.interior_player_x, self.interior_player_y
        ):
            return "near_exit"

        return ""

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
