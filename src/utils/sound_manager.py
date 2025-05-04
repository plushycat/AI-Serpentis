import pygame
import os
import datetime
import json
from src.utils.config import load_config, save_config

# File path for sound settings
CONFIG_FILE = "statics/game_settings.json"

class SoundManager:
    """Centralized sound management system for the game"""
    
    _instance = None
    _initialized = False
    _sounds = {}
    _config = None
    
    # Sound settings with defaults
    music_on = True
    sound_effects_on = True
    click_sounds_on = True
    master_volume = 0.7
    music_volume = 0.5
    sound_effects_volume = 0.6
    
    def __init__(self):
        """Initialize the sound manager singleton"""
        self.sounds = {}
        self.initialized = False
        self.config = None
        self.master_volume = 1.0
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        
        # Flag to track if music is already playing
        self.music_started = False

        if SoundManager._initialized:
            return
            
        self._log("Sound manager initializing...")
        
        # Ensure mixer is initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                self._log("Mixer initialized")
            except Exception as e:
                self._log(f"Error initializing mixer: {e}")
                return
        
        # Load settings from config file
        self.load_settings()
        
        # Load sound resources
        self._load_resources()
        
        # Override global click_sound - this is the crucial part for fixing click sounds
        self._patch_global_click_sound()
        
        # Apply settings to mixer
        self.apply_settings()
        
        SoundManager._initialized = True
        self._log("Sound manager initialized successfully")
    
    @classmethod
    def get_instance(cls):
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance
    
    def initialize(self):
        """Initialize the sound system - call this after pygame.init()"""
        if self.initialized:
            return  # Prevent double initialization
            
        self.initialized = True
        self._load_resources()
        self._load_config()
    
    def load_settings(self):
        """Load sound settings from the unified config file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Check if audio settings exist in the config
                    if "audio" in config:
                        audio = config["audio"]
                        self.music_on = audio.get("music_on", self.music_on)
                        self.sound_effects_on = audio.get("sound_effects_on", self.sound_effects_on)
                        self.click_sounds_on = audio.get("click_sounds_on", self.click_sounds_on)
                        self.master_volume = audio.get("master_volume", self.master_volume)
                        self.music_volume = audio.get("music_volume", self.music_volume)
                        self.sound_effects_volume = audio.get("sound_effects_volume", self.sound_effects_volume)
                    else:
                        self._log("No audio section found in config, using defaults")
        except Exception as e:
            self._log(f"Error loading sound settings: {e}")
    
    def save_settings(self):
        """Save sound settings to the unified config file"""
        try:
            # Load the current config first
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            
            # Update or create the audio section
            if "audio" not in config:
                config["audio"] = {}
                
            # Update sound settings
            config["audio"]["music_on"] = self.music_on
            config["audio"]["sound_effects_on"] = self.sound_effects_on
            config["audio"]["click_sounds_on"] = self.click_sounds_on
            config["audio"]["master_volume"] = self.master_volume
            config["audio"]["music_volume"] = self.music_volume
            config["audio"]["sound_effects_volume"] = self.sound_effects_volume
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            # Save the updated config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
                
            self._log("Sound settings saved successfully")
        except Exception as e:
            self._log(f"Error saving sound settings: {e}")
    
    def _load_resources(self):
        """Load all sound resources"""
        try:
            # Load background music
            bg_music_path = self._get_asset_path("assets/sounds/bg_music.mp3")
            if os.path.exists(bg_music_path):
                pygame.mixer.music.load(bg_music_path)
                self._log("Background music loaded")
            else:
                self._log(f"Warning: Music file not found at {bg_music_path}")
            
            # Load UI click sound
            click_sound_path = self._get_asset_path("assets/sounds/ui_click.mp3")
            if os.path.exists(click_sound_path):
                self._sounds["click"] = pygame.mixer.Sound(click_sound_path)
                self._log("Click sound loaded")
            else:
                self._log(f"Warning: Click sound file not found at {click_sound_path}")
            
            # Load game sounds
            self._load_game_sound("eat", "assets/sounds/eat-food.mp3")
            self._load_game_sound("game_over", "assets/sounds/game-over.mp3")
            self._load_game_sound("level_up", "assets/sounds/level_up.mp3")
            
            # Add these sounds for the countdown
            self._load_game_sound("countdown_tick", "assets/sounds/countdown.mp3")
            self._load_game_sound("pvai_begin", "assets/sounds/pvai_begin.mp3")
        except Exception as e:
            self._log(f"Error loading sound resources: {e}")
    
    def _patch_global_click_sound(self):
        """Replace the global click_sound with our managed version"""
        try:
            import src.ui.shared_globals
            
            # Create a proxy object that respects our settings
            class ClickSoundProxy:
                def __init__(self, manager):
                    self.manager = manager
                
                def play(self):
                    """Only play if click sounds are enabled"""
                    self.manager.play_click()
            
            # Apply the patch
            src.ui.shared_globals.click_sound = ClickSoundProxy(self)
            self._log("Successfully patched global click_sound")
        except Exception as e:
            self._log(f"Error patching global click_sound: {e}")
    
    def _load_game_sound(self, name, path):
        """Load a game sound effect"""
        full_path = self._get_asset_path(path)
        if os.path.exists(full_path):
            self._sounds[name] = pygame.mixer.Sound(full_path)
            self._log(f"Sound '{name}' loaded")
        else:
            self._log(f"Warning: Sound '{name}' file not found at {full_path}")
    
    def _get_asset_path(self, path):
        """Resolve asset path considering working directory variations"""
        # Try direct path first
        if os.path.exists(path):
            return path
            
        # Try from project root
        root_path = os.path.join(os.getcwd(), path)
        if os.path.exists(root_path):
            return root_path
            
        # Just return the original path, it will fail safely when used
        return path
    
    def apply_settings(self):
        """Apply current audio settings to pygame mixer"""
        try:
            # Apply music settings
            if self.music_on:
                effective_music_volume = self.master_volume * self.music_volume
                pygame.mixer.music.set_volume(effective_music_volume)
                
                # Start music if not already playing
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                self._log(f"Music enabled at volume {int(effective_music_volume*100)}%")
            else:
                pygame.mixer.music.stop()
                self._log("Music disabled")
            
            # Apply sound effect volumes
            effective_sfx_volume = self.master_volume * self.sound_effects_volume
            for sound in self._sounds.values():
                sound.set_volume(effective_sfx_volume)
            
            self._log(f"Sound effects volume set to {int(effective_sfx_volume*100)}%")
            return True
        except Exception as e:
            self._log(f"Error applying audio settings: {e}")
            return False
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_on = not self.music_on
        self.apply_settings()
        self.save_settings()
        return self.music_on
    
    def toggle_sound_effects(self):
        """Toggle sound effects on/off"""
        self.sound_effects_on = not self.sound_effects_on
        self.save_settings()
        return self.sound_effects_on
    
    def toggle_click_sounds(self):
        """Toggle UI click sounds on/off"""
        self.click_sounds_on = not self.click_sounds_on
        self.save_settings()
        return self.click_sounds_on
    
    def set_master_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
        self.apply_settings()
        self.save_settings()
        return self.master_volume
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        self.apply_settings()
        self.save_settings()
        return self.music_volume
    
    def set_sound_effects_volume(self, volume):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sound_effects_volume = max(0.0, min(1.0, volume))
        self.apply_settings()
        self.save_settings()
        return self.sound_effects_volume
    
    def play_sound(self, sound_name):
        """Play a sound effect if sound effects are enabled"""
        if not self.sound_effects_on or sound_name not in self._sounds:
            return False
        
        try:
            self._sounds[sound_name].play()
            return True
        except Exception as e:
            self._log(f"Error playing sound '{sound_name}': {e}")
            return False
    
    def play_click(self):
        """Play UI click sound if enabled"""
        if not self.click_sounds_on or "click" not in self._sounds:
            return False
        
        try:
            self._sounds["click"].play()
            return True
        except Exception as e:
            self._log(f"Error playing click sound: {e}")
            return False
    
    def play_music(self):
        """Play background music if enabled in settings"""
        if not self.initialized:
            return
            
        # Check if music is already playing to prevent double play
        if self.music_started:
            return
            
        # Set the flag to indicate we've started music
        self.music_started = True
        
        config = load_config()
        music_on = config.get("audio", {}).get("music_on", True)
        
        if music_on:
            try:
                # Stop any currently playing music first
                pygame.mixer.music.stop()
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except Exception as e:
                print(f"Error playing music: {e}")
    
    def _log(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] SoundManager: {message}")


# Initialize singleton instance
sound_manager = SoundManager.get_instance()

# Convenience functions
def play_click():
    """Play UI click sound if enabled"""
    return sound_manager.play_click()

def play_sound(sound_name):
    """Play a sound effect if sound effects are enabled"""
    return sound_manager.play_sound(sound_name)

def toggle_music():
    """Toggle music on/off"""
    return sound_manager.toggle_music()

def toggle_sound_effects():
    """Toggle sound effects on/off"""
    return sound_manager.toggle_sound_effects()

def toggle_click_sounds():
    """Toggle UI click sounds on/off"""
    return sound_manager.toggle_click_sounds()