from constants import *
from sprites import *
from base_classes import Entity

class Player(Entity):
    def __init__(self):
        super().__init__(MAP_WIDTH // 2, MAP_HEIGHT // 2, player_sprite, 3, 100)
        self.attack_cooldown = 0
        self.attack_range = 30
        self.attack_damage = 20
        self.coins = 0

    def move(self, dx, dy, buildings):
        new_x = self.rect.x + dx * self.speed
        new_y = self.rect.y + dy * self.speed

        new_x = max(0, min(new_x, MAP_WIDTH - self.rect.width))
        new_y = max(0, min(new_y, MAP_HEIGHT - self.rect.height))

        new_rect = self.rect.copy()
        new_rect.x = new_x
        new_rect.y = new_y

        for building in buildings:
            if new_rect.colliderect(building.rect) and not building.entrance.colliderect(new_rect):
                if dx > 0:
                    new_x = building.rect.left - self.rect.width
                elif dx < 0:
                    new_x = building.rect.right
                if dy > 0:
                    new_y = building.rect.top - self.rect.height
                elif dy < 0:
                    new_y = building.rect.bottom

        self.rect.x = new_x
        self.rect.y = new_y

    def collect_coin(self, coin):
        self.coins += 1
        print(f"Coin collected! Total coins: {self.coins}")

    def attack(self, monsters):
        if self.attack_cooldown == 0:
            for monster in monsters:
                if self.rect.colliderect(monster.rect):
                    monster.health -= self.attack_damage
                    print(f"Attacked {monster.__class__.__name__} for {self.attack_damage} damage")
            self.attack_cooldown = 30
        else:
            self.attack_cooldown -= 1