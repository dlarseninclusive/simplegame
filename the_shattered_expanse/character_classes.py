
class CharacterClass:
    def __init__(self, name, base_health, base_attack):
        self.name = name
        self.base_health = base_health
        self.base_attack = base_attack

class Warrior(CharacterClass):
    def __init__(self):
        super().__init__("Warrior", 120, 15)
        self.special_ability = "Berserk"

class Mage(CharacterClass):
    def __init__(self):
        super().__init__("Mage", 80, 25)
        self.special_ability = "Fireball"

class Thief(CharacterClass):
    def __init__(self):
        super().__init__("Thief", 90, 10)
        self.special_ability = "Stealth"
