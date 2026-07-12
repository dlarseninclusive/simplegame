# py_horror Fix Log

## 2026-07-11 — game.py shadowed the wrapper's `game` package

- **Error**: `ModuleNotFoundError: No module named 'game.inventory'; 'game' is
  not a package` when running `run_wrapped.py` standalone.
- **Cause**: This module directory goes on `sys.path` so sibling imports work,
  and it contained a top-level `game.py`. A regular module always wins over a
  namespace package (the wrapper's `C:\beginners_guide\game\` has no
  `__init__.py`), regardless of `sys.path` order, so `import game` resolved to
  `py_horror/game.py` and `game.inventory` / `game.overlay` imports failed.
- **Solution**: Renamed `game.py` to `horror_game.py` and updated the import
  in `main.py`. Standalone behaviour is unchanged.

## 2026-07-11 — constants.py created its own display at import time

- **Error**: Importing any py_horror module inside The Tutorial wrapper called
  `pygame.display.set_mode((1280, 720))` at import time (from `constants.py`),
  resizing/hijacking the wrapper's window — a contract violation (`run()` must
  use the passed screen and never call `set_mode`).
- **Cause**: `constants.py` unconditionally ran `pygame.init()`,
  `set_mode(...)` and `set_caption(...)` as module-level side effects.
- **Solution**: `constants.py` now reuses `pygame.display.get_surface()` when
  a display already exists and only creates its own window when run truly
  standalone (no display yet). `pygame.init()` is idempotent and kept so the
  module still works standalone.

## 2026-07-11 — monsters dealt no damage (death was unreachable)

- **Error**: Not a crash, but the player's health could never decrease: no
  code path ever damaged the player, so the health bar, "horror", and any
  death handling were dead weight.
- **Cause**: `Monster.update()` only wanders; neither `game.py` nor the
  entities ever applied damage to the player.
- **Solution**: The wrapped port (`run_wrapped.py`) applies contact damage per
  monster type (zombie 8, tracker 5, bat 3, boss 15) with a 60-frame
  invulnerability window, publishes `PlotEvent.DEATH`, and respawns the player
  at the village centre. The standalone game is untouched.
