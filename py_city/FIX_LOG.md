# Py City Fix Log

Running log of bugs found and fixed during development. Append new fixes to the top.

---

## 2025-12-02: InteriorNPCRole forward reference error

**Error:**
```
NameError: name 'InteriorNPCRole' is not defined
```

**Location:** `city_entities.py:1390` in `InteriorManager` class definition

**Cause:** `InteriorManager.INTERIOR_TO_NPCS` dictionary referenced `InteriorNPCRole` enum which is defined later in the file. Python evaluates class-level attributes at class definition time.

**Fix:** Changed to use string role names in the mapping and convert to enum values in `enter_building()` method where `InteriorNPCRole` is guaranteed to be defined.

**Commit:** `653ec32`

---

## 2025-12-02: InteriorManager variable name error

**Error:**
```
NameError: name 'SCREEN_WIDTH' is not defined
```

**Location:** `run_wrapped.py:541`

**Cause:** Used `SCREEN_WIDTH` and `SCREEN_HEIGHT` instead of the actual variable names `WIDTH` and `HEIGHT` that are defined in the `run()` function.

**Fix:** Changed `InteriorManager(SCREEN_WIDTH, SCREEN_HEIGHT)` to `InteriorManager(WIDTH, HEIGHT)`

**Commit:** `1831a97`

---

## 2025-12-02: RoadNode not hashable

**Error:**
```
TypeError: unhashable type: 'RoadNode'
```

**Location:** `city_entities.py:1099` in `get_random_path()`

**Cause:** `RoadNode` dataclass has a mutable `connections` list field, which makes it unhashable by default. The `visited = {start_node}` set operation failed.

**Fix:** Added `@dataclass(eq=False)` decorator and implemented custom `__hash__` and `__eq__` methods based on position (x, y).

**Commit:** `650e071`

---

## 2025-12-02: Corruption visual alpha ValueError

**Error:**
```
ValueError: invalid color argument
```

**Location:** `corruption.py` in `draw_visual_corruption()`

**Cause:** Alpha value could become negative after decay calculation or exceed 255.

**Fix:** Clamped alpha value: `clamped_alpha = max(0, min(255, int(alpha)))`

**Commit:** (part of earlier corruption implementation)

---
