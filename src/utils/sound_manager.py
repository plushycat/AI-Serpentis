import pygame
import os
import datetime
import json
from src.utils.config import load_config, save_config, CONFIG_FILE  # Import the path constant

class SoundManager:
    """Centralized sound management system for the game"""
    
    _instance = None
    _initialized = False
    _sounds = {}
    
    def __init__(self):
        """Initialize the sound manager singleton"""
        # Initialize these core attributes only once
        if not hasattr(self, 'sounds'):
            self.sounds = {}
            self.initialized = False
            self.config = None
            self.music_started = False
            
            # Set these as placeholders only - they will be overwritten by load_settings()
            self.music_on = None
            self.sound_effects_on = None
            self.click_sounds_on = None 
            self.master_volume = None
            self.music_volume = None
            self.sound_effects_volume = None

        # Return early if already fully initialized
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
        
        # IMPORTANT: Load settings from config FIRST - before any other operations
        # This ensures we have user preferences before applying them
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
        self.load_settings()  # Correct method name
    
    def load_settings(self):
        """Load sound settings from the unified config file"""
        try:
            # IMPORTANT: Load directly from config - don't rely on cached values
            config = load_config()
            
            # Always use values from config, with class defaults as fallback
            if "audio" in config:
                audio = config["audio"]
                self.music_on = audio.get("music_on", True)
                self.sound_effects_on = audio.get("sound_effects_on", True)
                self.click_sounds_on = audio.get("click_sounds_on", True)
                self.master_volume = audio.get("master_volume", 0.7)
                self.music_volume = audio.get("music_volume", 0.5)
                self.sound_effects_volume = audio.get("sound_effects_volume", 0.6)
                
                # Debug print to verify loading
                self._log(f"Loaded settings: master={self.master_volume:.2f}, music={self.music_volume:.2f}, sfx={self.sound_effects_volume:.2f}")
            else:
                # This else branch was incomplete - adding proper defaults here
                self._log("No audio section found in config, using defaults")
                self.music_on = True
                self.sound_effects_on = True
                self.click_sounds_on = True
                self.master_volume = 0.7
                self.music_volume = 0.5
                self.sound_effects_volume = 0.6
        except Exception as e:
            self._log(f"Error loading sound settings: {e}")
            # Still set defaults even on error
            self.music_on = True
            self.sound_effects_on = True
            self.click_sounds_on = True
            self.master_volume = 0.7
            self.music_volume = 0.5
            self.sound_effects_volume = 0.6
    
    def save_settings(self):
        """Save sound settings to the unified config file"""
        try:
            # Load current config using the shared config module
            config = load_config()
            
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
            
            # Save using the config module function
            save_success = save_config(config)
            if not save_success:
                self._log("ERROR: Failed to save config file")
                return False
                
            # Perform complete verification
            try:
                verification = load_config()
                if "audio" not in verification:
                    self._log("ERROR: Audio section missing from saved config")
                    return False
                    
                # Verify all audio settings, not just master volume
                audio = verification["audio"]
                all_match = (
                    audio.get("music_on") == self.music_on and
                    audio.get("sound_effects_on") == self.sound_effects_on and
                    audio.get("click_sounds_on") == self.click_sounds_on and
                    audio.get("master_volume") == self.master_volume and
                    audio.get("music_volume") == self.music_volume and
                    audio.get("sound_effects_volume") == self.sound_effects_volume
                )
                
                if all_match:
                    self._log("Sound settings saved and verified successfully")
                    return True
                else:
                    self._log("WARNING: Settings verification failed - values don't match")
                    return False
                    
            except Exception as e:
                self._log(f"Error verifying saved settings: {e}")
                return False
                
        except Exception as e:
            self._log(f"Error saving sound settings: {e}")
            return False
    
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
        # Use instance variables instead of reloading config
        if not self.sound_effects_on or sound_name not in self._sounds:
            return False
        
        try:
            # Apply current volume from instance variables
            effective_volume = self.master_volume * self.sound_effects_volume
            self._sounds[sound_name].set_volume(effective_volume)
            
            # Play the sound with current settings
            self._sounds[sound_name].play()
            return True
        except Exception as e:
            self._log(f"Error playing sound '{sound_name}': {e}")
            return False

    def play_click(self):
        """Play UI click sound if enabled"""
        # Use instance variables instead of reloading config
        if not self.click_sounds_on or "click" not in self._sounds:
            return False
        
        try:
            # Apply current volume from instance variables
            effective_volume = self.master_volume * self.sound_effects_volume
            self._sounds["click"].set_volume(effective_volume)
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
        
        # Use instance variable instead of reloading from disk
        if self.music_on:
            try:
                # Stop any currently playing music first
                pygame.mixer.music.stop()
                pygame.mixer.music.play(-1)  # Loop indefinitely
                self._log("Started playing background music")
            except Exception as e:
                self._log(f"Error playing music: {e}")
    
    def refresh_settings(self):
        """Reload settings from config and apply them"""
        self.load_settings()
        self.apply_settings()
        self._log("Sound settings refreshed from config")
    
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

def ensure_settings_saved():
    """Ensure all sound settings are properly saved before exit"""
    print("ENSURE_SETTINGS_SAVED called - saving sound settings before exit")
    result = sound_manager.save_settings()
    print(f"Save result: {result}")
    
    # Double-check that the settings were actually written
    try:
        from src.utils.config import CONFIG_FILE
        print(f"Config file location: {os.path.abspath(CONFIG_FILE)}")
        if os.path.exists(CONFIG_FILE):
            print(f"Config file exists and is {os.path.getsize(CONFIG_FILE)} bytes")
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if "audio" in config:
                    print("Audio settings in config file:", config["audio"])
                else:
                    print("No audio section in config file!")
        else:
            print("Config file does not exist!")
    except Exception as e:
        print(f"Error verifying config file: {e}")
    
    return result