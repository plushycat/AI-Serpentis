import sys
import os
import pygame
import atexit
from src.ai.agent import Agent
from src.ai.model import Linear_QNet
from src.game.snake_game import SnakeGame
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization
from src.ai.watch_fibonacci_ai import watch_ai as watch_fibonacci_ai
from src.ai.transfer_fibonacci_ai import finetune as train_fibonacci_ai
from src.utils.scores import load_high_scores, save_high_score, resort_all_high_scores

import pygame
import sys

# Initialize pygame first - before ANY imports
pygame.init()

# Import and initialize shared globals immediately
from src.ui.shared_globals import init_globals

# Initialize all shared resources
init_globals()

# Replace the exit handler with our new one
def save_all_settings_on_exit():
    """Save ALL game settings before exit"""
    print("MAIN: Saving all settings before program exit")
    
    try:
        # Use our new centralized settings manager
        from src.utils.settings_manager import save_all_settings
        result = save_all_settings()
        print(f"All settings saved: {result}")
        return result
    except Exception as e:
        print(f"Error in save_all_settings_on_exit: {e}")
        return False

# Register our comprehensive exit handler
atexit.register(save_all_settings_on_exit)

def main():
    try:
        # Import here to avoid circular imports
        from src.ui.pages.home_page import home_page
        from src.utils.sound_manager import sound_manager
        from src.utils.settings_manager import settings_manager
        
        # Make sure settings are loaded at startup
        settings_manager.load_all_settings()
        
        # Resort all high scores at startup to fix existing data
        resort_all_high_scores()
        
        # Add refresh settings call before starting the UI
        sound_manager.refresh_settings()
        
        home_page()
    except Exception as e:
        print(f"Error in main application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()