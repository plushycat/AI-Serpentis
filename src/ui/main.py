import pygame
import os
import sys

# Initialize pygame
pygame.init()

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

# Load and prepare sound effects
try:
    pygame.mixer.init()
    music_on_icon = pygame.image.load("assets/images/music_on.png")
    music_off_icon = pygame.image.load("assets/images/music_off.png")
    music_on_icon = pygame.transform.scale(music_on_icon, (40, 40))
    music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))
    
    # Load and prepare background music
    pygame.mixer.music.load("assets/sounds/background-music.mp3")
    click_sound = pygame.mixer.Sound("assets/sounds/click.wav")
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
    
    # Initialize mixer anyway for potential future loads
    pygame.mixer.init()

# Import the home page to start the game
from src.ui.pages.home_page import home_page

if __name__ == "__main__":
    home_page()