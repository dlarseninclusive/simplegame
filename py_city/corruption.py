"""
Corruption Manager for Py City
==============================

Introduces entropy-based "wrongness" into the game loop as horror progresses.
The corruption should feel emergent - like the game itself is decaying.

Entropy Levels by Phase:
- TUTORIAL: 0.0 (pristine, teaching the player)
- LIVING_CITY: 0.05 (barely perceptible micro-glitches)
- SOMETHING_WRONG: 0.3 (noticeable but deniable)
- EXIT_SEARCH: 0.6 (reality breaking down)
- COMPLETED: 0.8 (full corruption, escape imminent)
"""

import random
import math
import pygame


class CorruptionManager:
    """Manages entropy-based corruption effects across the game loop."""

    # Phase-to-entropy mapping
    PHASE_ENTROPY = {
        "TUTORIAL": 0.0,
        "LIVING_CITY": 0.05,
        "SOMETHING_WRONG": 0.3,
        "EXIT_SEARCH": 0.6,
        "COMPLETED": 0.8,
    }

    def __init__(self):
        self.entropy = 0.0
        self.target_entropy = 0.0

        # Time dilation state
        self._time_warp_active = False
        self._time_warp_factor = 1.0
        self._time_warp_duration = 0.0
        self._time_warp_cooldown = 0.0

        # Input hesitation state
        self._input_lag_buffer = []  # Delayed inputs
        self._input_lag_timer = 0.0
        self._movement_drift = (0.0, 0.0)  # Accumulated drift

        # Visual corruption state
        self._skip_clear_next_frame = False
        self._glitch_rects = []  # Active visual glitches
        self._building_flicker_id = None
        self._building_flicker_timer = 0.0

        # Wraparound distortion
        self._wrap_offset = (0, 0)  # Offset applied to wraparound

        # Tracking for narrator triggers
        self.blocked_escapes = 0
        self.time_warps_triggered = 0
        self.visual_glitches_shown = 0

    def update_entropy(self, phase_name: str):
        """Set target entropy based on current game phase."""
        self.target_entropy = self.PHASE_ENTROPY.get(phase_name, 0.0)

        # Smooth transition to target entropy
        diff = self.target_entropy - self.entropy
        self.entropy += diff * 0.01  # Gradual shift

    def update(self, dt: float):
        """Update corruption systems each frame."""
        # Update time warp
        if self._time_warp_active:
            self._time_warp_duration -= dt
            if self._time_warp_duration <= 0:
                self._time_warp_active = False
                self._time_warp_factor = 1.0

        # Cooldown for time warp
        if self._time_warp_cooldown > 0:
            self._time_warp_cooldown -= dt

        # Random chance to trigger time warp (at sufficient entropy)
        if (self.entropy > 0.2 and
            not self._time_warp_active and
            self._time_warp_cooldown <= 0):
            if random.random() < self.entropy * 0.005:  # ~0.15% at 0.3 entropy
                self._trigger_time_warp()

        # Update input lag timer
        if self._input_lag_timer > 0:
            self._input_lag_timer -= dt

        # Decay movement drift
        dx, dy = self._movement_drift
        self._movement_drift = (dx * 0.95, dy * 0.95)

        # Update glitch rects (fade out)
        self._glitch_rects = [
            (rect, alpha - dt * 500, color)
            for rect, alpha, color in self._glitch_rects
            if alpha > 0
        ]

        # Building flicker timer
        if self._building_flicker_timer > 0:
            self._building_flicker_timer -= dt
            if self._building_flicker_timer <= 0:
                self._building_flicker_id = None

        # Random chance to skip next frame clear (afterimage effect)
        if self.entropy > 0.25:
            if random.random() < self.entropy * 0.008:  # ~0.24% at 0.3 entropy
                self._skip_clear_next_frame = True

        # Random visual glitch
        if self.entropy > 0.15:
            if random.random() < self.entropy * 0.01:
                self._spawn_glitch_rect()

    def _trigger_time_warp(self):
        """Trigger a brief time dilation effect."""
        self._time_warp_active = True
        self._time_warp_cooldown = 5.0 + random.random() * 10.0  # 5-15 second cooldown

        # At lower entropy: subtle (0.85-1.15)
        # At higher entropy: dramatic (0.5-1.5)
        if self.entropy < 0.4:
            self._time_warp_factor = random.uniform(0.85, 1.15)
            self._time_warp_duration = random.uniform(0.5, 1.5)
        else:
            self._time_warp_factor = random.choice([
                random.uniform(0.5, 0.7),   # Slow motion
                random.uniform(1.3, 1.8),   # Fast forward
            ])
            self._time_warp_duration = random.uniform(0.3, 0.8)

        self.time_warps_triggered += 1

    def _spawn_glitch_rect(self):
        """Create a visual glitch rectangle."""
        # Will be positioned during draw phase
        w = random.randint(20, 100)
        h = random.randint(10, 60)

        # Glitch colors: void black, static white, or corruption purple
        color = random.choice([
            (0, 0, 0),          # Void
            (255, 255, 255),    # Static flash
            (128, 0, 128),      # Corruption purple
            (0, 255, 128),      # Matrix green
        ])

        self._glitch_rects.append((
            pygame.Rect(0, 0, w, h),  # Position set in draw
            255,  # Alpha
            color
        ))
        self.visual_glitches_shown += 1

    def warp_time(self, dt: float) -> float:
        """Apply time dilation to delta time."""
        if self._time_warp_active:
            return dt * self._time_warp_factor
        return dt

    def should_block_escape(self) -> bool:
        """
        Determine if ESC key should be ignored this frame.
        Returns True if the escape should be blocked.
        """
        if self.entropy < 0.3:
            return False

        # Higher entropy = higher chance of blocking
        block_chance = (self.entropy - 0.3) * 0.2  # Max ~10% at 0.8 entropy
        if random.random() < block_chance:
            self.blocked_escapes += 1
            return True
        return False

    def get_input_hesitation(self) -> float:
        """
        Get input delay in seconds for current entropy level.
        Returns 0 for no delay.
        """
        if self.entropy < 0.2:
            return 0.0

        # Occasional hesitation spikes
        if random.random() < self.entropy * 0.02:
            return random.uniform(0.05, 0.15)  # 50-150ms hesitation
        return 0.0

    def get_movement_drift(self) -> tuple:
        """
        Get accumulated movement drift (character overshoots).
        Returns (dx, dy) drift values.
        """
        return self._movement_drift

    def add_movement_drift(self, dx: float, dy: float):
        """Add drift when movement keys are released."""
        if self.entropy < 0.3:
            return

        # Scale drift by entropy
        drift_scale = self.entropy * 0.3
        self._movement_drift = (
            self._movement_drift[0] + dx * drift_scale,
            self._movement_drift[1] + dy * drift_scale,
        )

    def get_wrap_distortion(self) -> tuple:
        """
        Get wraparound coordinate distortion.
        Returns (x_offset, y_offset) to apply to wrap coordinates.
        """
        if self.entropy < 0.5:
            return (0, 0)

        # At high entropy, occasional wrap distortion
        if random.random() < self.entropy * 0.01:
            # Subtle offset that feels "wrong"
            return (
                random.randint(-50, 50),
                random.randint(-50, 50),
            )
        return (0, 0)

    def should_skip_npc_update(self) -> bool:
        """
        Determine if an NPC's update should be skipped (freeze glitch).
        Called per-NPC per-frame.
        """
        if self.entropy < 0.2:
            return False
        return random.random() < self.entropy * 0.003  # ~0.1% at 0.3 entropy

    def get_flicker_building_id(self):
        """
        Get the ID of a building that should flicker this frame.
        Returns None if no building should flicker.
        """
        return self._building_flicker_id

    def trigger_building_flicker(self, building_id):
        """Request a specific building to flicker briefly."""
        if self.entropy < 0.25:
            return

        self._building_flicker_id = building_id
        self._building_flicker_timer = 0.05  # 50ms flicker

    def should_skip_screen_clear(self) -> bool:
        """
        Check if screen.fill() should be skipped (afterimage effect).
        Resets the flag after checking.
        """
        if self._skip_clear_next_frame:
            self._skip_clear_next_frame = False
            return True
        return False

    def draw_visual_corruption(self, screen: pygame.Surface):
        """
        Draw visual corruption effects on top of the rendered frame.
        Call this just before pygame.display.flip().
        """
        if not self._glitch_rects:
            return

        screen_w, screen_h = screen.get_size()

        for rect, alpha, color in self._glitch_rects:
            # Clamp alpha to valid range
            clamped_alpha = max(0, min(255, int(alpha)))
            if clamped_alpha <= 0:
                continue

            # Position glitch randomly on screen (handle edge cases)
            max_x = max(0, screen_w - rect.width)
            max_y = max(0, screen_h - rect.height)
            rect.x = random.randint(0, max_x) if max_x > 0 else 0
            rect.y = random.randint(0, max_y) if max_y > 0 else 0

            # Create semi-transparent glitch surface
            glitch_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            glitch_color = (color[0], color[1], color[2], clamped_alpha)
            glitch_surf.fill(glitch_color)

            screen.blit(glitch_surf, rect.topleft)

    def draw_scan_lines(self, screen: pygame.Surface):
        """
        Draw CRT-style scan lines at high entropy.
        Subtle visual degradation effect.
        """
        if self.entropy < 0.4:
            return

        # Only draw occasionally to avoid constant visual noise
        if random.random() > self.entropy * 0.3:
            return

        screen_h = screen.get_height()
        line_spacing = 4

        line_surf = pygame.Surface((screen.get_width(), 1), pygame.SRCALPHA)
        alpha = int(20 * self.entropy)  # Max ~16 alpha
        line_surf.fill((0, 0, 0, alpha))

        for y in range(0, screen_h, line_spacing):
            screen.blit(line_surf, (0, y))

    def get_narrator_trigger(self) -> str | None:
        """
        Check if corruption should trigger narrator commentary.
        Returns event string or None.
        """
        # Time warp just triggered
        if self._time_warp_active and self._time_warp_duration > 0.9 * (0.3 + random.random() * 0.5):
            if self.time_warps_triggered % 3 == 0:  # Every 3rd warp
                return "TIME_GLITCH"

        # Multiple escape blocks
        if self.blocked_escapes > 0 and self.blocked_escapes % 2 == 0:
            self.blocked_escapes += 1  # Prevent repeat trigger
            return "ESCAPE_BLOCKED"

        return None

    def get_corruption_debug_info(self) -> dict:
        """Get debug info for development/testing."""
        return {
            "entropy": round(self.entropy, 3),
            "target_entropy": round(self.target_entropy, 3),
            "time_warp_active": self._time_warp_active,
            "time_warp_factor": round(self._time_warp_factor, 2),
            "glitch_rects": len(self._glitch_rects),
            "blocked_escapes": self.blocked_escapes,
            "time_warps": self.time_warps_triggered,
        }


# Narrator fallback lines for corruption events
CORRUPTION_NARRATOR_LINES = {
    "TIME_GLITCH": [
        "Time... slips, doesn't it?",
        "The clock hands move at their own whim now.",
        "Reality stutters. Did you notice?",
        "Even time abandons this place.",
    ],
    "ESCAPE_BLOCKED": [
        "No escape. Not yet.",
        "The exit refuses you.",
        "You haven't earned your freedom.",
        "Stay. The city needs you.",
    ],
    "VISUAL_GLITCH": [
        "Did you see that? No? Good.",
        "The cracks are showing.",
        "Reality is... thin here.",
    ],
}
