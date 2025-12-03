# Py City Tests

Regression tests for Py City game components.

## Overview

These tests validate core game systems without requiring a pygame display. They use a mock pygame implementation to avoid initialization issues.

## Test Coverage

| Test Class | Systems Tested |
|------------|----------------|
| `TestDayNightCycle` | Time progression, day/night detection, window lighting |
| `TestWeatherSystem` | Weather states, temperature, events |
| `TestBuildingStyles` | Building generation, style enums, window states |
| `TestCrimeSimulation` | Crime tracking, night mode, updates |
| `TestNarratorQueue` | Line queuing, gap enforcement, priority |
| `TestGameLoopPhases` | Game phase enum existence |
| `TestCityMap` | Block generation, sidewalk nodes, configuration |
| `TestCamera` | Camera positioning, clamping |
| `TestCorruptionManager` | Entropy scaling, time warp, escape blocking |
| `TestVehicles` | Vehicle types, creation, speed variation |
| `TestAnimals` | Animal types, creation, building collision |
| `TestSpecialBuildings` | Building types, door detection |
| `TestRoadNetwork` | Grid generation, pathfinding |
| `TestInvestigationSystem` | Clue types, case creation |
| `TestBuildingInteriors` | Interior types, furniture, enter/exit |

## Running Tests

```bash
# Run all tests
python -m pytest tests/test_regression.py -v

# Run specific test class
python -m pytest tests/test_regression.py -v -k "TestVehicles"

# Run with coverage
python -m pytest tests/test_regression.py -v --cov=.

# Run from py_city directory
cd vendor/simplegame/py_city
python -m pytest tests/ -v
```

## Special Instructions

### Adding New Tests

1. Import new classes in the imports section at the top of `test_regression.py`
2. Create a new test class inheriting from `unittest.TestCase`
3. Use `MockPygame.Rect` and `MockPygame.Surface` for pygame objects
4. Test logic only - avoid testing rendering code

### Mock Pygame

The `MockPygame` class provides minimal implementations of:
- `Rect` - Rectangle with collision detection
- `Surface` - Drawing surface (no-op methods)
- `font.Font` - Font rendering (no-op)
- `draw` - Drawing functions (no-op)
- `time.get_ticks()` - Returns 0

This allows testing game logic without initializing pygame's display.

### Test Naming Convention

- Test methods must start with `test_`
- Use descriptive names: `test_vehicle_speed_varies_by_type`
- Group related tests in the same class

## Current Test Count

63 tests across 15 test classes (as of 2025-12-02)
