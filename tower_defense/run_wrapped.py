"""Tower Defense — wrapped for The Tutorial.

Implements the wrapper scene contract:
    run(screen, clock, guide, scene_slug, tone) -> bool (completed)

Differences from the standalone main.py:
- Uses the provided screen/clock at any resolution (no set_mode/quit/exit);
  the base sits at the true screen centre and enemies spawn at the real edges
- Game state is local to run() — safe to re-enter
- Events route through GameOverlay (narrator, subtitles, shared inventory on I)
- Controls follow the wrapper contract: WASD/arrows move the knight,
  left-click places a turret at the cursor, E places one at the knight,
  ESC pauses. (I was unbound in the original; the overlay owns it.)
- Wave starts, a crumbling base, defeat, and victory feed the live narrator
- Carrying py_city's city_keycard grants bonus starting resources
- Surviving TARGET_WAVES full waves completes the fragment and grants the
  tower_core item
"""

import os
import random
import sys

# Sibling modules import by bare name regardless of CWD
TD_DIR = os.path.dirname(os.path.abspath(__file__))
if TD_DIR not in sys.path:
    sys.path.insert(0, TD_DIR)

import pygame

FPS = 60
IDLE_SECONDS = 45.0
TARGET_WAVES = 10          # survive (and clear) this many waves to complete
GAME_OVER_FRAMES = 150     # ~2.5s of GAME OVER before the loop ends


def run(screen, clock, guide, scene_slug, tone):
    """Run the wrapped Tower Defense. Returns True if completed."""
    # Vendor imports are deferred: load_assets() calls convert_alpha(), which
    # needs the display the wrapper has already created.
    from assets import load_assets
    from base import Base
    from config import (
        BLACK,
        ENEMY_KILL_REWARD,
        PLAYER_SPEED,
        STARTING_RESOURCES,
        TILE_SIZE,
        TURRET_COST,
        WHITE,
    )
    from player import Player
    from turret import Turret
    from wave_manager import WaveManager

    from game.inventory import Item, SharedInventory
    from game.overlay import GameOverlay
    from game.plot_event_bus import PlotEvent, publish

    width, height = screen.get_size()

    overlay = GameOverlay.create(guide)
    overlay.set_scene(scene_slug)  # also pre-generates this scene's narrator lines
    guide.prefetch("WAVE_START", scene_slug, {}, tone, count=1)
    guide.prefetch("VICTORY", scene_slug, {}, tone, count=1)

    shared_inv = SharedInventory.load_or_create()

    # ------------------------------------------------------------- world setup
    assets = load_assets()

    all_sprites = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    turret_group = pygame.sprite.Group()
    bullet_group = pygame.sprite.Group()

    base = Base()
    base.x, base.y = width // 2, height // 2  # centre of the real screen

    player = Player(100, 100, assets["knight"])
    all_sprites.add(player)

    class EdgeWaveManager(WaveManager):
        """Spawns at the edges of the actual screen, not config's 800x600."""

        def get_random_edge_position(self):
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                return (random.randint(0, width), 0)
            if edge == "bottom":
                return (random.randint(0, width), height)
            if edge == "left":
                return (0, random.randint(0, height))
            return (width, random.randint(0, height))

    wave_manager = EdgeWaveManager(base, all_sprites, enemy_group, assets)

    player_resources = STARTING_RESOURCES

    # Cross-module payoff: py_city's keycard shorts the supply depot open
    if shared_inv.has("city_keycard"):
        player_resources += 50
        overlay.narrate(
            "That keycard opens more than transit gates. The quartermaster "
            "didn't ask questions. Fifty extra — spend them wisely."
        )

    font = pygame.font.SysFont(None, 24)
    big_font = pygame.font.SysFont(None, 60)

    def try_place_turret(pos):
        nonlocal player_resources
        if player_resources >= TURRET_COST:
            turret = Turret(pos[0], pos[1], assets["tower"], assets["fireball"])
            turret_group.add(turret)
            all_sprites.add(turret)
            player_resources -= TURRET_COST

    # ----------------------------------------------------------- local state
    paused = False
    level_completed = False
    game_over_timer = -1     # >= 0 once the base falls
    last_wave_count = 0
    warned_low_base = False
    idle_time = 0.0
    idle_warned = False

    # ------------------------------------------------------------- main loop
    running = True
    while running:
        clock.tick(FPS)
        dt = 1.0 / FPS

        events = overlay.handle_events(pygame.event.get())
        for event in events:
            if event.type == pygame.QUIT:
                publish(PlotEvent.QUIT_CLICK)
                running = False
            elif event.type == pygame.KEYDOWN:
                idle_time = 0.0
                idle_warned = False
                if event.key == pygame.K_ESCAPE:
                    publish(PlotEvent.ESC_PRESS)
                    paused = not paused
                elif event.key == pygame.K_e and not paused and game_over_timer < 0:
                    # Contract interact key: raise a turret where the knight stands
                    try_place_turret(player.rect.center)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                idle_time = 0.0
                idle_warned = False
                if not paused and game_over_timer < 0:
                    try_place_turret(event.pos)

        # ------------------------------------------------------------ update
        if not paused and game_over_timer < 0:
            keys = pygame.key.get_pressed()
            dx = ((keys[pygame.K_d] or keys[pygame.K_RIGHT]) -
                  (keys[pygame.K_a] or keys[pygame.K_LEFT])) * PLAYER_SPEED
            dy = ((keys[pygame.K_s] or keys[pygame.K_DOWN]) -
                  (keys[pygame.K_w] or keys[pygame.K_UP])) * PLAYER_SPEED
            player.rect.x = max(0, min(player.rect.x + dx, width - player.rect.width))
            player.rect.y = max(0, min(player.rect.y + dy, height - player.rect.height))

            # Waves stop coming once the target is reached — clear the last one
            if wave_manager.wave_count < TARGET_WAVES:
                wave_manager.update()
            if wave_manager.wave_count != last_wave_count:
                last_wave_count = wave_manager.wave_count
                if last_wave_count == 1:
                    overlay.narrate(
                        "Here they come. Ten waves stand between you and the "
                        "way out. The tower has seen worse odds... barely."
                    )
                elif last_wave_count in (5, TARGET_WAVES):
                    state = {"wave": last_wave_count, "of": TARGET_WAVES,
                             "base_health": base.current_health}
                    line = guide.gen_line("WAVE_START", scene_slug, state, tone)
                    guide.speak_async(line)
                    overlay.narrate(line)
                    guide.prefetch("WAVE_START", scene_slug, {}, tone, count=1)

            for turret in turret_group:
                turret.update(enemy_group, bullet_group)
            bullet_group.update()
            enemy_group.update()

            # Bullets vs enemies
            for bullet in bullet_group:
                hit_enemies = pygame.sprite.spritecollide(bullet, enemy_group, False)
                if hit_enemies:
                    for enemy in hit_enemies:
                        old_health = enemy.health
                        enemy.take_damage(bullet.damage)
                        if old_health > 0 and enemy.health <= 0:
                            player_resources += ENEMY_KILL_REWARD
                    bullet.kill()

            # The base groans under the assault
            if not warned_low_base and base.current_health <= base.max_health * 0.4:
                warned_low_base = True
                overlay.show_warning("THE TOWER IS FAILING")
                guide.prefetch("DEATH", scene_slug,
                               {"base_health": base.current_health}, tone, count=1)

            if base.is_destroyed():
                publish(PlotEvent.DEATH,
                        {"cause": "base_destroyed",
                         "wave": wave_manager.wave_count})
                overlay.narrate(
                    "And down it comes. Every tower falls eventually — yours "
                    "simply chose an audience."
                )
                game_over_timer = GAME_OVER_FRAMES

            # Victory: all target waves spawned and the field is clear
            if (not level_completed and not base.is_destroyed()
                    and wave_manager.wave_count >= TARGET_WAVES
                    and len(enemy_group) == 0):
                level_completed = True
                line = guide.gen_line(
                    "VICTORY", scene_slug,
                    {"waves": TARGET_WAVES,
                     "base_health": base.current_health}, tone)
                guide.speak_async(line)
                overlay.narrate(line)
                overlay.show_fourth_wall("OBJECTIVE RESOLVED: ten_waves_weathered")
                game_over_timer = GAME_OVER_FRAMES  # linger on the win briefly

            # Idle — the Guide dislikes being kept waiting
            idle_time += dt
            if idle_time > IDLE_SECONDS and not idle_warned:
                publish(PlotEvent.IDLE, {"seconds": idle_time})
                idle_warned = True

        elif game_over_timer >= 0:
            game_over_timer -= 1
            if game_over_timer <= 0:
                running = False

        # ------------------------------------------------------------ render
        screen.fill(BLACK)

        tile_img = assets.get("tile")
        if tile_img:
            tw = max(tile_img.get_width(), 1)
            th = max(tile_img.get_height(), 1)
            for y in range(0, height, max(th, TILE_SIZE)):
                for x in range(0, width, max(tw, TILE_SIZE)):
                    screen.blit(tile_img, (x, y))

        base.draw(screen)
        all_sprites.draw(screen)
        bullet_group.draw(screen)

        # HUD
        screen.blit(font.render(f"Resources: {player_resources}", True, WHITE),
                    (10, 10))
        screen.blit(font.render(
            f"Wave: {wave_manager.wave_count}/{TARGET_WAVES}", True, WHITE),
            (10, 34))
        screen.blit(font.render(
            f"Base: {base.current_health}/{base.max_health}", True, WHITE),
            (10, 58))
        hint = font.render(
            "WASD/arrows move | click or E: build turret (50) | ESC pause | I inventory",
            True, (170, 170, 170))
        screen.blit(hint, (10, height - 28))

        if game_over_timer >= 0:
            text = big_font.render(
                "VICTORY" if level_completed else "GAME OVER", True, WHITE)
            screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

        if paused:
            dim = pygame.Surface((width, height))
            dim.set_alpha(180)
            dim.fill((20, 20, 30))
            screen.blit(dim, (0, 0))
            text = big_font.render("PAUSED", True, (220, 220, 230))
            screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

        # Overlay last (narrator subtitles, notifications, shared inventory)
        overlay.update(dt)
        overlay.draw(screen)

        pygame.display.flip()

    # ------------------------------------------------------------- shutdown
    if level_completed:
        shared_inv.add(Item(
            id="tower_core",
            name="Tower Core",
            item_type="artifact",
            rarity="uncommon",
            source_module="tower_defense",
            description=("Still warm. It kept the tower standing through ten "
                         "waves; it hasn't noticed the tower is gone."),
            stackable=False,
        ))
    shared_inv.save()
    overlay.clear_all()
    return level_completed


# Standalone entry point for launcher (subprocess mode)
if __name__ == "__main__":
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Tower Defense - The Tutorial")
    clock = pygame.time.Clock()

    from game.guide_voice import Guide
    guide = Guide()

    completed = run(screen, clock, guide, "tower_defense", "uneasy")

    pygame.quit()

    from game.completion import STATUS_COMPLETED, STATUS_QUIT, write_result
    write_result("tower_defense", STATUS_COMPLETED if completed else STATUS_QUIT)
    sys.exit(0)
