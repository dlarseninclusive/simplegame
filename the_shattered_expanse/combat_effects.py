import pygame
import random

class DamageNumber(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, color=(255, 0, 0)):
        super().__init__()
        self.font = pygame.font.Font(None, 24)
        self.original_y = y
        self.float_height = 30
        self.lifetime = 1.0  # seconds
        self.age = 0
        
        # Create the damage text
        self.image = self.font.render(str(int(damage)), True, color)
        self.rect = self.image.get_rect(center=(x, y))
        
        # Random horizontal offset
        self.offset_x = random.randint(-10, 10)
        self.rect.x += self.offset_x

    def update(self, dt):
        self.age += dt
        # Float upward
        progress = self.age / self.lifetime
        self.rect.y = self.original_y - (self.float_height * progress)
        
        # Fade out
        if progress >= 0.7:
            fade = 1.0 - ((progress - 0.7) / 0.3)
            self.image.set_alpha(int(255 * fade))
        
        return self.age < self.lifetime

class HitFlash(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255, 180), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 0.1  # seconds
        self.age = 0

    def update(self, dt):
        self.age += dt
        fade = 1.0 - (self.age / self.lifetime)
        self.image.set_alpha(int(180 * fade))
        return self.age < self.lifetime

class AttackAnimation:
    def __init__(self, attacker_rect, target_rect, weapon_sprite=None):
        self.start_pos = attacker_rect.center
        self.end_pos = target_rect.center
        self.progress = 0
        self.duration = 0.2  # seconds
        self.weapon_sprite = weapon_sprite
        
        # Calculate swing arc points
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        self.mid_point = (
            self.start_pos[0] + dx * 0.5 - dy * 0.2,
            self.start_pos[1] + dy * 0.5 + dx * 0.2
        )
    
    def update(self, dt):
        self.progress = min(1.0, self.progress + dt / self.duration)
        return self.progress < 1.0
    
    def draw(self, screen, camera_offset):
        if self.progress >= 1.0:
            return
            
        # Calculate current position along the arc
        t = self.progress
        # Quadratic bezier curve
        x = (1-t)**2 * self.start_pos[0] + 2*(1-t)*t * self.mid_point[0] + t**2 * self.end_pos[0]
        y = (1-t)**2 * self.start_pos[1] + 2*(1-t)*t * self.mid_point[1] + t**2 * self.end_pos[1]
        
        # Draw attack trail
        points = []
        for i in range(5):
            t_trail = max(0, t - i*0.05)
            x_trail = (1-t_trail)**2 * self.start_pos[0] + 2*(1-t_trail)*t_trail * self.mid_point[0] + t_trail**2 * self.end_pos[0]
            y_trail = (1-t_trail)**2 * self.start_pos[1] + 2*(1-t_trail)*t_trail * self.mid_point[1] + t_trail**2 * self.end_pos[1]
            points.append((x_trail, y_trail))
            
        if len(points) > 1:
            pygame.draw.lines(screen, (255, 255, 255), False, points, 2)
        
        # Draw weapon sprite if available
        if self.weapon_sprite:
            # Rotate and position weapon along attack arc
            rotated_weapon = pygame.transform.rotate(self.weapon_sprite, t * 180)
            weapon_rect = rotated_weapon.get_rect(center=(x, y))
            screen.blit(rotated_weapon, weapon_rect)
