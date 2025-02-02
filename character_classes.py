class CharacterClass:
    def __init__(self, name, base_health, base_attack, abilities=None):
        self.name = name
        self.base_health = base_health
        self.base_attack = base_attack
        self.abilities = abilities or []

class Warrior(CharacterClass):
    def __init__(self):
        super().__init__("Warrior", base_health=150, base_attack=20, abilities=["Slash", "Block"])

class Mage(CharacterClass):
    def __init__(self):
        super().__init__("Mage", base_health=100, base_attack=30, abilities=["Fireball", "Teleport"])

class Thief(CharacterClass):
    def __init__(self):
        super().__init__("Thief", base_health=80, base_attack=15, abilities=["Steal", "Backstab"])
