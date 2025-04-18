import pygame
import json
import os
import random
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional

# Define color constants
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
BLUE_LIGHT = (100, 100, 255)
GREEN = (0, 255, 0)
GREEN_LIGHT = (100, 255, 100)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 255)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 105, 180)

@dataclass
class SnakeTheme:
    """A class to store snake appearance customization."""
    name: str
    head_color: Tuple[int, int, int]
    body_gradient: bool = True
    gradient_intensity: float = 10.0  # How quickly the gradient changes
    
    def get_segment_color(self, segment_index: int) -> Tuple[int, int, int]:
        """Calculate the color for a specific snake segment based on the gradient."""
        if not self.body_gradient:
            return self.head_color
            
        # Apply gradient effect
        factor = segment_index * self.gradient_intensity
        r = max(0, min(255, self.head_color[0] - factor))
        g = max(0, min(255, self.head_color[1] - factor))
        b = max(0, min(255, self.head_color[2] - factor))
        return (int(r), int(g), int(b))

@dataclass
class FoodTheme:
    """A class to store food appearance customization."""
    name: str
    color: Tuple[int, int, int]
    pulsate: bool = True
    random_colors: bool = False
    color_options: List[Tuple[int, int, int]] = None
    
    def __post_init__(self):
        if self.color_options is None:
            self.color_options = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, PINK]
    
    def get_food_color(self, frame_count: int) -> Tuple[int, int, int]:
        """Get the food color, potentially modified by pulsation."""
        if self.random_colors:
            # Using a pre-generated color or picking a new one
            return self.color
        
        if not self.pulsate:
            return self.color
            
        # Apply a pulsating effect based on the frame count
        pulse_factor = abs((frame_count % 60) - 30) / 30.0  # 0.0 to 1.0
        r = min(255, self.color[0] + int(pulse_factor * 55))
        g = min(255, self.color[1] + int(pulse_factor * 55))
        b = min(255, self.color[2] + int(pulse_factor * 55))
        return (r, g, b)
    
    def new_random_color(self) -> Tuple[int, int, int]:
        """Select a new random color for food."""
        if not self.random_colors:
            return self.color
        
        self.color = random.choice(self.color_options)
        return self.color

class GameCustomization:
    """Manages all customization settings for the game."""
    
    def __init__(self):
        self.config_file = "statics/customization.json"
        
        # Default snake themes
        self.snake_themes = {
            "classic": SnakeTheme("Classic Green", GREEN),
            "blue": SnakeTheme("Cool Blue", BLUE),
            "fire": SnakeTheme("Fire", (255, 100, 0), True, 15.0),
            "purple": SnakeTheme("Royal Purple", PURPLE),
            "rainbow": SnakeTheme("Rainbow", (255, 0, 0), True, 40.0),
            "neon": SnakeTheme("Neon", (0, 255, 255), True, 8.0),
        }
        
        # Default food themes
        self.food_themes = {
            "apple": FoodTheme("Red Apple", RED),
            "blueberry": FoodTheme("Blueberry", BLUE),
            "rainbow": FoodTheme("Rainbow", RED, True, True),
            "golden": FoodTheme("Golden", (255, 215, 0), True),
        }
        
        # Current selections
        self.current_snake_theme = "classic"
        self.current_food_theme = "apple"
        
        # Load saved settings if available
        self.load_settings()
    
    def load_settings(self):
        """Load customization settings from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.current_snake_theme = data.get("snake_theme", "classic")
                    self.current_food_theme = data.get("food_theme", "apple")
        except Exception as e:
            print(f"Error loading customization settings: {e}")
    
    def save_settings(self):
        """Save current customization settings to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({
                    "snake_theme": self.current_snake_theme,
                    "food_theme": self.current_food_theme
                }, f)
        except Exception as e:
            print(f"Error saving customization settings: {e}")
    
    def get_current_snake_theme(self) -> SnakeTheme:
        """Get the currently selected snake theme."""
        return self.snake_themes.get(self.current_snake_theme, self.snake_themes["classic"])
    
    def get_current_food_theme(self) -> FoodTheme:
        """Get the currently selected food theme."""
        return self.food_themes.get(self.current_food_theme, self.food_themes["apple"])
    
    def set_snake_theme(self, theme_key: str):
        """Set the current snake theme."""
        if theme_key in self.snake_themes:
            self.current_snake_theme = theme_key
            self.save_settings()
            return True
        return False
    
    def set_food_theme(self, theme_key: str):
        """Set the current food theme."""
        if theme_key in self.food_themes:
            self.current_food_theme = theme_key
            self.save_settings()
            return True
        return False

    def get_all_snake_themes(self) -> Dict[str, SnakeTheme]:
        """Get all available snake themes."""
        return self.snake_themes
    
    def get_all_food_themes(self) -> Dict[str, FoodTheme]:
        """Get all available food themes."""
        return self.food_themes

# Create a global instance for easy access
customization = GameCustomization()