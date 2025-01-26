# File: main.py

import pygame
import sys

# Import your config constants
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, WHITE,
    STARTING_RESOURCES, TURRET_COST, ENEMY_KILL_REWARD,
    TILE_SIZE
)

# Load your asset loader (should include "tower", "knight", "fireball", etc.)
from assets import load_assets

# If using a tile-based level, import from level_map
# (Otherwise, you can skip this or just fill background differently)
from level_map import LEVEL_DATA

# Import your game classes
from player import Player
from base import Base
from wave_manager import WaveManager

# IMPORTANT: Your turret.py must accept a fireball image for bullet creation.
from turret import Turret

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower Defense with Fireball Projectiles")
    clock = pygame.time.Clock()

    # Load images
    ASSETS = load_assets()
    
    # Sprite Groups
    all_sprites = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    turret_group = pygame.sprite.Group()
    bullet_group = pygame.sprite.Group()

    # Create base and player
    base = Base()
    # Pass the knight image for the player sprite
    player = Player(100, 100, ASSETS["knight"])
    all_sprites.add(player)

    # Wave Manager (spawns enemies)
    wave_manager = WaveManager(base, all_sprites, enemy_group, ASSETS)

    # Player resources (for turret placement cost)
    player_resources = STARTING_RESOURCES

    running = True
    while running:
        clock.tick(FPS)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left-click => place turret if enough resources
                if player_resources >= TURRET_COST:
                    mx, my = pygame.mouse.get_pos()
                    # Pass both tower image & fireball image to the turret
                    turret = Turret(
                        mx,
                        my,
                        ASSETS["tower"],    # The tower sprite
                        ASSETS["fireball"]  # The bullet (fireball) sprite
                    )
                    turret_group.add(turret)
                    all_sprites.add(turret)
                    player_resources -= TURRET_COST

        # --- Update ---
        keys = pygame.key.get_pressed()
        player.update(keys)

        wave_manager.update()

        # Update turrets, bullets, and enemies
        for turret in turret_group:
            turret.update(enemy_group, bullet_group)
        bullet_group.update()
        enemy_group.update()

        # Check collisions between bullets and enemies
        for bullet in bullet_group:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemy_group, False)
            if hit_enemies:
                for enemy in hit_enemies:
                    old_health = enemy.health
                    enemy.take_damage(bullet.damage)
                    if old_health > 0 and enemy.health <= 0:
                        # Award resources for the kill
                        player_resources += ENEMY_KILL_REWARD
                bullet.kill()

        # --- Drawing ---
        screen.fill(BLACK)

        # 1) Draw tile-based background (if using a tile map)
        tile_img = ASSETS.get("tile", None)
        if tile_img:  # Only if you actually loaded a tile in assets.py
            for row_index, row in enumerate(LEVEL_DATA):
                for col_index, tile_id in enumerate(row):
                    # If you have multiple tile types, you might pick different images
                    x = col_index * TILE_SIZE
                    y = row_index * TILE_SIZE
                    screen.blit(tile_img, (x, y))

        # 2) Draw the base
        base.draw(screen)

        # 3) Draw all sprites (player, turrets, enemies, bullets)
        all_sprites.draw(screen)
        bullet_group.draw(screen)

        # Check if base is destroyed => game over
        if base.is_destroyed():
            draw_game_over(screen)
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
        else:
            # Draw resource count (top-left)
            draw_resource_count(screen, player_resources)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def draw_resource_count(surface, resources):
    font = pygame.font.SysFont(None, 24)
    text = font.render(f"Resources: {resources}", True, WHITE)
    surface.blit(text, (10, 10))


def draw_game_over(surface):
    font = pygame.font.SysFont(None, 60)
    text = font.render("GAME OVER", True, WHITE)
    rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    surface.blit(text, rect)


if __name__ == "__main__":
    main()
