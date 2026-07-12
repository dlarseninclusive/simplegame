"""Village Horror (py_horror) — wrapped for The Tutorial.

Implements the wrapper scene contract:
    run(screen, clock, guide, scene_slug, tone) -> bool (completed)

Differences from the standalone game.py:
- Uses the provided screen/clock (no set_mode/pygame.quit/sys.exit)
- Game state is local to run() — safe to re-enter
- Events route through GameOverlay (narrator, subtitles, shared inventory on I)
- Controls follow the wrapper contract: WASD/arrows move, E enter/exit
  buildings (SPACE still works too), ENTER attack, left-click move-to,
  right-click magic missile, M minimap, ESC pause. The old I=instructions
  binding is gone (I opens the shared inventory; instructions live on Tab).
- Monsters now deal contact damage, so DEATH is actually reachable
- Scene changes, first coin, deaths, and the boss kill feed the live narrator
- Carrying the shattered_artifact from the Expanse sharpens your attacks
- Defeating the boss in the mansion completes the fragment and grants the
  faded_polaroid item
"""

import os
import random
import sys

# Sibling modules import by bare name regardless of CWD
HORROR_DIR = os.path.dirname(os.path.abspath(__file__))
if HORROR_DIR not in sys.path:
    sys.path.insert(0, HORROR_DIR)

import pygame

FPS = 60
IDLE_SECONDS = 45.0
CONTACT_DAMAGE = {"zombie": 8, "tracker": 5, "bat": 3, "Boss": 15}
HURT_COOLDOWN_FRAMES = 60  # i-frames after a hit


def run(screen, clock, guide, scene_slug, tone):
    """Run the wrapped Village Horror. Returns True if completed."""
    # Vendor imports are deferred: sprites.py calls convert_alpha() at import
    # time, which needs the display the wrapper has already created.
    import constants as C
    from entities import Player
    from environment import GraveyardScene, IndoorScene, MansionScene, Village

    from game.inventory import Item, SharedInventory
    from game.overlay import GameOverlay
    from game.plot_event_bus import PlotEvent, publish

    width, height = screen.get_size()

    overlay = GameOverlay.create(guide)
    overlay.set_scene(scene_slug)  # also pre-generates this scene's narrator lines
    guide.prefetch("PICKUP", scene_slug, {}, tone, count=1)
    guide.prefetch("BOSS_ENCOUNTER", scene_slug, {}, tone, count=1)

    shared_inv = SharedInventory.load_or_create()

    # ------------------------------------------------------------- world setup
    player = Player()
    village = Village()
    indoor_scenes = {b: IndoorScene(b) for b in village.buildings
                     if b is not village.mansion and b is not village.graveyard_entrance}
    mansion_scene = MansionScene(village.mansion)
    graveyard_scene = GraveyardScene()

    # Cross-module payoff: the Expanse artifact sharpens your strikes
    if shared_inv.has("shattered_artifact"):
        player.attack_damage += 10
        overlay.show_whisper("...the artifact remembers how things break...")

    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)

    # Rain / lightning shader state (village only)
    shader_surface = pygame.Surface((width, height))
    shader_surface.set_alpha(50)
    rain_drops = [(random.randint(0, width), random.randint(0, height))
                  for _ in range(100)]
    lightning_active = False
    lightning_start_time = 0
    lightning_duration = 0
    next_lightning_time = pygame.time.get_ticks() + random.randint(15000, 30000)

    # ----------------------------------------------------------- local state
    current_scene = "village"
    current_building = None
    near_entrance = False
    show_instructions = True
    show_minimap = False
    paused = False
    camera_x = camera_y = 0
    effects = pygame.sprite.Group()
    magic_missiles = pygame.sprite.Group()

    level_completed = False
    death_count = 0
    hurt_cooldown = 0
    first_coin = True
    mansion_narrated = False
    graveyard_narrated = False
    idle_time = 0.0
    idle_warned = False

    def scene_groups():
        """(monsters, coins) for the active scene."""
        if current_scene == "village":
            return village.monsters, village.coins
        if current_scene == "mansion":
            return mansion_scene.monsters, mansion_scene.coins
        if current_scene == "graveyard":
            return graveyard_scene.monsters, graveyard_scene.coins
        return indoor_scenes[current_building].monsters, indoor_scenes[current_building].coins

    def remove_monster(monster):
        nonlocal level_completed
        monsters, coins = scene_groups()
        monsters.remove(monster)
        dropped = monster.drop_coin()
        if dropped:
            coins.add(dropped)
        if getattr(monster, "monster_type", "") == "Boss":
            level_completed = True
            overlay.show_fourth_wall("OBJECTIVE RESOLVED: the_thing_in_the_mansion")
            overlay.narrate(
                "The master of the house is... vacated. Do help yourself to "
                "whatever it was guarding. It won't be needing it."
            )

    def try_enter_exit():
        nonlocal current_scene, current_building
        if current_scene == "village" and near_entrance:
            if current_building is village.mansion:
                current_scene = "mansion"
            elif current_building is village.graveyard_entrance:
                current_scene = "graveyard"
            else:
                current_scene = "indoor"
            player.rect.midbottom = (C.WIDTH // 2, C.HEIGHT - 50)
        elif current_scene in ("indoor", "mansion", "graveyard") and near_entrance:
            current_scene = "village"
            player.rect.center = current_building.entrance.center
            current_building = None

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
                elif event.key in (pygame.K_e, pygame.K_SPACE):
                    if not paused:
                        try_enter_exit()
                elif event.key == pygame.K_TAB:
                    # Instructions moved off I (reserved for shared inventory)
                    show_instructions = not show_instructions
                elif event.key == pygame.K_m:
                    show_minimap = not show_minimap
            elif event.type == pygame.MOUSEBUTTONDOWN and not paused:
                idle_time = 0.0
                idle_warned = False
                if event.button == 1:  # move to pointer
                    if current_scene == "village":
                        player.set_target((event.pos[0] + camera_x,
                                           event.pos[1] + camera_y))
                    else:
                        player.set_target(event.pos)
                elif event.button == 3:  # magic missile
                    if current_scene == "village":
                        target = (event.pos[0] + camera_x, event.pos[1] + camera_y)
                    else:
                        target = event.pos
                    missile = player.fire_magic_missile(target)
                    if missile:
                        magic_missiles.add(missile)

        # ------------------------------------------------------------ update
        if not paused:
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - \
                 (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - \
                 (keys[pygame.K_UP] or keys[pygame.K_w])

            monsters, coins = scene_groups()

            if current_scene == "village":
                player.move(dx, dy, village.buildings)
                village.update(player)
                # Near an entrance?
                near_entrance = False
                for building in village.buildings:
                    if building.entrance.colliderect(player.rect):
                        near_entrance = True
                        current_building = building
                        break
                if village.graveyard_entrance.entrance.colliderect(player.rect):
                    near_entrance = True
                    current_building = village.graveyard_entrance
            else:
                player.move(dx, dy, [])
                if current_scene == "mansion":
                    mansion_scene.update(player)
                    if not mansion_narrated:
                        mansion_narrated = True
                        line = guide.gen_line("BOSS_ENCOUNTER", scene_slug,
                                              {"place": "the mansion"}, tone)
                        guide.speak_async(line)
                        overlay.narrate(line)
                elif current_scene == "graveyard":
                    graveyard_scene.update(player)
                    if not graveyard_narrated:
                        graveyard_narrated = True
                        overlay.show_whisper("...twenty stones, and room for one more...")
                else:
                    indoor_scenes[current_building].update(player)
                # Near the exit?
                exit_rect = pygame.Rect(C.WIDTH // 2 - 20, C.HEIGHT - 20, 40, 20)
                near_entrance = exit_rect.colliderect(player.rect)

            if keys[pygame.K_RETURN]:
                player.attack(monsters)
                for monster in list(monsters):
                    if monster.health <= 0:
                        remove_monster(monster)

            # Coins
            collected = pygame.sprite.spritecollide(player, coins, True)
            for coin in collected:
                effects.add(player.collect_coin(coin))
                if first_coin:
                    first_coin = False
                    line = guide.gen_line("PICKUP", scene_slug,
                                          {"item": "a dead man's coin"}, tone)
                    guide.speak_async(line)

            # Magic missiles
            for missile in magic_missiles:
                hit = pygame.sprite.spritecollide(missile, monsters, False)
                for monster in hit:
                    monster.health -= missile.damage
                    if monster.health <= 0:
                        remove_monster(monster)
                    missile.kill()
                    break

            # Monsters hurt on contact (the standalone game forgot to)
            if hurt_cooldown > 0:
                hurt_cooldown -= 1
            else:
                for monster in monsters:
                    if player.rect.colliderect(monster.rect):
                        dmg = CONTACT_DAMAGE.get(
                            getattr(monster, "monster_type", ""), 5)
                        player.health -= dmg
                        hurt_cooldown = HURT_COOLDOWN_FRAMES
                        break

            # Death: the narrator notices, then the village takes you back
            if player.health <= 0:
                death_count += 1
                publish(PlotEvent.DEATH,
                        {"cause": current_scene, "count": death_count})
                player.health = player.max_health
                player.target_pos = None
                current_scene = "village"
                current_building = None
                player.rect.center = (C.MAP_WIDTH // 2, C.MAP_HEIGHT // 2)

            player.update()
            effects.update()
            magic_missiles.update()

            # Camera (village scrolls; interiors are fixed rooms)
            if current_scene == "village":
                camera_x = max(0, min(player.rect.centerx - width // 2,
                                      C.MAP_WIDTH - width))
                camera_y = max(0, min(player.rect.centery - height // 2,
                                      C.MAP_HEIGHT - height))
            else:
                camera_x = camera_y = 0
            player.camera_x = camera_x
            player.camera_y = camera_y

            # Idle — the Guide dislikes being kept waiting
            idle_time += dt
            if idle_time > IDLE_SECONDS and not idle_warned:
                publish(PlotEvent.IDLE, {"seconds": idle_time})
                idle_warned = True

            # Rain / lightning (village atmosphere)
            if current_scene == "village":
                for i, (rx, ry) in enumerate(rain_drops):
                    ry += 5
                    if ry > height:
                        ry = random.randint(-10, 0)
                        rx = random.randint(0, width)
                    rain_drops[i] = (rx, ry)
                now = pygame.time.get_ticks()
                if lightning_active:
                    if now - lightning_start_time >= lightning_duration:
                        lightning_active = False
                        next_lightning_time = now + random.randint(15000, 30000)
                elif now >= next_lightning_time:
                    lightning_active = True
                    lightning_start_time = now
                    lightning_duration = random.randint(250, 750)

        # ------------------------------------------------------------ render
        screen.fill(C.BLACK)
        if current_scene == "village":
            village.draw(screen, camera_x, camera_y)
            # rain shader
            shader_surface.fill((105, 128, 180))
            for rx, ry in rain_drops:
                pygame.draw.line(shader_surface, (200, 200, 200),
                                 (rx, ry), (rx, ry + 5))
            if lightning_active:
                flash = pygame.Surface((width, height))
                flash.fill((255, 255, 255))
                flash.set_alpha(100)
                screen.blit(flash, (0, 0))
            screen.blit(shader_surface, (0, 0),
                        special_flags=pygame.BLEND_RGBA_MULT)
            for building in village.buildings:
                dark = pygame.Surface((building.rect.width, building.rect.height))
                dark.fill((0, 0, 0))
                dark.set_alpha(100)
                screen.blit(dark, (building.rect.x - camera_x,
                                   building.rect.y - camera_y))
        elif current_scene == "mansion":
            mansion_scene.draw(screen, 0, 0)
        elif current_scene == "graveyard":
            graveyard_scene.draw(screen, 0, 0)
        else:
            indoor_scenes[current_building].draw(screen, 0, 0)

        # Player + health bar
        screen.blit(player.image, (player.rect.x - camera_x,
                                   player.rect.y - camera_y))
        player.draw_health_bar(screen, camera_x, camera_y)

        for effect in effects:
            screen.blit(effect.image, (effect.rect.x - camera_x,
                                       effect.rect.y - camera_y))
        for missile in magic_missiles:
            screen.blit(missile.image, (missile.rect.x - camera_x,
                                        missile.rect.y - camera_y))

        if near_entrance:
            text = font.render("Press E to enter/exit", True, C.YELLOW)
            screen.blit(text, (width // 2 - text.get_width() // 2, 20))

        coin_text = font.render(f"Coins: {player.coins}", True, C.YELLOW)
        screen.blit(coin_text, (10, 10))

        if show_instructions:
            lines = [
                "Village Horror:",
                "- WASD / arrows to move (or left-click to walk there)",
                "- Right-click to fire a magic missile",
                "- E near green rectangles to enter/exit buildings",
                "- ENTER to attack nearby monsters",
                "- Collect coins dropped by defeated monsters",
                "- Defeat the boss monster in the mansion",
                "- M minimap, Tab this help, I shared inventory, ESC pause",
            ]
            panel = pygame.Surface((width, height))
            panel.set_alpha(200)
            panel.fill(C.BLACK)
            screen.blit(panel, (0, 0))
            for i, line in enumerate(lines):
                screen.blit(small_font.render(line, True, C.WHITE),
                            (20, 20 + i * 30))

        if show_minimap:
            minimap_size = 150
            minimap = pygame.Surface((minimap_size, minimap_size))
            minimap.fill(C.BLACK)
            minimap.set_alpha(200)
            sx = minimap_size / C.MAP_WIDTH
            sy = minimap_size / C.MAP_HEIGHT
            for building in village.buildings:
                pygame.draw.rect(minimap, C.WHITE,
                                 (int(building.rect.x * sx), int(building.rect.y * sy),
                                  max(3, int(building.rect.width * sx)),
                                  max(3, int(building.rect.height * sy))))
            pygame.draw.rect(minimap, C.DARK_GREEN,
                             (int(village.graveyard_entrance.rect.x * sx),
                              int(village.graveyard_entrance.rect.y * sy), 5, 5))
            pygame.draw.circle(minimap, C.RED,
                               (int(player.rect.centerx * sx),
                                int(player.rect.centery * sy)), 2)
            screen.blit(minimap, (width - minimap_size - 10, 10))

        if paused:
            dim = pygame.Surface((width, height))
            dim.set_alpha(180)
            dim.fill((20, 20, 30))
            screen.blit(dim, (0, 0))
            pause_text = font.render("PAUSED", True, (220, 220, 230))
            screen.blit(pause_text,
                        pause_text.get_rect(center=(width // 2, height // 2 - 30)))
            hint = small_font.render("ESC to resume", True, (180, 180, 190))
            screen.blit(hint, hint.get_rect(center=(width // 2, height // 2 + 20)))

        # Overlay last (narrator subtitles, notifications, shared inventory)
        overlay.update(dt)
        overlay.draw(screen)

        pygame.display.flip()

    # ------------------------------------------------------------- shutdown
    if level_completed:
        shared_inv.add(Item(
            id="faded_polaroid",
            name="Faded Polaroid",
            item_type="quest",
            rarity="uncommon",
            source_module="py_horror",
            description=("A photograph of the mansion, taken from inside the "
                         "mansion, on a night no one was holding the camera."),
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
    pygame.display.set_caption("Village Horror - The Tutorial")
    clock = pygame.time.Clock()

    from game.guide_voice import Guide
    guide = Guide()

    completed = run(screen, clock, guide, "py_horror", "uneasy")

    pygame.quit()

    from game.completion import STATUS_COMPLETED, STATUS_QUIT, write_result
    write_result("py_horror", STATUS_COMPLETED if completed else STATUS_QUIT)
    sys.exit(0)
