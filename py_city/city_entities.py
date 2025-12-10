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
    parked: bool = False  # Parked cars don't move

    # Path following
    path: List[Tuple[float, float]] = field(default_factory=list)
    path_index: int = 0

    def __post_init__(self):
        """Set color based on vehicle type."""
        type_colors = {
            # Expanded car palette - common real car colors
            VehicleType.CAR: [
                (180, 50, 50),    # Red
                (50, 50, 180),    # Blue
                (50, 150, 50),    # Green
                (180, 180, 50),   # Yellow
                (100, 100, 100),  # Gray
                (200, 200, 200),  # Silver
                (30, 30, 30),     # Black
                (240, 240, 240),  # White
                (150, 80, 50),    # Brown
                (80, 130, 150),   # Teal
                (140, 70, 140),   # Purple
                (200, 100, 50),   # Orange
                (70, 90, 80),     # Dark green
                (120, 80, 60),    # Bronze
            ],
            VehicleType.TRUCK: [
                (80, 80, 80),     # Dark gray
                (100, 80, 60),    # Brown
                (60, 80, 100),    # Blue-gray
                (180, 50, 50),    # Red
                (240, 240, 240),  # White
                (30, 30, 30),     # Black
            ],
            VehicleType.BUS: [
                (200, 150, 50),   # Yellow (school bus)
                (50, 100, 150),   # Blue (city bus)
                (150, 150, 150),  # Gray (transit)
                (180, 50, 50),    # Red (tour bus)
            ],
            VehicleType.POLICE_CAR: [(30, 30, 30)],  # Black with lights
            VehicleType.AMBULANCE: [(255, 255, 255)],  # White with cross
            VehicleType.TAXI: [(255, 200, 50), (255, 220, 80)],  # Yellow variants
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
        """Update vehicle position."""
        # Parked cars don't move
        if self.parked:
            return

        if self.waiting:
            self.wait_timer -= dt
            if self.wait_timer <= 0:
                self.waiting = False
            return

        # Move along path
        if self.path and self.path_index < len(self.path):
            target_x, target_y = self.path[self.path_index]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 5:  # Reached waypoint
                self.path_index += 1
                if self.path_index >= len(self.path):
                    # Generate new path
                    if road_network:
                        self.path = road_network.get_random_path(self.x, self.y)
                        self.path_index = 0
            else:
                # Move toward waypoint
                self.direction = (dx / dist, dy / dist)
                self.x += self.direction[0] * self.speed * dt * 60
                self.y += self.direction[1] * self.speed * dt * 60

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

        # Type-specific details (police lights drawn last for visibility)
        if self.vehicle_type == VehicleType.AMBULANCE:
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

        # Police car light bar - drawn LAST to ensure visibility on top of everything
        if self.vehicle_type == VehicleType.POLICE_CAR:
            light_time = pygame.time.get_ticks()
            flash_phase = (light_time // 150) % 2

            # Light bar background (black bar across roof)
            if horizontal:
                bar_rect = pygame.Rect(cx - 10, cy - 5, 20, 8)
            else:
                bar_rect = pygame.Rect(cx - 5, cy - 10, 8, 20)
            pygame.draw.rect(screen, (20, 20, 25), bar_rect, border_radius=2)

            # Flashing lights - bright and prominent
            if flash_phase == 0:
                # Red bright, blue dim
                red_color = (255, 60, 60)
                blue_color = (40, 60, 120)
            else:
                # Red dim, blue bright
                red_color = (120, 30, 30)
                blue_color = (80, 140, 255)

            if horizontal:
                # Lights side by side on roof
                pygame.draw.rect(screen, red_color, (cx - 9, cy - 4, 8, 6), border_radius=2)
                pygame.draw.rect(screen, blue_color, (cx + 1, cy - 4, 8, 6), border_radius=2)
            else:
                # Lights stacked vertically when car is vertical
                pygame.draw.rect(screen, red_color, (cx - 4, cy - 9, 6, 8), border_radius=2)
                pygame.draw.rect(screen, blue_color, (cx - 4, cy + 1, 6, 8), border_radius=2)


class VehicleManager:
    """Manages all vehicles in the city."""

    def __init__(self, world_width: int, world_height: int, road_network: 'RoadNetwork' = None):
        self.world_width = world_width
        self.world_height = world_height
        self.road_network = road_network
        self.vehicles: List[Vehicle] = []
        self.max_vehicles = 15
        self.max_parked = 20  # Additional parked vehicles on roads
        self.max_lot_parked = 30  # Vehicles in parking lots

    def spawn_vehicles(self, road_segments: List[Tuple[int, int, int, int]], parking_lots: List = None):
        """Spawn initial vehicles on road segments."""
        # Spawn moving vehicles
        for _ in range(self.max_vehicles):
            if road_segments:
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

                # Random vehicle type (weighted)
                vtype = random.choices(
                    [VehicleType.CAR, VehicleType.TAXI, VehicleType.TRUCK,
                     VehicleType.BUS, VehicleType.POLICE_CAR],
                    weights=[60, 15, 10, 8, 7]
                )[0]

                vehicle = Vehicle(x=x, y=y, vehicle_type=vtype, direction=direction)

                # Give vehicle an initial path so it starts moving
                if self.road_network:
                    vehicle.path = self.road_network.get_random_path(x, y)
                    vehicle.path_index = 0

                self.vehicles.append(vehicle)

        # Spawn parked vehicles along road edges
        self._spawn_parked_vehicles(road_segments)

        # Spawn cars in parking lots
        if parking_lots:
            self._spawn_lot_vehicles(parking_lots)

    def _spawn_parked_vehicles(self, road_segments: List[Tuple[int, int, int, int]]):
        """Spawn parked cars along the sides of roads."""
        for _ in range(self.max_parked):
            if road_segments:
                # Pick random road segment
                x1, y1, x2, y2 = random.choice(road_segments)
                t = random.random()

                # Position along the road
                road_x = x1 + t * (x2 - x1)
                road_y = y1 + t * (y2 - y1)

                # Determine road direction and offset to the side
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx * dx + dy * dy)
                if length > 0:
                    # Perpendicular offset (park on side of road)
                    perp_x, perp_y = -dy / length, dx / length
                    # Randomly choose left or right side, offset by ~20 pixels
                    side = random.choice([-1, 1])
                    offset = 18 + random.randint(-3, 3)
                    x = road_x + perp_x * offset * side
                    y = road_y + perp_y * offset * side

                    # Direction aligned with road (parked cars face along road)
                    direction = (dx / length, dy / length)
                    if random.random() < 0.5:  # Sometimes face opposite direction
                        direction = (-direction[0], -direction[1])
                else:
                    x, y = road_x, road_y
                    direction = (1, 0)

                # Only cars and trucks park (no buses, taxis, police, ambulances)
                vtype = random.choices(
                    [VehicleType.CAR, VehicleType.TRUCK],
                    weights=[85, 15]
                )[0]

                vehicle = Vehicle(x=x, y=y, vehicle_type=vtype, direction=direction, parked=True)
                self.vehicles.append(vehicle)

    def _spawn_lot_vehicles(self, parking_lots: List):
        """Spawn parked cars in parking lots."""
        if not parking_lots:
            return

        # Collect all available parking spaces
        all_spaces = []
        for lot in parking_lots:
            for space in lot.parking_spaces:
                all_spaces.append(space)

        if not all_spaces:
            return

        # Randomly select spaces to fill (about 60-80% occupancy)
        random.shuffle(all_spaces)
        num_to_spawn = min(self.max_lot_parked, int(len(all_spaces) * random.uniform(0.6, 0.8)))

        for i in range(num_to_spawn):
            if i >= len(all_spaces):
                break

            x, y, dir_x, dir_y = all_spaces[i]

            # Mostly cars, occasionally trucks and one police car
            if i == 0 and random.random() < 0.3:
                # First car might be a police car parked in the lot
                vtype = VehicleType.POLICE_CAR
            else:
                vtype = random.choices(
                    [VehicleType.CAR, VehicleType.TRUCK],
                    weights=[90, 10]
                )[0]

            vehicle = Vehicle(
                x=x, y=y,
                vehicle_type=vtype,
                direction=(dir_x, dir_y),
                parked=True
            )
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

    def get_building_by_type(self, building_type: SpecialBuildingType) -> Optional[SpecialBuilding]:
        """Get a special building by its type."""
        for building in self.buildings:
            if building.building_type == building_type:
                return building
        return None

    @property
    def jail(self) -> Optional[SpecialBuilding]:
        """Get the jail building."""
        return self.get_building_by_type(SpecialBuildingType.JAIL)

    @property
    def police_station(self) -> Optional[SpecialBuilding]:
        """Get the police station."""
        return self.get_building_by_type(SpecialBuildingType.POLICE_STATION)

    @property
    def hospital(self) -> Optional[SpecialBuilding]:
        """Get the hospital."""
        return self.get_building_by_type(SpecialBuildingType.HOSPITAL)

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
# ROAD NETWORK (for vehicle pathfinding)
# =============================================================================

@dataclass(eq=False)
class RoadNode:
    """A node in the road network."""
    x: float
    y: float
    connections: List['RoadNode'] = field(default_factory=list)

    def __hash__(self):
        """Hash based on position (unique per node)."""
        return hash((self.x, self.y))


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
