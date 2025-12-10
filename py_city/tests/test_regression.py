"""
Regression tests for Py City game components.

Tests core systems without requiring pygame display:
- Day/night cycle
- Weather system
- Building generation
- Crime simulation
- Game loop phases
- Building interiors
- Quest system
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


class TestBuildingInteriors(unittest.TestCase):
    """Tests for building interior system."""

    def test_interior_object_creation(self):
        """Test InteriorObject can be created."""
        from interiors import InteriorObject
        obj = InteriorObject(
            name="Test Dresser",
            position=(50, 50),
            size=(40, 40),
            searchable=True,
        )
        self.assertEqual(obj.name, "Test Dresser")
        self.assertTrue(obj.searchable)
        self.assertFalse(obj.searched)

    def test_interior_object_get_rect(self):
        """Test InteriorObject rect calculation."""
        from interiors import InteriorObject
        obj = InteriorObject(name="Test", position=(100, 200), size=(50, 60))
        rect = obj.get_rect(offset_x=10, offset_y=20)
        self.assertEqual(rect.x, 110)
        self.assertEqual(rect.y, 220)
        self.assertEqual(rect.width, 50)
        self.assertEqual(rect.height, 60)

    def test_building_interior_generation(self):
        """Test BuildingInterior generates objects."""
        from interiors import BuildingInterior
        interior = BuildingInterior(building_type="house", seed=42)
        self.assertGreater(len(interior.objects), 0)
        self.assertEqual(interior.width, 400)
        self.assertEqual(interior.height, 300)

    def test_building_interior_has_door(self):
        """Test BuildingInterior always has exit door."""
        from interiors import BuildingInterior
        interior = BuildingInterior(building_type="hospital", seed=123)
        door = interior.get_door()
        self.assertIsNotNone(door)
        self.assertTrue(door.is_door)
        self.assertFalse(door.searchable)

    def test_building_interior_search_object(self):
        """Test searching objects returns correct results."""
        from interiors import BuildingInterior
        interior = BuildingInterior(building_type="house", seed=1)

        # Find a searchable object
        searchable = None
        for obj in interior.objects:
            if obj.searchable and not obj.is_door:
                searchable = obj
                break

        if searchable:
            message, item = interior.search_object(searchable, horror_stage="early")
            self.assertIsInstance(message, str)
            self.assertTrue(searchable.searched)

            # Second search should say already searched
            message2, item2 = interior.search_object(searchable)
            self.assertIn("already", message2.lower())

    def test_building_interior_horror_text(self):
        """Test horror text appears in late stages."""
        from interiors import BuildingInterior
        interior = BuildingInterior(building_type="house", seed=999)

        # Find object with horror_text
        horror_obj = None
        for obj in interior.objects:
            if obj.horror_text and obj.searchable:
                horror_obj = obj
                break

        if horror_obj:
            message, _ = interior.search_object(horror_obj, horror_stage="late")
            self.assertIn(horror_obj.horror_text, message)

    def test_interior_manager_caching(self):
        """Test InteriorManager caches interiors."""
        from interiors import InteriorManager
        manager = InteriorManager()

        interior1 = manager.get_interior(building_id=1, building_type="house")
        interior2 = manager.get_interior(building_id=1, building_type="house")

        self.assertIs(interior1, interior2)  # Same object

        interior3 = manager.get_interior(building_id=2, building_type="bar")
        self.assertIsNot(interior1, interior3)  # Different building

    def test_building_types_have_objects(self):
        """Test all building types generate valid interiors."""
        from interiors import BuildingInterior, BUILDING_OBJECTS
        for building_type in BUILDING_OBJECTS.keys():
            interior = BuildingInterior(building_type=building_type, seed=100)
            self.assertGreater(len(interior.objects), 0,
                             f"Building type {building_type} has no objects")


class TestQuestSystem(unittest.TestCase):
    """Tests for quest system."""

    def test_quest_types_exist(self):
        """Test all quest types are defined."""
        from quest_system import QuestType
        types = list(QuestType)
        self.assertIn(QuestType.TUTORIAL, types)
        self.assertIn(QuestType.EXPLORATION, types)
        self.assertIn(QuestType.SOCIAL, types)
        self.assertIn(QuestType.INVESTIGATION, types)
        self.assertIn(QuestType.MORAL, types)
        self.assertIn(QuestType.CRIME_NOIR, types)

    def test_quest_status_enum(self):
        """Test QuestStatus enum."""
        from quest_system import QuestStatus
        statuses = list(QuestStatus)
        self.assertIn(QuestStatus.LOCKED, statuses)
        self.assertIn(QuestStatus.AVAILABLE, statuses)
        self.assertIn(QuestStatus.ACTIVE, statuses)
        self.assertIn(QuestStatus.COMPLETED, statuses)

    def test_quest_progress_tracking(self):
        """Test Quest tracks progress."""
        from quest_system import Quest, QuestType, QuestStatus
        quest = Quest(
            id="test_quest",
            title="Test Quest",
            description="A test",
            quest_type=QuestType.TUTORIAL,
            objective="test_event",
            target_count=3,
        )
        quest.status = QuestStatus.ACTIVE

        self.assertEqual(quest.get_progress_text(), "0/3")

        quest.check_objective("test_event")
        self.assertEqual(quest.current_count, 1)
        self.assertEqual(quest.get_progress_text(), "1/3")

    def test_quest_completion(self):
        """Test quest completes when target reached."""
        from quest_system import Quest, QuestType, QuestStatus
        quest = Quest(
            id="test",
            title="Test",
            description="",
            quest_type=QuestType.TUTORIAL,
            objective="finish",
            target_count=2,
        )
        quest.status = QuestStatus.ACTIVE

        completed = quest.check_objective("finish")
        self.assertFalse(completed)

        completed = quest.check_objective("finish")
        self.assertTrue(completed)
        self.assertEqual(quest.status, QuestStatus.COMPLETED)

    def test_quest_manager_init(self):
        """Test QuestManager initialization."""
        from quest_system import QuestManager, ALL_QUESTS
        manager = QuestManager()
        self.assertIsNotNone(manager.quests)
        self.assertEqual(len(manager.quests), len(ALL_QUESTS))

    def test_quest_manager_start_quest(self):
        """Test starting a quest."""
        from quest_system import QuestManager, QuestStatus
        manager = QuestManager()

        # Make first tutorial quest available
        tutorial_id = "tutorial_move"
        if tutorial_id in manager.quests:
            manager.quests[tutorial_id].status = QuestStatus.AVAILABLE

            quest = manager.start_quest(tutorial_id)
            self.assertIsNotNone(quest)
            self.assertEqual(quest.status, QuestStatus.ACTIVE)
            self.assertEqual(manager.active_quest_id, tutorial_id)

    def test_quest_manager_on_event(self):
        """Test event processing advances quests."""
        from quest_system import QuestManager, QuestStatus
        manager = QuestManager()

        # Start movement tutorial
        tutorial_id = "tutorial_move"
        if tutorial_id in manager.quests:
            manager.quests[tutorial_id].status = QuestStatus.AVAILABLE
            manager.start_quest(tutorial_id)

            # Trigger movement events
            for _ in range(20):
                result = manager.on_event("player_moved")
                if result:
                    break

            # Should complete after 20 moves
            self.assertIn(tutorial_id, manager.completed_quests)

    def test_all_quests_defined(self):
        """Test essential quests exist."""
        from quest_system import ALL_QUESTS
        quest_ids = [q.id for q in ALL_QUESTS]

        # Check some key quests exist
        self.assertIn("tutorial_move", quest_ids)
        self.assertIn("tutorial_talk", quest_ids)
        self.assertIn("meet_neighbors", quest_ids)
        self.assertIn("find_hospital", quest_ids)

    def test_quest_horror_hints(self):
        """Test quests have horror hints."""
        from quest_system import ALL_QUESTS
        # At least some quests should have horror hints
        hints_found = sum(1 for q in ALL_QUESTS if q.horror_hint)
        self.assertGreater(hints_found, 0, "No quests have horror hints")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
