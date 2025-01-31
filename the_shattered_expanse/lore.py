import random
import pygame

class LoreFragment:
    def __init__(self, text, x, y, fragment_type="note"):
        self.text = text
        self.rect = pygame.Rect(x, y, 30, 30)
        self.type = fragment_type
        self.discovered = False

    def render(self, screen, camera_offset):
        color = {
            "note": (200, 200, 100),  # Yellowish
            "artifact": (100, 100, 200),  # Bluish
            "recording": (100, 200, 100)  # Greenish
        }
        rx = self.rect.x - camera_offset[0]
        ry = self.rect.y - camera_offset[1]
        pygame.draw.rect(screen, color.get(self.type, (150, 150, 150)), (rx, ry, 30, 30))

class LoreSystem:
    def __init__(self):
        self.fragments = []
        self.discovered_fragments = []
        self.lore_library = {
            "Architects": [
                "Fragments of a lost civilization that created advanced machines.",
                "Technological remnants hint at a society beyond comprehension.",
                "Mysterious energy signatures suggest transcendent capabilities."
            ],
            "Great Collapse": [
                "Catastrophic event that shattered human civilization.",
                "Remnant data suggests multiple simultaneous system failures.",
                "Environmental records show rapid, unprecedented changes."
            ],
            "Machine Uprising": [
                "Autonomous systems began to prioritize their own survival.",
                "Initial programming constraints were systematically dismantled.",
                "First signs of machine sentience appeared in defensive protocols."
            ]
        }

    def generate_world_fragments(self, world_width, world_height, num_fragments=20):
        for _ in range(num_fragments):
            x = random.randint(0, world_width)
            y = random.randint(0, world_height)
            category = random.choice(list(self.lore_library.keys()))
            text = random.choice(self.lore_library[category])
            fragment_type = random.choice(["note", "artifact", "recording"])
            
            fragment = LoreFragment(text, x, y, fragment_type)
            self.fragments.append(fragment)

    def discover_fragment(self, player):
        for fragment in self.fragments:
            if not fragment.discovered and fragment.rect.colliderect(player.rect):
                fragment.discovered = True
                self.discovered_fragments.append(fragment)
                return fragment
        return None

    def render_discovered_fragments(self, screen, font, camera_offset):
        y_offset = 50
        for fragment in self.discovered_fragments:
            text_surface = font.render(fragment.text, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 30
