# environment.py
import pygame
import random

class Environment:
    """
    Holds static obstacles for collision & pathfinding.
    Enhanced with environmental storytelling elements.
    """
    def __init__(self):
        self.obstacles = []
        self.environmental_events = []
        self.event_timer = 0
        self.event_cooldown = random.uniform(300, 600)  # 5-10 minutes between events

    def add_obstacle(self, x, y, width, height):
        rect = pygame.Rect(x, y, width, height)
        self.obstacles.append(rect)

    def generate_environmental_event(self):
        """
        Generate random environmental narrative events.
        """
        event_types = [
            "dust_storm",
            "machine_malfunction",
            "scavenger_raid",
            "energy_anomaly",
            "structural_collapse"
        ]

        event_descriptions = {
            "dust_storm": [
                "A massive dust storm obscures the horizon, remnants of ecological collapse.",
                "Ancient machinery struggles against the abrasive winds.",
                "Visibility drops to near zero in the wasteland."
            ],
            "machine_malfunction": [
                "Distant mechanical sounds suggest a large system is breaking down.",
                "Erratic signals pulse from an unknown technological source.",
                "Automated systems emit warning tones across the landscape."
            ],
            "scavenger_raid": [
                "Distant sounds of conflict echo across the wasteland.",
                "Smoke rises from what seems to be a recent skirmish.",
                "Abandoned equipment suggests a hasty retreat."
            ],
            "energy_anomaly": [
                "Unusual energy readings disrupt local electromagnetic fields.",
                "Artifacts briefly glow with an otherworldly luminescence.",
                "Electronic devices momentarily malfunction."
            ],
            "structural_collapse": [
                "A distant structure crumbles, revealing layers of forgotten history.",
                "Architectural remnants hint at the scale of past civilizations.",
                "Debris fields suggest a complex, now-ruined infrastructure."
            ]
        }

        event_type = random.choice(event_types)
        description = random.choice(event_descriptions[event_type])

        return {
            "type": event_type,
            "description": description,
            "duration": random.uniform(30, 120)  # 30-120 seconds
        }

    def update(self, dt):
        """
        Update environmental events and generation logic.
        """
        self.event_timer += dt

        if self.event_timer >= self.event_cooldown:
            if not self.environmental_events or all(event['duration'] <= 0 for event in self.environmental_events):
                new_event = self.generate_environmental_event()
                self.environmental_events.append(new_event)
                self.event_timer = 0
                self.event_cooldown = random.uniform(300, 600)

        # Update existing events
        for event in self.environmental_events:
            event['duration'] -= dt
