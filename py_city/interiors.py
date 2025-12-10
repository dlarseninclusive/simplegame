"""
Building Interior System for py_city.

Generates procedural interiors for buildings with searchable objects
that can contain items. Interiors vary by building type and can have
horror elements that appear in later stages.

Supports multi-level buildings:
- Ground floor (level 0): Main interior
- Basement (level -1): Darker, more horror content
- Upper floor (level 1): Additional exploration (hospital, bank)
"""

import random
from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum
import pygame

# Import inventory items if available
try:
    from game.inventory import Item, get_item, ItemCategory
except ImportError:
    # Fallback for standalone testing
    Item = None
    get_item = None
    ItemCategory = None


class FloorLevel(IntEnum):
    """Building floor levels."""
    BASEMENT = -1
    GROUND = 0
    UPPER = 1


@dataclass
class InteriorObject:
    """
    A searchable object inside a building.

    Objects can contain items and have horror text that appears
    in LATE/FINALE stages.
    """
    name: str
    position: tuple[int, int]  # Position within interior (relative)
    size: tuple[int, int] = (40, 40)
    color: tuple[int, int, int] = (60, 60, 65)
    searchable: bool = True
    searched: bool = False
    item_id: Optional[str] = None  # ID of item contained (from inventory.py)
    search_text: str = ""  # Text shown when searching
    empty_text: str = "Nothing here."
    horror_text: str = ""  # Appears in LATE stage when searching
    interactable: bool = True
    is_door: bool = False  # Special flag for exit door
    is_stairs: bool = False  # Special flag for stairs
    stairs_direction: int = 0  # +1 = up, -1 = down

    def get_rect(self, offset_x: int = 0, offset_y: int = 0) -> pygame.Rect:
        """Get pygame rect for collision/rendering."""
        return pygame.Rect(
            self.position[0] + offset_x,
            self.position[1] + offset_y,
            self.size[0],
            self.size[1]
        )


# Object templates for different building types
HOUSE_OBJECTS = [
    {"name": "Dresser", "size": (50, 30), "color": (80, 60, 40),
     "search_text": "You rummage through the drawers...",
     "horror_text": "The clothes in here are your size. Exactly your size."},
    {"name": "Bed", "size": (70, 50), "color": (100, 80, 90),
     "search_text": "You check under the bed...",
     "horror_text": "Something is under the bed. It's breathing. You don't look."},
    {"name": "Closet", "size": (40, 60), "color": (70, 55, 40),
     "search_text": "You search the closet...",
     "horror_text": "The closet is deeper than it should be. Much deeper."},
    {"name": "Nightstand", "size": (25, 25), "color": (65, 50, 35),
     "search_text": "You open the drawer...",
     "horror_text": "There's a note inside: 'They're watching through your screen.'"},
    {"name": "Bookshelf", "size": (60, 70), "color": (75, 60, 45),
     "search_text": "You scan the book titles...",
     "horror_text": "One book is titled with YOUR name. It's your biography. It ends today."},
]

HOSPITAL_OBJECTS = [
    {"name": "Medical Cabinet", "size": (50, 60), "color": (200, 200, 210),
     "search_text": "You check the medical supplies...",
     "horror_text": "All the medications are labeled with your name."},
    {"name": "Hospital Bed", "size": (70, 40), "color": (220, 220, 230),
     "search_text": "You examine the bed...",
     "horror_text": "The indent in the mattress is shaped exactly like you."},
    {"name": "Filing Cabinet", "size": (35, 50), "color": (150, 150, 160),
     "search_text": "You flip through patient files...",
     "horror_text": "Every file is about you. Different dates. Same diagnosis: 'Doesn't know.'"},
    {"name": "Crash Cart", "size": (40, 35), "color": (200, 50, 50),
     "search_text": "You check the equipment...",
     "horror_text": "The defibrillator has been used 47 times. On you."},
]

POLICE_STATION_OBJECTS = [
    {"name": "Evidence Locker", "size": (50, 60), "color": (100, 100, 110),
     "search_text": "You examine the evidence bags...",
     "horror_text": "There's evidence of crimes you don't remember committing."},
    {"name": "Desk", "size": (60, 35), "color": (80, 70, 60),
     "search_text": "You search the desk drawers...",
     "horror_text": "A wanted poster with your face. 'WANTED: For knowing too much.'"},
    {"name": "Filing Cabinet", "size": (35, 50), "color": (120, 120, 130),
     "search_text": "You look through case files...",
     "horror_text": "Every unsolved case has a note: 'Perpetrator is currently playing.'"},
    {"name": "Gun Safe", "size": (30, 45), "color": (60, 60, 65),
     "searchable": False,
     "search_text": "It's locked.",
     "horror_text": "The combination is your birthday. You've never told anyone that."},
]

BAR_OBJECTS = [
    {"name": "Bar Counter", "size": (100, 30), "color": (70, 50, 35),
     "search_text": "You check behind the bar...",
     "horror_text": "A note: 'The usual for the visitor.' Dated three years ago."},
    {"name": "Jukebox", "size": (40, 55), "color": (150, 100, 50),
     "searchable": False, "interactable": True,
     "search_text": "The jukebox hums quietly.",
     "horror_text": "It only plays one song. Your favorite song. How does it know?"},
    {"name": "Pool Table", "size": (80, 45), "color": (30, 100, 30),
     "searchable": False,
     "search_text": "Just a pool table.",
     "horror_text": "The balls are arranged to spell LEAVE."},
]

BANK_OBJECTS = [
    {"name": "Teller Window", "size": (50, 40), "color": (180, 180, 190),
     "search_text": "You look through the window...",
     "horror_text": "There's an account in your name. Balance: Your remaining time."},
    {"name": "Safe Deposit Box", "size": (30, 30), "color": (100, 100, 110),
     "search_text": "The box is sealed.",
     "horror_text": "Your box is already open. Something was taken."},
    {"name": "Manager's Desk", "size": (55, 35), "color": (90, 70, 50),
     "search_text": "You search the desk...",
     "horror_text": "A ledger shows transactions from 'PLAYER_1'. The amounts are your karma."},
]

COURTHOUSE_OBJECTS = [
    {"name": "Judge's Bench", "size": (70, 40), "color": (80, 60, 45),
     "search_text": "You examine the bench...",
     "horror_text": "A gavel inscribed: 'For use on persistent players.'"},
    {"name": "Witness Stand", "size": (35, 35), "color": (100, 80, 60),
     "search_text": "You check the stand...",
     "horror_text": "Previous testimony: 'I saw them try to quit. They couldn't.'"},
    {"name": "Court Records", "size": (50, 50), "color": (90, 80, 70),
     "search_text": "You flip through records...",
     "horror_text": "Case #∞: The Player vs. Reality. Verdict: Denied exit."},
]

# Map building types to object templates (ground floor)
BUILDING_OBJECTS = {
    "house": HOUSE_OBJECTS,
    "hospital": HOSPITAL_OBJECTS,
    "police_station": POLICE_STATION_OBJECTS,
    "bar": BAR_OBJECTS,
    "bank": BANK_OBJECTS,
    "courthouse": COURTHOUSE_OBJECTS,
}

# Basement objects - darker, more disturbing
BASEMENT_OBJECTS = {
    "house": [
        {"name": "Old Crate", "size": (45, 40), "color": (50, 40, 30),
         "search_text": "You pry open the dusty crate...",
         "horror_text": "Inside are photos of people who look like you. Hundreds of them."},
        {"name": "Furnace", "size": (50, 55), "color": (40, 35, 35), "searchable": False,
         "search_text": "The furnace is cold. Dead cold.",
         "horror_text": "Something scratches from inside. 'Let me out,' it whispers."},
        {"name": "Shelves", "size": (60, 50), "color": (55, 45, 35),
         "search_text": "You examine the dusty shelves...",
         "horror_text": "Jars of preserved... something. They have your face."},
        {"name": "Trunk", "size": (55, 35), "color": (45, 35, 25),
         "search_text": "You open the old trunk...",
         "horror_text": "Letters addressed to you. Dated decades from now."},
    ],
    "hospital": [
        {"name": "Morgue Drawer", "size": (60, 30), "color": (120, 120, 130),
         "search_text": "You pull open the cold drawer...",
         "horror_text": "The toe tag has your name. And today's date."},
        {"name": "Storage Tank", "size": (45, 60), "color": (100, 110, 120),
         "search_text": "You peer into the murky tank...",
         "horror_text": "Something floats inside. It opens its eyes. YOUR eyes."},
        {"name": "Filing Cabinet", "size": (35, 50), "color": (90, 90, 100),
         "search_text": "Basement records...",
         "horror_text": "Autopsy reports. All the same cause of death: 'Kept playing.'"},
    ],
    "police_station": [
        {"name": "Evidence Archive", "size": (55, 55), "color": (80, 80, 90),
         "search_text": "You dig through cold case evidence...",
         "horror_text": "Evidence bag labeled 'PLAYER #47'. Your belongings inside."},
        {"name": "Holding Cell", "size": (70, 60), "color": (50, 50, 55), "searchable": False,
         "search_text": "An old holding cell.",
         "horror_text": "The walls are covered in tally marks. They add up to your playtime."},
        {"name": "Locked Safe", "size": (40, 40), "color": (60, 60, 65),
         "search_text": "The safe won't open...",
         "horror_text": "A sticky note: 'Contains what's left of the last one who tried to leave.'"},
    ],
}

# Upper floor objects - for buildings that have them
UPPER_FLOOR_OBJECTS = {
    "hospital": [
        {"name": "Patient Bed", "size": (65, 40), "color": (200, 200, 210),
         "search_text": "An empty patient bed...",
         "horror_text": "The nameplate: YOUR NAME. Admitted: 'FOREVER'."},
        {"name": "Monitoring Equipment", "size": (40, 50), "color": (60, 80, 90),
         "search_text": "Medical monitors...",
         "horror_text": "The heart rate matches yours exactly. Even as you hold your breath."},
        {"name": "IV Stand", "size": (25, 55), "color": (150, 150, 160), "searchable": False,
         "search_text": "Just an IV stand.",
         "horror_text": "The bag is labeled: 'Memory Suppressant.'"},
    ],
    "bank": [
        {"name": "Executive Desk", "size": (65, 40), "color": (70, 50, 35),
         "search_text": "You search the mahogany desk...",
         "horror_text": "A contract. Your signature at the bottom. 'I agree to stay forever.'"},
        {"name": "Vault Door", "size": (60, 70), "color": (80, 80, 85), "searchable": False,
         "search_text": "The vault is sealed.",
         "horror_text": "Through the window: piles of... something. That used to be players."},
        {"name": "Security Monitor", "size": (45, 35), "color": (30, 30, 40),
         "search_text": "You check the security feeds...",
         "horror_text": "Every camera shows you. From angles that shouldn't exist."},
    ],
}

# Which building types have which floors
BUILDING_FLOORS = {
    "house": [FloorLevel.GROUND, FloorLevel.BASEMENT],
    "hospital": [FloorLevel.BASEMENT, FloorLevel.GROUND, FloorLevel.UPPER],
    "police_station": [FloorLevel.BASEMENT, FloorLevel.GROUND],
    "bar": [FloorLevel.GROUND],  # No extra floors
    "bank": [FloorLevel.GROUND, FloorLevel.UPPER],
    "courthouse": [FloorLevel.GROUND],  # No extra floors
}

# Items that can be found in each building type (ground floor)
BUILDING_ITEMS = {
    "house": ["old_photograph", "torn_note"],
    "hospital": ["patient_record", "city_map"],
    "police_station": ["police_badge"],
    "bar": [],
    "bank": [],
    "courthouse": [],
}

# Items found in basements (rarer, more important)
BASEMENT_ITEMS = {
    "house": ["basement_key", "broken_watch"],
    "hospital": ["sedative_vial"],
    "police_station": ["worn_key", "evidence_photo"],
}

# Items found on upper floors
UPPER_FLOOR_ITEMS = {
    "hospital": ["patient_wristband"],
    "bank": ["safe_combination"],
}


@dataclass
class InteriorLevel:
    """
    A single floor/level of a building interior.

    Contains objects specific to this floor.
    """
    level: int  # FloorLevel value: -1=basement, 0=ground, 1=upper
    objects: list[InteriorObject] = field(default_factory=list)
    wall_color: tuple[int, int, int] = (35, 35, 40)
    floor_color: tuple[int, int, int] = (50, 50, 55)

    def get_level_name(self) -> str:
        """Get human-readable level name."""
        if self.level == FloorLevel.BASEMENT:
            return "Basement"
        elif self.level == FloorLevel.UPPER:
            return "Upper Floor"
        return "Ground Floor"


@dataclass
class BuildingInterior:
    """
    A multi-level building interior.

    Contains multiple floors with objects to search.
    Supports stairs between levels.
    """
    building_type: str
    width: int = 400
    height: int = 300
    levels: dict[int, InteriorLevel] = field(default_factory=dict)
    current_level: int = FloorLevel.GROUND
    seed: int = 0
    items_placed: list[str] = field(default_factory=list)

    # Convenience properties for backwards compatibility
    @property
    def objects(self) -> list[InteriorObject]:
        """Get objects on current level."""
        if self.current_level in self.levels:
            return self.levels[self.current_level].objects
        return []

    @property
    def wall_color(self) -> tuple[int, int, int]:
        """Get wall color for current level."""
        if self.current_level in self.levels:
            return self.levels[self.current_level].wall_color
        return (35, 35, 40)

    @property
    def floor_color(self) -> tuple[int, int, int]:
        """Get floor color for current level."""
        if self.current_level in self.levels:
            return self.levels[self.current_level].floor_color
        return (50, 50, 55)

    def __post_init__(self):
        if not self.levels:
            self._generate_all_levels()

    def _generate_all_levels(self):
        """Generate all levels for this building type."""
        available_floors = BUILDING_FLOORS.get(self.building_type, [FloorLevel.GROUND])

        for floor_level in available_floors:
            self._generate_level(floor_level)

    def _generate_level(self, level: int):
        """Generate a single level."""
        random.seed(self.seed + level * 1000)  # Different seed per level

        # Get templates and items based on level
        if level == FloorLevel.BASEMENT:
            templates = BASEMENT_OBJECTS.get(self.building_type, HOUSE_OBJECTS)
            available_items = BASEMENT_ITEMS.get(self.building_type, []).copy()
            wall_color = (25, 25, 30)  # Darker walls
            floor_color = (35, 35, 40)  # Darker floor
        elif level == FloorLevel.UPPER:
            templates = UPPER_FLOOR_OBJECTS.get(self.building_type, HOUSE_OBJECTS)
            available_items = UPPER_FLOOR_ITEMS.get(self.building_type, []).copy()
            wall_color = (40, 40, 45)
            floor_color = (55, 55, 60)  # Slightly brighter
        else:  # Ground floor
            templates = BUILDING_OBJECTS.get(self.building_type, HOUSE_OBJECTS)
            available_items = BUILDING_ITEMS.get(self.building_type, []).copy()
            wall_color = (35, 35, 40)
            floor_color = (50, 50, 55)

        level_obj = InteriorLevel(
            level=level,
            wall_color=wall_color,
            floor_color=floor_color,
        )

        # Place 3-5 objects randomly
        num_objects = random.randint(3, min(5, len(templates)))
        selected = random.sample(templates, num_objects) if templates else []

        # Grid-based placement to avoid overlap
        grid_cols = 3
        grid_rows = 2
        cell_w = (self.width - 60) // grid_cols
        cell_h = (self.height - 60) // grid_rows

        positions = []
        for row in range(grid_rows):
            for col in range(grid_cols):
                x = 30 + col * cell_w + random.randint(10, max(11, cell_w - 60))
                y = 30 + row * cell_h + random.randint(10, max(11, cell_h - 60))
                positions.append((x, y))

        random.shuffle(positions)

        for i, template in enumerate(selected):
            pos = positions[i] if i < len(positions) else (
                random.randint(30, self.width - 80),
                random.randint(30, self.height - 80)
            )

            # Maybe place an item in this object
            item_id = None
            if available_items and template.get("searchable", True) and random.random() < 0.5:
                item_id = available_items.pop(0)
                self.items_placed.append(item_id)

            obj = InteriorObject(
                name=template["name"],
                position=pos,
                size=template.get("size", (40, 40)),
                color=template.get("color", (60, 60, 65)),
                searchable=template.get("searchable", True),
                search_text=template.get("search_text", f"You search the {template['name'].lower()}..."),
                empty_text=template.get("empty_text", "Nothing useful here."),
                horror_text=template.get("horror_text", ""),
                interactable=template.get("interactable", True),
                item_id=item_id,
            )
            level_obj.objects.append(obj)

        # Add stairs based on what levels exist
        available_floors = BUILDING_FLOORS.get(self.building_type, [FloorLevel.GROUND])

        # Add stairs down if basement exists and we're on ground
        if level == FloorLevel.GROUND and FloorLevel.BASEMENT in available_floors:
            stairs_down = InteriorObject(
                name="Stairs Down",
                position=(30, self.height // 2 - 25),  # Left side
                size=(45, 50),
                color=(50, 45, 40),
                searchable=False,
                interactable=True,
                is_stairs=True,
                stairs_direction=-1,
                search_text="Stairs leading down into darkness.",
                horror_text="The basement waits. It's been waiting a long time.",
            )
            level_obj.objects.append(stairs_down)

        # Add stairs up if upper floor exists and we're on ground
        if level == FloorLevel.GROUND and FloorLevel.UPPER in available_floors:
            stairs_up = InteriorObject(
                name="Stairs Up",
                position=(self.width - 75, self.height // 2 - 25),  # Right side
                size=(45, 50),
                color=(65, 55, 45),
                searchable=False,
                interactable=True,
                is_stairs=True,
                stairs_direction=1,
                search_text="Stairs leading up.",
                horror_text="Something shuffles above. Or someone.",
            )
            level_obj.objects.append(stairs_up)

        # Add return stairs from basement/upper to ground
        if level == FloorLevel.BASEMENT:
            stairs_up = InteriorObject(
                name="Stairs Up",
                position=(30, self.height // 2 - 25),
                size=(45, 50),
                color=(60, 50, 40),
                searchable=False,
                interactable=True,
                is_stairs=True,
                stairs_direction=1,
                search_text="Back up to the ground floor.",
            )
            level_obj.objects.append(stairs_up)

        if level == FloorLevel.UPPER:
            stairs_down = InteriorObject(
                name="Stairs Down",
                position=(self.width - 75, self.height // 2 - 25),
                size=(45, 50),
                color=(55, 50, 45),
                searchable=False,
                interactable=True,
                is_stairs=True,
                stairs_direction=-1,
                search_text="Back down to the ground floor.",
            )
            level_obj.objects.append(stairs_down)

        # Only add exit door on ground floor
        if level == FloorLevel.GROUND:
            door = InteriorObject(
                name="Door",
                position=(self.width // 2 - 25, self.height - 45),
                size=(50, 35),
                color=(100, 70, 50),
                searchable=False,
                interactable=True,
                is_door=True,
                search_text="The way out.",
            )
            level_obj.objects.append(door)

        self.levels[level] = level_obj

    def get_current_level(self) -> InteriorLevel:
        """Get the current level object."""
        return self.levels.get(self.current_level)

    def get_level_name(self) -> str:
        """Get name of current level."""
        level = self.get_current_level()
        return level.get_level_name() if level else "Unknown"

    def can_change_level(self, direction: int) -> bool:
        """Check if we can go up (+1) or down (-1)."""
        new_level = self.current_level + direction
        return new_level in self.levels

    def change_level(self, direction: int) -> bool:
        """Go up (+1) or down (-1). Returns True if successful."""
        new_level = self.current_level + direction
        if new_level in self.levels:
            self.current_level = new_level
            return True
        return False

    def get_object_at(self, x: int, y: int) -> Optional[InteriorObject]:
        """Get object at screen position on current level."""
        for obj in self.objects:
            rect = obj.get_rect()
            if rect.collidepoint(x, y):
                return obj
        return None

    def get_nearby_object(self, x: int, y: int, radius: int = 50) -> Optional[InteriorObject]:
        """Get nearest interactable object within radius on current level."""
        nearest = None
        nearest_dist = float('inf')

        for obj in self.objects:
            if not obj.interactable:
                continue
            rect = obj.get_rect()
            cx, cy = rect.centerx, rect.centery
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < radius and dist < nearest_dist:
                nearest = obj
                nearest_dist = dist

        return nearest

    def get_door(self) -> Optional[InteriorObject]:
        """Get the exit door object (only on ground floor)."""
        for obj in self.objects:
            if obj.is_door:
                return obj
        return None

    def get_stairs(self) -> list[InteriorObject]:
        """Get all stair objects on current level."""
        return [obj for obj in self.objects if obj.is_stairs]

    def search_object(self, obj: InteriorObject, horror_stage: str = "early") -> tuple[str, Optional[str]]:
        """
        Search an object.

        Returns (message, item_id or None).
        """
        if not obj.searchable:
            return (obj.search_text, None)

        if obj.searched:
            return ("You've already searched here.", None)

        obj.searched = True

        # Build message - basements always show horror text
        show_horror = (horror_stage in ("late", "finale") or
                       self.current_level == FloorLevel.BASEMENT)
        if show_horror and obj.horror_text:
            message = f"{obj.search_text}\n\n{obj.horror_text}"
        else:
            message = obj.search_text

        # Return item if present
        if obj.item_id:
            item_id = obj.item_id
            obj.item_id = None  # Remove from object
            return (message, item_id)

        return (f"{message}\n\n{obj.empty_text}", None)

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0,
             player_pos: tuple[int, int] = None):
        """
        Draw the current level.

        Args:
            screen: Surface to draw on
            offset_x, offset_y: Position offset for centering
            player_pos: Player position for highlighting nearby objects
        """
        level = self.get_current_level()
        if not level:
            return

        # Draw floor (darker for basement)
        floor_rect = pygame.Rect(offset_x, offset_y, self.width, self.height)
        pygame.draw.rect(screen, level.floor_color, floor_rect)

        # Draw walls (border)
        pygame.draw.rect(screen, level.wall_color, floor_rect, 8)

        # Draw level indicator
        font = pygame.font.Font(None, 20)
        level_text = level.get_level_name()
        level_surf = font.render(level_text, True, (150, 150, 160))
        screen.blit(level_surf, (offset_x + 10, offset_y + 10))

        # Draw objects
        for obj in level.objects:
            rect = obj.get_rect(offset_x, offset_y)

            # Highlight if player is nearby
            highlight = False
            if player_pos and obj.interactable:
                dist = ((player_pos[0] - rect.centerx) ** 2 +
                        (player_pos[1] - rect.centery) ** 2) ** 0.5
                highlight = dist < 50

            # Draw object
            color = obj.color
            if obj.searched:
                # Dim searched objects
                color = tuple(max(0, c - 30) for c in color)
            elif highlight:
                # Brighten highlighted objects
                color = tuple(min(255, c + 40) for c in color)

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (80, 80, 85), rect, 2)

            # Draw stair indicator (triangle)
            if obj.is_stairs:
                cx, cy = rect.centerx, rect.centery
                if obj.stairs_direction > 0:  # Up arrow
                    points = [(cx, cy - 10), (cx - 8, cy + 5), (cx + 8, cy + 5)]
                else:  # Down arrow
                    points = [(cx, cy + 10), (cx - 8, cy - 5), (cx + 8, cy - 5)]
                pygame.draw.polygon(screen, (200, 200, 210), points)

            # Draw object name
            name_font = pygame.font.Font(None, 18)
            name_surf = name_font.render(obj.name, True, (180, 180, 190))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 2
            screen.blit(name_surf, (name_x, name_y))

            # Draw interaction hint if highlighted
            if highlight:
                if obj.is_door:
                    hint_text = "[E] Exit"
                elif obj.is_stairs:
                    if obj.stairs_direction > 0:
                        hint_text = "[E] Go Up"
                    else:
                        hint_text = "[E] Go Down"
                elif obj.searched:
                    continue  # No hint for already searched objects
                else:
                    hint_text = "[E] Search"
                hint_surf = name_font.render(hint_text, True, (255, 255, 100))
                hint_x = rect.centerx - hint_surf.get_width() // 2
                hint_y = rect.top - 18
                screen.blit(hint_surf, (hint_x, hint_y))

    def reset(self):
        """Reset all objects on all levels to unsearched state."""
        for level in self.levels.values():
            for obj in level.objects:
                obj.searched = False
        self.current_level = FloorLevel.GROUND


class InteriorManager:
    """
    Manages building interiors across the game.

    Caches generated interiors so they persist during a session.
    """

    def __init__(self):
        self._interiors: dict[int, BuildingInterior] = {}  # building_id -> interior

    def get_interior(self, building_id: int, building_type: str) -> BuildingInterior:
        """Get or create interior for a building."""
        if building_id not in self._interiors:
            self._interiors[building_id] = BuildingInterior(
                building_type=building_type,
                seed=building_id  # Use building ID as seed for consistency
            )
        return self._interiors[building_id]

    def reset_to_ground(self, building_id: int):
        """Reset a building interior to ground floor (for when player exits)."""
        if building_id in self._interiors:
            self._interiors[building_id].current_level = FloorLevel.GROUND

    def clear(self):
        """Clear all cached interiors."""
        self._interiors.clear()
