import os
import json
import atexit

# Import shared globals instead of from home_page
from src.ui.shared_globals import (
    music_on, background_theme, debug_mode, enhanced_effects
)

# Import player position function
from src.game.player_vs_ai import get_player_position

# File paths
CONFIG_FILE = "statics/game_settings.json"

def get_default_config():
    """Return default configuration if none exists"""
    return {
        "appearance": {
            "background_theme": "dark",
            "enhanced_effects": True
        },
        "gameplay": {
            "player_position": "right",
            "debug_mode": False,
            "classic_speed": 10,  # Separate speed for Classic mode
            "fibonacci_speed": 8   # Separate speed for Fibonacci mode (slightly slower default)
        },
        "audio": {
            "music_on": True,
            "sound_effects_on": True,
            "click_sounds_on": True,
            "master_volume": 0.7,
            "music_volume": 0.5,
            "sound_effects_volume": 0.8
        }
    }

def load_config():
    """Load all game configuration settings from a single file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default config if it doesn't exist
            default_config = get_default_config()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            # Save default config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=4)
                
            return default_config
    except Exception as e:
        print(f"Error loading config: {e}")
        # Return basic default config if there's an error
        return get_default_config()

def save_config(config):
    """Save all game configuration settings to a single file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def save_all_settings():
    """Save all settings when program exits"""
    try:
        config = load_config()
        config["appearance"]["background_theme"] = background_theme
        config["appearance"]["enhanced_effects"] = enhanced_effects
        config["gameplay"]["debug_mode"] = debug_mode
        config["audio"]["music_on"] = music_on
        save_config(config)
        print("All settings saved successfully")
    except Exception as e:
        print(f"Error saving settings: {e}")

# Register the exit handler
atexit.register(save_all_settings)