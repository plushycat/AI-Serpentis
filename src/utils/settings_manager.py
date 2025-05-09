import os
import json
import pygame
from src.utils.config import load_config, save_config, CONFIG_FILE
from src.utils.sound_manager import sound_manager

def save_all_settings():
    """Save ALL game settings to disk at exit time"""
    print("SETTINGS_MANAGER: Saving all settings before exit")
    all_settings_saved = True
    
    try:
        # 1. Save audio settings through sound manager
        audio_result = sound_manager.save_settings()
        print(f"Audio settings save result: {audio_result}")
        all_settings_saved = all_settings_saved and audio_result
        
        # 2. Load current config to avoid overwriting other settings
        config = load_config()
        
        # 3. Update appearance settings
        try:
            from src.ui.shared_globals import background_theme, enhanced_effects, debug_mode
            
            if "appearance" in config:
                config["appearance"]["background_theme"] = background_theme
                config["appearance"]["enhanced_effects"] = enhanced_effects
                print(f"Appearance settings saved: theme={background_theme}, effects={enhanced_effects}")
        except Exception as e:
            print(f"Error saving appearance settings: {e}")
            all_settings_saved = False
            
        # 4. Update gameplay settings
        try:
            if "gameplay" in config:
                config["gameplay"]["debug_mode"] = debug_mode
                
                # Save player position
                try:
                    from src.game.player_vs_ai import get_player_position
                    position = get_player_position()
                    if position:
                        config["gameplay"]["player_position"] = position
                        print(f"Player position saved: {position}")
                except Exception as e:
                    print(f"Error saving player position: {e}")
                
                # Save game speeds
                try:
                    # These should already be in config if they were adjusted during gameplay
                    classic_speed = config["gameplay"].get("classic_speed", 10)
                    fibonacci_speed = config["gameplay"].get("fibonacci_speed", 8)
                    print(f"Game speeds saved: classic={classic_speed}, fibonacci={fibonacci_speed}")
                except Exception as e:
                    print(f"Error saving game speeds: {e}")
        except Exception as e:
            print(f"Error saving gameplay settings: {e}")
            all_settings_saved = False
        
        # 5. Save customization settings (snake & food themes)
        try:
            from src.game.customization import game_customization
            customization_result = game_customization.save_settings()
            print(f"Customization settings saved: {customization_result}")
        except Exception as e:
            print(f"Error saving customization settings: {e}")
            
        # 6. Save all config changes to disk
        config_result = save_config(config)
        print(f"Config file save result: {config_result}")
        all_settings_saved = all_settings_saved and config_result
        
        # 7. Verify the settings were actually written
        if os.path.exists(CONFIG_FILE):
            print(f"Config file exists and is {os.path.getsize(CONFIG_FILE)} bytes")
            with open(CONFIG_FILE, 'r') as f:
                verification = json.load(f)
                print(f"Config sections verified: {list(verification.keys())}")
        else:
            print("WARNING: Config file does not exist after save!")
            all_settings_saved = False
            
        return all_settings_saved
        
    except Exception as e:
        print(f"Error in save_all_settings: {e}")
        return False