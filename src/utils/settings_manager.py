import os
import json
import datetime
import sys
import atexit
import pygame

# Singleton pattern for settings manager
class SettingsManager:
    _instance = None
    _initialized = False
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the settings manager"""
        # Skip if already initialized (singleton pattern)
        if SettingsManager._initialized:
            return
            
        # Get script directory
        self.script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_file = os.path.join(self.script_dir, "statics", "game_settings.json")
        self.customization_file = os.path.join(self.script_dir, "statics", "customization.json")
        
        # Default configuration values
        self.default_config = {
            "appearance": {
                "background_theme": "dark",
                "enhanced_effects": True
            },
            "gameplay": {
                "debug_mode": False,
                "player_position": "right",
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
        
        # Initialize state
        self._config = None
        self._customization = None
        
        # Load settings immediately
        self.load_all_settings()
        
        # Register exit handler
        atexit.register(self.save_all_settings)
        
        # Mark as initialized
        SettingsManager._initialized = True
        self._log("Settings Manager initialized")
    
    def _log(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SettingsManager: {message}")
    
    def load_all_settings(self):
        """Load all settings from files"""
        self._config = self.load_config()
        self._customization = self.load_customization()
        return True
    
    def load_config(self):
        """Load game configuration settings from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config if it doesn't exist
                default_config = self.default_config.copy()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                
                # Save default config
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                    
                return default_config
        except Exception as e:
            self._log(f"Error loading config: {e}")
            # Return copy of default config if there's an error
            return self.default_config.copy()
    
    def load_customization(self):
        """Load customization settings from file"""
        try:
            if os.path.exists(self.customization_file):
                with open(self.customization_file, 'r') as f:
                    return json.load(f)
            else:
                # Default customization
                default_customization = {
                    "snake_theme": "classic",
                    "food_theme": "apple"
                }
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.customization_file), exist_ok=True)
                
                # Save default
                with open(self.customization_file, 'w') as f:
                    json.dump(default_customization, f, indent=4)
                
                return default_customization
        except Exception as e:
            self._log(f"Error loading customization: {e}")
            return {"snake_theme": "classic", "food_theme": "apple"}
    
    def get_config(self):
        """Get the current configuration (refreshing if needed)"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def get_customization(self):
        """Get the current customization settings (refreshing if needed)"""
        if self._customization is None:
            self._customization = self.load_customization()
        return self._customization
    
    def save_config(self, config=None):
        """Save configuration to file with error handling and disk syncing"""
        try:
            # Use provided config or current config
            config_to_save = config if config is not None else self._config
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Write to file with pretty formatting
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            
            # Success
            self._log(f"Config saved successfully to {self.config_file}")
            return True
            
        except Exception as e:
            self._log(f"Error saving config: {e}")
            return False
    
    def save_customization(self):
        """Save customization settings to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.customization_file), exist_ok=True)
            
            # Write to file
            with open(self.customization_file, 'w') as f:
                json.dump(self._customization, f, indent=4)
            
            self._log(f"Customization settings saved to {self.customization_file}")
            return True
        except Exception as e:
            self._log(f"Error saving customization: {e}")
            return False
    
    def save_all_settings(self):
        """Save ALL settings before program exit"""
        self._log("Saving all settings before exit")
        all_settings_saved = True
        
        try:
            # 1. Update config from globals
            try:
                import src.ui.shared_globals as globals_module
                
                # Update appearance settings
                if "appearance" in self._config:
                    self._config["appearance"]["background_theme"] = globals_module.background_theme
                    self._config["appearance"]["enhanced_effects"] = globals_module.enhanced_effects
                    
                # Update gameplay settings
                if "gameplay" in self._config:
                    self._config["gameplay"]["debug_mode"] = globals_module.debug_mode
                    
                    # Save player position if available
                    if hasattr(globals_module, 'player_position'):
                        self._config["gameplay"]["player_position"] = globals_module.player_position
                
                self._log("Updated config from shared globals")
            except Exception as e:
                self._log(f"Error updating from globals: {e}")
                all_settings_saved = False
            
            # 2. Update audio settings from sound manager
            try:
                from src.utils.sound_manager import sound_manager
                
                if "audio" not in self._config:
                    self._config["audio"] = {}
                
                self._config["audio"]["music_on"] = sound_manager.music_on
                self._config["audio"]["sound_effects_on"] = sound_manager.sound_effects_on
                self._config["audio"]["click_sounds_on"] = sound_manager.click_sounds_on
                self._config["audio"]["master_volume"] = sound_manager.master_volume
                self._config["audio"]["music_volume"] = sound_manager.music_volume
                self._config["audio"]["sound_effects_volume"] = sound_manager.sound_effects_volume
                
                self._log("Updated audio settings from sound manager")
            except Exception as e:
                self._log(f"Error updating audio settings: {e}")
                all_settings_saved = False
            
            # 3. Update customization from customization manager
            try:
                from src.game.customization import customization
                
                self._customization["snake_theme"] = customization.current_snake_theme
                self._customization["food_theme"] = customization.current_food_theme
                
                self._log("Updated customization settings")
            except Exception as e:
                self._log(f"Error updating customization: {e}")
                all_settings_saved = False
            
            # 4. Save all configuration to disk
            config_saved = self.save_config()
            customization_saved = self.save_customization()
            
            all_settings_saved = all_settings_saved and config_saved and customization_saved
            
            # 5. Verify saved files exist
            if os.path.exists(self.config_file) and os.path.exists(self.customization_file):
                self._log(f"Verified settings files exist")
            else:
                self._log("WARNING: One or more settings files missing after save!")
                all_settings_saved = False
            
            return all_settings_saved
            
        except Exception as e:
            self._log(f"Error in save_all_settings: {e}")
            return False
    
    def get_setting(self, section, key, default=None):
        """Get a specific setting with fallback to default"""
        try:
            if section in self._config and key in self._config[section]:
                return self._config[section][key]
            return default
        except:
            return default
    
    def set_setting(self, section, key, value):
        """Set a specific setting and save immediately"""
        try:
            if section not in self._config:
                self._config[section] = {}
            
            self._config[section][key] = value
            self.save_config()
            return True
        except Exception as e:
            self._log(f"Error setting {section}.{key}: {e}")
            return False

# Create the singleton instance
settings_manager = SettingsManager.get_instance()

# Utility functions for external code to use
def get_config():
    """Get the current configuration"""
    return settings_manager.get_config()

def save_config(config=None):
    """Save configuration to file"""
    return settings_manager.save_config(config)

def get_setting(section, key, default=None):
    """Get a specific setting with fallback"""
    return settings_manager.get_setting(section, key, default)

def set_setting(section, key, value):
    """Set a specific setting and save"""
    return settings_manager.set_setting(section, key, value)

def save_all_settings():
    """Save all settings at once"""
    return settings_manager.save_all_settings()