RESOURCE_DATA = {
    "scrap": {
        "display_name": "Scrap Metal",
        "value": 1,
        "description": "Rusted metal bits for forging or trading."
    },
    "water": {
        "display_name": "Fresh Water",
        "value": 2,
        "thirst_recovery": 30,
        "description": "Essential for survival."
    },
    "food": {
        "display_name": "Dried Rations",
        "value": 3,
        "hunger_recovery": 20,
        "description": "Basic sustenance."
    },
    "artifact": {
        "display_name": "Ancient Artifact",
        "value": 10,
        "description": "Relic from the Architects."
    }
}

EQUIPMENT_DATA = {
    "rusty_sword": {
        "name": "Rusty Sword",
        "type": "weapon",
        "stats": {"damage_multiplier": 1.2},
        "description": "An old but serviceable blade"
    },
    "scrap_armor": {
        "name": "Scrap Metal Armor",
        "type": "chest",
        "stats": {"armor": 2},
        "description": "Crude but protective chest piece"
    },
    "leather_boots": {
        "name": "Leather Boots",
        "type": "feet",
        "stats": {"armor": 1, "speed": 1.1},
        "description": "Well-worn boots"
    },
    "metal_helmet": {
        "name": "Metal Helmet",
        "type": "head",
        "stats": {"armor": 1},
        "description": "Basic head protection"
    },
    "scrap_leggings": {
        "name": "Scrap Leggings",
        "type": "legs",
        "stats": {"armor": 1},
        "description": "Makeshift leg protection"
    },
    "wooden_shield": {
        "name": "Wooden Shield",
        "type": "offhand",
        "stats": {"armor": 1},
        "description": "Simple wooden shield"
    }
}

# Enemy loot tables and drop chances
ENEMY_LOOT_TABLE = {
    "warrior": [
        ("rusty_sword", 0.3),
        ("scrap_armor", 0.3),
        ("scrap", 0.8),
        ("food", 0.4),
        ("water", 0.4),
        ("artifact", 0.1)
    ],
    "scout": [
        ("leather_boots", 0.3),
        ("wooden_shield", 0.2),
        ("food", 0.6),
        ("water", 0.6),
        ("wood", 0.4)
    ],
    "scholar": [
        ("artifact", 0.4),
        ("food", 0.3),
        ("water", 0.3)
    ],
    "trader": [
        ("food", 0.8),
        ("water", 0.8),
        ("scrap", 0.6),
        ("artifact", 0.2)
    ],
    "priest": [
        ("artifact", 0.5),
        ("food", 0.4),
        ("water", 0.4)
    ]
}

def generate_loot(enemy_type):
    """Generate random loot based on enemy type"""
    import random
    from item import Item
    
    loot = []
    if enemy_type in ENEMY_LOOT_TABLE:
        for item_id, chance in ENEMY_LOOT_TABLE[enemy_type]:
            if random.random() < chance:
                if item_id in EQUIPMENT_DATA:
                    # Create equipment item
                    data = EQUIPMENT_DATA[item_id]
                    item = Item(
                        data["name"],
                        data["type"],
                        data["stats"]
                    )
                    loot.append((item, 1))
                else:
                    # Create resource item
                    loot.append((item_id, random.randint(1, 3)))
    return loot

def get_resource_data(resource_type):
    return RESOURCE_DATA.get(resource_type, {})

def get_equipment_data(equipment_type):
    return EQUIPMENT_DATA.get(equipment_type, {})
