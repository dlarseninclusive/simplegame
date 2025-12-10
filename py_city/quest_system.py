"""
Quest System for py_city.

Provides objectives that guide player through the game phases:
- TUTORIAL: Learn controls
- LIVING_CITY: Explore and build relationships
- SOMETHING_WRONG: Investigate anomalies
- EXIT_SEARCH: Find the way out

Quests plant horror seeds via completion hints and NPC dialogue.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable
import random


class QuestType(Enum):
    """Categories of quests."""
    TUTORIAL = auto()       # Learn game mechanics
    EXPLORATION = auto()    # Find locations
    SOCIAL = auto()         # Talk to NPCs
    INVESTIGATION = auto()  # Discover secrets
    MORAL = auto()          # Make choices
    CRIME_NOIR = auto()     # Late-game noir quests


class QuestStatus(Enum):
    """Quest completion status."""
    LOCKED = auto()         # Not yet available
    AVAILABLE = auto()      # Can be started
    ACTIVE = auto()         # Currently in progress
    COMPLETED = auto()      # Finished successfully
    FAILED = auto()         # Cannot complete


@dataclass
class Quest:
    """A single quest with objectives and rewards."""
    id: str
    title: str
    description: str        # Guide narrates this when quest starts
    quest_type: QuestType

    # Objectives (one must be met to complete)
    objective: str          # Event type to track, e.g., "talk_to_count:3"
    target_count: int = 1   # How many times objective must be triggered

    # Rewards
    karma_reward: int = 0
    trust_reward: int = 0   # Given to random nearby NPC

    # Horror elements
    horror_hint: str = ""           # Narrator says this on completion
    completion_message: str = ""    # UI notification

    # Requirements
    requires_phase: str = ""        # GamePhase name, empty = any
    requires_quest: str = ""        # Quest ID that must be completed first

    # State (managed by QuestManager)
    status: QuestStatus = QuestStatus.LOCKED
    current_count: int = 0

    def check_objective(self, event_type: str, count: int = 1) -> bool:
        """
        Check if an event progresses this quest.

        Returns True if quest was completed by this event.
        """
        if self.status != QuestStatus.ACTIVE:
            return False

        # Parse objective type
        obj_type, _, obj_param = self.objective.partition(":")

        if obj_type == event_type or self.objective == event_type:
            self.current_count += count
            if self.current_count >= self.target_count:
                self.status = QuestStatus.COMPLETED
                return True

        return False

    def get_progress_text(self) -> str:
        """Get progress string like '2/3'."""
        return f"{self.current_count}/{self.target_count}"


# === TUTORIAL QUESTS ===
TUTORIAL_QUESTS = [
    Quest(
        id="tutorial_move",
        title="First Steps",
        description="Try moving around. WASD or arrow keys. Right-click to walk to a location.",
        quest_type=QuestType.TUTORIAL,
        objective="player_moved",
        target_count=20,
        completion_message="Good. You can move.",
        horror_hint="",
    ),
    Quest(
        id="tutorial_talk",
        title="Make Contact",
        description="Approach someone and press E to talk.",
        quest_type=QuestType.TUTORIAL,
        objective="npc_talked",
        target_count=1,
        requires_quest="tutorial_move",
        completion_message="Communication established.",
        horror_hint="They seem happy to see you. Almost too happy.",
    ),
]

# === LIVING CITY QUESTS ===
LIVING_CITY_QUESTS = [
    Quest(
        id="meet_neighbors",
        title="Meet the Neighbors",
        description="Why not introduce yourself to a few citizens? Talk to 3 people.",
        quest_type=QuestType.SOCIAL,
        objective="npc_talked",
        target_count=3,
        requires_phase="LIVING_CITY",
        karma_reward=10,
        trust_reward=5,
        completion_message="You're making friends.",
        horror_hint="Notice how they never blink. Or maybe you do.",
    ),
    Quest(
        id="find_hospital",
        title="Emergency Services",
        description="Every city needs a hospital. Can you find it?",
        quest_type=QuestType.EXPLORATION,
        objective="found_hospital",
        target_count=1,
        requires_phase="LIVING_CITY",
        karma_reward=5,
        completion_message="Hospital located.",
        horror_hint="The sign says 24 hours. But I've never seen anyone leave.",
    ),
    Quest(
        id="find_police_station",
        title="Law and Order",
        description="The police station should be nearby. Find it to understand how order is kept.",
        quest_type=QuestType.EXPLORATION,
        objective="found_police_station",
        target_count=1,
        requires_phase="LIVING_CITY",
        karma_reward=5,
        completion_message="Police station found.",
        horror_hint="The cells are never empty. But the criminals... where do they come from?",
    ),
    Quest(
        id="witness_crime",
        title="Dark Underbelly",
        description="This city has crime. Watch and learn how it unfolds.",
        quest_type=QuestType.INVESTIGATION,
        objective="crime_witnessed",
        target_count=1,
        requires_phase="LIVING_CITY",
        completion_message="You've seen the darkness.",
        horror_hint="The victim didn't scream. Like they expected it.",
    ),
    Quest(
        id="help_or_ignore",
        title="The Choice",
        description="You witnessed a crime. Did you help? Did you join? Your karma remembers.",
        quest_type=QuestType.MORAL,
        objective="crime_intervened",  # Either help or join triggers this
        target_count=1,
        requires_quest="witness_crime",
        completion_message="You made a choice.",
        horror_hint="Whatever you chose... the city noted it.",
    ),
    Quest(
        id="build_trust",
        title="Earning Trust",
        description="Some people take time to open up. Keep talking to the same person.",
        quest_type=QuestType.SOCIAL,
        objective="npc_trust_increased",
        target_count=3,  # 3 positive interactions with same NPC
        requires_quest="meet_neighbors",
        karma_reward=15,
        trust_reward=10,
        completion_message="Someone trusts you now.",
        horror_hint="They're starting to tell you things. Things they shouldn't know.",
    ),
    Quest(
        id="enter_building",
        title="What's Inside",
        description="Buildings hold secrets. Press E near a building to enter.",
        quest_type=QuestType.EXPLORATION,
        objective="building_entered",
        target_count=1,
        requires_phase="LIVING_CITY",
        completion_message="You're inside.",
        horror_hint="It looks different in here. Smaller than it should be.",
    ),
    Quest(
        id="find_item",
        title="Hidden Things",
        description="Search inside buildings. Press E near furniture to look.",
        quest_type=QuestType.INVESTIGATION,
        objective="item_found",
        target_count=1,
        requires_quest="enter_building",
        karma_reward=5,
        completion_message="You found something.",
        horror_hint="This item... it was waiting for you.",
    ),
]

# === SOMETHING WRONG QUESTS ===
SOMETHING_WRONG_QUESTS = [
    Quest(
        id="first_anomaly",
        title="Something's Off",
        description="You've felt it. Something wrong. Look for the signs.",
        quest_type=QuestType.INVESTIGATION,
        objective="anomaly_discovered",
        target_count=1,
        requires_phase="SOMETHING_WRONG",
        karma_reward=10,
        completion_message="Anomaly discovered.",
        horror_hint="You weren't supposed to find that.",
    ),
    Quest(
        id="gather_clues",
        title="Piecing Together",
        description="Talk to people. High trust reveals secrets. Find 3 clues.",
        quest_type=QuestType.INVESTIGATION,
        objective="clue_discovered",
        target_count=3,
        requires_quest="first_anomaly",
        karma_reward=20,
        completion_message="The picture becomes clearer.",
        horror_hint="Or does it? Each answer brings more questions.",
    ),
    Quest(
        id="the_watcher",
        title="Being Watched",
        description="Someone has been following you. Find The Watcher anomaly.",
        quest_type=QuestType.INVESTIGATION,
        objective="found_the_watcher",
        target_count=1,
        requires_quest="first_anomaly",
        karma_reward=15,
        completion_message="You found The Watcher.",
        horror_hint="He was always there. Waiting. For you specifically.",
    ),
]

# === EXIT SEARCH QUESTS ===
EXIT_SEARCH_QUESTS = [
    Quest(
        id="find_exit",
        title="The Way Out",
        description="There has to be an exit. There HAS to be.",
        quest_type=QuestType.EXPLORATION,
        objective="exit_found",
        target_count=1,
        requires_phase="EXIT_SEARCH",
        completion_message="You found it. The exit.",
        horror_hint="But exits in places like this... they're never quite what they seem.",
    ),
    Quest(
        id="final_choice",
        title="Leave or Stay",
        description="The portal awaits. Your choice. Your consequence.",
        quest_type=QuestType.MORAL,
        objective="exit_used_or_stayed",
        target_count=1,
        requires_quest="find_exit",
        completion_message="You chose.",
        horror_hint="",  # No hint - this is the end
    ),
]

# === CRIME NOIR QUESTS (unlocked via high investigation) ===
CRIME_NOIR_QUESTS = [
    Quest(
        id="noir_missing_person",
        title="The Missing Person",
        description="Someone's been asking about a person who vanished. Help them... or don't.",
        quest_type=QuestType.CRIME_NOIR,
        objective="missing_person_clue",
        target_count=3,
        requires_quest="gather_clues",
        karma_reward=25,
        completion_message="Case closed. But was it justice?",
        horror_hint="The missing person was you. In another iteration.",
    ),
    Quest(
        id="noir_corruption",
        title="Blue Shadows",
        description="The police aren't what they seem. Investigate.",
        quest_type=QuestType.CRIME_NOIR,
        objective="police_corruption_evidence",
        target_count=2,
        requires_quest="gather_clues",
        karma_reward=30,
        completion_message="The truth is ugly.",
        horror_hint="They serve something else. Something that isn't human.",
    ),
]


# Combine all quests
ALL_QUESTS = (
    TUTORIAL_QUESTS +
    LIVING_CITY_QUESTS +
    SOMETHING_WRONG_QUESTS +
    EXIT_SEARCH_QUESTS +
    CRIME_NOIR_QUESTS
)


class QuestManager:
    """
    Manages active quests, tracks progress, and delivers rewards.

    Integrates with:
    - GameLoopManager for phase-based unlocks
    - NarratorQueue for quest delivery
    - PlotStateManager for horror integration
    """

    def __init__(self):
        # Create copies of quests for this session
        self.quests = {q.id: Quest(**q.__dict__) for q in ALL_QUESTS}
        self.active_quest_id: Optional[str] = None
        self.completed_quests: list[str] = []

        # Callbacks
        self.on_quest_complete: Optional[Callable[[Quest], None]] = None
        self.on_quest_available: Optional[Callable[[Quest], None]] = None

    def update_phase(self, phase_name: str):
        """
        Update quest availability based on current game phase.

        Called when GamePhase changes.
        """
        for quest in self.quests.values():
            if quest.status == QuestStatus.LOCKED:
                # Check if phase requirement met
                if quest.requires_phase and quest.requires_phase != phase_name:
                    continue
                # Check if prerequisite quest complete
                if quest.requires_quest and quest.requires_quest not in self.completed_quests:
                    continue
                # Quest becomes available
                quest.status = QuestStatus.AVAILABLE
                if self.on_quest_available:
                    self.on_quest_available(quest)

    def start_quest(self, quest_id: str) -> Optional[Quest]:
        """
        Start a quest by ID.

        Returns the quest if started, None if not available.
        """
        quest = self.quests.get(quest_id)
        if not quest or quest.status != QuestStatus.AVAILABLE:
            return None

        quest.status = QuestStatus.ACTIVE
        self.active_quest_id = quest_id
        return quest

    def start_next_available(self) -> Optional[Quest]:
        """
        Start the next available quest.

        Returns the quest if one was started.
        """
        for quest in self.quests.values():
            if quest.status == QuestStatus.AVAILABLE:
                return self.start_quest(quest.id)
        return None

    def get_active_quest(self) -> Optional[Quest]:
        """Get the currently active quest."""
        if self.active_quest_id:
            return self.quests.get(self.active_quest_id)
        return None

    def on_event(self, event_type: str, count: int = 1) -> Optional[Quest]:
        """
        Process a game event for quest progress.

        Returns completed quest if any.
        """
        active = self.get_active_quest()
        if active and active.check_objective(event_type, count):
            # Quest completed
            self.completed_quests.append(active.id)
            self.active_quest_id = None

            # Unlock dependent quests
            for quest in self.quests.values():
                if quest.status == QuestStatus.LOCKED:
                    if quest.requires_quest == active.id:
                        quest.status = QuestStatus.AVAILABLE
                        if self.on_quest_available:
                            self.on_quest_available(quest)

            if self.on_quest_complete:
                self.on_quest_complete(active)

            return active

        return None

    def get_available_quests(self) -> list[Quest]:
        """Get all available quests."""
        return [q for q in self.quests.values() if q.status == QuestStatus.AVAILABLE]

    def get_objective_text(self) -> str:
        """Get current objective for UI display."""
        active = self.get_active_quest()
        if active:
            return f"{active.title}: {active.get_progress_text()}"
        return ""

    def save(self) -> dict:
        """Serialize for save game."""
        return {
            "completed": self.completed_quests,
            "active": self.active_quest_id,
            "progress": {
                qid: {"status": q.status.name, "count": q.current_count}
                for qid, q in self.quests.items()
                if q.status != QuestStatus.LOCKED
            }
        }

    def load(self, data: dict):
        """Load from save game."""
        self.completed_quests = data.get("completed", [])
        self.active_quest_id = data.get("active")

        for qid, progress in data.get("progress", {}).items():
            if qid in self.quests:
                self.quests[qid].status = QuestStatus[progress["status"]]
                self.quests[qid].current_count = progress["count"]


# Legacy compatibility - original simple quests
class LegacyQuest:
    """Original quest class for backwards compatibility."""
    def __init__(self, description, target_type, target_count):
        self.description = description
        self.target_type = target_type
        self.target_count = target_count
        self.current_count = 0

    def update(self, event_type):
        if event_type == self.target_type:
            self.current_count += 1
            return self.current_count >= self.target_count
        return False


# Legacy quests for old code
available_quests = [
    LegacyQuest("Catch 3 criminals", "criminal_caught", 3),
    LegacyQuest("Help 5 civilians", "civilian_helped", 5),
    LegacyQuest("Patrol the city (visit 10 buildings)", "building_visited", 10)
]
