# File: assets.py

import pygame

def load_assets():
    """
    Loads each sprite and applies a unique scale factor.
    Returns a dict called 'assets' with all scaled surfaces.
    """

    assets = {}

    # =====================
    # Example scale factors
    # =====================
    KNIGHT_SCALE       = 0.1  # The knight might be large, so scale down more
    TOWER_SCALE        = 0.05
    ATTACKER1_SCALE    = 0.5
    ATTACKER2_SCALE    = 0.5
    ATTACKER3_SCALE    = 0.5
    FIREBALL_SCALE     = 0.3  # Fireball might be super big originally, so heavily reduce
    TILE_SCALE         = 0.05  # Maybe the tile is already perfect size

    # ----------------------
    # 1) Load Knight
    # ----------------------
    knight_orig = pygame.image.load("sprites/knight.png").convert_alpha()
    w_knight, h_knight = knight_orig.get_size()
    knight_scaled = pygame.transform.scale(
        knight_orig,
        (int(w_knight * KNIGHT_SCALE), int(h_knight * KNIGHT_SCALE))
    )
    assets["knight"] = knight_scaled

    # ----------------------
    # 2) Load Tower
    # ----------------------
    tower_orig = pygame.image.load("sprites/tower.png").convert_alpha()
    w_tower, h_tower = tower_orig.get_size()
    tower_scaled = pygame.transform.scale(
        tower_orig,
        (int(w_tower * TOWER_SCALE), int(h_tower * TOWER_SCALE))
    )
    assets["tower"] = tower_scaled

    # ----------------------
    # 3) Load Attackers
    # ----------------------
    # Attacker1
    attacker1_orig = pygame.image.load("sprites/attacker1.png").convert_alpha()
    w_a1, h_a1 = attacker1_orig.get_size()
    attacker1_scaled = pygame.transform.scale(
        attacker1_orig,
        (int(w_a1 * ATTACKER1_SCALE), int(h_a1 * ATTACKER1_SCALE))
    )
    assets["attacker1"] = attacker1_scaled

    # Attacker2
    attacker2_orig = pygame.image.load("sprites/attacker2.png").convert_alpha()
    w_a2, h_a2 = attacker2_orig.get_size()
    attacker2_scaled = pygame.transform.scale(
        attacker2_orig,
        (int(w_a2 * ATTACKER2_SCALE), int(h_a2 * ATTACKER2_SCALE))
    )
    assets["attacker2"] = attacker2_scaled

    # Attacker3
    attacker3_orig = pygame.image.load("sprites/attacker3.png").convert_alpha()
    w_a3, h_a3 = attacker3_orig.get_size()
    attacker3_scaled = pygame.transform.scale(
        attacker3_orig,
        (int(w_a3 * ATTACKER3_SCALE), int(h_a3 * ATTACKER3_SCALE))
    )
    assets["attacker3"] = attacker3_scaled

    # ----------------------
    # 4) Load Fireball
    # ----------------------
    fireball_orig = pygame.image.load("sprites/fireball.png").convert_alpha()
    w_fb, h_fb = fireball_orig.get_size()
    fireball_scaled = pygame.transform.scale(
        fireball_orig,
        (int(w_fb * FIREBALL_SCALE), int(h_fb * FIREBALL_SCALE))
    )
    assets["fireball"] = fireball_scaled

    # ----------------------
    # 5) Load Tile
    # ----------------------
    tile_orig = pygame.image.load("sprites/tile.png").convert_alpha()
    w_tile, h_tile = tile_orig.get_size()
    tile_scaled = pygame.transform.scale(
        tile_orig,
        (int(w_tile * TILE_SCALE), int(h_tile * TILE_SCALE))
    )
    assets["tile"] = tile_scaled

    return assets
