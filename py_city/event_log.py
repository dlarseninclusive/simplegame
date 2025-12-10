"""
Event Log System for py_city.

Tracks and displays game events including:
- NPC dialogue
- Narrator lines
- Quest updates
- Discoveries
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import time


class EventType(Enum):
    """Types of events that can be logged."""
    NARRATOR = "narrator"
    NPC_DIALOGUE = "npc"
    QUEST = "quest"
    DISCOVERY = "discovery"
    SYSTEM = "system"


@dataclass
class LogEntry:
    """A single event log entry."""
    event_type: EventType
    text: str
    timestamp: float  # Game time or real time
    speaker: str = ""  # NPC name for dialogue, empty for narrator
    location: str = ""  # Optional location info

    def get_prefix(self) -> str:
        """Get display prefix based on event type."""
        if self.event_type == EventType.NARRATOR:
            return "[Guide]"
        elif self.event_type == EventType.NPC_DIALOGUE:
            return f"[{self.speaker}]" if self.speaker else "[NPC]"
        elif self.event_type == EventType.QUEST:
            return "[Quest]"
        elif self.event_type == EventType.DISCOVERY:
            return "[Found]"
        else:
            return "[...]"

    def get_color(self) -> tuple[int, int, int]:
        """Get display color based on event type."""
        if self.event_type == EventType.NARRATOR:
            return (180, 160, 120)  # Gold/amber for narrator
        elif self.event_type == EventType.NPC_DIALOGUE:
            return (120, 180, 220)  # Light blue for NPCs
        elif self.event_type == EventType.QUEST:
            return (100, 200, 100)  # Green for quests
        elif self.event_type == EventType.DISCOVERY:
            return (200, 150, 255)  # Purple for discoveries
        else:
            return (150, 150, 160)  # Gray for system


class EventLog:
    """
    Manages a log of game events.

    Stores recent dialogue, narrator lines, and other events
    for display in the Tab menu.
    """

    def __init__(self, max_entries: int = 100):
        self.entries: list[LogEntry] = []
        self.max_entries = max_entries
        self._start_time = time.time()

    def _get_game_time(self) -> float:
        """Get elapsed time since log started."""
        return time.time() - self._start_time

    def add(self, event_type: EventType, text: str,
            speaker: str = "", location: str = ""):
        """Add a new log entry."""
        entry = LogEntry(
            event_type=event_type,
            text=text,
            timestamp=self._get_game_time(),
            speaker=speaker,
            location=location,
        )
        self.entries.append(entry)

        # Trim old entries if needed
        while len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def log_narrator(self, text: str):
        """Log a narrator/guide line."""
        self.add(EventType.NARRATOR, text)

    def log_npc_dialogue(self, npc_name: str, text: str):
        """Log NPC dialogue."""
        self.add(EventType.NPC_DIALOGUE, text, speaker=npc_name)

    def log_quest(self, text: str):
        """Log a quest update."""
        self.add(EventType.QUEST, text)

    def log_discovery(self, text: str, location: str = ""):
        """Log a discovery (item found, anomaly, etc)."""
        self.add(EventType.DISCOVERY, text, location=location)

    def log_system(self, text: str):
        """Log a system message."""
        self.add(EventType.SYSTEM, text)

    def get_recent(self, count: int = 20) -> list[LogEntry]:
        """Get the most recent entries."""
        return self.entries[-count:] if self.entries else []

    def get_by_type(self, event_type: EventType) -> list[LogEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.event_type == event_type]

    def get_narrator_lines(self) -> list[LogEntry]:
        """Get all narrator lines."""
        return self.get_by_type(EventType.NARRATOR)

    def get_npc_dialogues(self) -> list[LogEntry]:
        """Get all NPC dialogues."""
        return self.get_by_type(EventType.NPC_DIALOGUE)

    def clear(self):
        """Clear all log entries."""
        self.entries.clear()

    def count(self) -> int:
        """Get total entry count."""
        return len(self.entries)


# Global event log instance
_event_log: Optional[EventLog] = None


def get_event_log() -> EventLog:
    """Get the global event log instance."""
    global _event_log
    if _event_log is None:
        _event_log = EventLog()
    return _event_log


def reset_event_log():
    """Reset the global event log."""
    global _event_log
    _event_log = EventLog()
