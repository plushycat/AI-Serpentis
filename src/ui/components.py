import pygame
import math
import random

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 200, 0)
YELLOW = (255, 240, 60)
GOLD = (255, 215, 0)

# Import button colors and dark gradients from shared globals
from src.ui.shared_globals import (
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT,
    dark_gradients,
    get_asset_path
)

class Particle:
    """Background particle for visual effects"""
    def __init__(self):
        self.x = random.randint(0, 1280)
        self.y = random.randint(0, 720)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.2, 1.0)
        self.color = (random.randint(180, 255), random.randint(180, 255), 255)
        self.alpha = random.randint(30, 100)

    def update(self):
        self.y += self.speed
        if self.y > 720:
            self.y = 0
            self.x = random.randint(0, 1280)

    def draw(self, surface):
        # Create a surface with per-pixel alpha
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        
        # Draw a semi-transparent circle
        pygame.draw.circle(s, self.color + (self.alpha,), (self.size, self.size), self.size)
        surface.blit(s, (self.x, self.y))

def draw_smooth_gradient(screen, current_gradient=0, next_gradient=1, blend=0):
    """Draw a smooth gradient background"""
    height = screen.get_height()
    width = screen.get_width()
    
    # Get the current and next gradient colors
    current_top, current_bottom = dark_gradients[current_gradient]
    next_top, next_bottom = dark_gradients[next_gradient]
    
    # Blend between current and next gradient
    top_color = (
        int(current_top[0] * (1-blend) + next_top[0] * blend),
        int(current_top[1] * (1-blend) + next_top[1] * blend),
        int(current_top[2] * (1-blend) + next_top[2] * blend)
    )
    
    bottom_color = (
        int(current_bottom[0] * (1-blend) + next_bottom[0] * blend),
        int(current_bottom[1] * (1-blend) + next_bottom[1] * blend),
        int(current_bottom[2] * (1-blend) + next_bottom[2] * blend)
    )
    
    # Draw the gradient
    for y in range(height):
        # Calculate color at this line
        ratio = y / height
        line_color = (
            int(top_color[0] * (1-ratio) + bottom_color[0] * ratio),
            int(top_color[1] * (1-ratio) + bottom_color[1] * ratio),
            int(top_color[2] * (1-ratio) + bottom_color[2] * ratio)
        )
        pygame.draw.line(screen, line_color, (0, y), (width, y))

def glowing_text(screen, text, font, x, y, base_color, step):
    glow = abs(math.sin(step / 20)) * 180
    color = (
        min(255, base_color[0] + glow),
        min(255, base_color[1] + glow),
        min(255, base_color[2] + glow),
    )
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))


def draw_button(screen, rect, text, font, base_color, hover_color, mouse_pos):
    """Draw a button with hover effect"""
    is_hovered = rect.collidepoint(mouse_pos)
    color = hover_color if is_hovered else base_color
    
    pygame.draw.rect(screen, color, rect, border_radius=10)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    
    return is_hovered

def draw_fancy_button(screen, rect, text, font, base_color, hover_color, mouse_pos, step):
    """Draw a button with pulsing glow border effect when hovered"""
    hovered = draw_button(screen, rect, text, font, base_color, hover_color, mouse_pos)
    if hovered:
        glow_width = int(abs(math.sin(step / 15)) * 4) + 1
        glow_rect = rect.inflate(10, 10)
        pygame.draw.rect(screen, hover_color, glow_rect, glow_width, border_radius=12)
    return hovered

def draw_slider(screen, x, y, width, min_val, max_val, current_val):
    """Draw a slider control"""
    pygame.draw.line(screen, GRAY, (x, y), (x + width, y), 5)
    slider_pos = x + int((current_val - min_val) / (max_val - min_val) * width)
    pygame.draw.circle(screen, WHITE, (slider_pos, y), 10)
    return slider_pos