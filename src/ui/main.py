import pygame
import os
import sys

# Initialize pygame first
pygame.init()

# Then initialize sound manager but DON'T play music yet
from src.utils.sound_manager import sound_manager
sound_manager.initialize()  # Just initialize, don't play yet

# Load fonts and other resources
try:
    # Initialize fonts
    title_font = pygame.font.Font("assets/fonts/game_over.ttf", 96)
    menu_font = pygame.font.Font("assets/fonts/game_over.ttf", 36)
    footer_font = pygame.font.Font("assets/fonts/game_over.ttf", 24)
except FileNotFoundError:
    print("Warning: Font files not found. Using system fonts.")
    title_font = pygame.font.SysFont("Arial", 96)
    menu_font = pygame.font.SysFont("Arial", 36)
    footer_font = pygame.font.SysFont("Arial", 24)

# Load and prepare UI icons only, not sounds (sound_manager handles audio)
try:
    music_on_icon = pygame.image.load("assets/images/music_on.png")
    music_off_icon = pygame.image.load("assets/images/music_off.png")
    music_on_icon = pygame.transform.scale(music_on_icon, (40, 40))
    music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))    
    music_loaded = True
except Exception as e:
    print(f"Warning: Resource files not found. {e}")
    # Create fallback icons
    music_on_icon = pygame.Surface((40, 40))
    music_off_icon = pygame.Surface((40, 40))
    music_on_icon.fill((0, 200, 0))  # Green
    music_off_icon.fill((200, 0, 0))  # Red
    
    # Create dummy sound objects
    click_sound = None
    music_loaded = False

# Let home_page handle playing the music once
from src.ui.pages.home_page import home_page

if __name__ == "__main__":
    home_page()