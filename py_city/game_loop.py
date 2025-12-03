"""
Py City Game Loop Manager

Manages the tutorial progression, crime simulation, anomaly discovery,
and narrator commentary that deteriorates over time.

Phases:
1. Tutorial - Learn controls with increasingly strange instructions
2. Living City - Observe/participate in crime simulation
3. Something Wrong - Discover anomalies in the city
4. Exit - Find the way out
"""

import random
import math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import deque


class NarratorQueue:
    """
    Manages narrator line timing to prevent overlapping speech.

    Lines are queued and only spoken when enough time has passed
    since the last line. Priority lines (like discoveries) can
    skip the queue.
    """

    def __init__(self, min_gap: float = 6.0, max_queue: int = 3):
        """
        Args:
            min_gap: Minimum seconds between narrator lines
            max_queue: Maximum queued lines (oldest dropped if exceeded)
        """
        self.min_gap = min_gap
        self.max_queue = max_queue
        self.last_speak_time: float = -10.0  # Allow immediate first line
        self.queue: deque[tuple[str, bool]] = deque()  # (line, is_priority)
        self.current_time: float = 0.0

    def update(self, dt: float) -> Optional[str]:
        """
        Update timer and return a line to speak if ready.

        Returns:
            Line to speak, or None if not ready/no lines queued
        """
        self.current_time += dt

        # Check if we can speak
        if self.current_time - self.last_speak_time < self.min_gap:
            return None

        # Get next line from queue
        if self.queue:
            line, _ = self.queue.popleft()
            self.last_speak_time = self.current_time
            return line

        return None

    def queue_line(self, line: str, priority: bool = False):
        """
        Queue a line to be spoken.

        Args:
            line: The text to speak
            priority: If True, insert at front of queue
        """
        if priority:
            self.queue.appendleft((line, True))
        else:
            self.queue.append((line, False))

        # Trim queue if too long (drop oldest non-priority)
        while len(self.queue) > self.max_queue:
            # Find first non-priority to remove
            for i, (_, is_prio) in enumerate(self.queue):
                if not is_prio:
                    del self.queue[i]
                    break
            else:
                # All priority, remove oldest
                self.queue.popleft()

    def queue_if_empty(self, line: str):
        """Queue a line only if the queue is empty (for ambient comments)."""
        if not self.queue:
            self.queue_line(line, priority=False)

    def clear(self):
        """Clear all queued lines."""
        self.queue.clear()

    def can_speak_now(self) -> bool:
        """Check if enough time has passed to speak immediately."""
        return self.current_time - self.last_speak_time >= self.min_gap

    def force_speak(self, line: str):
        """
        Speak immediately, resetting the timer.
        Use sparingly for critical lines.
        """
        self.last_speak_time = self.current_time
        return line


class GamePhase(Enum):
    """Current phase of the Py City experience."""
    TUTORIAL = auto()
    LIVING_CITY = auto()
    SOMETHING_WRONG = auto()
    EXIT_SEARCH = auto()
    COMPLETED = auto()


class TutorialStep(Enum):
    """Individual tutorial steps."""
    WELCOME = auto()
    MOVE = auto()
    MOVE_MORE = auto()
    FIND_NPC = auto()
    TALK = auto()
    ALIGNMENT_INTRO = auto()
    ALIGNMENT_CHOICE = auto()
    MUTE_HINT = auto()
    TUTORIAL_END = auto()


@dataclass
class TutorialInstruction:
    """A single tutorial instruction."""
    step: TutorialStep
    text: str
    wait_for: Optional[str] = None  # What player action to wait for (None = time-based)
    delay_after: float = 2.0  # Seconds after condition met before next instruction
    is_creepy: bool = False  # Marks deteriorating instructions


# Tutorial instruction sequence - player-paced
TUTORIAL_SEQUENCE = [
    TutorialInstruction(
        TutorialStep.WELCOME,
        "Welcome to the city. I'll be your guide. Press I if you need help with controls.",
        wait_for=None,  # Just wait for delay
        delay_after=5.0
    ),
    TutorialInstruction(
        TutorialStep.MOVE,
        "Use the arrow keys to move. Or right-click to walk somewhere.",
        wait_for="move",  # Wait for player to move
        delay_after=2.0
    ),
    TutorialInstruction(
        TutorialStep.MOVE_MORE,
        "Good. The city stretches in all directions. It... loops back on itself.",
        wait_for=None,
        delay_after=5.0
    ),
    TutorialInstruction(
        TutorialStep.FIND_NPC,
        "Find someone to talk to. Press E near them to interact.",
        wait_for="talk",  # Wait for player to talk to NPC
        delay_after=2.0,
        is_creepy=True
    ),
    TutorialInstruction(
        TutorialStep.ALIGNMENT_INTRO,
        "You can choose who you want to be here. Hero or villain. The city watches.",
        wait_for=None,
        delay_after=4.0
    ),
    TutorialInstruction(
        TutorialStep.ALIGNMENT_CHOICE,
        "Press G for good. N for neutral. Or... let your actions decide.",
        wait_for="align",  # Wait for player to choose alignment
        delay_after=3.0,
        is_creepy=True
    ),
    TutorialInstruction(
        TutorialStep.MUTE_HINT,
        "Press M if my voice... bothers you. Tab shows your status. Space to... defend yourself.",
        wait_for=None,
        delay_after=4.0
    ),
    TutorialInstruction(
        TutorialStep.TUTORIAL_END,
        "You've learned enough. Now... observe the city. Watch for crimes. Or commit them.",
        wait_for=None,
        delay_after=4.0
    ),
]


@dataclass
class Anomaly:
    """An anomaly/glitch in the city."""
    id: str
    name: str
    description: str
    x: float
    y: float
    radius: float = 50.0
    discovered: bool = False
    discovery_text: str = ""
    narrator_reaction: str = ""
    hidden: bool = False  # Hidden until previous anomaly discovered
    visual_type: str = "pulse"  # Visual effect type for distinctiveness


@dataclass
class Crime:
    """An active crime in progress."""
    criminal_id: int
    victim_id: Optional[int] = None
    crime_type: str = "mugging"  # mugging, burglary
    in_progress: bool = True
    being_chased: bool = False
    chase_timer: float = 0.0
    x: float = 0.0
    y: float = 0.0


class CrimeSimulation:
    """Manages crime events in the city."""

    def __init__(self, world_width: int, world_height: int):
        self.world_width = world_width
        self.world_height = world_height
        self.active_crimes: list[Crime] = []
        self.crime_cooldown: float = 0.0
        self.min_cooldown: float = 12.0  # Faster crimes by default
        self.max_cooldown: float = 25.0
        self.is_night: bool = False  # Night mode for crime bonus

        # Stats
        self.total_muggings: int = 0
        self.total_burglaries: int = 0
        self.criminals_caught: int = 0
        self.criminals_escaped: int = 0

        # Callbacks
        self.on_crime_start: Optional[Callable] = None
        self.on_crime_end: Optional[Callable] = None
        self.on_chase_start: Optional[Callable] = None
        self.on_arrest: Optional[Callable] = None

    def set_night_mode(self, is_night: bool):
        """Set night mode - crimes happen more often and are harder to catch."""
        self.is_night = is_night

    def update(self, dt: float, criminals: list, police: list,
               civilians: list, player_x: float, player_y: float) -> list[str]:
        """
        Update crime simulation.

        Returns list of event strings for narrator.
        """
        events = []

        # Night bonus: crimes happen faster at night
        cooldown_reduction = dt * 1.5 if self.is_night else dt
        self.crime_cooldown -= cooldown_reduction

        # Try to start new crime (more max crimes at night)
        max_concurrent = 5 if self.is_night else 3
        if self.crime_cooldown <= 0 and len(self.active_crimes) < max_concurrent:
            event = self._try_start_crime(criminals, civilians)
            if event:
                events.append(event)

        # Update active crimes
        for crime in self.active_crimes[:]:  # Copy list for safe removal
            event = self._update_crime(dt, crime, criminals, police,
                                       player_x, player_y)
            if event:
                events.append(event)

        return events

    def _try_start_crime(self, criminals: list, civilians: list) -> Optional[str]:
        """Try to start a new crime."""
        # Find available criminal (not in jail, not already committing crime)
        available_criminals = [
            c for c in criminals
            if not c.in_jail and not c.committed_crime and not c.in_building
        ]

        if not available_criminals:
            return None

        criminal = random.choice(available_criminals)

        # Decide crime type
        crime_type = random.choice(["mugging", "mugging", "burglary"])  # Mugging more common

        if crime_type == "mugging":
            # Find nearby civilian
            nearby_civilians = [
                civ for civ in civilians
                if not civ.in_jail and not civ.in_building
                and self._distance(criminal.x, criminal.y, civ.x, civ.y) < 200
            ]

            if nearby_civilians:
                victim = random.choice(nearby_civilians)
                crime = Crime(
                    criminal_id=id(criminal),
                    victim_id=id(victim),
                    crime_type="mugging",
                    x=criminal.x,
                    y=criminal.y
                )
                self.active_crimes.append(crime)
                criminal.committed_crime = True
                self.total_muggings += 1
                self.crime_cooldown = random.uniform(self.min_cooldown, self.max_cooldown)

                if self.on_crime_start:
                    self.on_crime_start(crime)

                return "mugging_started"

        elif crime_type == "burglary":
            # Criminal enters a building
            crime = Crime(
                criminal_id=id(criminal),
                crime_type="burglary",
                x=criminal.x,
                y=criminal.y
            )
            self.active_crimes.append(crime)
            criminal.committed_crime = True
            criminal.breaking_in = True
            self.total_burglaries += 1
            self.crime_cooldown = random.uniform(self.min_cooldown, self.max_cooldown)

            if self.on_crime_start:
                self.on_crime_start(crime)

            return "burglary_started"

        return None

    def _update_crime(self, dt: float, crime: Crime, criminals: list,
                      police: list, player_x: float, player_y: float) -> Optional[str]:
        """Update a single crime."""
        # Find the criminal
        criminal = None
        for c in criminals:
            if id(c) == crime.criminal_id:
                criminal = c
                break

        if not criminal:
            self.active_crimes.remove(crime)
            return None

        # Update crime position
        crime.x = criminal.x
        crime.y = criminal.y

        if crime.being_chased:
            crime.chase_timer += dt

            # Check if police caught criminal
            for cop in police:
                if self._distance(cop.x, cop.y, criminal.x, criminal.y) < 40:
                    # Arrested!
                    criminal.in_jail = True
                    criminal.committed_crime = False
                    criminal.breaking_in = False
                    self.criminals_caught += 1
                    self.active_crimes.remove(crime)

                    if self.on_arrest:
                        self.on_arrest(crime, criminal)

                    if self.on_crime_end:
                        self.on_crime_end(crime, "arrested")

                    return "criminal_arrested"

            # Criminal escapes after long chase
            if crime.chase_timer > 20.0:
                criminal.committed_crime = False
                criminal.breaking_in = False
                self.criminals_escaped += 1
                self.active_crimes.remove(crime)

                if self.on_crime_end:
                    self.on_crime_end(crime, "escaped")

                return "criminal_escaped"

        else:
            # Crime in progress - check if police notice
            for cop in police:
                if self._distance(cop.x, cop.y, criminal.x, criminal.y) < 150:
                    crime.being_chased = True

                    if self.on_chase_start:
                        self.on_chase_start(crime)

                    return "chase_started"

            # Crime auto-completes after some time if not caught
            crime.chase_timer += dt
            if crime.chase_timer > 8.0 and not crime.being_chased:
                criminal.committed_crime = False
                criminal.breaking_in = False
                self.active_crimes.remove(crime)

                if self.on_crime_end:
                    self.on_crime_end(crime, "completed")

                return "crime_completed"

        return None

    def _distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate distance between two points."""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def player_intervene(self, player_x: float, player_y: float,
                         help_police: bool) -> Optional[Crime]:
        """
        Player intervenes in nearby crime.

        Returns the crime if intervention was successful.
        """
        for crime in self.active_crimes:
            if self._distance(player_x, player_y, crime.x, crime.y) < 100:
                if help_police:
                    # Help police - start chase immediately
                    crime.being_chased = True
                    return crime
                else:
                    # Help criminal - let them escape
                    self.active_crimes.remove(crime)
                    self.criminals_escaped += 1
                    return crime
        return None


@dataclass
class GameState:
    """Complete game state for Py City."""
    phase: GamePhase = GamePhase.TUTORIAL
    phase_timer: float = 0.0

    # Tutorial state
    tutorial_index: int = 0
    tutorial_timer: float = 0.0
    tutorial_waiting_for: Optional[str] = None  # What action we're waiting for
    tutorial_spoke_current: bool = False  # Have we spoken the current instruction?
    player_has_moved: bool = False
    player_has_talked: bool = False
    player_has_aligned: bool = False

    # Living city state
    crimes: list = field(default_factory=list)
    crime_cooldown: float = 0.0
    player_interventions: int = 0

    # Anomaly state
    anomalies: list = field(default_factory=list)
    anomalies_discovered: int = 0
    anomalies_required: int = 5

    # Exit state
    exit_x: float = 0.0
    exit_y: float = 0.0
    exit_spawned: bool = False

    # Narrator state
    narrator_sanity: float = 1.0  # Decreases as game progresses
    last_narrator_time: float = 0.0
    narrator_cooldown: float = 25.0  # Seconds between ambient comments (was 8, now slower)


class GameLoopManager:
    """Manages the Py City game loop and progression."""

    def __init__(self, world_width: int, world_height: int,
                 guide=None, overlay=None, narrator_queue: NarratorQueue = None):
        self.world_width = world_width
        self.world_height = world_height
        self.guide = guide
        self.overlay = overlay
        self.state = GameState()

        # Narrator queue to prevent overlapping speech (use provided or create new)
        self.narrator = narrator_queue or NarratorQueue(min_gap=5.0, max_queue=4)

        # Callbacks
        self.on_phase_change: Optional[Callable] = None
        self.on_instruction: Optional[Callable] = None
        self.on_anomaly_discovered: Optional[Callable] = None
        self.on_crime_started: Optional[Callable] = None
        self.on_exit_ready: Optional[Callable] = None

        # Generate anomalies
        self._generate_anomalies()

    def _queue_narrator(self, line: str, priority: bool = False):
        """Queue a line to the narrator (respects mute and pacing)."""
        if self.overlay and self.overlay.audio.muted:
            return
        self.narrator.queue_line(line, priority)

    def _generate_anomalies(self):
        """Generate anomaly locations throughout the city."""
        anomaly_templates = [
            Anomaly(
                id="staring_npc",
                name="The Watcher",
                description="An NPC that stands perfectly still, staring at nothing.",
                x=0, y=0,
                discovery_text="They haven't moved. Not once. Their eyes follow you.",
                narrator_reaction="They're just resting. Move along.",
                visual_type="pulse_purple"
            ),
            Anomaly(
                id="no_door_building",
                name="The Sealed Building",
                description="A building with no entrance. How do people get in?",
                x=0, y=0,
                discovery_text="There's no door. There was never a door.",
                narrator_reaction="Not all buildings need doors. Don't ask why.",
                visual_type="pulse_red"
            ),
            Anomaly(
                id="repeating_npc",
                name="The Loop",
                description="An NPC repeating the same phrase over and over.",
                x=0, y=0,
                discovery_text="'Nice weather.' 'Nice weather.' 'Nice weather.'",
                narrator_reaction="They like talking about weather. It's... normal.",
                visual_type="pulse_green"
            ),
            Anomaly(
                id="dead_end_road",
                name="The Nowhere Road",
                description="A road that leads to nothing. Just... stops.",
                x=0, y=0,
                discovery_text="The road ends. Beyond it, there's nothing to render.",
                narrator_reaction="Construction zone. Don't look too closely.",
                visual_type="pulse_cyan"
            ),
            Anomaly(
                id="knowing_npc",
                name="The One Who Knows",
                description="An NPC who knows your name. You never told them.",
                x=0, y=0,
                discovery_text="'I've been waiting for you, player.'",
                narrator_reaction="Lucky guess. Names are... guessable.",
                visual_type="pulse_yellow"
            ),
            Anomaly(
                id="flickering_lamp",
                name="The Broken Light",
                description="A streetlamp that flickers in a pattern. SOS?",
                x=0, y=0,
                discovery_text="The light blinks: ... --- ... Help?",
                narrator_reaction="Electrical fault. Ignore it.",
                visual_type="flicker_white"
            ),
            Anomaly(
                id="shadow_figure",
                name="The Shadow",
                description="Something in the corner of your vision. Gone when you look.",
                x=0, y=0,
                discovery_text="You saw it. It saw you. Now it's gone.",
                narrator_reaction="Your eyes are tired. Rest them. Close them.",
                visual_type="fade_black"
            ),
        ]

        # Place anomalies on sidewalks (not in buildings)
        # Use 6 anomalies, need 5 to progress
        # Only spawn first anomaly initially, rest spawn on discovery
        margin = 200
        for i, anomaly in enumerate(anomaly_templates[:6]):
            # Find valid sidewalk position (not in building)
            max_attempts = 50
            for _ in range(max_attempts):
                x = random.randint(margin, self.world_width - margin)
                y = random.randint(margin, self.world_height - margin)

                # Check if position is on a road/sidewalk (not in a building block)
                # Buildings are on a grid - roads are the gaps
                block_size = 200  # Approximate block + road size
                road_width = 40
                x_in_grid = x % block_size
                y_in_grid = y % block_size

                # If x or y coordinate is in the road area (first 40px of each grid cell)
                if x_in_grid < road_width or y_in_grid < road_width:
                    anomaly.x = x
                    anomaly.y = y
                    break
            else:
                # Fallback if no valid position found
                anomaly.x = random.randint(margin, self.world_width - margin)
                anomaly.y = random.randint(margin, self.world_height - margin)

            # Only first anomaly is initially active, rest hidden until previous discovered
            if i > 0:
                anomaly.hidden = True
            else:
                anomaly.hidden = False

            self.state.anomalies.append(anomaly)

    def start(self):
        """Start the game loop."""
        self.state.phase = GamePhase.TUTORIAL
        self.state.tutorial_timer = 2.0  # Initial delay before first instruction

        # Welcome message
        self._queue_narrator("Welcome to the city.", priority=True)

    def update(self, dt: float, player_x: float, player_y: float,
               player_moving: bool = False):
        """Update game state each frame."""
        self.state.phase_timer += dt

        if self.state.phase == GamePhase.TUTORIAL:
            self._update_tutorial(dt, player_moving)
        elif self.state.phase == GamePhase.LIVING_CITY:
            self._update_living_city(dt, player_x, player_y)
        elif self.state.phase == GamePhase.SOMETHING_WRONG:
            self._update_anomalies(dt, player_x, player_y)
        elif self.state.phase == GamePhase.EXIT_SEARCH:
            self._update_exit(dt, player_x, player_y)

        # Decrease narrator sanity over time
        self.state.narrator_sanity = max(0.1,
            self.state.narrator_sanity - dt * 0.005)

    def _update_tutorial(self, dt: float, player_moving: bool):
        """Update tutorial phase - player-paced progression."""
        if player_moving:
            self.state.player_has_moved = True

        # Check if tutorial is complete
        if self.state.tutorial_index >= len(TUTORIAL_SEQUENCE):
            self._transition_to_phase(GamePhase.LIVING_CITY)
            return

        instruction = TUTORIAL_SEQUENCE[self.state.tutorial_index]

        # If we haven't spoken this instruction yet, speak it
        if not self.state.tutorial_spoke_current:
            self._queue_narrator(instruction.text)
            self.state.tutorial_spoke_current = True
            self.state.tutorial_waiting_for = instruction.wait_for
            self.state.tutorial_timer = instruction.delay_after if not instruction.wait_for else 0
            if self.on_instruction:
                self.on_instruction(instruction)
            return

        # If waiting for a player action, check if completed
        if self.state.tutorial_waiting_for:
            action_done = False
            if self.state.tutorial_waiting_for == "move" and self.state.player_has_moved:
                action_done = True
            elif self.state.tutorial_waiting_for == "talk" and self.state.player_has_talked:
                action_done = True
            elif self.state.tutorial_waiting_for == "align" and self.state.player_has_aligned:
                action_done = True

            if action_done:
                # Action completed, start delay timer
                self.state.tutorial_waiting_for = None
                self.state.tutorial_timer = instruction.delay_after
            return  # Still waiting or just started timer

        # Count down timer for time-based progression
        if self.state.tutorial_timer > 0:
            self.state.tutorial_timer -= dt
            return

        # Timer done, advance to next instruction
        self.state.tutorial_index += 1
        self.state.tutorial_spoke_current = False

    def _update_living_city(self, dt: float, player_x: float, player_y: float):
        """Update living city crime simulation."""
        self.state.crime_cooldown -= dt

        # Transition to anomaly phase after some time (or Tab to skip)
        if self.state.phase_timer > 90.0:  # 1.5 minutes in living city
            self._transition_to_phase(GamePhase.SOMETHING_WRONG)
            return

        # Occasional narrator comments (max 3 total during this phase)
        if not hasattr(self.state, '_living_comments_made'):
            self.state._living_comments_made = 0

        self.state.last_narrator_time += dt
        if (self.state.last_narrator_time > self.state.narrator_cooldown and
                self.state._living_comments_made < 3):
            self.state.last_narrator_time = 0
            self.state._living_comments_made += 1
            self._living_city_comment()

    def _update_anomalies(self, dt: float, player_x: float, player_y: float):
        """Check for anomaly discovery."""
        for anomaly in self.state.anomalies:
            if anomaly.discovered:
                continue

            # Check if player is near anomaly
            dx = anomaly.x - player_x
            dy = anomaly.y - player_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < anomaly.radius:
                self._discover_anomaly(anomaly)

        # Check if enough anomalies discovered
        if self.state.anomalies_discovered >= self.state.anomalies_required:
            self._transition_to_phase(GamePhase.EXIT_SEARCH)

    def _update_exit(self, dt: float, player_x: float, player_y: float):
        """Update exit search phase."""
        if not self.state.exit_spawned:
            # Spawn exit at edge of world
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top':
                self.state.exit_x = self.world_width // 2
                self.state.exit_y = 50
            elif edge == 'bottom':
                self.state.exit_x = self.world_width // 2
                self.state.exit_y = self.world_height - 50
            elif edge == 'left':
                self.state.exit_x = 50
                self.state.exit_y = self.world_height // 2
            else:
                self.state.exit_x = self.world_width - 50
                self.state.exit_y = self.world_height // 2

            self.state.exit_spawned = True

            self._queue_narrator(
                "You've seen too much. The exit is... somewhere. Find it.",
                priority=True
            )

            if self.on_exit_ready:
                self.on_exit_ready(self.state.exit_x, self.state.exit_y)

        # Check if player reached exit
        dx = self.state.exit_x - player_x
        dy = self.state.exit_y - player_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 60:
            self._transition_to_phase(GamePhase.COMPLETED)

    def _transition_to_phase(self, new_phase: GamePhase):
        """Transition to a new game phase."""
        old_phase = self.state.phase
        self.state.phase = new_phase
        self.state.phase_timer = 0.0

        if self.on_phase_change:
            self.on_phase_change(old_phase, new_phase)

        # Phase transition messages (priority since phase changes are important)
        if new_phase == GamePhase.LIVING_CITY:
            self._queue_narrator(
                "The tutorial is over. Now watch. Learn how this city breathes.",
                priority=True
            )
        elif new_phase == GamePhase.SOMETHING_WRONG:
            self._queue_narrator(
                "Something feels different now, doesn't it? Look closer.",
                priority=True
            )
        elif new_phase == GamePhase.COMPLETED:
            self._queue_narrator(
                "You found the exit. But this is just the beginning.",
                priority=True
            )

    def _discover_anomaly(self, anomaly: Anomaly):
        """Handle anomaly discovery."""
        anomaly.discovered = True
        self.state.anomalies_discovered += 1

        # Show discovery text (priority since discoveries are important)
        self._queue_narrator(anomaly.discovery_text, priority=True)

        if self.on_anomaly_discovered:
            self.on_anomaly_discovered(anomaly)

        # Narrator reaction (delayed)
        # This would be handled by a timer in the main loop

    def _living_city_comment(self):
        """Random narrator comment during living city phase."""
        if not self.guide or not self.overlay or self.overlay.audio.muted:
            return

        comments = [
            "The citizens go about their routines. Day after day.",
            "Crime never sleeps in this city. Neither do I.",
            "Watch them. Learn their patterns. They never change.",
            "Some call this city home. Others call it a prison.",
            "The police try their best. It's never enough.",
            "Everyone here has a story. Most of them end badly.",
        ]

        # Add creepier comments as sanity decreases
        if self.state.narrator_sanity < 0.7:
            comments.extend([
                "Have you noticed how they walk? Always the same paths.",
                "They don't see you watching. But I do.",
                "This city was here before you. It will be here after.",
            ])

        if self.state.narrator_sanity < 0.4:
            comments.extend([
                "They're not real. You know that, right?",
                "I've watched so many players come through here.",
                "Don't get attached. They reset when you leave.",
            ])

        # Use queue_if_empty for ambient comments (don't interrupt important messages)
        self.narrator.queue_if_empty(random.choice(comments))

    # --- Event handlers called from main game ---

    def on_player_talked(self, npc_type: str):
        """Called when player talks to an NPC."""
        self.state.player_has_talked = True

        if self.state.phase == GamePhase.TUTORIAL:
            responses = [
                "Good. Communication is important here.",
                "They have things to say. Listen carefully.",
                "Everyone knows something. Whether they'll share it...",
            ]
            self._queue_narrator(random.choice(responses))

    def on_player_aligned(self, alignment: str):
        """Called when player chooses alignment."""
        self.state.player_has_aligned = True

        if alignment == "good":
            self._queue_narrator(
                "Good. A noble choice. We'll see how long it lasts."
            )
        else:
            self._queue_narrator(
                "Evil. How... predictable. The city shapes us all."
            )

    def on_player_attacked(self, npc_type: str, fatal: bool = False):
        """Called when player attacks an NPC."""
        # Track attacks for horror progression
        if not hasattr(self.state, 'attacks'):
            self.state.attacks = 0
        self.state.attacks += 1

        if fatal:
            if not hasattr(self.state, 'kills'):
                self.state.kills = 0
            self.state.kills += 1

    def on_player_intervention(self, helped_police: bool):
        """Called when player intervenes in a crime."""
        self.state.player_interventions += 1

        if helped_police:
            comments = [
                "Justice served. For now.",
                "The law wins this time.",
                "A hero. How... refreshing.",
            ]
        else:
            comments = [
                "You let them go. Interesting choice.",
                "The criminal escapes. Was that mercy or apathy?",
                "Rules are suggestions to you, aren't they?",
            ]
        self._queue_narrator(random.choice(comments))

    def get_current_objective(self) -> str:
        """Get current objective text for UI."""
        if self.state.phase == GamePhase.TUTORIAL:
            if self.state.tutorial_index < len(TUTORIAL_SEQUENCE):
                return "Follow the Guide's instructions"
            return "Tutorial complete"
        elif self.state.phase == GamePhase.LIVING_CITY:
            return "Observe the city"
        elif self.state.phase == GamePhase.SOMETHING_WRONG:
            found = self.state.anomalies_discovered
            needed = self.state.anomalies_required
            return f"Find anomalies ({found}/{needed})"
        elif self.state.phase == GamePhase.EXIT_SEARCH:
            return "Find the exit"
        elif self.state.phase == GamePhase.COMPLETED:
            return "Level complete"
        return ""

    def is_complete(self) -> bool:
        """Check if the level is complete."""
        return self.state.phase == GamePhase.COMPLETED
