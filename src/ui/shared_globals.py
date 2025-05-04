import pygame
import os
import sys
from src.utils.config import load_config, save_config

# Global function for late binding
def play_click():
    from src.utils.sound_manager import play_click as _play_click
    return _play_click()

# Function to handle paths consistently
def get_asset_path(relative_path):
    """Get absolute path to asset, works in development and in PyInstaller bundle"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Game variables
snake_color = (0, 255, 0)  # Default green
background_theme = "dark"
debug_mode = False
enhanced_effects = True
music_on = True
click_sound = None
music_loaded = False
music_on_icon = None
music_off_icon = None
help_icon = None
scores_icon = None
current_gradient = 0
next_gradient = 1
gradient_blend = 0.0

# Button gradient colors - moved from components.py
BUTTON_BASE_LEFT = (0, 241, 143)   # Left side of gradient 
BUTTON_BASE_RIGHT = (0, 161, 250)  # Right side of gradient
BUTTON_HOVER_LEFT = (50, 255, 170) # Lighter version for hover
BUTTON_HOVER_RIGHT = (50, 180, 255) # Lighter version for hover

# Dark mode gradients for background - moved from components.py
dark_gradients = [
    [(25, 25, 50), (15, 15, 35)],   # Deep blue
    [(30, 20, 50), (15, 10, 35)],   # Purple-ish
    [(20, 30, 50), (10, 15, 35)],   # Blue-green
    [(40, 20, 40), (20, 10, 30)]    # Burgundy
]

# Initialize these later
title_font = None
menu_font = None
footer_font = None
screen = None

def init_globals():
    """Initialize global variables that require pygame to be initialized"""
    global title_font, menu_font, footer_font, screen
    global music_on_icon, music_off_icon, click_sound, music_loaded
    global help_icon, scores_icon
    
    # Initialize screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")
    
    # Initialize fonts with proper error handling
    try:
        # Get absolute paths using the asset_path helper
        font_path = get_asset_path("assets/fonts/game_over.ttf")
        
        # MORE REASONABLE FONT SIZES (matches old_main.py)
        title_font = pygame.font.Font(font_path, 96)   # Back to original
        menu_font = pygame.font.Font(font_path, 48)    # Better size for menus
        footer_font = pygame.font.Font(font_path, 36)  # Better size for entries
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Font files not found: {e}. Using system fonts.")
        title_font = pygame.font.SysFont("Arial", 96)  # Back to original
        menu_font = pygame.font.SysFont("Arial", 48)   # Better size for menus
        footer_font = pygame.font.SysFont("Arial", 36) # Better size for entries
    
    # Load sound effects and assets with better error handling
    try:
        pygame.mixer.init()
        
        # Define target size for all icons
        ICON_SIZE = (52, 52)  # Larger size for better quality with high-res icons
        
        # Check if files exist before loading
        music_on_path = get_asset_path("assets/images/music_on.png")
        music_off_path = get_asset_path("assets/images/music_off.png")
        help_icon_path = get_asset_path("assets/images/help_icon.png")
        scores_icon_path = get_asset_path("assets/images/high_score.png")
        
        # Load and scale music icons
        if os.path.exists(music_on_path) and os.path.exists(music_off_path):
            music_on_icon = pygame.image.load(music_on_path)
            music_off_icon = pygame.image.load(music_off_path)
            # Scale directly to final size, skipping intermediate transformations
            music_on_icon = scale_preserving_aspect_ratio(music_on_icon, ICON_SIZE)
            music_off_icon = scale_preserving_aspect_ratio(music_off_icon, ICON_SIZE)
        else:
            # Create fallback icons
            print("Warning: Music icon images not found. Using fallback.")
            music_on_icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
            music_off_icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
            pygame.draw.circle(music_on_icon, (0, 200, 0), (ICON_SIZE[0]//2, ICON_SIZE[1]//2), ICON_SIZE[0]//2)
            pygame.draw.circle(music_off_icon, (200, 0, 0), (ICON_SIZE[0]//2, ICON_SIZE[1]//2), ICON_SIZE[0]//2)
        
        # Load and scale help and scores icons
        if os.path.exists(help_icon_path) and os.path.exists(scores_icon_path):
            help_icon = pygame.image.load(help_icon_path)
            scores_icon = pygame.image.load(scores_icon_path)
            # Scale directly to final size
            help_icon = scale_preserving_aspect_ratio(help_icon, ICON_SIZE)
            scores_icon = scale_preserving_aspect_ratio(scores_icon, ICON_SIZE)
        else:
            print("Warning: Help or scores icon images not found. Using fallback.")
            help_icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
            scores_icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
            # Draw circular fallbacks for better appearance
            pygame.draw.circle(help_icon, (0, 150, 250), (ICON_SIZE[0]//2, ICON_SIZE[1]//2), ICON_SIZE[0]//2)
            pygame.draw.circle(scores_icon, (250, 150, 0), (ICON_SIZE[0]//2, ICON_SIZE[1]//2), ICON_SIZE[0]//2)
            
            # Add "?" text to help icon
            temp_font = pygame.font.SysFont("Arial", ICON_SIZE[0]//2)
            text_surf = temp_font.render("?", True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(ICON_SIZE[0]//2, ICON_SIZE[1]//2))
            help_icon.blit(text_surf, text_rect)
        
        # Use sound_manager's proxy instead of direct sound
        class ClickSoundProxy:
            def play(self):
                play_click()
        
        click_sound = ClickSoundProxy()
            
        music_loaded = True
    except Exception as e:
        print(f"Warning: Resource files not found: {e}")
        # Create fallback icons
        music_on_icon = pygame.Surface((40, 40))
        music_off_icon = pygame.Surface((40, 40))
        music_on_icon.fill((0, 200, 0))  # Green
        music_off_icon.fill((200, 0, 0))  # Red
        
        help_icon = pygame.Surface((56, 56))
        scores_icon = pygame.Surface((56, 56))
        help_icon.fill((0, 150, 250))  # Blue for help
        scores_icon.fill((250, 150, 0))  # Orange for scores
        
        # Create dummy sound objects
        click_sound = None
        music_loaded = False
        
    # Always ensure mixer is initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    # Late-bind the sound manager
    from src.utils.sound_manager import sound_manager
    # Now safe to use sound_manager

def update_theme(theme):
    """Update the global theme variable"""
    global background_theme
    background_theme = theme
    print(f"Theme updated to: {theme}")  # Add logging to verify function execution

def scale_preserving_aspect_ratio(image, target_size):
    """
    Scale an image to fit within target_size while preserving aspect ratio.
    
    Args:
        image: The Pygame surface to scale
        target_size: Tuple of (width, height) - the maximum dimensions
        
    Returns:
        Scaled image centered within target size bounds
    """
    if image is None:
        return None
        
    # Get original dimensions
    orig_width, orig_height = image.get_size()
    
    # Calculate scaling factor to fit within target size
    scale_width = target_size[0] / orig_width
    scale_height = target_size[1] / orig_height
    scale_factor = min(scale_width, scale_height)
    
    # Calculate new dimensions
    new_width = int(orig_width * scale_factor)
    new_height = int(orig_height * scale_factor)
    
    # Scale the image
    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
    
    # Create a surface of the target size with transparency
    result_surface = pygame.Surface(target_size, pygame.SRCALPHA)
    
    # Calculate position to center the scaled image
    x_offset = (target_size[0] - new_width) // 2
    y_offset = (target_size[1] - new_height) // 2
    
    # Blit the scaled image onto the result surface
    result_surface.blit(scaled_image, (x_offset, y_offset))
    
    return result_surface