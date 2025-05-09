import sys
import os
import pygame
import atexit
from src.ai.agent import Agent
from src.ai.model import Linear_QNet
from src.game.snake_game import SnakeGame
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization  # Import correctly here
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

# Define a comprehensive exit handler that saves ALL settings
def save_all_settings_on_exit():
    """Save ALL game settings before exit"""
    print("MAIN: Saving all settings before program exit")
    
    try:
        # 1. Save audio settings via sound manager
        from src.utils.sound_manager import sound_manager
        audio_result = sound_manager.save_settings()
        print(f"Audio settings save result: {audio_result}")
        
        # 2. Save appearance and gameplay settings
        from src.utils.config import load_config, save_config
        import src.ui.shared_globals as globals_module  # Import the module instead of specific variables
        
        config = load_config()
        
        # Update appearance settings with current values from the module
        if "appearance" in config:
            config["appearance"]["background_theme"] = globals_module.background_theme
            config["appearance"]["enhanced_effects"] = globals_module.enhanced_effects
            print(f"Appearance settings saved: theme={globals_module.background_theme}, effects={globals_module.enhanced_effects}")
        
        # Update gameplay settings with current values
        if "gameplay" in config:
            config["gameplay"]["debug_mode"] = globals_module.debug_mode
            
            # Also save player position if it exists in shared_globals
            if hasattr(globals_module, 'player_position'):
                config["gameplay"]["player_position"] = globals_module.player_position
                print(f"Player position saved: {globals_module.player_position}")
            
            # Save game speeds - don't modify if they're already in the config
            classic_speed = config["gameplay"].get("classic_speed", 10)
            fibonacci_speed = config["gameplay"].get("fibonacci_speed", 8)
            print(f"Game speeds saved: classic={classic_speed}, fibonacci={fibonacci_speed}")
        
        # Save the config to disk
        save_success = save_config(config)
        print(f"Config saved successfully: {save_success}")
        
        # 3. Save customization settings (snake and food themes)
        try:
            from src.game.customization import customization
            customization.save_settings()
            print("Customization settings saved successfully")
        except Exception as e:
            print(f"Error saving customization settings: {e}")
        
        return True
    except Exception as e:
        print(f"Error in save_all_settings_on_exit: {e}")
        return False

# Register our comprehensive exit handler
atexit.register(save_all_settings_on_exit)

# Now it's safe to import home_page
def main():
    try:
        # Import here to avoid circular imports
        from src.ui.pages.home_page import home_page
        from src.utils.sound_manager import sound_manager
        
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