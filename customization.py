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
LIME = (50, 205, 50)
GOLD = (255, 215, 0)
TEAL = (0, 128, 128)
MAGENTA = (255, 0, 255)

@dataclass
class SnakeTheme:
    """A class to store snake appearance customization."""
    name: str
    head_color: Tuple[int, int, int]
    tail_color: Tuple[int, int, int] = None  # Second color for gradient
    body_gradient: bool = True
    gradient_intensity: float = 1.0  # How quickly the gradient changes
    
    def __post_init__(self):
        # If no tail color is provided, default to a visible alternative
        if self.tail_color is None:
            # For dark colors, make the tail lighter
            if sum(self.head_color) < 380:  # Threshold for determining dark colors
                self.tail_color = tuple(min(255, c + 80) for c in self.head_color)
            # For light colors, make the tail darker
            else:
                self.tail_color = tuple(max(0, c - 80) for c in self.head_color)
    
    def get_segment_color(self, segment_index: int) -> Tuple[int, int, int]:
        """Calculate the color for a specific snake segment based on the gradient."""
        if not self.body_gradient:
            return self.head_color
            
        # Apply improved gradient effect between head and tail colors
        # Use sigmoid-like function for smoother transition
        segment_ratio = min(1.0, segment_index * self.gradient_intensity / 10)
        
        # Interpolate between head and tail color
        r = int(self.head_color[0] * (1 - segment_ratio) + self.tail_color[0] * segment_ratio)
        g = int(self.head_color[1] * (1 - segment_ratio) + self.tail_color[1] * segment_ratio)
        b = int(self.head_color[2] * (1 - segment_ratio) + self.tail_color[2] * segment_ratio)
        
        return (r, g, b)

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
            self.color_options = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, PINK, LIME, GOLD]
    
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
        
        # Enhanced snake themes with two-color gradients
        self.snake_themes = {
            "classic": SnakeTheme("Classic Green", GREEN, (0, 100, 0)),
            "blue": SnakeTheme("Cool Blue", (0, 100, 255), (0, 0, 150)),
            "fire": SnakeTheme("Fire", (255, 100, 0), (200, 0, 0)),
            "purple": SnakeTheme("Royal Purple", PURPLE, (100, 0, 100)),
            "neon": SnakeTheme("Neon", CYAN, (0, 150, 150)),
            "gold": SnakeTheme("Golden", GOLD, ORANGE),
            "lime": SnakeTheme("Lime", LIME, (0, 100, 0)),
            "tropical": SnakeTheme("Tropical", (0, 255, 200), TEAL),
            "rose": SnakeTheme("Rose", PINK, (150, 50, 100)),
            "sky": SnakeTheme("Sky Blue", (135, 206, 250), BLUE),
        }
        
        # Default food themes
        self.food_themes = {
            "apple": FoodTheme("Red Apple", RED),
            "blueberry": FoodTheme("Blueberry", BLUE),
            "rainbow": FoodTheme("Rainbow", RED, True, True),
            "golden": FoodTheme("Golden", GOLD, True),
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
        if self.current_snake_theme == "random":
            # Choose a random theme but not the random theme itself
            theme_keys = [k for k in self.snake_themes.keys() if k != "random"]
            return self.snake_themes[random.choice(theme_keys)]
        return self.snake_themes.get(self.current_snake_theme, self.snake_themes["classic"])
    
    def get_current_food_theme(self) -> FoodTheme:
        """Get the currently selected food theme."""
        return self.food_themes.get(self.current_food_theme, self.food_themes["apple"])
    
    def set_snake_theme(self, theme_key: str):
        """Set the current snake theme."""
        if theme_key in self.snake_themes or theme_key == "random":
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
        themes = self.snake_themes.copy()
        # Add the random theme option
        themes["random"] = SnakeTheme("Random", (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        return themes
    
    def get_all_food_themes(self) -> Dict[str, FoodTheme]:
        """Get all available food themes."""
        return self.food_themes

# Create a global instance for easy access
customization = GameCustomization()