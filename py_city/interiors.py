"""
Building Interior System for py_city.

Generates procedural interiors for buildings with searchable objects
that can contain items. Interiors vary by building type and can have
horror elements that appear in later stages.
"""

import random
from dataclasses import dataclass, field
from typing import Optional
import pygame

# Import inventory items if available
try:
    from game.inventory import Item, get_item, ItemCategory
except ImportError:
    # Fallback for standalone testing
    Item = None
    get_item = None
    ItemCategory = None


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

# Map building types to object templates
BUILDING_OBJECTS = {
    "house": HOUSE_OBJECTS,
    "hospital": HOSPITAL_OBJECTS,
    "police_station": POLICE_STATION_OBJECTS,
    "bar": BAR_OBJECTS,
    "bank": BANK_OBJECTS,
    "courthouse": COURTHOUSE_OBJECTS,
}

# Items that can be found in each building type
BUILDING_ITEMS = {
    "house": ["old_photograph", "torn_note", "basement_key"],
    "hospital": ["patient_record", "city_map"],
    "police_station": ["police_badge", "worn_key"],
    "bar": [],
    "bank": [],
    "courthouse": [],
}


@dataclass
class BuildingInterior:
    """
    A generated interior for a building.

    Contains layout, objects to search, and handles rendering.
    """
    building_type: str
    width: int = 400
    height: int = 300
    objects: list[InteriorObject] = field(default_factory=list)
    wall_color: tuple[int, int, int] = (35, 35, 40)
    floor_color: tuple[int, int, int] = (50, 50, 55)
    seed: int = 0
    items_placed: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.objects:
            self._generate()

    def _generate(self):
        """Generate interior layout based on building type."""
        random.seed(self.seed)

        templates = BUILDING_OBJECTS.get(self.building_type, HOUSE_OBJECTS)
        available_items = BUILDING_ITEMS.get(self.building_type, []).copy()

        # Place 3-5 objects randomly
        num_objects = random.randint(3, min(5, len(templates)))
        selected = random.sample(templates, num_objects)

        # Grid-based placement to avoid overlap
        grid_cols = 3
        grid_rows = 2
        cell_w = (self.width - 60) // grid_cols
        cell_h = (self.height - 60) // grid_rows

        positions = []
        for row in range(grid_rows):
            for col in range(grid_cols):
                x = 30 + col * cell_w + random.randint(10, cell_w - 60)
                y = 30 + row * cell_h + random.randint(10, cell_h - 60)
                positions.append((x, y))

        random.shuffle(positions)

        for i, template in enumerate(selected):
            pos = positions[i] if i < len(positions) else (
                random.randint(30, self.width - 80),
                random.randint(30, self.height - 80)
            )

            # Maybe place an item in this object
            item_id = None
            if available_items and template.get("searchable", True) and random.random() < 0.4:
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
            self.objects.append(obj)

        # Always add exit door at bottom center
        door = InteriorObject(
            name="Door",
            position=(self.width // 2 - 25, self.height - 45),  # Bottom center
            size=(50, 35),
            color=(100, 70, 50),  # Wooden brown
            searchable=False,
            interactable=True,
            is_door=True,
            search_text="The way out.",
        )
        self.objects.append(door)

    def get_object_at(self, x: int, y: int) -> Optional[InteriorObject]:
        """Get object at screen position."""
        for obj in self.objects:
            rect = obj.get_rect()
            if rect.collidepoint(x, y):
                return obj
        return None

    def get_nearby_object(self, x: int, y: int, radius: int = 50) -> Optional[InteriorObject]:
        """Get nearest interactable object within radius."""
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
        """Get the exit door object."""
        for obj in self.objects:
            if obj.is_door:
                return obj
        return None

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

        # Build message
        if horror_stage in ("late", "finale") and obj.horror_text:
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
        Draw the interior.

        Args:
            screen: Surface to draw on
            offset_x, offset_y: Position offset for centering
            player_pos: Player position for highlighting nearby objects
        """
        # Draw floor
        floor_rect = pygame.Rect(offset_x, offset_y, self.width, self.height)
        pygame.draw.rect(screen, self.floor_color, floor_rect)

        # Draw walls (border)
        pygame.draw.rect(screen, self.wall_color, floor_rect, 8)

        # Draw objects
        for obj in self.objects:
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

            # Draw object name
            font = pygame.font.Font(None, 18)
            name_surf = font.render(obj.name, True, (180, 180, 190))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 2
            screen.blit(name_surf, (name_x, name_y))

            # Draw interaction hint if highlighted
            if highlight:
                if obj.is_door:
                    hint_text = "[E] Exit"
                elif obj.searched:
                    continue  # No hint for already searched objects
                else:
                    hint_text = "[E] Search"
                hint_surf = font.render(hint_text, True, (255, 255, 100))
                hint_x = rect.centerx - hint_surf.get_width() // 2
                hint_y = rect.top - 18
                screen.blit(hint_surf, (hint_x, hint_y))

    def reset(self):
        """Reset all objects to unsearched state (for testing)."""
        for obj in self.objects:
            obj.searched = False


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

    def clear(self):
        """Clear all cached interiors."""
        self._interiors.clear()
