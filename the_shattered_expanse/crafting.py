# crafting.py

class CraftingSystem:
    """
    Allows players to craft or upgrade items using resources.
    """
    def __init__(self):
        self.is_open = False
        # Example recipes: "Metal Plate" from 2 scrap, "Refined Water" from 1 water
        self.recipes = {
            "Metal Plate": {"scrap": 2},
            "Refined Water": {"water": 1},
            "Building Materials": {"scrap": 3},
            "Advanced Components": {"scrap": 2, "artifact": 1},
            "Power Core": {"artifact": 2},
            "Repair Kit": {"scrap": 1, "artifact": 1}
        }

    def open_crafting_menu(self, player):
        """
        In a real game, you'd open a GUI. For now, we just print to console.
        """
        self.is_open = True
        print("=== Crafting Menu ===")
        for recipe_name, cost in self.recipes.items():
            print(f"{recipe_name} => cost: {cost}")
        print("Type the name in console to craft (not fully implemented here).")

    def craft_item(self, player, item_name):
        """ 
        Actually craft the item if the player has enough resources.
        Then add to inventory or apply an effect.
        """
        if item_name not in self.recipes:
            print("Recipe not found.")
            return

        cost = self.recipes[item_name]
        if self.check_resources(player, cost):
            self.deduct_resources(player, cost)
            print(f"Crafted {item_name}!")
            # You could add the result to player's inventory
            # e.g. player.inventory[item_name] = player.inventory.get(item_name, 0) + 1
        else:
            print("Not enough resources to craft this.")

    def check_resources(self, player, cost_dict):
        for rtype, needed in cost_dict.items():
            if player.inventory.get(rtype, 0) < needed:
                return False
        return True

    def deduct_resources(self, player, cost_dict):
        for rtype, needed in cost_dict.items():
            player.inventory[rtype] -= needed
