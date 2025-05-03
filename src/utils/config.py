import os
import json
import atexit
import sys

# Default configuration values - define them here instead of importing
DEFAULT_CONFIG = {
    "appearance": {
        "background_theme": "dark",
        "enhanced_effects": True
    },
    "gameplay": {
        "debug_mode": False,
        "player_position": "right",  # Simply set default here instead of importing
        "classic_speed": 10,
        "fibonacci_speed": 8,
        "game_speed": 10
    },
    "audio": {
        "music_on": True,
        "sound_effects_on": True,
        "click_sounds_on": True,
        "master_volume": 0.7,
        "music_volume": 0.5,
        "sound_effects_volume": 0.6
    }
}

# REMOVE THIS IMPORT to break the circular dependency
# from src.game.player_vs_ai import get_player_position

# File paths
CONFIG_FILE = "statics/game_settings.json"

def get_default_config():
    """Return default configuration if none exists"""
    return DEFAULT_CONFIG

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
    # Load the current config, don't try to reference global variables
    try:
        config = load_config()
        # No changes needed - just save the current config
        save_config(config)
        print("All settings saved successfully")
    except Exception as e:
        print(f"Error saving settings: {e}")

# Register the exit handler
atexit.register(save_all_settings)