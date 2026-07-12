# tower_defense Fix Log

## 2026-07-11 — sprite loading depended on the current working directory

- **Error**: `FileNotFoundError: No file 'sprites/knight.png' found in working
  directory` whenever the game was launched from anywhere but its own folder
  (The Tutorial wrapper launches games from the repo root).
- **Cause**: `assets.py` loaded every sprite with a CWD-relative path
  (`pygame.image.load("sprites/knight.png")`).
- **Solution**: `assets.py` now resolves sprites relative to its own file via
  `_sprite_path()` (`os.path.dirname(os.path.abspath(__file__))/sprites`).
  Behaviour when run from the module directory is unchanged.

## 2026-07-11 — wave spawns and base position hardcoded to 800x600

- **Error**: Not a crash, but at the wrapper's resolution (1280x720) enemies
  spawned along the edges of an invisible 800x600 rectangle in the middle of
  the screen, and the base sat off-centre.
- **Cause**: `WaveManager.get_random_edge_position()` and `BASE_POSITION` use
  `config.SCREEN_WIDTH/HEIGHT` constants.
- **Solution**: The wrapped port (`run_wrapped.py`) re-centres the base on the
  real screen (`base.x, base.y = width // 2, height // 2`) and subclasses
  `WaveManager` (`EdgeWaveManager`) to spawn at the actual screen edges. The
  standalone game is untouched.
