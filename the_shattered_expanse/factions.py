# factions.py

class Factions:
    """
    Detailed faction system with cities, territories, and complex interactions.
    """
    def __init__(self, world_width=4000, world_height=4000):
        # Spread cities across the map
        self.faction_data = {
            "Automatons": {
                "description": "Rogue machines left by the Architects.",
                "allies": [],
                "enemies": ["Scavengers", "Cog Preachers"],
                "city": {
                    "name": "Machine Nexus",
                    "location": (world_width - 300, world_height - 300),
                    "size": (250, 250),
                    "population": 500,
                    "defenses": "High-tech automated turrets"
                },
                "territory": [(world_width - 500, world_height - 500, 500, 500)]
            },
            "Scavengers": {
                "description": "Nomadic freebooters seeking scrap.",
                "allies": [],
                "enemies": ["Automatons"],
                "city": {
                    "name": "Rust Haven",
                    "location": (100, 100),
                    "size": (250, 250),
                    "population": 300,
                    "defenses": "Makeshift walls and traps"
                },
                "territory": [(0, 0, 500, 500)]
            },
            "Cog Preachers": {
                "description": "Zealots worshiping ancient machinery.",
                "allies": [],
                "enemies": [],
                "city": {
                    "name": "Sanctum of Gears",
                    "location": (world_width // 2 - 125, world_height // 2 - 125),
                    "size": (250, 250),
                    "population": 200,
                    "defenses": "Religious barriers and mechanical guardians"
                },
                "territory": [(world_width // 2 - 250, world_height // 2 - 250, 500, 500)]
            }
        }

    def check_territory(self, x, y):
        """
        Return which faction's territory (if any) the point (x,y) is in.
        """
        for fac, data in self.faction_data.items():
            for (tx, ty, tw, th) in data["territory"]:
                if tx <= x <= tx+tw and ty <= y <= ty+th:
                    return fac
        return None

    def is_allied(self, faction1, faction2):
        return faction2 in self.faction_data[faction1]["allies"]
