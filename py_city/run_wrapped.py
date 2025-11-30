"""
py_city wrapper for Beginner's Guide integration.

This module wraps py_city to work with the adapter system, hooking:
- NPC dialogue to HorrorNPCDialogue for LLM-generated horror dialogue
- GameOverlay for subtitles, notifications, and fourth-wall effects
- PlotEventBus for tracking player behavior

Features:
- Large scrollable city map with camera following player
- Proper street grid with wide roads and sidewalks
- Rain weather system with narrator commentary
- NPC pathfinding along sidewalks
- Tutorial system with deteriorating narrator
- Crime simulation (mugging, chasing, arrests)
- Anomaly discovery system
- Exit/level completion

Usage via py_adapter:
    load_py_scene(screen, clock, asset_path, guide, scene_slug, tone)
    # where asset_path points to this file
"""

import math
import os
import random
import sys

import pygame

# Add py_city directory to path for imports
PY_CITY_DIR = os.path.dirname(os.path.abspath(__file__))
if PY_CITY_DIR not in sys.path:
    sys.path.insert(0, PY_CITY_DIR)

# Import our new city systems
from city_map import Camera, CityConfig, CityMap, WeatherSystem, DayNightCycle, TimeOfDay
from game_loop import GameLoopManager, GamePhase, CrimeSimulation, NarratorQueue

# NPC type to archetype mapping
NPC_TYPE_TO_ARCHETYPE = {
    "criminal": "mysterious",  # Criminals know something is wrong
    "police": "guard",         # Authority figures
    "civilian": "civilian",    # Regular folk
}

# NPC type to horror traits
NPC_TYPE_TO_TRAITS = {
    "criminal": ["desperate", "knowing"],      # Criminals trying to escape
    "police": ["paranoid", "oblivious"],       # Guards seeing threats, missing the real one
    "civilian": ["oblivious", "melancholic"],  # Civilians unaware of the horror
}

# Rain narrator lines
RAIN_NARRATOR_LINES = {
    "rain_started": [
        "The rain begins to fall. As if the sky itself weeps for what happens here.",
        "Rain. It always rains when things are about to get... interesting.",
        "Do you feel that? The rain. It's been waiting for you.",
    ],
    "rain_heavy": [
        "The downpour intensifies. You can barely see through it. Perfect.",
        "Such heavy rain. It washes away so many things. Evidence. Memory. Hope.",
        "Listen to it pound against the pavement. Like a heartbeat. Like YOUR heartbeat.",
    ],
    "rain_stopped": [
        "The rain stops. But the dampness remains. As do you.",
        "Silence falls with the last drops. Don't you miss the noise already?",
        "The storm passes. But storms always return here. They always return.",
    ],
}

# Crime event narrator lines
CRIME_NARRATOR_LINES = {
    "mugging_started": [
        "Someone's about to have a very bad day.",
        "Crime never sleeps. Neither should you.",
        "Watch. Learn. Choose.",
    ],
    "burglary_started": [
        "Breaking and entering. Such desperation.",
        "They think no one's watching. You are.",
        "Property means nothing here. But they don't know that yet.",
    ],
    "chase_started": [
        "The hunt begins.",
        "Run, run, run. They always run.",
        "Justice or escape? Place your bets.",
    ],
    "criminal_arrested": [
        "Order restored. For now.",
        "Caught. Like they always are. Eventually.",
        "The system works. Doesn't it?",
    ],
    "criminal_escaped": [
        "Gone. Like they were never here.",
        "Freedom has a price. They'll pay it later.",
        "Some escape. Most don't. The math is patient.",
    ],
}


class CityNPC:
    """NPC that navigates the city using sidewalk pathfinding."""

    def __init__(self, x: float, y: float, sprite: pygame.Surface,
                 npc_type: str, city_map: CityMap):
        self.x = x
        self.y = y
        self.size = 35
        self.speed = 1.5
        self.sprite = sprite
        self.type = npc_type
        self.city_map = city_map

        # State
        self.health = 100
        self.in_jail = False
        self.jail_timer = 600
        self.committed_crime = False
        self.in_building = False
        self.breaking_in = False

        # Pathfinding
        self.path = []
        self.path_index = 0
        self.wait_timer = random.uniform(0.5, 3.0)  # Stagger initial movement

    def _generate_new_path(self):
        """Generate a new path to a random destination."""
        # Pick a random sidewalk node as destination
        if self.city_map.sidewalk_nodes:
            dest_node = random.choice(self.city_map.sidewalk_nodes)
            self.path = self.city_map.find_path(
                self.x, self.y,
                dest_node.x, dest_node.y
            )
            self.path_index = 0

    def move(self, dt: float):
        """Move along the path."""
        if self.in_jail or self.in_building:
            return

        # Waiting before moving?
        if self.wait_timer > 0:
            self.wait_timer -= dt
            if self.wait_timer <= 0:
                self._generate_new_path()
            return

        # No path? Generate one
        if not self.path or self.path_index >= len(self.path):
            self.wait_timer = random.uniform(1.0, 4.0)  # Pause before next path
            return

        # Follow path
        target_x, target_y = self.path[self.path_index]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 3:  # Close enough to waypoint
            self.x, self.y = target_x, target_y
            self.path_index += 1
        else:
            # Move toward waypoint
            speed = self.speed * dt * 60
            self.x += (dx / dist) * speed
            self.y += (dy / dist) * speed

    def draw(self, screen: pygame.Surface, camera: Camera):
        """Draw NPC with health bar."""
        screen_x, screen_y = camera.apply(self.x, self.y)

        # Skip if off screen
        if (screen_x < -self.size or screen_x > camera.screen_width + self.size or
            screen_y < -self.size or screen_y > camera.screen_height + self.size):
            return

        # Draw sprite
        screen.blit(self.sprite, (screen_x, screen_y))

        # Health bar
        bar_width = self.size
        bar_height = 4
        pygame.draw.rect(screen, (255, 0, 0),
                         (screen_x, screen_y - 8, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0),
                         (screen_x, screen_y - 8,
                          int(bar_width * (self.health / 100)), bar_height))

        # Crime indicator
        if self.breaking_in or self.committed_crime:
            pygame.draw.circle(screen, (255, 255, 0),
                               (int(screen_x + self.size / 2),
                                int(screen_y + self.size / 2)), 5)


class CityPlayer:
    """Player that moves in the city with camera tracking."""

    def __init__(self, x: float, y: float, sprite: pygame.Surface,
                 world_width: int, world_height: int):
        self.x = x
        self.y = y
        self.size = 35
        self.speed = 5
        self.sprite = sprite
        self.health = 100
        self.karma = 0
        self.alignment = "neutral"
        self.world_width = world_width
        self.world_height = world_height

    def move(self, dx: int, dy: int, city_map: CityMap, dt: float):
        """Move with collision detection."""
        move_speed = self.speed * dt * 60

        new_x = self.x + dx * move_speed
        new_y = self.y + dy * move_speed

        # Check collision
        new_rect = pygame.Rect(new_x, new_y, self.size, self.size)
        if not city_map.is_colliding(new_rect):
            self.x = max(0, min(new_x, self.world_width - self.size))
            self.y = max(0, min(new_y, self.world_height - self.size))

    def draw(self, screen: pygame.Surface, camera: Camera):
        """Draw player with health bar."""
        screen_x, screen_y = camera.apply(self.x, self.y)

        screen.blit(self.sprite, (screen_x, screen_y))

        # Health bar
        bar_width = self.size
        bar_height = 5
        pygame.draw.rect(screen, (255, 0, 0),
                         (screen_x, screen_y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0),
                         (screen_x, screen_y - 10,
                          int(bar_width * (self.health / 100)), bar_height))

    def change_alignment(self, alignment: str):
        self.alignment = alignment

    def interact(self, npcs, radius: float = 50) -> 'CityNPC':
        """Find nearby NPC to interact with."""
        for npc in npcs:
            dx = npc.x - self.x
            dy = npc.y - self.y
            if math.sqrt(dx * dx + dy * dy) < radius:
                return npc
        return None


def run(screen, clock, guide, scene_slug, tone):
    """
    Run py_city with Beginner's Guide integration.

    Args:
        screen: pygame display surface
        clock: pygame clock
        guide: Guide instance for TTS
        scene_slug: Scene identifier
        tone: Narrator tone
    """
    # Import overlay system (late import to avoid circular deps)
    from game.overlay import GameOverlay
    from game.plot_event_bus import PlotEvent, publish
    from game.plot_state import PlotStateManager

    # Load existing state or create new
    plot_state = PlotStateManager.load_or_create()

    # Initialize overlay
    overlay = GameOverlay.create(guide)
    overlay.set_scene(scene_slug)

    # Screen dimensions
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Create city configuration
    city_config = CityConfig(
        world_width=3200,
        world_height=2400,
        block_width=180,
        block_height=140,
        road_width=70,
        sidewalk_width=14,
    )

    # Create city map
    city_map = CityMap(city_config)

    # Create camera
    camera = Camera(WIDTH, HEIGHT, city_config.world_width, city_config.world_height)

    # Create weather system (rain + wind + temperature)
    weather = WeatherSystem(city_config.world_width, city_config.world_height)

    # Create day/night cycle (starts at 8:00 AM, 1 real minute = 1 game hour)
    day_night = DayNightCycle(start_hour=8.0, time_scale=60.0)

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    # Load sprites
    sprite_size = (45, 45)
    try:
        player_sprite = pygame.transform.scale(
            pygame.image.load(os.path.join(PY_CITY_DIR, 'player.png')), sprite_size
        )
        criminal_sprite = pygame.transform.scale(
            pygame.image.load(os.path.join(PY_CITY_DIR, 'criminal.png')), sprite_size
        )
        police_sprite = pygame.transform.scale(
            pygame.image.load(os.path.join(PY_CITY_DIR, 'police.png')), sprite_size
        )
        civilian_sprite = pygame.transform.scale(
            pygame.image.load(os.path.join(PY_CITY_DIR, 'civilian.png')), sprite_size
        )
    except pygame.error:
        # Fallback to colored rectangles
        player_sprite = pygame.Surface(sprite_size)
        player_sprite.fill((0, 200, 0))
        criminal_sprite = pygame.Surface(sprite_size)
        criminal_sprite.fill((200, 0, 0))
        police_sprite = pygame.Surface(sprite_size)
        police_sprite.fill((0, 0, 200))
        civilian_sprite = pygame.Surface(sprite_size)
        civilian_sprite.fill((200, 200, 0))

    # Create player on a sidewalk (not in a building)
    # Find a sidewalk node near center of world
    player_start_x = city_config.world_width // 2
    player_start_y = city_config.world_height // 2

    # Snap to nearest sidewalk node
    if city_map.sidewalk_nodes:
        nearest_node = city_map.get_nearest_sidewalk_node(player_start_x, player_start_y)
        if nearest_node:
            player_start_x = nearest_node.x
            player_start_y = nearest_node.y

    player = CityPlayer(
        player_start_x,
        player_start_y,
        player_sprite,
        city_config.world_width,
        city_config.world_height
    )

    # Create NPCs
    all_npcs = []
    criminals = []
    police = []
    civilians = []

    # Spawn NPCs on sidewalks
    def spawn_npc_on_sidewalk(sprite, npc_type) -> CityNPC:
        """Spawn an NPC at a random sidewalk node."""
        if city_map.sidewalk_nodes:
            node = random.choice(city_map.sidewalk_nodes)
            return CityNPC(node.x, node.y, sprite, npc_type, city_map)
        return CityNPC(100, 100, sprite, npc_type, city_map)

    # Create criminals
    for _ in range(6):
        npc = spawn_npc_on_sidewalk(criminal_sprite, "criminal")
        all_npcs.append(npc)
        criminals.append(npc)

    # Create police
    for _ in range(5):
        npc = spawn_npc_on_sidewalk(police_sprite, "police")
        all_npcs.append(npc)
        police.append(npc)

    # Create civilians
    for _ in range(20):
        npc = spawn_npc_on_sidewalk(civilian_sprite, "civilian")
        all_npcs.append(npc)
        civilians.append(npc)

    # Register NPCs with overlay system
    _register_npcs_with_overlay(overlay, all_npcs, plot_state)

    # Create narrator queue for pacing (shared between game loop and main loop)
    narrator_queue = NarratorQueue(min_gap=5.0, max_queue=3)

    # Initialize game loop manager
    game_loop = GameLoopManager(
        city_config.world_width,
        city_config.world_height,
        guide=guide,
        overlay=overlay,
        narrator_queue=narrator_queue
    )

    # Initialize crime simulation
    crime_sim = CrimeSimulation(city_config.world_width, city_config.world_height)

    # Track exit portal location
    exit_portal = {"x": 0, "y": 0, "active": False, "pulse": 0.0}

    def on_exit_ready(x, y):
        exit_portal["x"] = x
        exit_portal["y"] = y
        exit_portal["active"] = True

    game_loop.on_exit_ready = on_exit_ready

    # Track discovered anomalies for visual markers
    discovered_anomalies = []

    def on_anomaly_discovered(anomaly):
        discovered_anomalies.append(anomaly)
        # Show notification via the notifications subsystem
        overlay.notifications.show_glitch(f"ANOMALY DETECTED: {anomaly.name}", duration=4.0)

    game_loop.on_anomaly_discovered = on_anomaly_discovered

    # Game state tracking
    dialog_timer = 0
    talking_npc = None
    idle_timer = 0.0
    last_player_pos = (player.x, player.y)
    player_moving = False

    # Instructions
    instructions_text = [
        "Arrow keys: Move",
        "Space: Talk to NPC",
        "G/E: Good/Evil",
        "H: Help police",
        "M: Mute narrator",
        "Tab: Skip phase",
        "ESC: Pause menu",
    ]
    show_instructions = True

    # Pause menu state
    paused = False
    pause_menu_selection = 0  # 0 = Resume, 1 = Exit to Main
    pause_menu_options = ["Resume Game", "Exit to Main Menu"]

    # Start the game loop
    game_loop.start()

    running = True
    level_completed = False

    while running:
        dt = clock.tick(60) / 1000.0

        # Handle events (overlay first)
        events = pygame.event.get()
        events = overlay.handle_events(events)

        for event in events:
            if event.type == pygame.QUIT:
                publish(PlotEvent.QUIT_CLICK)
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    publish(PlotEvent.ESC_PRESS)
                    paused = not paused  # Toggle pause menu
                    pause_menu_selection = 0  # Reset selection

                # Pause menu controls
                elif paused:
                    if event.key == pygame.K_UP:
                        pause_menu_selection = (pause_menu_selection - 1) % len(pause_menu_options)
                    elif event.key == pygame.K_DOWN:
                        pause_menu_selection = (pause_menu_selection + 1) % len(pause_menu_options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if pause_menu_selection == 0:  # Resume
                            paused = False
                        elif pause_menu_selection == 1:  # Exit to Main
                            running = False
                    # Skip other inputs while paused
                    continue

                elif event.key == pygame.K_g:
                    player.change_alignment("good")
                    game_loop.on_player_aligned("good")

                elif event.key == pygame.K_e:
                    player.change_alignment("evil")
                    game_loop.on_player_aligned("evil")

                elif event.key == pygame.K_i:
                    show_instructions = not show_instructions

                elif event.key == pygame.K_m:
                    overlay.audio.muted = not overlay.audio.muted
                    if overlay.audio.muted:
                        overlay.audio.stop()
                        narrator_queue.clear()
                        print("Narrator muted")
                    else:
                        print("Narrator unmuted")

                elif event.key == pygame.K_TAB:
                    # Skip to next phase
                    current = game_loop.state.phase
                    if current == GamePhase.TUTORIAL:
                        game_loop._transition_to_phase(GamePhase.LIVING_CITY)
                    elif current == GamePhase.LIVING_CITY:
                        game_loop._transition_to_phase(GamePhase.SOMETHING_WRONG)
                    elif current == GamePhase.SOMETHING_WRONG:
                        # Mark enough anomalies as discovered
                        for anomaly in game_loop.state.anomalies[:5]:
                            anomaly.discovered = True
                        game_loop.state.anomalies_discovered = 5
                        game_loop._transition_to_phase(GamePhase.EXIT_SEARCH)
                    elif current == GamePhase.EXIT_SEARCH:
                        game_loop._transition_to_phase(GamePhase.COMPLETED)
                    narrator_queue.clear()  # Clear queued lines on skip

                elif event.key == pygame.K_h:
                    # Help police with nearby crime
                    crime = crime_sim.player_intervene(player.x, player.y, True)
                    if crime:
                        game_loop.on_player_intervention(True)
                        player.karma += 5

                elif event.key == pygame.K_SPACE:
                    # NPC interaction
                    interacted = player.interact(all_npcs)
                    if interacted:
                        npc_id = f"npc_{id(interacted)}"
                        situation = _get_situation(interacted, player, plot_state)
                        overlay.show_npc_dialogue(npc_id, "", situation)
                        dialog_timer = 4.0
                        talking_npc = interacted
                        idle_timer = 0.0
                        game_loop.on_player_talked(interacted.type)

        # Skip game updates when paused
        if not paused:
            # Track idle time
            if (player.x, player.y) == last_player_pos:
                idle_timer += dt
                player_moving = False
                if idle_timer >= 30.0:
                    publish(PlotEvent.IDLE, {"seconds": idle_timer})
                    idle_timer = 0.0
            else:
                idle_timer = 0.0
                player_moving = True
                last_player_pos = (player.x, player.y)

            # Player movement
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            player.move(dx, dy, city_map, dt)

        # Camera follows player
        camera.follow(player.x + player.size // 2, player.y + player.size // 2)

        # Update game loop (tutorial, phases, anomalies)
        game_loop.update(dt, player.x, player.y, player_moving)

        # Check for level completion
        if game_loop.is_complete():
            level_completed = True
            running = False

        # Update crime simulation (only during living city phase)
        if game_loop.state.phase in (GamePhase.LIVING_CITY, GamePhase.SOMETHING_WRONG):
            # Set night mode for crime bonus
            crime_sim.set_night_mode(day_night.is_night())
            crime_events = crime_sim.update(
                dt, criminals, police, civilians,
                player.x, player.y
            )
            # Queue narrator comments on crime events
            for event in crime_events:
                if not overlay.audio.muted:
                    lines = CRIME_NARRATOR_LINES.get(event, [])
                    if lines:
                        narrator_queue.queue_line(random.choice(lines))

        # Process narrator queue - speak next line if ready
        if guide and not overlay.audio.muted:
            line_to_speak = narrator_queue.update(dt)
            if line_to_speak:
                guide.speak_async(line_to_speak)

        # Update NPCs
        for npc in all_npcs:
            if npc is talking_npc and dialog_timer > 0:
                continue  # Pause talking NPC
            if not npc.in_jail:
                npc.move(dt)

        # Update day/night cycle
        time_event = day_night.update(dt)
        if time_event and not overlay.audio.muted:
            narrator_queue.queue_line(time_event)

        # Update weather (rain, wind, temp) with current time of day
        weather_event = weather.update(dt, day_night.get_time_of_day())
        if weather_event and not overlay.audio.muted:
            lines = RAIN_NARRATOR_LINES.get(weather_event, [])
            if lines:
                narrator_queue.queue_line(random.choice(lines))

        # Update window states based on time
        lit_chance = day_night.get_window_lit_chance()
        city_map.update_windows(dt, lit_chance)

        # Update overlay
        overlay.update(dt)

        # Update exit portal pulse
        if exit_portal["active"]:
            exit_portal["pulse"] += dt * 3

        # Dialog timer
        if dialog_timer > 0:
            dialog_timer -= dt
            if dialog_timer <= 0:
                talking_npc = None

        # --- Rendering ---
        # Draw city with day/night lighting
        darkness_alpha = day_night.get_darkness_alpha()
        city_map.draw(screen, camera, darkness_alpha)

        # Draw anomaly markers (before NPCs so they appear under)
        for anomaly in game_loop.state.anomalies:
            if not anomaly.discovered:
                # Undiscovered anomalies have subtle shimmer
                ax, ay = camera.apply(anomaly.x, anomaly.y)
                if 0 <= ax < WIDTH and 0 <= ay < HEIGHT:
                    shimmer = int(abs(math.sin(game_loop.state.phase_timer * 2)) * 30)
                    pygame.draw.circle(screen, (50 + shimmer, 50 + shimmer, 80 + shimmer),
                                       (int(ax), int(ay)), 8, 2)

        # Draw exit portal
        if exit_portal["active"]:
            ex, ey = camera.apply(exit_portal["x"], exit_portal["y"])
            if -100 <= ex < WIDTH + 100 and -100 <= ey < HEIGHT + 100:
                # Pulsing portal effect
                pulse = abs(math.sin(exit_portal["pulse"]))
                radius = int(30 + pulse * 15)
                # Outer glow
                for i in range(3):
                    alpha = int((3 - i) * 30 * pulse)
                    glow_color = (100, 200, 255)
                    glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*glow_color, alpha),
                                       (radius * 2, radius * 2), radius + i * 10)
                    screen.blit(glow_surf, (int(ex) - radius * 2, int(ey) - radius * 2))
                # Inner portal
                pygame.draw.circle(screen, (150, 220, 255), (int(ex), int(ey)), radius)
                pygame.draw.circle(screen, (200, 240, 255), (int(ex), int(ey)), radius - 5)
                # "EXIT" text
                exit_font = pygame.font.Font(None, 20)
                exit_text = exit_font.render("EXIT", True, (50, 50, 80))
                screen.blit(exit_text, (int(ex) - 15, int(ey) - 8))

        # Draw crime indicators
        for crime in crime_sim.active_crimes:
            cx, cy = camera.apply(crime.x, crime.y)
            if 0 <= cx < WIDTH and 0 <= cy < HEIGHT:
                if crime.being_chased:
                    # Red flashing indicator for chase
                    flash = int(abs(math.sin(game_loop.state.phase_timer * 8)) * 255)
                    pygame.draw.circle(screen, (flash, 0, 0), (int(cx), int(cy) - 40), 8)
                else:
                    # Yellow indicator for crime in progress
                    pygame.draw.circle(screen, (255, 200, 0), (int(cx), int(cy) - 40), 6)

        # Draw NPCs
        for npc in all_npcs:
            if not npc.in_jail and not npc.in_building:
                npc.draw(screen, camera)

        # Draw player
        player.draw(screen, camera)

        # Draw weather effects on top of world
        weather.draw(screen, camera)

        # UI elements (screen-space, not affected by camera)
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)

        # Objective panel (top-center)
        objective = game_loop.get_current_objective()
        if objective:
            obj_surf = font.render(objective, True, (200, 220, 255))
            obj_rect = obj_surf.get_rect(centerx=WIDTH // 2, y=10)
            obj_bg = pygame.Surface((obj_rect.width + 20, obj_rect.height + 10), pygame.SRCALPHA)
            obj_bg.fill((20, 20, 30, 180))
            screen.blit(obj_bg, (obj_rect.x - 10, obj_rect.y - 5))
            screen.blit(obj_surf, obj_rect)

        # Phase indicator
        phase_name = game_loop.state.phase.name.replace("_", " ").title()
        phase_surf = small_font.render(f"[{phase_name}]", True, (120, 120, 150))
        screen.blit(phase_surf, (WIDTH // 2 - phase_surf.get_width() // 2, 35))

        # Stats panel (left side)
        stats_bg = pygame.Surface((180, 180))
        stats_bg.set_alpha(180)
        stats_bg.fill((40, 40, 40))
        screen.blit(stats_bg, (5, 5))

        stats = [
            f"Muggings: {crime_sim.total_muggings}",
            f"Burglaries: {crime_sim.total_burglaries}",
            f"Arrests: {crime_sim.criminals_caught}",
            f"Escaped: {crime_sim.criminals_escaped}",
            f"Karma: {player.karma:.0f}",
            f"Alignment: {player.alignment}",
        ]
        for i, stat in enumerate(stats):
            text_surface = font.render(stat, True, WHITE)
            screen.blit(text_surface, (12, 12 + i * 24))

        # Time/Weather panel (right side)
        time_panel_bg = pygame.Surface((160, 80))
        time_panel_bg.set_alpha(180)
        time_panel_bg.fill((40, 40, 50))
        screen.blit(time_panel_bg, (WIDTH - 165, 5))

        time_str = day_night.get_time_string()
        time_period = day_night.get_time_of_day().value.title()
        weather_str = weather.get_weather_string()
        temp_str = weather.get_temperature_string()

        time_text = font.render(f"{time_str}", True, (220, 220, 180))
        screen.blit(time_text, (WIDTH - 158, 10))
        period_text = small_font.render(f"Day {day_night.day_count} - {time_period}", True, (180, 180, 200))
        screen.blit(period_text, (WIDTH - 158, 32))
        weather_text = small_font.render(f"{weather_str}", True, (150, 180, 220))
        screen.blit(weather_text, (WIDTH - 158, 50))
        temp_text = small_font.render(f"{temp_str}", True, (200, 180, 150))
        screen.blit(temp_text, (WIDTH - 158, 68))

        # Instructions panel
        if show_instructions:
            inst_bg = pygame.Surface((170, 155))
            inst_bg.fill((40, 40, 40))
            inst_bg.set_alpha(180)
            screen.blit(inst_bg, (WIDTH - 180, 10))
            for i, line in enumerate(instructions_text):
                text_surface = font.render(line, True, WHITE)
                screen.blit(text_surface, (WIDTH - 170, 20 + i * 24))

        # Mute indicator
        if overlay.audio.muted:
            mute_text = font.render("[MUTED]", True, (200, 80, 80))
            screen.blit(mute_text, (WIDTH // 2 - 30, 55))

        # Rain indicator (now using weather system)
        if weather.is_raining:
            rain_text = small_font.render(f"Rain: {int(weather.rain_intensity * 100)}%", True, (150, 170, 200))
            screen.blit(rain_text, (WIDTH // 2 - 30, 75))

        # Anomaly counter (during anomaly phase)
        if game_loop.state.phase == GamePhase.SOMETHING_WRONG:
            anom_text = font.render(
                f"Anomalies: {game_loop.state.anomalies_discovered}/{game_loop.state.anomalies_required}",
                True, (180, 150, 200)
            )
            screen.blit(anom_text, (WIDTH // 2 - 50, HEIGHT - 40))

        # Minimap (bottom-right corner)
        _draw_minimap(screen, WIDTH, player, all_npcs, city_config,
                      exit_portal if exit_portal["active"] else None,
                      game_loop.state.anomalies)

        # Draw overlay on top
        overlay.draw(screen)

        # Draw pause menu if paused
        if paused:
            _draw_pause_menu(screen, pause_menu_options, pause_menu_selection, font)

        pygame.display.flip()

    # Cleanup and save state
    overlay.clear_all()
    plot_state.save()
    print(f"Game state saved. Stage: {plot_state.get_stage().value}, Awareness: {plot_state.get_awareness():.2f}")

    # Return completion status
    return level_completed


def _draw_minimap(screen: pygame.Surface, screen_width: int,
                  player: CityPlayer, npcs: list, config: CityConfig,
                  exit_portal: dict = None, anomalies: list = None):
    """Draw a minimap in the corner."""
    map_size = 120
    margin = 10
    map_x = screen_width - map_size - margin
    map_y = screen.get_height() - map_size - margin

    # Background
    minimap = pygame.Surface((map_size, map_size))
    minimap.fill((30, 30, 35))
    minimap.set_alpha(200)

    # Scale factor
    scale_x = map_size / config.world_width
    scale_y = map_size / config.world_height

    # Draw anomalies (purple dots for undiscovered)
    if anomalies:
        for anomaly in anomalies:
            if not anomaly.discovered:
                ax = int(anomaly.x * scale_x)
                ay = int(anomaly.y * scale_y)
                pygame.draw.circle(minimap, (150, 100, 200), (ax, ay), 3)

    # Draw exit portal (cyan pulsing)
    if exit_portal:
        ex = int(exit_portal["x"] * scale_x)
        ey = int(exit_portal["y"] * scale_y)
        pygame.draw.circle(minimap, (100, 200, 255), (ex, ey), 5)
        pygame.draw.circle(minimap, (150, 220, 255), (ex, ey), 3)

    # Draw NPCs (small dots by type)
    for npc in npcs:
        if npc.in_jail:
            continue
        nx = int(npc.x * scale_x)
        ny = int(npc.y * scale_y)
        if npc.type == "criminal":
            color = (255, 80, 80) if npc.committed_crime else (180, 60, 60)
        elif npc.type == "police":
            color = (80, 80, 255)
        else:
            color = (150, 150, 60)
        pygame.draw.circle(minimap, color, (nx, ny), 2)

    # Draw player (green dot, larger)
    px = int(player.x * scale_x)
    py = int(player.y * scale_y)
    pygame.draw.circle(minimap, (0, 255, 0), (px, py), 4)
    pygame.draw.circle(minimap, (100, 255, 100), (px, py), 2)

    # Border
    pygame.draw.rect(minimap, (100, 100, 100), (0, 0, map_size, map_size), 1)

    screen.blit(minimap, (map_x, map_y))


def _draw_pause_menu(screen: pygame.Surface, options: list, selection: int, font: pygame.font.Font):
    """Draw the pause menu overlay."""
    # Semi-transparent dark overlay
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Menu box
    menu_width = 400
    menu_height = 250
    menu_x = (screen.get_width() - menu_width) // 2
    menu_y = (screen.get_height() - menu_height) // 2

    # Dark horror-themed background
    menu_bg = pygame.Surface((menu_width, menu_height))
    menu_bg.fill((20, 20, 25))

    # Border with subtle red glow
    pygame.draw.rect(menu_bg, (80, 40, 40), (0, 0, menu_width, menu_height), 3)
    pygame.draw.rect(menu_bg, (120, 60, 60), (2, 2, menu_width - 4, menu_height - 4), 1)

    screen.blit(menu_bg, (menu_x, menu_y))

    # Title
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("PAUSED", True, (200, 200, 210))
    title_rect = title_text.get_rect(centerx=screen.get_width() // 2, y=menu_y + 30)
    screen.blit(title_text, title_rect)

    # Menu options
    option_start_y = menu_y + 100
    for i, option in enumerate(options):
        is_selected = (i == selection)

        # Highlight selected option
        if is_selected:
            color = (220, 180, 180)
            # Selection indicator
            indicator = font.render(">", True, (200, 100, 100))
            screen.blit(indicator, (menu_x + 60, option_start_y + i * 50))
        else:
            color = (140, 140, 150)

        option_text = font.render(option, True, color)
        option_rect = option_text.get_rect(centerx=screen.get_width() // 2, y=option_start_y + i * 50)
        screen.blit(option_text, option_rect)

    # Instructions
    inst_font = pygame.font.Font(None, 20)
    inst_text = inst_font.render("Use Arrow Keys to navigate, Enter/Space to select", True, (120, 120, 130))
    inst_rect = inst_text.get_rect(centerx=screen.get_width() // 2, y=menu_y + menu_height - 30)
    screen.blit(inst_text, inst_rect)


def _register_npcs_with_overlay(overlay, npcs, plot_state):
    """Register all NPCs with the overlay's NPC dialogue system."""
    from game.plot_state import HorrorStage

    for npc in npcs:
        npc_id = f"npc_{id(npc)}"
        archetype = NPC_TYPE_TO_ARCHETYPE.get(npc.type, "civilian")
        traits = list(NPC_TYPE_TO_TRAITS.get(npc.type, []))

        # Add stage-dependent traits
        stage = plot_state.get_stage()
        if stage == HorrorStage.LATE:
            if "knowing" not in traits:
                traits.append("paranoid")
        elif stage == HorrorStage.FINALE:
            traits = ["corrupted", "glitching"]

        # Generate backstory based on type
        backstory = _generate_backstory(npc.type)
        secret = _generate_secret(npc.type, stage)

        # Create NPC in overlay system
        overlay.create_npc(
            npc_id=npc_id,
            name=_generate_name(npc.type),
            archetype=archetype,
            horror_traits=traits,
            backstory=backstory,
            secret=secret,
            voice_enabled=False,
        )


# Name pools for unique generation
_USED_NAMES: set = set()

_CRIMINAL_FIRST = ["Silent", "Shadow", "Crooked", "Slick", "One-Eyed", "Dirty", "Lucky", "Mad", "Scarred", "Hollow"]
_CRIMINAL_NICK = ["Whisper", "Shade", "Rat", "Snake", "Ghost", "Fingers", "Eddie", "Tony", "Vince", "Malone"]

_POLICE_RANK = ["Officer", "Deputy", "Sergeant", "Detective", "Constable", "Chief"]
_POLICE_LAST = ["Mills", "Clark", "Hayes", "Stone", "Brooks", "Walsh", "Cooper", "Murphy", "Jensen", "Torres", "Kim"]

_CIVILIAN_FIRST = ["Old", "Young", "Quiet", "Nervous", "Tired", "Pale", "Lost", "Forgotten", "Weary", "Lonely"]
_CIVILIAN_NAME = ["Martha", "Tom", "Sarah", "Jim", "Mary", "Pete", "Agnes", "Walter", "Edna", "Frank", "Betty",
                  "Earl", "Ruth", "Harold", "Dorothy", "George", "Helen", "Charles", "Margaret"]


def _generate_name(npc_type):
    """Generate a unique random name for NPC type."""
    max_attempts = 30

    for _ in range(max_attempts):
        if npc_type == "criminal":
            name = f"{random.choice(_CRIMINAL_FIRST)} {random.choice(_CRIMINAL_NICK)}"
        elif npc_type == "police":
            name = f"{random.choice(_POLICE_RANK)} {random.choice(_POLICE_LAST)}"
        else:
            name = f"{random.choice(_CIVILIAN_FIRST)} {random.choice(_CIVILIAN_NAME)}"

        if name not in _USED_NAMES:
            _USED_NAMES.add(name)
            return name

    fallback = f"Unknown #{len(_USED_NAMES) + 1}"
    _USED_NAMES.add(fallback)
    return fallback


def _generate_backstory(npc_type):
    """Generate backstory for NPC type."""
    if npc_type == "criminal":
        return "They've been here longer than they remember. The city feels wrong, but they can't leave."
    elif npc_type == "police":
        return "Sworn to protect a city that doesn't feel real. The rules change when no one's looking."
    else:
        return "Just trying to live a normal life, even when nothing feels normal anymore."


def _generate_secret(npc_type, stage):
    """Generate secret knowledge based on type and stage."""
    from game.plot_state import HorrorStage

    if stage in (HorrorStage.EARLY, HorrorStage.MID):
        return ""

    if npc_type == "criminal":
        return "They've seen the edges of the world. There's nothing beyond the city limits."
    elif npc_type == "police":
        return "The laws they enforce were written by something that isn't human."
    else:
        return "They remember dying. More than once."


def _get_situation(npc: CityNPC, player: CityPlayer, plot_state):
    """Determine dialogue situation based on context."""
    from game.plot_state import HorrorStage

    stage = plot_state.get_stage()

    if npc.in_jail:
        return "imprisoned"
    if npc.health < 50:
        return "injured"
    if npc.breaking_in:
        return "caught"
    if npc.committed_crime:
        return "guilty"

    if player.alignment == "evil":
        return "threatened"
    if player.karma < -5:
        return "afraid"

    if stage == HorrorStage.FINALE:
        return "breaking"
    if stage == HorrorStage.LATE:
        return "suspicious"

    return "greeting"


# Exit codes for launcher integration
EXIT_QUIT = 0       # Player quit normally
EXIT_COMPLETED = 1  # Player completed the level


# Standalone entry point for launcher
if __name__ == "__main__":
    # Add beginners_guide root to path for game imports
    from pathlib import Path
    root = Path(__file__).parent.parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Py City - The Tutorial")
    clock = pygame.time.Clock()

    # Initialize Guide
    from game.guide_voice import Guide
    guide = Guide()

    # Run the game and get completion status
    completed = run(screen, clock, guide, "py_city_streets", "accusatory")

    pygame.quit()

    # Exit with appropriate code for launcher
    sys.exit(EXIT_COMPLETED if completed else EXIT_QUIT)
