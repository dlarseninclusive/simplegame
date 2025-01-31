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

def get_resource_data(resource_type):
    return RESOURCE_DATA.get(resource_type, {})
