# factions.py

class Factions:
    """
    Basic definitions for Shattered Expanse factions with territory & alliances.
    """
    def __init__(self):
        # store some territory bounds as placeholders
        self.faction_data = {
            "Automatons": {
                "description": "Rogue machines left by the Architects.",
                "allies": [],
                "enemies": ["Scavengers", "Cog Preachers"],
                "territory": [(1000, 1000, 500, 500)]  # x,y,w,h area
            },
            "Scavengers": {
                "description": "Nomadic freebooters seeking scrap.",
                "allies": [],
                "enemies": ["Automatons"],
                "territory": [(200, 200, 300, 300)]
            },
            "Cog Preachers": {
                "description": "Zealots worshiping ancient machinery.",
                "allies": [],
                "enemies": [],
                "territory": []
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
