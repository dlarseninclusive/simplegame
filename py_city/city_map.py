"""
CityMap - Large scrollable city with proper streets, sidewalks, and buildings.

Features:
- Large world map (much bigger than screen)
- Camera that follows player
- Proper city grid with blocks
- Wide roads with sidewalks
- Rain weather system with wind
- Day/night cycle
- Varied building styles
"""

import random
import math
import pygame
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum


class TimeOfDay(Enum):
    """Time periods affecting gameplay and visuals."""
    DAWN = "dawn"        # 5:00 - 7:00
    MORNING = "morning"  # 7:00 - 12:00
    AFTERNOON = "afternoon"  # 12:00 - 17:00
    EVENING = "evening"  # 17:00 - 20:00
    NIGHT = "night"      # 20:00 - 5:00


class DayNightCycle:
    """Manages game time and day/night transitions."""

    def __init__(self, start_hour: float = 8.0, time_scale: float = 60.0):
        """
        Args:
            start_hour: Starting hour (0-24)
            time_scale: How many game seconds per real second (60 = 1 min real = 1 hr game)
        """
        self.game_hour = start_hour
        self.time_scale = time_scale
        self.day_count = 1

        # Lighting colors for different times
        self.lighting_colors = {
            TimeOfDay.DAWN: (255, 200, 180),      # Warm orange-pink
            TimeOfDay.MORNING: (255, 255, 255),   # Neutral
            TimeOfDay.AFTERNOON: (255, 250, 240), # Warm white
            TimeOfDay.EVENING: (255, 180, 120),   # Orange sunset
            TimeOfDay.NIGHT: (100, 120, 180),     # Cool blue
        }

        # Darkness overlay alpha for different times
        self.darkness_alpha = {
            TimeOfDay.DAWN: 30,
            TimeOfDay.MORNING: 0,
            TimeOfDay.AFTERNOON: 0,
            TimeOfDay.EVENING: 40,
            TimeOfDay.NIGHT: 120,
        }

    def update(self, dt: float) -> Optional[str]:
        """Update time. Returns narrator message if time period changes."""
        old_period = self.get_time_of_day()

        # Advance time (dt is in seconds, time_scale converts to game hours)
        hours_passed = (dt * self.time_scale) / 3600.0
        self.game_hour += hours_passed

        # Handle day rollover
        if self.game_hour >= 24.0:
            self.game_hour -= 24.0
            self.day_count += 1

        new_period = self.get_time_of_day()

        # Check for period transition
        if old_period != new_period:
            messages = {
                TimeOfDay.DAWN: "The city stirs. Dawn brings false hope.",
                TimeOfDay.MORNING: "Morning. The illusion of normalcy begins.",
                TimeOfDay.AFTERNOON: "Afternoon shadows grow longer.",
                TimeOfDay.EVENING: "Evening falls. They come out at night.",
                TimeOfDay.NIGHT: "Night. The city shows its true face.",
            }
            return messages.get(new_period)

        return None

    def get_time_of_day(self) -> TimeOfDay:
        """Get current time period."""
        h = self.game_hour
        if 5 <= h < 7:
            return TimeOfDay.DAWN
        elif 7 <= h < 12:
            return TimeOfDay.MORNING
        elif 12 <= h < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= h < 20:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT

    def get_hour_minute(self) -> Tuple[int, int]:
        """Get current time as (hour, minute)."""
        hour = int(self.game_hour) % 24
        minute = int((self.game_hour % 1) * 60)
        return hour, minute

    def get_time_string(self) -> str:
        """Get formatted time string."""
        h, m = self.get_hour_minute()
        period = "AM" if h < 12 else "PM"
        display_h = h % 12
        if display_h == 0:
            display_h = 12
        return f"{display_h}:{m:02d} {period}"

    def is_night(self) -> bool:
        """Check if it's nighttime (for crime bonus, etc)."""
        return self.get_time_of_day() in (TimeOfDay.NIGHT, TimeOfDay.EVENING)

    def get_lighting_tint(self) -> Tuple[int, int, int]:
        """Get current lighting color tint."""
        return self.lighting_colors.get(self.get_time_of_day(), (255, 255, 255))

    def get_darkness_alpha(self) -> int:
        """Get current darkness overlay alpha."""
        return self.darkness_alpha.get(self.get_time_of_day(), 0)

    def get_window_lit_chance(self) -> float:
        """Get probability of windows being lit based on time."""
        period = self.get_time_of_day()
        chances = {
            TimeOfDay.DAWN: 0.6,
            TimeOfDay.MORNING: 0.2,
            TimeOfDay.AFTERNOON: 0.1,
            TimeOfDay.EVENING: 0.7,
            TimeOfDay.NIGHT: 0.8,
        }
        return chances.get(period, 0.4)


@dataclass
class CityConfig:
    """Configuration for city generation."""
    # World size (in pixels) - larger for more exploration
    world_width: int = 4800
    world_height: int = 3600

    # Block layout
    block_width: int = 200  # Building block width
    block_height: int = 160  # Building block height
    road_width: int = 80  # Wide roads
    sidewalk_width: int = 16  # Sidewalk on each side of road

    # Colors
    road_color: Tuple[int, int, int] = (45, 45, 50)
    sidewalk_color: Tuple[int, int, int] = (130, 130, 130)
    grass_color: Tuple[int, int, int] = (60, 90, 50)
    building_lot_color: Tuple[int, int, int] = (70, 100, 60)
    road_line_color: Tuple[int, int, int] = (200, 200, 80)


class Camera:
    """Camera that follows the player with smooth movement."""

    def __init__(self, screen_width: int, screen_height: int,
                 world_width: int, world_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.x = 0.0
        self.y = 0.0
        self.smoothing = 0.1  # Lower = smoother/slower following

    def follow(self, target_x: float, target_y: float):
        """Smoothly follow a target position with wraparound support."""
        # Target camera position (centered on target)
        target_cam_x = target_x - self.screen_width // 2
        target_cam_y = target_y - self.screen_height // 2

        # Handle wraparound for smooth following across edges
        # Check if target wrapped around and adjust camera accordingly
        dx = target_cam_x - self.x
        dy = target_cam_y - self.y

        # If distance is more than half world, target likely wrapped
        if abs(dx) > self.world_width / 2:
            if dx > 0:
                target_cam_x -= self.world_width
            else:
                target_cam_x += self.world_width

        if abs(dy) > self.world_height / 2:
            if dy > 0:
                target_cam_y -= self.world_height
            else:
                target_cam_y += self.world_height

        # Smooth interpolation
        self.x += (target_cam_x - self.x) * self.smoothing
        self.y += (target_cam_y - self.y) * self.smoothing

        # Wraparound camera position (instead of clamping)
        self.x = self.x % self.world_width
        self.y = self.y % self.world_height

    def apply(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates with wraparound."""
        # Basic screen position
        screen_x = world_x - self.x
        screen_y = world_y - self.y

        # Handle wraparound: if object is far off screen, it might be wrapping
        # Normalize to closest representation
        if screen_x < -self.world_width / 2:
            screen_x += self.world_width
        elif screen_x > self.world_width / 2:
            screen_x -= self.world_width

        if screen_y < -self.world_height / 2:
            screen_y += self.world_height
        elif screen_y > self.world_height / 2:
            screen_y -= self.world_height

        return (int(screen_x), int(screen_y))

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Convert a world rect to screen rect with wraparound support."""
        screen_x, screen_y = self.apply(rect.x, rect.y)
        return pygame.Rect(screen_x, screen_y, rect.width, rect.height)

    def is_visible(self, rect: pygame.Rect, margin: int = 50) -> bool:
        """Check if a rect is visible on screen (with margin for smooth transitions and wraparound)."""
        # Get screen-space position of the rect
        screen_x, screen_y = self.apply(rect.x, rect.y)

        # Check if rect is on screen (with margin)
        if (screen_x + rect.width >= -margin and
            screen_x < self.screen_width + margin and
            screen_y + rect.height >= -margin and
            screen_y < self.screen_height + margin):
            return True

        return False


class WeatherSystem:
    """Weather system with rain, wind, and temperature."""

    def __init__(self, world_width: int, world_height: int):
        self.world_width = world_width
        self.world_height = world_height

        # Rain state
        self.is_raining = False
        self.rain_intensity = 0.0  # 0.0 to 1.0
        self.target_intensity = 0.0
        self.raindrops: List[List[float]] = []  # [x, y, speed, length]
        self.rain_timer = 0.0
        self.rain_change_interval = 120.0  # Longer rain duration
        self.narrator_notified = False

        # Wind state
        self.wind_speed = 0.0  # -100 to 100 (negative = left, positive = right)
        self.target_wind = 0.0
        self.wind_timer = 0.0
        self.wind_change_interval = 30.0

        # Temperature (cosmetic, affects descriptions)
        self.temperature = 68  # Fahrenheit
        self.target_temp = 68

        # Rain rendering settings
        self.rain_color = (150, 170, 200)
        self.rain_splash_color = (100, 120, 150)
        self.max_drops = 500

    def get_weather_string(self) -> str:
        """Get weather description for info display."""
        conditions = []

        if self.is_raining:
            if self.rain_intensity > 0.7:
                conditions.append("Heavy Rain")
            elif self.rain_intensity > 0.3:
                conditions.append("Rain")
            else:
                conditions.append("Light Rain")
        else:
            conditions.append("Clear")

        if abs(self.wind_speed) > 60:
            conditions.append("Strong Wind")
        elif abs(self.wind_speed) > 30:
            conditions.append("Windy")

        return ", ".join(conditions)

    def get_temperature_string(self) -> str:
        """Get temperature for display."""
        return f"{int(self.temperature)}F"

    def update(self, dt: float, time_of_day: TimeOfDay = None) -> Optional[str]:
        """
        Update weather state. Returns a narrator message if weather changes.
        """
        narrator_message = None

        # Update wind
        self.wind_timer += dt
        if self.wind_timer >= self.wind_change_interval:
            self.wind_timer = 0.0
            self.wind_change_interval = random.uniform(20.0, 60.0)
            # Change wind direction/speed
            self.target_wind = random.uniform(-80, 80)

        # Smoothly transition wind
        wind_diff = self.target_wind - self.wind_speed
        self.wind_speed += wind_diff * dt * 0.5

        # Update temperature based on time of day
        if time_of_day:
            target_temps = {
                TimeOfDay.DAWN: 55,
                TimeOfDay.MORNING: 62,
                TimeOfDay.AFTERNOON: 72,
                TimeOfDay.EVENING: 65,
                TimeOfDay.NIGHT: 52,
            }
            self.target_temp = target_temps.get(time_of_day, 68)
            # Add rain cooling effect
            if self.is_raining:
                self.target_temp -= 8

        # Smoothly transition temperature
        temp_diff = self.target_temp - self.temperature
        self.temperature += temp_diff * dt * 0.1

        # Weather change timer
        self.rain_timer += dt
        if self.rain_timer >= self.rain_change_interval:
            self.rain_timer = 0.0
            self.rain_change_interval = random.uniform(90.0, 180.0)  # Longer intervals

            # Decide weather change
            if not self.is_raining and random.random() < 0.35:
                # Start raining
                self.is_raining = True
                self.target_intensity = random.uniform(0.3, 1.0)
                self.narrator_notified = False
                # Rain often brings wind
                self.target_wind = random.uniform(40, 80) * random.choice([-1, 1])
            elif self.is_raining and random.random() < 0.25:  # Less likely to stop
                # Stop raining
                self.target_intensity = 0.0

        # Smoothly transition intensity
        if self.rain_intensity < self.target_intensity:
            self.rain_intensity = min(self.rain_intensity + dt * 0.2, self.target_intensity)
        elif self.rain_intensity > self.target_intensity:
            self.rain_intensity = max(self.rain_intensity - dt * 0.1, self.target_intensity)

        # Check if rain stopped
        if self.rain_intensity <= 0.01 and self.is_raining:
            self.is_raining = False
            narrator_message = "rain_stopped"
            self.narrator_notified = True

        # Notify narrator when rain starts
        if self.is_raining and not self.narrator_notified and self.rain_intensity > 0.2:
            self.narrator_notified = True
            if self.target_intensity > 0.7:
                narrator_message = "rain_heavy"
            else:
                narrator_message = "rain_started"

        # Update raindrops
        self._update_drops(dt)

        return narrator_message

    def _update_drops(self, dt: float):
        """Update raindrop positions with wind effect."""
        # Add new drops based on intensity
        drops_to_add = int(self.rain_intensity * 25)
        for _ in range(drops_to_add):
            if len(self.raindrops) < self.max_drops:
                self.raindrops.append([
                    random.uniform(0, self.world_width),
                    random.uniform(-100, 0),
                    random.uniform(400, 700),  # Fall speed
                    random.uniform(8, 20)  # Length
                ])

        # Update existing drops with wind
        drops_to_remove = []
        for i, drop in enumerate(self.raindrops):
            drop[1] += drop[2] * dt  # Fall
            drop[0] += self.wind_speed * dt * 2  # Wind drift (uses actual wind)

            if drop[1] > self.world_height or drop[0] < -50 or drop[0] > self.world_width + 50:
                drops_to_remove.append(i)

        # Remove fallen drops
        for i in reversed(drops_to_remove):
            self.raindrops.pop(i)

    def draw(self, screen: pygame.Surface, camera: Camera):
        """Draw rain effect with wind-angled drops."""
        if self.rain_intensity <= 0.01:
            return

        # Calculate wind angle offset for raindrop rendering
        wind_offset = self.wind_speed * 0.1  # How much the drop slants

        # Draw visible raindrops
        for drop in self.raindrops:
            screen_x, screen_y = camera.apply(drop[0], drop[1])

            # Skip if off screen
            if screen_x < -20 or screen_x > camera.screen_width + 20:
                continue
            if screen_y < -drop[3] or screen_y > camera.screen_height + 20:
                continue

            # Draw raindrop as a slanted line based on wind
            end_x = screen_x + wind_offset
            end_y = screen_y + drop[3]
            pygame.draw.line(
                screen,
                self.rain_color,
                (int(screen_x), int(screen_y)),
                (int(end_x), int(end_y)),
                1
            )

        # Rain overlay for atmosphere
        if self.rain_intensity > 0.3:
            overlay = pygame.Surface((camera.screen_width, camera.screen_height), pygame.SRCALPHA)
            overlay.fill((100, 110, 130, int(30 * self.rain_intensity)))
            screen.blit(overlay, (0, 0))


class BuildingStyle(Enum):
    """Different building architectural styles."""
    MODERN = "modern"        # Glass/steel, blue tints
    BRICK = "brick"          # Red/brown brick
    CONCRETE = "concrete"    # Gray brutalist
    ART_DECO = "art_deco"    # Tan/gold accents
    INDUSTRIAL = "industrial"  # Dark, pipes


class CityBlock:
    """A city block containing buildings with cached window states."""

    # Class-level timing for window state changes
    _window_change_timer = 0.0
    _window_change_interval = 8.0  # Seconds between window state changes

    @classmethod
    def update_window_timer(cls, dt: float) -> bool:
        """Update global window timer. Returns True if windows should change."""
        cls._window_change_timer += dt
        if cls._window_change_timer >= cls._window_change_interval:
            cls._window_change_timer = 0.0
            return True
        return False

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.buildings: List[pygame.Rect] = []
        self.building_colors: List[Tuple[int, int, int]] = []
        self.building_styles: List[BuildingStyle] = []
        self.building_window_states: List[List[bool]] = []  # Cached lit/unlit states
        self._generate_buildings()

    def _generate_buildings(self):
        """Generate buildings within this block."""
        # Leave some margin inside the block
        margin = 10
        inner_rect = pygame.Rect(
            self.rect.x + margin,
            self.rect.y + margin,
            self.rect.width - margin * 2,
            self.rect.height - margin * 2
        )

        # Randomly place 1-4 buildings
        num_buildings = random.randint(1, 4)

        if num_buildings == 1:
            # Single large building
            self.buildings.append(inner_rect.copy())
            style = random.choice(list(BuildingStyle))
            self.building_styles.append(style)
            self.building_colors.append(self._style_color(style))
        else:
            # Split into smaller buildings
            if random.random() < 0.5:
                # Horizontal split
                h1 = inner_rect.height // 2 - 5
                self.buildings.append(pygame.Rect(
                    inner_rect.x, inner_rect.y,
                    inner_rect.width, h1
                ))
                self.buildings.append(pygame.Rect(
                    inner_rect.x, inner_rect.y + h1 + 10,
                    inner_rect.width, inner_rect.height - h1 - 10
                ))
            else:
                # Vertical split
                w1 = inner_rect.width // 2 - 5
                self.buildings.append(pygame.Rect(
                    inner_rect.x, inner_rect.y,
                    w1, inner_rect.height
                ))
                self.buildings.append(pygame.Rect(
                    inner_rect.x + w1 + 10, inner_rect.y,
                    inner_rect.width - w1 - 10, inner_rect.height
                ))

            for _ in self.buildings:
                style = random.choice(list(BuildingStyle))
                self.building_styles.append(style)
                self.building_colors.append(self._style_color(style))

        # Initialize window states for each building
        for building in self.buildings:
            window_count = self._count_windows(building)
            self.building_window_states.append([random.random() > 0.4 for _ in range(window_count)])

    def _style_color(self, style: BuildingStyle) -> Tuple[int, int, int]:
        """Get base color for building style."""
        style_colors = {
            BuildingStyle.MODERN: [(90, 110, 130), (100, 120, 140), (80, 100, 120)],
            BuildingStyle.BRICK: [(140, 80, 60), (150, 90, 70), (130, 70, 50)],
            BuildingStyle.CONCRETE: [(100, 100, 100), (90, 90, 95), (110, 110, 105)],
            BuildingStyle.ART_DECO: [(140, 130, 100), (150, 140, 110), (130, 120, 90)],
            BuildingStyle.INDUSTRIAL: [(70, 70, 80), (60, 65, 75), (80, 80, 85)],
        }
        base = random.choice(style_colors.get(style, [(100, 100, 100)]))
        # Add slight variation
        return tuple(max(0, min(255, c + random.randint(-10, 10))) for c in base)

    def _count_windows(self, building: pygame.Rect) -> int:
        """Count how many windows a building has."""
        if building.width <= 40 or building.height <= 40:
            return 0
        win_w, win_h = 8, 10
        margin = 12
        spacing_x, spacing_y = 16, 18
        cols = max(0, (building.width - margin * 2 - win_w) // spacing_x + 1)
        rows = max(0, (building.height - margin * 2 - win_h) // spacing_y + 1)
        return cols * rows

    def regenerate_window_states(self, lit_chance: float = 0.6):
        """Regenerate window lit/unlit states with some randomness."""
        for i, building in enumerate(self.buildings):
            window_count = len(self.building_window_states[i])
            # Only change some windows, not all at once
            for j in range(window_count):
                if random.random() < 0.2:  # 20% chance each window changes
                    self.building_window_states[i][j] = random.random() < lit_chance

    def draw(self, screen: pygame.Surface, camera: Camera, darkness_alpha: int = 0):
        """Draw the block and its buildings."""
        if not camera.is_visible(self.rect):
            return

        self._draw_buildings(screen, camera, darkness_alpha, 0, 0)

    def draw_at_offset(self, screen: pygame.Surface, camera: Camera,
                       offset_x: int, offset_y: int, darkness_alpha: int = 0):
        """Draw the block at a world offset position (for wraparound)."""
        self._draw_buildings(screen, camera, darkness_alpha, offset_x, offset_y)

    def _draw_buildings(self, screen: pygame.Surface, camera: Camera,
                        darkness_alpha: int, offset_x: int, offset_y: int):
        """Internal method to draw buildings with optional world offset."""
        for idx, (building, color, style) in enumerate(zip(
            self.buildings, self.building_colors, self.building_styles
        )):
            # Create offset building rect for wraparound
            offset_building = pygame.Rect(
                building.x + offset_x,
                building.y + offset_y,
                building.width,
                building.height
            )
            screen_rect = pygame.Rect(
                offset_building.x - int(camera.x),
                offset_building.y - int(camera.y),
                building.width,
                building.height
            )

            # Skip if off screen
            if (screen_rect.right < 0 or screen_rect.left > camera.screen_width or
                screen_rect.bottom < 0 or screen_rect.top > camera.screen_height):
                continue

            # Apply darkness tint
            if darkness_alpha > 0:
                darkened = tuple(max(0, c - darkness_alpha // 3) for c in color)
                pygame.draw.rect(screen, darkened, screen_rect)
            else:
                pygame.draw.rect(screen, color, screen_rect)

            # Building details based on style
            self._draw_style_details(screen, screen_rect, style)

            # Building outline
            pygame.draw.rect(screen, (40, 40, 40), screen_rect, 2)

            # Windows (if building is big enough)
            if building.width > 40 and building.height > 40:
                window_states = self.building_window_states[idx] if idx < len(self.building_window_states) else []
                self._draw_windows(screen, screen_rect, style, window_states)

    def _draw_style_details(self, screen: pygame.Surface, rect: pygame.Rect, style: BuildingStyle):
        """Draw architectural details based on building style."""
        if style == BuildingStyle.MODERN:
            # Vertical glass stripes
            stripe_color = (120, 140, 160)
            for x in range(rect.x + 5, rect.x + rect.width - 5, 20):
                pygame.draw.line(screen, stripe_color, (x, rect.y), (x, rect.y + rect.height), 2)
        elif style == BuildingStyle.BRICK:
            # Subtle horizontal lines for brick rows
            brick_line = (100, 60, 40)
            for y in range(rect.y + 8, rect.y + rect.height - 4, 8):
                pygame.draw.line(screen, brick_line, (rect.x + 2, y), (rect.x + rect.width - 2, y), 1)
        elif style == BuildingStyle.ART_DECO:
            # Gold accent at top
            accent = (180, 160, 100)
            pygame.draw.rect(screen, accent, (rect.x, rect.y, rect.width, 6))
        elif style == BuildingStyle.INDUSTRIAL:
            # Pipes on side
            pipe_color = (90, 90, 100)
            pygame.draw.line(screen, pipe_color, (rect.x + 3, rect.y + 10), (rect.x + 3, rect.y + rect.height - 5), 3)

    def _draw_windows(self, screen: pygame.Surface, screen_rect: pygame.Rect,
                      style: BuildingStyle, window_states: List[bool]):
        """Draw windows on a building using cached states."""
        # Window colors vary by style
        window_lit_colors = {
            BuildingStyle.MODERN: (200, 220, 255),    # Cool white/blue
            BuildingStyle.BRICK: (255, 220, 150),     # Warm yellow
            BuildingStyle.CONCRETE: (200, 200, 180),  # Neutral
            BuildingStyle.ART_DECO: (255, 240, 200),  # Warm gold
            BuildingStyle.INDUSTRIAL: (180, 200, 180),  # Greenish
        }
        window_color = window_lit_colors.get(style, (180, 180, 140))
        window_dark = (40, 45, 60)

        # Calculate window grid
        win_w, win_h = 8, 10
        margin = 12
        spacing_x = 16
        spacing_y = 18

        window_idx = 0
        x = screen_rect.x + margin
        while x + win_w < screen_rect.x + screen_rect.width - margin:
            y = screen_rect.y + margin
            while y + win_h < screen_rect.y + screen_rect.height - margin:
                # Use cached state
                is_lit = window_states[window_idx] if window_idx < len(window_states) else False
                color = window_color if is_lit else window_dark
                pygame.draw.rect(screen, color, (x, y, win_w, win_h))
                window_idx += 1
                y += spacing_y
            x += spacing_x

    def is_colliding(self, rect: pygame.Rect) -> bool:
        """Check if a rect collides with any building in this block."""
        for building in self.buildings:
            if building.colliderect(rect):
                return True
        return False


class WaterBody:
    """A lake or pond in the city."""

    def __init__(self, x: int, y: int, width: int, height: int, is_river: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_river = is_river
        self.wave_offset = random.uniform(0, math.pi * 2)  # Random phase for wave animation

        # Colors
        self.water_color = (40, 80, 120)
        self.water_highlight = (60, 100, 140)
        self.shore_color = (100, 90, 70)  # Sandy/muddy shore

    def draw(self, screen: pygame.Surface, camera: 'Camera', time: float = 0):
        """Draw the water body with animated waves."""
        screen_rect = camera.apply_rect(self.rect)

        # Skip if off screen
        if (screen_rect.right < 0 or screen_rect.left > camera.screen_width or
            screen_rect.bottom < 0 or screen_rect.top > camera.screen_height):
            return

        # Shore/bank (slightly larger rectangle)
        shore_rect = screen_rect.inflate(6, 6)
        pygame.draw.rect(screen, self.shore_color, shore_rect, border_radius=8)

        # Water base
        pygame.draw.rect(screen, self.water_color, screen_rect, border_radius=6)

        # Animated wave highlights
        wave_time = time + self.wave_offset
        num_waves = max(1, screen_rect.width // 40)

        for i in range(num_waves):
            wave_x = screen_rect.x + 20 + i * 40
            wave_y = screen_rect.y + 15 + math.sin(wave_time * 2 + i * 0.5) * 5
            wave_width = 25 + math.sin(wave_time + i) * 5

            if wave_x + wave_width < screen_rect.right - 10:
                pygame.draw.line(screen, self.water_highlight,
                               (wave_x, int(wave_y)),
                               (wave_x + int(wave_width), int(wave_y)), 2)

        # Second row of waves
        for i in range(num_waves):
            wave_x = screen_rect.x + 30 + i * 40
            wave_y = screen_rect.y + screen_rect.height // 2 + math.sin(wave_time * 1.5 + i * 0.7) * 4
            wave_width = 20 + math.sin(wave_time * 0.8 + i) * 4

            if wave_x + wave_width < screen_rect.right - 10:
                pygame.draw.line(screen, self.water_highlight,
                               (wave_x, int(wave_y)),
                               (wave_x + int(wave_width), int(wave_y)), 2)

    def is_colliding(self, rect: pygame.Rect) -> bool:
        """Check if a rect collides with the water."""
        return self.rect.colliderect(rect)


class Bridge:
    """A bridge that spans over water."""

    def __init__(self, x: int, y: int, width: int, height: int, is_horizontal: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_horizontal = is_horizontal

        # Colors
        self.deck_color = (90, 85, 80)  # Concrete
        self.rail_color = (60, 60, 65)  # Metal rails
        self.stripe_color = (200, 200, 80)  # Yellow road stripes

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw the bridge."""
        screen_rect = camera.apply_rect(self.rect)

        # Skip if off screen
        if (screen_rect.right < 0 or screen_rect.left > camera.screen_width or
            screen_rect.bottom < 0 or screen_rect.top > camera.screen_height):
            return

        # Bridge deck
        pygame.draw.rect(screen, self.deck_color, screen_rect)

        # Rails
        rail_width = 4
        if self.is_horizontal:
            # Top rail
            pygame.draw.rect(screen, self.rail_color,
                           (screen_rect.x, screen_rect.y, screen_rect.width, rail_width))
            # Bottom rail
            pygame.draw.rect(screen, self.rail_color,
                           (screen_rect.x, screen_rect.bottom - rail_width, screen_rect.width, rail_width))
            # Road stripe (dashed)
            center_y = screen_rect.centery
            for stripe_x in range(screen_rect.x, screen_rect.right, 30):
                stripe_w = min(15, screen_rect.right - stripe_x)
                pygame.draw.rect(screen, self.stripe_color,
                               (stripe_x, center_y - 1, stripe_w, 3))
        else:
            # Left rail
            pygame.draw.rect(screen, self.rail_color,
                           (screen_rect.x, screen_rect.y, rail_width, screen_rect.height))
            # Right rail
            pygame.draw.rect(screen, self.rail_color,
                           (screen_rect.right - rail_width, screen_rect.y, rail_width, screen_rect.height))
            # Road stripe (dashed)
            center_x = screen_rect.centerx
            for stripe_y in range(screen_rect.y, screen_rect.bottom, 30):
                stripe_h = min(15, screen_rect.bottom - stripe_y)
                pygame.draw.rect(screen, self.stripe_color,
                               (center_x - 1, stripe_y, 3, stripe_h))


class ParkingLot:
    """A parking lot with marked spaces for parked vehicles."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.parking_spaces: List[Tuple[int, int, float, float]] = []  # (x, y, dir_x, dir_y)
        self._generate_spaces()

    def _generate_spaces(self):
        """Generate parking space positions within the lot."""
        margin = 15
        space_width = 30
        space_height = 50
        aisle_width = 40

        inner_x = self.rect.x + margin
        inner_y = self.rect.y + margin
        inner_w = self.rect.width - margin * 2
        inner_h = self.rect.height - margin * 2

        # Calculate rows of parking spaces
        # Each row has spaces on both sides of an aisle
        row_height = space_height * 2 + aisle_width
        num_rows = max(1, inner_h // row_height)

        for row in range(num_rows):
            row_y = inner_y + row * row_height

            # Top row of spaces (facing down into aisle)
            x = inner_x
            while x + space_width <= inner_x + inner_w:
                self.parking_spaces.append((x + space_width // 2, row_y + space_height // 2, 0, 1))
                x += space_width + 5

            # Bottom row of spaces (facing up into aisle)
            if row_y + space_height + aisle_width + space_height <= inner_y + inner_h:
                x = inner_x
                bottom_y = row_y + space_height + aisle_width
                while x + space_width <= inner_x + inner_w:
                    self.parking_spaces.append((x + space_width // 2, bottom_y + space_height // 2, 0, -1))
                    x += space_width + 5

    def get_random_space(self) -> Optional[Tuple[int, int, float, float]]:
        """Get a random parking space (x, y, dir_x, dir_y)."""
        if self.parking_spaces:
            return random.choice(self.parking_spaces)
        return None

    def draw(self, screen: pygame.Surface, camera: 'Camera'):
        """Draw the parking lot with marked spaces."""
        screen_rect = camera.apply_rect(self.rect)

        # Skip if off screen
        if (screen_rect.right < 0 or screen_rect.left > camera.screen_width or
            screen_rect.bottom < 0 or screen_rect.top > camera.screen_height):
            return

        # Parking lot surface (asphalt)
        lot_color = (50, 50, 55)
        pygame.draw.rect(screen, lot_color, screen_rect)

        # Border
        pygame.draw.rect(screen, (70, 70, 75), screen_rect, 2)

        # Draw parking space lines
        line_color = (200, 200, 190)  # White/off-white lines
        margin = 15
        space_width = 30
        space_height = 50
        aisle_width = 40

        # Calculate positions for drawing
        inner_x = screen_rect.x + margin
        inner_y = screen_rect.y + margin
        inner_w = screen_rect.width - margin * 2
        inner_h = screen_rect.height - margin * 2

        row_height = space_height * 2 + aisle_width
        num_rows = max(1, inner_h // row_height)

        for row in range(num_rows):
            row_y = inner_y + row * row_height

            # Top row space lines
            x = inner_x
            while x + space_width <= inner_x + inner_w:
                # Left line
                pygame.draw.line(screen, line_color, (x, row_y), (x, row_y + space_height), 2)
                # Right line
                pygame.draw.line(screen, line_color, (x + space_width, row_y), (x + space_width, row_y + space_height), 2)
                # Back line
                pygame.draw.line(screen, line_color, (x, row_y), (x + space_width, row_y), 2)
                x += space_width + 5

            # Bottom row space lines
            if row_y + space_height + aisle_width + space_height <= inner_y + inner_h:
                x = inner_x
                bottom_y = row_y + space_height + aisle_width
                while x + space_width <= inner_x + inner_w:
                    # Left line
                    pygame.draw.line(screen, line_color, (x, bottom_y), (x, bottom_y + space_height), 2)
                    # Right line
                    pygame.draw.line(screen, line_color, (x + space_width, bottom_y), (x + space_width, bottom_y + space_height), 2)
                    # Back line (at bottom)
                    pygame.draw.line(screen, line_color, (x, bottom_y + space_height), (x + space_width, bottom_y + space_height), 2)
                    x += space_width + 5


class SidewalkNode:
    """A node in the sidewalk pathfinding network."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.neighbors: List['SidewalkNode'] = []

    def connect(self, other: 'SidewalkNode'):
        """Connect this node to another."""
        if other not in self.neighbors:
            self.neighbors.append(other)
        if self not in other.neighbors:
            other.neighbors.append(self)


class CityMap:
    """
    The main city map with streets, sidewalks, and buildings.
    """

    def __init__(self, config: CityConfig = None):
        self.config = config or CityConfig()
        self.blocks: List[CityBlock] = []
        self.parking_lots: List[ParkingLot] = []
        self.water_bodies: List[WaterBody] = []
        self.bridges: List[Bridge] = []
        self.sidewalk_nodes: List[SidewalkNode] = []
        self.sidewalk_rects: List[pygame.Rect] = []  # For rendering
        self.time = 0.0  # For water animation

        # Pre-render surfaces for performance
        self._road_surface: Optional[pygame.Surface] = None
        self._sidewalk_surface: Optional[pygame.Surface] = None

        self._generate_city()

    def _generate_city(self):
        """Generate the city layout."""
        cfg = self.config

        # Calculate grid
        cell_width = cfg.block_width + cfg.road_width
        cell_height = cfg.block_height + cfg.road_width

        cols = cfg.world_width // cell_width
        rows = cfg.world_height // cell_height

        # First, create a lake spanning multiple cells
        self._generate_lake(cols, rows, cell_width, cell_height, cfg)

        # Track which cells are empty for parking lot placement
        empty_cells = []

        # Create blocks (avoid water areas)
        for row in range(rows):
            for col in range(cols):
                x = col * cell_width + cfg.road_width
                y = row * cell_height + cfg.road_width

                # Check if this cell overlaps with water
                cell_rect = pygame.Rect(x, y, cfg.block_width, cfg.block_height)
                overlaps_water = any(water.rect.colliderect(cell_rect) for water in self.water_bodies)

                if overlaps_water:
                    continue  # Don't place buildings in water

                # Some blocks are empty (parks/lots)
                if random.random() < 0.15:
                    empty_cells.append((x, y, cfg.block_width, cfg.block_height))
                    continue

                block = CityBlock(x, y, cfg.block_width, cfg.block_height)
                self.blocks.append(block)

        # Turn some empty cells into parking lots (about 40% of empty spaces)
        for x, y, w, h in empty_cells:
            if random.random() < 0.4:
                lot = ParkingLot(x, y, w, h)
                self.parking_lots.append(lot)

        # Generate sidewalk network
        self._generate_sidewalks()

        # Pre-render static elements
        self._render_roads()

    def _generate_lake(self, cols: int, rows: int, cell_width: int, cell_height: int, cfg):
        """Generate a lake with a bridge crossing it."""
        # Place lake in a random area (not too close to edges)
        lake_col = random.randint(2, max(3, cols - 4))
        lake_row = random.randint(2, max(3, rows - 4))

        # Lake spans 2-3 cells wide and 3-4 cells tall (or vice versa)
        lake_width_cells = random.randint(2, 3)
        lake_height_cells = random.randint(3, 4)

        # Calculate lake position and size
        lake_x = lake_col * cell_width
        lake_y = lake_row * cell_height
        lake_width = lake_width_cells * cell_width - cfg.road_width // 2
        lake_height = lake_height_cells * cell_height - cfg.road_width // 2

        # Create the lake
        lake = WaterBody(lake_x, lake_y, lake_width, lake_height)
        self.water_bodies.append(lake)

        # Add a bridge across the lake (horizontal bridge through middle)
        bridge_y = lake_y + lake_height // 2 - cfg.road_width // 2
        bridge = Bridge(
            lake_x - 20,  # Extend slightly beyond lake
            bridge_y,
            lake_width + 40,
            cfg.road_width,
            is_horizontal=True
        )
        self.bridges.append(bridge)

    def _generate_sidewalks(self):
        """Generate sidewalk pathfinding nodes at intersections."""
        cfg = self.config
        cell_width = cfg.block_width + cfg.road_width
        cell_height = cfg.block_height + cfg.road_width

        cols = cfg.world_width // cell_width + 1
        rows = cfg.world_height // cell_height + 1

        # Create node grid
        node_grid = {}

        for row in range(rows):
            for col in range(cols):
                # Nodes at intersections (corners of blocks)
                x = col * cell_width + cfg.sidewalk_width
                y = row * cell_height + cfg.sidewalk_width

                node = SidewalkNode(x, y)
                self.sidewalk_nodes.append(node)
                node_grid[(col, row)] = node

        # Connect adjacent nodes
        for (col, row), node in node_grid.items():
            # Right neighbor
            if (col + 1, row) in node_grid:
                node.connect(node_grid[(col + 1, row)])
            # Down neighbor
            if (col, row + 1) in node_grid:
                node.connect(node_grid[(col, row + 1)])

        # Generate sidewalk rectangles for rendering
        for node in self.sidewalk_nodes:
            for neighbor in node.neighbors:
                if neighbor.x > node.x or neighbor.y > node.y:
                    # Horizontal or vertical sidewalk segment
                    if neighbor.x > node.x:
                        # Horizontal
                        rect = pygame.Rect(
                            node.x - cfg.sidewalk_width,
                            node.y - cfg.sidewalk_width,
                            neighbor.x - node.x + cfg.sidewalk_width * 2,
                            cfg.sidewalk_width * 2
                        )
                    else:
                        # Vertical
                        rect = pygame.Rect(
                            node.x - cfg.sidewalk_width,
                            node.y - cfg.sidewalk_width,
                            cfg.sidewalk_width * 2,
                            neighbor.y - node.y + cfg.sidewalk_width * 2
                        )
                    self.sidewalk_rects.append(rect)

    def _render_roads(self):
        """Pre-render road surface with sidewalks, crosswalks, and road markings."""
        cfg = self.config

        # Create road surface
        self._road_surface = pygame.Surface(
            (cfg.world_width, cfg.world_height)
        )
        self._road_surface.fill(cfg.grass_color)

        cell_width = cfg.block_width + cfg.road_width
        cell_height = cfg.block_height + cfg.road_width

        # Draw roads
        cols = cfg.world_width // cell_width + 1
        rows = cfg.world_height // cell_height + 1

        # Colors for road features
        sidewalk_edge_color = (100, 100, 105)  # Darker sidewalk edge (curb)
        crosswalk_color = (180, 180, 170)  # Off-white crosswalk stripes
        dash_gap = 20  # Gap between dashed line segments

        # Vertical roads
        for col in range(cols):
            x = col * cell_width
            pygame.draw.rect(
                self._road_surface,
                cfg.road_color,
                (x, 0, cfg.road_width, cfg.world_height)
            )

            # Draw sidewalk strips on both sides of road
            sidewalk_strip_width = 8
            # Left sidewalk strip
            pygame.draw.rect(
                self._road_surface,
                cfg.sidewalk_color,
                (x, 0, sidewalk_strip_width, cfg.world_height)
            )
            pygame.draw.line(
                self._road_surface,
                sidewalk_edge_color,
                (x + sidewalk_strip_width, 0),
                (x + sidewalk_strip_width, cfg.world_height),
                1
            )
            # Right sidewalk strip
            pygame.draw.rect(
                self._road_surface,
                cfg.sidewalk_color,
                (x + cfg.road_width - sidewalk_strip_width, 0, sidewalk_strip_width, cfg.world_height)
            )
            pygame.draw.line(
                self._road_surface,
                sidewalk_edge_color,
                (x + cfg.road_width - sidewalk_strip_width - 1, 0),
                (x + cfg.road_width - sidewalk_strip_width - 1, cfg.world_height),
                1
            )

            # Dashed center line (yellow)
            center_x = x + cfg.road_width // 2
            for dash_y in range(0, cfg.world_height, dash_gap * 2):
                pygame.draw.line(
                    self._road_surface,
                    cfg.road_line_color,
                    (center_x, dash_y),
                    (center_x, min(dash_y + dash_gap, cfg.world_height)),
                    2
                )

        # Horizontal roads
        for row in range(rows):
            y = row * cell_height
            pygame.draw.rect(
                self._road_surface,
                cfg.road_color,
                (0, y, cfg.world_width, cfg.road_width)
            )

            # Draw sidewalk strips on both sides of road
            sidewalk_strip_width = 8
            # Top sidewalk strip
            pygame.draw.rect(
                self._road_surface,
                cfg.sidewalk_color,
                (0, y, cfg.world_width, sidewalk_strip_width)
            )
            pygame.draw.line(
                self._road_surface,
                sidewalk_edge_color,
                (0, y + sidewalk_strip_width),
                (cfg.world_width, y + sidewalk_strip_width),
                1
            )
            # Bottom sidewalk strip
            pygame.draw.rect(
                self._road_surface,
                cfg.sidewalk_color,
                (0, y + cfg.road_width - sidewalk_strip_width, cfg.world_width, sidewalk_strip_width)
            )
            pygame.draw.line(
                self._road_surface,
                sidewalk_edge_color,
                (0, y + cfg.road_width - sidewalk_strip_width - 1),
                (cfg.world_width, y + cfg.road_width - sidewalk_strip_width - 1),
                1
            )

            # Dashed center line (yellow)
            center_y = y + cfg.road_width // 2
            for dash_x in range(0, cfg.world_width, dash_gap * 2):
                pygame.draw.line(
                    self._road_surface,
                    cfg.road_line_color,
                    (dash_x, center_y),
                    (min(dash_x + dash_gap, cfg.world_width), center_y),
                    2
                )

        # Draw crosswalks at intersections
        for row in range(rows):
            for col in range(cols):
                intersection_x = col * cell_width
                intersection_y = row * cell_height

                # Crosswalk stripe settings
                stripe_width = 4
                stripe_gap = 6
                crosswalk_margin = 12  # Distance from intersection center

                # Vertical crosswalks (crossing horizontal roads)
                # Top of intersection
                for stripe_x in range(intersection_x + crosswalk_margin,
                                     intersection_x + cfg.road_width - crosswalk_margin,
                                     stripe_width + stripe_gap):
                    pygame.draw.rect(
                        self._road_surface,
                        crosswalk_color,
                        (stripe_x, intersection_y + 2, stripe_width, sidewalk_strip_width - 2)
                    )
                    pygame.draw.rect(
                        self._road_surface,
                        crosswalk_color,
                        (stripe_x, intersection_y + cfg.road_width - sidewalk_strip_width,
                         stripe_width, sidewalk_strip_width - 2)
                    )

                # Horizontal crosswalks (crossing vertical roads)
                # Left of intersection
                for stripe_y in range(intersection_y + crosswalk_margin,
                                     intersection_y + cfg.road_width - crosswalk_margin,
                                     stripe_width + stripe_gap):
                    pygame.draw.rect(
                        self._road_surface,
                        crosswalk_color,
                        (intersection_x + 2, stripe_y, sidewalk_strip_width - 2, stripe_width)
                    )
                    pygame.draw.rect(
                        self._road_surface,
                        crosswalk_color,
                        (intersection_x + cfg.road_width - sidewalk_strip_width,
                         stripe_y, sidewalk_strip_width - 2, stripe_width)
                    )

        # Draw sidewalk network on top (at intersections)
        for rect in self.sidewalk_rects:
            pygame.draw.rect(self._road_surface, cfg.sidewalk_color, rect)

    def get_nearest_sidewalk_node(self, x: float, y: float) -> Optional[SidewalkNode]:
        """Find the nearest sidewalk node to a position."""
        if not self.sidewalk_nodes:
            return None

        nearest = None
        nearest_dist = float('inf')

        for node in self.sidewalk_nodes:
            dx = node.x - x
            dy = node.y - y
            dist = dx * dx + dy * dy
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = node

        return nearest

    def find_path(self, start_x: float, start_y: float,
                  end_x: float, end_y: float) -> List[Tuple[float, float]]:
        """
        Find a path along sidewalks from start to end.
        Uses simple BFS pathfinding.
        """
        start_node = self.get_nearest_sidewalk_node(start_x, start_y)
        end_node = self.get_nearest_sidewalk_node(end_x, end_y)

        if not start_node or not end_node:
            return [(end_x, end_y)]

        if start_node == end_node:
            return [(end_node.x, end_node.y)]

        # BFS
        from collections import deque
        queue = deque([(start_node, [start_node])])
        visited = {start_node}

        while queue:
            node, path = queue.popleft()

            if node == end_node:
                return [(n.x, n.y) for n in path]

            for neighbor in node.neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        # No path found, return direct
        return [(end_x, end_y)]

    def is_on_sidewalk(self, x: float, y: float, margin: int = 20) -> bool:
        """Check if a position is on or near a sidewalk."""
        for rect in self.sidewalk_rects:
            if rect.inflate(margin, margin).collidepoint(x, y):
                return True
        return False

    def is_colliding(self, rect: pygame.Rect) -> bool:
        """Check if a rect collides with any building."""
        for block in self.blocks:
            if block.is_colliding(rect):
                return True
        return False

    def update(self, dt: float, lit_chance: float = 0.6):
        """Update city state including windows and water animation."""
        self.time += dt

        # Update window states periodically
        if CityBlock.update_window_timer(dt):
            for block in self.blocks:
                block.regenerate_window_states(lit_chance)

    def update_windows(self, dt: float, lit_chance: float = 0.6):
        """Update window states periodically. (Legacy - use update() instead)"""
        self.update(dt, lit_chance)

    def draw(self, screen: pygame.Surface, camera: Camera, darkness_alpha: int = 0):
        """Draw the city with optional darkness overlay."""
        # Draw pre-rendered roads/sidewalks with wraparound support
        if self._road_surface:
            cam_x = int(camera.x) % self.config.world_width
            cam_y = int(camera.y) % self.config.world_height

            # Calculate how much of the view extends beyond world edges
            right_overflow = max(0, (cam_x + camera.screen_width) - self.config.world_width)
            bottom_overflow = max(0, (cam_y + camera.screen_height) - self.config.world_height)

            # Main visible area (top-left quadrant)
            main_width = camera.screen_width - right_overflow
            main_height = camera.screen_height - bottom_overflow

            if main_width > 0 and main_height > 0:
                visible_rect = pygame.Rect(cam_x, cam_y, main_width, main_height)
                screen.blit(self._road_surface, (0, 0), visible_rect)

            # Right edge wraparound (draw left side of world on right of screen)
            if right_overflow > 0 and main_height > 0:
                wrap_rect = pygame.Rect(0, cam_y, right_overflow, main_height)
                screen.blit(self._road_surface, (main_width, 0), wrap_rect)

            # Bottom edge wraparound (draw top of world on bottom of screen)
            if bottom_overflow > 0 and main_width > 0:
                wrap_rect = pygame.Rect(cam_x, 0, main_width, bottom_overflow)
                screen.blit(self._road_surface, (0, main_height), wrap_rect)

            # Corner wraparound (top-left of world in bottom-right of screen)
            if right_overflow > 0 and bottom_overflow > 0:
                wrap_rect = pygame.Rect(0, 0, right_overflow, bottom_overflow)
                screen.blit(self._road_surface, (main_width, main_height), wrap_rect)

        # Draw water bodies (lakes, ponds)
        for water in self.water_bodies:
            water.draw(screen, camera, self.time)

        # Draw bridges over water
        for bridge in self.bridges:
            bridge.draw(screen, camera)

        # Draw parking lots (before buildings so they appear behind)
        for lot in self.parking_lots:
            lot.draw(screen, camera)

        # Draw buildings with darkness (handle wraparound by drawing at multiple positions)
        for block in self.blocks:
            # Draw at normal position
            block.draw(screen, camera, darkness_alpha)

            # For wraparound: check if block should also appear at wrapped positions
            # This handles blocks near world edges that need to appear on opposite side
            block_right = block.rect.x + block.rect.width
            block_bottom = block.rect.y + block.rect.height

            cam_x = camera.x % self.config.world_width
            cam_y = camera.y % self.config.world_height
            cam_right = cam_x + camera.screen_width
            cam_bottom = cam_y + camera.screen_height

            # If camera view wraps horizontally
            if cam_right > self.config.world_width:
                # Blocks on left side of world might need to appear on right of screen
                if block.rect.x < cam_right - self.config.world_width:
                    block.draw_at_offset(screen, camera, self.config.world_width, 0, darkness_alpha)

            # If camera view wraps vertically
            if cam_bottom > self.config.world_height:
                # Blocks on top of world might need to appear on bottom of screen
                if block.rect.y < cam_bottom - self.config.world_height:
                    block.draw_at_offset(screen, camera, 0, self.config.world_height, darkness_alpha)

            # Corner case: both horizontal and vertical wrap
            if cam_right > self.config.world_width and cam_bottom > self.config.world_height:
                if (block.rect.x < cam_right - self.config.world_width and
                    block.rect.y < cam_bottom - self.config.world_height):
                    block.draw_at_offset(screen, camera, self.config.world_width, self.config.world_height, darkness_alpha)

        # Apply overall darkness overlay for night
        if darkness_alpha > 20:
            overlay = pygame.Surface((camera.screen_width, camera.screen_height), pygame.SRCALPHA)
            overlay.fill((20, 25, 50, darkness_alpha // 2))
            screen.blit(overlay, (0, 0))
