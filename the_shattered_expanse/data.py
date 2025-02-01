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

def get_resource_data(resource_type):
    return RESOURCE_DATA.get(resource_type, {})

def get_equipment_data(equipment_type):
    return EQUIPMENT_DATA.get(equipment_type, {})
