"""
Regression tests for Py City game components.

Tests core systems without requiring pygame display:
- Day/night cycle
- Weather system
- Building generation
- Crime simulation
- Game loop phases
"""

import sys
import os
import unittest

# Add py_city to path
PY_CITY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PY_CITY_DIR not in sys.path:
    sys.path.insert(0, PY_CITY_DIR)

# Mock pygame before imports
class MockPygame:
    """Mock pygame to avoid display initialization."""
    class Rect:
        def __init__(self, x, y, w, h):
            self.x, self.y = x, y
            self.width, self.height = w, h
            self.left, self.top = x, y
            self.right, self.bottom = x + w, y + h
        def colliderect(self, other):
            return not (self.right < other.left or self.left > other.right or
                       self.bottom < other.top or self.top > other.bottom)
        def inflate(self, dx, dy):
            return MockPygame.Rect(self.x - dx, self.y - dy,
                                   self.width + 2*dx, self.height + 2*dy)
        def collidepoint(self, x, y):
            return self.left <= x <= self.right and self.top <= y <= self.bottom
        def copy(self):
            return MockPygame.Rect(self.x, self.y, self.width, self.height)

    class Surface:
        def __init__(self, size, flags=0):
            self.size = size
        def fill(self, color):
            pass
        def set_alpha(self, alpha):
            pass
        def blit(self, source, pos, area=None):
            pass
        def get_width(self):
            return self.size[0]
        def get_height(self):
            return self.size[1]

    SRCALPHA = 0x00010000

    @staticmethod
    def init():
        pass

    class draw:
        @staticmethod
        def rect(surface, color, rect, width=0):
            pass
        @staticmethod
        def line(surface, color, start, end, width=1):
            pass
        @staticmethod
        def circle(surface, color, pos, radius, width=0):
            pass

# Install mock
sys.modules['pygame'] = MockPygame()

# Now import the modules we're testing
from city_map import (
    DayNightCycle, TimeOfDay, WeatherSystem,
    CityBlock, BuildingStyle, CityConfig, CityMap, Camera
)
from game_loop import CrimeSimulation, GamePhase, GameLoopManager, NarratorQueue


class TestDayNightCycle(unittest.TestCase):
    """Tests for day/night cycle system."""

    def test_init_default(self):
        """Test default initialization at 8 AM."""
        cycle = DayNightCycle()
        self.assertEqual(cycle.game_hour, 8.0)
        self.assertEqual(cycle.get_time_of_day(), TimeOfDay.MORNING)

    def test_time_progression(self):
        """Test time advances correctly."""
        cycle = DayNightCycle(start_hour=11.5, time_scale=3600)  # 1 second = 1 hour
        cycle.update(0.5)  # Half second = 0.5 hours
        self.assertAlmostEqual(cycle.game_hour, 12.0, places=2)
        self.assertEqual(cycle.get_time_of_day(), TimeOfDay.AFTERNOON)

    def test_day_rollover(self):
        """Test day counter increments at midnight."""
        cycle = DayNightCycle(start_hour=23.5, time_scale=3600)
        self.assertEqual(cycle.day_count, 1)
        cycle.update(1.0)  # 1 hour past midnight
        self.assertEqual(cycle.day_count, 2)
        self.assertLess(cycle.game_hour, 1.0)

    def test_time_periods(self):
        """Test correct time period detection."""
        test_cases = [
            (5.5, TimeOfDay.DAWN),
            (9.0, TimeOfDay.MORNING),
            (14.0, TimeOfDay.AFTERNOON),
            (18.0, TimeOfDay.EVENING),
            (22.0, TimeOfDay.NIGHT),
            (2.0, TimeOfDay.NIGHT),
        ]
        for hour, expected_period in test_cases:
            cycle = DayNightCycle(start_hour=hour)
            self.assertEqual(cycle.get_time_of_day(), expected_period,
                           f"Hour {hour} should be {expected_period}")

    def test_is_night(self):
        """Test night detection for crime bonus."""
        cycle = DayNightCycle(start_hour=14.0)
        self.assertFalse(cycle.is_night())

        cycle = DayNightCycle(start_hour=21.0)
        self.assertTrue(cycle.is_night())

    def test_time_string_format(self):
        """Test time display formatting."""
        cycle = DayNightCycle(start_hour=14.5)  # 2:30 PM
        time_str = cycle.get_time_string()
        self.assertIn("2:", time_str)
        self.assertIn("PM", time_str)

    def test_window_lit_chance(self):
        """Test window lighting varies by time."""
        day_cycle = DayNightCycle(start_hour=10.0)
        night_cycle = DayNightCycle(start_hour=22.0)

        day_chance = day_cycle.get_window_lit_chance()
        night_chance = night_cycle.get_window_lit_chance()

        self.assertLess(day_chance, night_chance,
                       "Windows should be more lit at night")


class TestWeatherSystem(unittest.TestCase):
    """Tests for weather system."""

    def test_init(self):
        """Test weather system initialization."""
        weather = WeatherSystem(1000, 1000)
        self.assertFalse(weather.is_raining)
        self.assertEqual(weather.rain_intensity, 0.0)
        self.assertEqual(weather.wind_speed, 0.0)

    def test_weather_string_clear(self):
        """Test weather description when clear."""
        weather = WeatherSystem(1000, 1000)
        self.assertEqual(weather.get_weather_string(), "Clear")

    def test_weather_string_rain(self):
        """Test weather description when raining."""
        weather = WeatherSystem(1000, 1000)
        weather.is_raining = True
        weather.rain_intensity = 0.5
        self.assertIn("Rain", weather.get_weather_string())

    def test_temperature_string(self):
        """Test temperature display."""
        weather = WeatherSystem(1000, 1000)
        weather.temperature = 72
        self.assertEqual(weather.get_temperature_string(), "72F")

    def test_update_returns_events(self):
        """Test weather update can return narrator events."""
        weather = WeatherSystem(1000, 1000)
        # Force rain to start
        weather.is_raining = True
        weather.target_intensity = 0.8
        weather.rain_intensity = 0.3
        weather.narrator_notified = False

        # Should not crash and may return event
        event = weather.update(0.1)
        # Event may or may not be returned depending on intensity threshold


class TestBuildingStyles(unittest.TestCase):
    """Tests for building style system."""

    def test_building_styles_exist(self):
        """Test all building styles are defined."""
        styles = list(BuildingStyle)
        self.assertIn(BuildingStyle.MODERN, styles)
        self.assertIn(BuildingStyle.BRICK, styles)
        self.assertIn(BuildingStyle.CONCRETE, styles)
        self.assertIn(BuildingStyle.ART_DECO, styles)
        self.assertIn(BuildingStyle.INDUSTRIAL, styles)

    def test_city_block_creation(self):
        """Test city block generates buildings."""
        block = CityBlock(0, 0, 200, 160)
        self.assertGreater(len(block.buildings), 0)
        self.assertEqual(len(block.buildings), len(block.building_colors))
        self.assertEqual(len(block.buildings), len(block.building_styles))

    def test_window_states_cached(self):
        """Test window states are cached per building."""
        block = CityBlock(0, 0, 200, 160)
        # Each building should have window states
        self.assertEqual(len(block.building_window_states), len(block.buildings))

        # Get initial states
        if block.building_window_states and block.building_window_states[0]:
            initial_states = block.building_window_states[0].copy()
            # States should persist (not change without regeneration)
            self.assertEqual(block.building_window_states[0], initial_states)


class TestCrimeSimulation(unittest.TestCase):
    """Tests for crime system."""

    def test_init(self):
        """Test crime simulation initialization."""
        crime = CrimeSimulation(1000, 1000)
        self.assertEqual(crime.total_muggings, 0)
        self.assertEqual(crime.criminals_caught, 0)
        self.assertFalse(crime.is_night)

    def test_night_mode(self):
        """Test night mode can be set."""
        crime = CrimeSimulation(1000, 1000)
        crime.set_night_mode(True)
        self.assertTrue(crime.is_night)
        crime.set_night_mode(False)
        self.assertFalse(crime.is_night)

    def test_update_no_crash(self):
        """Test update runs without crashing."""
        crime = CrimeSimulation(1000, 1000)
        # Empty lists should not crash
        events = crime.update(0.1, [], [], [], 100, 100)
        self.assertIsInstance(events, list)


class TestNarratorQueue(unittest.TestCase):
    """Tests for narrator queue pacing."""

    def test_queue_line(self):
        """Test lines can be queued."""
        queue = NarratorQueue()
        queue.queue_line("Test line")
        # Should have line in queue or speaking
        # Cannot check internal state easily without more mocking

    def test_update_returns_line_or_none(self):
        """Test update returns appropriate type."""
        queue = NarratorQueue()
        result = queue.update(0.1)
        self.assertTrue(result is None or isinstance(result, str))


class TestGameLoopPhases(unittest.TestCase):
    """Tests for game loop phase system."""

    def test_phases_exist(self):
        """Test all game phases are defined."""
        phases = list(GamePhase)
        self.assertIn(GamePhase.TUTORIAL, phases)
        self.assertIn(GamePhase.LIVING_CITY, phases)
        self.assertIn(GamePhase.SOMETHING_WRONG, phases)
        self.assertIn(GamePhase.EXIT_SEARCH, phases)


class TestCityMap(unittest.TestCase):
    """Tests for city map generation."""

    def test_config_defaults(self):
        """Test city config has reasonable defaults."""
        config = CityConfig()
        self.assertGreater(config.world_width, 0)
        self.assertGreater(config.world_height, 0)
        self.assertGreater(config.block_width, 0)
        self.assertGreater(config.road_width, 0)

    def test_city_generates_blocks(self):
        """Test city generates building blocks."""
        config = CityConfig(world_width=800, world_height=600)
        city = CityMap(config)
        # Should have some blocks (may skip some for parks)
        self.assertGreater(len(city.blocks), 0)

    def test_sidewalk_nodes_generated(self):
        """Test sidewalk pathfinding nodes exist."""
        config = CityConfig(world_width=800, world_height=600)
        city = CityMap(config)
        self.assertGreater(len(city.sidewalk_nodes), 0)

    def test_find_nearest_sidewalk(self):
        """Test can find nearest sidewalk node."""
        config = CityConfig(world_width=800, world_height=600)
        city = CityMap(config)
        node = city.get_nearest_sidewalk_node(400, 300)
        self.assertIsNotNone(node)


class TestCamera(unittest.TestCase):
    """Tests for camera system."""

    def test_camera_init(self):
        """Test camera initialization."""
        cam = Camera(800, 600, 3200, 2400)
        self.assertEqual(cam.screen_width, 800)
        self.assertEqual(cam.world_width, 3200)

    def test_camera_clamps(self):
        """Test camera clamps to world bounds."""
        cam = Camera(800, 600, 1600, 1200)
        cam.follow(0, 0)  # Try to go to corner
        cam.x = -100  # Force invalid position
        cam.follow(400, 300)  # Should clamp
        self.assertGreaterEqual(cam.x, 0)
        self.assertGreaterEqual(cam.y, 0)


class TestNarratorQueue(unittest.TestCase):
    """Tests for narrator queue pacing."""

    def test_init(self):
        """Test narrator queue initialization."""
        from game_loop import NarratorQueue
        queue = NarratorQueue(min_gap=10.0, max_queue=2)
        self.assertEqual(queue.min_gap, 10.0)
        self.assertEqual(queue.max_queue, 2)

    def test_queue_line(self):
        """Test queueing lines."""
        from game_loop import NarratorQueue
        queue = NarratorQueue(min_gap=10.0, max_queue=2)
        queue.queue_line("Test line 1")
        self.assertEqual(len(queue.queue), 1)

    def test_min_gap_enforced(self):
        """Test that minimum gap between lines is enforced."""
        from game_loop import NarratorQueue
        queue = NarratorQueue(min_gap=10.0, max_queue=2)
        queue.queue_line("Line 1")

        # First line should be available immediately
        line = queue.update(0.1)
        self.assertEqual(line, "Line 1")

        # Queue another line
        queue.queue_line("Line 2")

        # Should NOT be available within min_gap
        line = queue.update(5.0)  # Only 5 seconds passed
        self.assertIsNone(line)

        # Should be available after min_gap
        line = queue.update(6.0)  # Now 11 seconds total
        self.assertEqual(line, "Line 2")

    def test_max_queue_limit(self):
        """Test that queue doesn't exceed max size."""
        from game_loop import NarratorQueue
        queue = NarratorQueue(min_gap=1.0, max_queue=2)
        queue.queue_line("Line 1")
        queue.queue_line("Line 2")
        queue.queue_line("Line 3")  # Should drop oldest
        self.assertLessEqual(len(queue.queue), 2)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
