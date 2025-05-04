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
        
        # Check if files exist before loading
        music_on_path = get_asset_path("assets/images/music_on.png")
        music_off_path = get_asset_path("assets/images/music_off.png")
        
        if os.path.exists(music_on_path) and os.path.exists(music_off_path):
            music_on_icon = pygame.image.load(music_on_path)
            music_off_icon = pygame.image.load(music_off_path)
            music_on_icon = pygame.transform.scale(music_on_icon, (40, 40))
            music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))
        else:
            # Create fallback icons
            print("Warning: Music icon images not found. Using fallback.")
            music_on_icon = pygame.Surface((40, 40))
            music_off_icon = pygame.Surface((40, 40))
            music_on_icon.fill((0, 200, 0))  # Green
            music_off_icon.fill((200, 0, 0))  # Red
        
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