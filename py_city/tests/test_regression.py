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
from corruption import CorruptionManager, CORRUPTION_NARRATOR_LINES
from city_entities import (
    Vehicle, VehicleType, VehicleManager,
    Animal, AnimalType, AnimalManager,
    SpecialBuilding, SpecialBuildingType, SpecialBuildingManager,
    RoadNetwork, Clue, ClueType, CrimeCase, InvestigationManager,
    InteriorType, Furniture, BuildingInterior, InteriorManager
)


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


class TestCorruptionManager(unittest.TestCase):
    """Tests for corruption/entropy system."""

    def test_init(self):
        """Test corruption manager initialization."""
        corruption = CorruptionManager()
        self.assertEqual(corruption.entropy, 0.0)
        self.assertEqual(corruption.target_entropy, 0.0)

    def test_entropy_by_phase(self):
        """Test entropy levels for different phases."""
        corruption = CorruptionManager()

        corruption.update_entropy("TUTORIAL")
        self.assertEqual(corruption.target_entropy, 0.0)

        corruption.update_entropy("LIVING_CITY")
        self.assertEqual(corruption.target_entropy, 0.05)

        corruption.update_entropy("SOMETHING_WRONG")
        self.assertEqual(corruption.target_entropy, 0.3)

        corruption.update_entropy("EXIT_SEARCH")
        self.assertEqual(corruption.target_entropy, 0.6)

    def test_time_warp_default(self):
        """Test time warp returns 1.0 by default."""
        corruption = CorruptionManager()
        dt = corruption.warp_time(0.016)
        self.assertEqual(dt, 0.016)

    def test_escape_blocking_low_entropy(self):
        """Test escape not blocked at low entropy."""
        corruption = CorruptionManager()
        corruption.entropy = 0.1
        # At low entropy, should never block
        blocked = corruption.should_block_escape()
        self.assertFalse(blocked)

    def test_narrator_lines_exist(self):
        """Test corruption narrator lines are defined."""
        self.assertIn("TIME_GLITCH", CORRUPTION_NARRATOR_LINES)
        self.assertIn("ESCAPE_BLOCKED", CORRUPTION_NARRATOR_LINES)
        self.assertGreater(len(CORRUPTION_NARRATOR_LINES["ESCAPE_BLOCKED"]), 0)


class TestVehicles(unittest.TestCase):
    """Tests for vehicle system."""

    def test_vehicle_types_exist(self):
        """Test all vehicle types are defined."""
        types = list(VehicleType)
        self.assertIn(VehicleType.CAR, types)
        self.assertIn(VehicleType.TRUCK, types)
        self.assertIn(VehicleType.BUS, types)
        self.assertIn(VehicleType.POLICE_CAR, types)
        self.assertIn(VehicleType.TAXI, types)

    def test_vehicle_creation(self):
        """Test vehicle can be created."""
        vehicle = Vehicle(x=100, y=100, vehicle_type=VehicleType.CAR, direction=(1, 0))
        self.assertEqual(vehicle.x, 100)
        self.assertEqual(vehicle.vehicle_type, VehicleType.CAR)
        self.assertFalse(vehicle.waiting)

    def test_vehicle_speed_varies_by_type(self):
        """Test different vehicle types have different speeds."""
        car = Vehicle(x=0, y=0, vehicle_type=VehicleType.CAR, direction=(1, 0))
        bus = Vehicle(x=0, y=0, vehicle_type=VehicleType.BUS, direction=(1, 0))
        police = Vehicle(x=0, y=0, vehicle_type=VehicleType.POLICE_CAR, direction=(1, 0))

        self.assertGreater(police.speed, car.speed)
        self.assertGreater(car.speed, bus.speed)

    def test_vehicle_manager_init(self):
        """Test vehicle manager initialization."""
        manager = VehicleManager(1000, 1000)
        self.assertEqual(len(manager.vehicles), 0)
        self.assertEqual(manager.max_vehicles, 15)


class TestAnimals(unittest.TestCase):
    """Tests for animal system."""

    def test_animal_types_exist(self):
        """Test all animal types are defined."""
        types = list(AnimalType)
        self.assertIn(AnimalType.DOG, types)
        self.assertIn(AnimalType.CAT, types)
        self.assertIn(AnimalType.PIGEON, types)
        self.assertIn(AnimalType.RAT, types)

    def test_animal_creation(self):
        """Test animal can be created."""
        animal = Animal(x=100, y=100, animal_type=AnimalType.DOG)
        self.assertEqual(animal.x, 100)
        self.assertEqual(animal.animal_type, AnimalType.DOG)
        self.assertEqual(animal.state, "idle")

    def test_animal_size_varies_by_type(self):
        """Test different animal types have different sizes."""
        dog = Animal(x=0, y=0, animal_type=AnimalType.DOG)
        cat = Animal(x=0, y=0, animal_type=AnimalType.CAT)
        rat = Animal(x=0, y=0, animal_type=AnimalType.RAT)

        self.assertGreater(dog.size, cat.size)
        self.assertGreater(cat.size, rat.size)

    def test_animal_manager_building_collision(self):
        """Test animal manager tracks building rects."""
        manager = AnimalManager(1000, 1000)
        rect = MockPygame.Rect(100, 100, 50, 50)
        manager.set_building_rects([rect])

        self.assertTrue(manager._is_in_building(125, 125))
        self.assertFalse(manager._is_in_building(0, 0))


class TestSpecialBuildings(unittest.TestCase):
    """Tests for special building system."""

    def test_building_types_exist(self):
        """Test all special building types are defined."""
        types = list(SpecialBuildingType)
        self.assertIn(SpecialBuildingType.JAIL, types)
        self.assertIn(SpecialBuildingType.COURTHOUSE, types)
        self.assertIn(SpecialBuildingType.HOSPITAL, types)
        self.assertIn(SpecialBuildingType.POLICE_STATION, types)
        self.assertIn(SpecialBuildingType.BANK, types)
        self.assertIn(SpecialBuildingType.BAR, types)

    def test_building_creation(self):
        """Test special building can be created."""
        building = SpecialBuilding(
            x=100, y=100, width=80, height=60,
            building_type=SpecialBuildingType.JAIL
        )
        self.assertEqual(building.building_type, SpecialBuildingType.JAIL)
        self.assertEqual(building.name, "City Jail")
        self.assertTrue(building.enterable)

    def test_building_door_position(self):
        """Test door is at bottom center."""
        building = SpecialBuilding(
            x=100, y=100, width=80, height=60,
            building_type=SpecialBuildingType.BANK
        )
        self.assertEqual(building.door_x, 140)  # 100 + 80/2
        self.assertEqual(building.door_y, 160)  # 100 + 60

    def test_is_near_door(self):
        """Test door proximity detection."""
        building = SpecialBuilding(
            x=100, y=100, width=80, height=60,
            building_type=SpecialBuildingType.BAR
        )
        self.assertTrue(building.is_near_door(140, 160, radius=30))
        self.assertFalse(building.is_near_door(0, 0, radius=30))


class TestRoadNetwork(unittest.TestCase):
    """Tests for road network pathfinding."""

    def test_road_network_init(self):
        """Test road network initialization."""
        network = RoadNetwork()
        self.assertEqual(len(network.nodes), 0)
        self.assertEqual(len(network.segments), 0)

    def test_build_from_grid(self):
        """Test road network generation from grid."""
        network = RoadNetwork()
        network.build_from_grid(
            world_width=800, world_height=600,
            block_width=150, block_height=120,
            road_width=50
        )
        self.assertGreater(len(network.nodes), 0)
        self.assertGreater(len(network.segments), 0)

    def test_get_nearest_node(self):
        """Test finding nearest node."""
        network = RoadNetwork()
        network.build_from_grid(800, 600, 150, 120, 50)
        node = network.get_nearest_node(400, 300)
        self.assertIsNotNone(node)

    def test_get_random_path(self):
        """Test path generation."""
        network = RoadNetwork()
        network.build_from_grid(800, 600, 150, 120, 50)
        path = network.get_random_path(400, 300, length=3)
        self.assertGreater(len(path), 0)


class TestInvestigationSystem(unittest.TestCase):
    """Tests for crime investigation system."""

    def test_clue_types_exist(self):
        """Test all clue types are defined."""
        types = list(ClueType)
        self.assertIn(ClueType.WITNESS, types)
        self.assertIn(ClueType.FOOTPRINT, types)
        self.assertIn(ClueType.WEAPON, types)

    def test_investigation_manager_init(self):
        """Test investigation manager initialization."""
        manager = InvestigationManager()
        self.assertEqual(len(manager.active_cases), 0)
        self.assertEqual(len(manager.solved_cases), 0)

    def test_create_case(self):
        """Test case creation generates clues."""
        manager = InvestigationManager()
        case = manager.create_case("robbery", 1000, 1000)

        self.assertEqual(case.crime_type, "robbery")
        self.assertEqual(len(case.clues), 3)
        self.assertFalse(case.solved)
        self.assertEqual(len(manager.active_cases), 1)


class TestBuildingInteriors(unittest.TestCase):
    """Tests for building interior system."""

    def test_interior_types_exist(self):
        """Test all interior types are defined."""
        types = list(InteriorType)
        self.assertIn(InteriorType.OFFICE, types)
        self.assertIn(InteriorType.JAIL_CELL, types)
        self.assertIn(InteriorType.COURTROOM, types)
        self.assertIn(InteriorType.BAR_ROOM, types)
        self.assertIn(InteriorType.SHOP_FLOOR, types)

    def test_furniture_creation(self):
        """Test furniture can be created."""
        furniture = Furniture(x=50, y=50, width=30, height=20, furniture_type="desk")
        self.assertEqual(furniture.x, 50)
        self.assertEqual(furniture.furniture_type, "desk")
        self.assertFalse(furniture.interactable)

    def test_building_interior_creation(self):
        """Test building interior generates furniture."""
        interior = BuildingInterior(width=400, height=300, interior_type=InteriorType.OFFICE)
        self.assertGreater(len(interior.furniture), 0)
        self.assertEqual(interior.width, 400)
        self.assertEqual(interior.exit_x, 200)  # width // 2

    def test_interior_layout_varies_by_type(self):
        """Test different interior types have different layouts."""
        office = BuildingInterior(width=400, height=300, interior_type=InteriorType.OFFICE)
        bar = BuildingInterior(width=400, height=300, interior_type=InteriorType.BAR_ROOM)

        # Different floor colors indicate different layouts
        self.assertNotEqual(office.floor_color, bar.floor_color)

    def test_interior_collision_rects(self):
        """Test collision rectangles are generated."""
        interior = BuildingInterior(width=400, height=300, interior_type=InteriorType.JAIL_CELL)
        rects = interior.get_collision_rects()
        self.assertEqual(len(rects), len(interior.furniture))

    def test_interior_near_exit(self):
        """Test exit detection."""
        interior = BuildingInterior(width=400, height=300, interior_type=InteriorType.OFFICE)
        # Near exit (bottom center)
        self.assertTrue(interior.is_near_exit(200, 290, radius=30))
        # Far from exit
        self.assertFalse(interior.is_near_exit(50, 50, radius=30))

    def test_interior_manager_init(self):
        """Test interior manager initialization."""
        manager = InteriorManager(800, 600)
        self.assertFalse(manager.is_inside)
        self.assertIsNone(manager.current_interior)

    def test_enter_building(self):
        """Test entering a building."""
        manager = InteriorManager(800, 600)
        building = SpecialBuilding(
            x=100, y=100, width=100, height=80,
            building_type=SpecialBuildingType.BAR
        )

        result = manager.enter_building(building)
        self.assertTrue(result)
        self.assertTrue(manager.is_inside)
        self.assertIsNotNone(manager.current_interior)
        self.assertEqual(manager.current_interior.interior_type, InteriorType.BAR_ROOM)

    def test_exit_building(self):
        """Test exiting a building."""
        manager = InteriorManager(800, 600)
        building = SpecialBuilding(
            x=100, y=100, width=100, height=80,
            building_type=SpecialBuildingType.BANK
        )

        manager.enter_building(building)
        self.assertTrue(manager.is_inside)

        exit_pos = manager.exit_building()
        self.assertFalse(manager.is_inside)
        self.assertIsNone(manager.current_interior)
        # Exit position should be near door
        self.assertEqual(exit_pos[0], building.door_x)

    def test_building_type_to_interior_mapping(self):
        """Test all building types map to interior types."""
        for building_type in SpecialBuildingType:
            interior_type = InteriorManager.BUILDING_TO_INTERIOR.get(building_type)
            self.assertIsNotNone(
                interior_type,
                f"Building type {building_type} has no interior mapping"
            )


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
