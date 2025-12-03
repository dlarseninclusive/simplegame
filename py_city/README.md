# Py City

A GTA-lite city simulation game with crime, vehicles, animals, and enterable buildings. Part of "The Tutorial" horror meta-game.

## Overview

Py City is an open-world city exploration game featuring:
- Large scrollable city with wraparound edges
- Day/night cycle and weather system
- NPCs with pathfinding and trust/hope system
- Crime simulation (mugging, arrests, chases)
- Vehicles driving on roads
- Animals wandering the streets
- Special buildings you can enter (jail, courthouse, hospital, etc.)
- Crime investigation system with clues
- Corruption/horror effects that increase over time
- Tutorial system with narrator commentary

## File Structure

### Core Game Files

| File | Purpose |
|------|---------|
| `run_wrapped.py` | Main entry point for "The Tutorial" integration. Contains the game loop, event handling, and rendering. |
| `main.py` | Standalone game launcher (not used in The Tutorial) |
| `city_map.py` | City generation, camera, weather, day/night cycle, building styles |
| `city_entities.py` | Vehicles, animals, special buildings, interiors, road network, investigation system |
| `game_loop.py` | Game phases, tutorial system, anomaly system, crime simulation, narrator queue |
| `corruption.py` | Horror effects (time dilation, input blocking, visual glitches, NPC freezing) |

### Supporting Files

| File | Purpose |
|------|---------|
| `npc.py` | NPC class with pathfinding and behavior |
| `player.py` | Player class with movement and stats |
| `buildings.py` | Legacy building definitions |
| `rendering.py` | Utility rendering functions |
| `utils.py` | Helper utilities |
| `game_state.py` | Game state storage |
| `quest_system.py` | Quest tracking (placeholder) |

### Other Files

| File | Purpose |
|------|---------|
| `FIX_LOG.md` | Running log of bugs and fixes |
| `tests/` | Regression tests |

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move player |
| Right-click | Click-to-move |
| Left-click / Space | Attack |
| E | Interact with NPC / Enter building / Exit building |
| I | Toggle instructions panel |
| M | Toggle audio mute |
| Tab | Toggle status panel |
| Escape | Pause menu |

## Game Phases

1. **TUTORIAL** - Initial phase with narrator guidance
2. **LIVING_CITY** - Normal city exploration
3. **SOMETHING_WRONG** - Anomalies begin appearing
4. **EXIT_SEARCH** - Finding the exit portal
5. **COMPLETED** - Level complete

## Special Instructions

### Adding New Vehicle Types
1. Add enum value to `VehicleType` in `city_entities.py`
2. Add color and size in `Vehicle.__post_init__()`
3. Add spawn weight in `VehicleManager.spawn_vehicles()`

### Adding New Building Interiors
1. Add enum value to `InteriorType` in `city_entities.py`
2. Add layout in `BuildingInterior._generate_layout()`
3. Map building type to interior in `InteriorManager.BUILDING_TO_INTERIOR`

### Adding New Anomalies
1. Add anomaly definition in `game_loop.py` `GameLoopManager._create_anomalies()`
2. Include name, description, narrator_reaction, and position

### Modifying Corruption Effects
Edit `corruption.py`:
- `PHASE_ENTROPY` - entropy levels per game phase
- `warp_time()` - time dilation effect
- `should_block_escape()` - ESC key blocking
- `draw_visual_corruption()` - glitch rectangles
- `draw_scan_lines()` - CRT scan line effect

## Running Tests

```bash
cd /path/to/py_city
python -m pytest tests/test_regression.py -v
```

## Integration with The Tutorial

This game is loaded via `py_adapter.py` in the main game. The `run()` function in `run_wrapped.py` is called with:
- `screen` - pygame display surface
- `clock` - pygame clock
- `guide` - AI narrator instance
- `scene_slug` - scene identifier
- `tone` - narrator tone setting

The game hooks into:
- `GameOverlay` for subtitles and notifications
- `PlotEventBus` for tracking player behavior
- `HorrorNPCDialogue` for AI-generated NPC responses
