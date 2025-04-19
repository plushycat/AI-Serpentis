import pygame
import torch
import sys
import math
import os
import random
import json  
from src.ai.model import Linear_QNet
from src.game.snake_game import SnakeGame
from src.game.snake_ai import SnakeGameAI
from src.ai.agent import Agent
from src.game.player_vs_ai import get_player_position, save_player_position
from src.game.customization import customization
import datetime
from typing import Dict, List, Any, Tuple
import atexit

title_font = pygame.font.Font("assets/fonts/game_over.ttf", 96)
click_sound = pygame.mixer.Sound("assets/sounds/ui_click.mp3")
highscore_file = "data/stats/highscores.json"

# Define file paths as constants for better maintainability
CONFIG_FILE = "statics/game_settings.json"
HIGHSCORE_FILE = "data/stats/highscores.json"

# Function to load all game settings
def load_config():
    """Load all game configuration settings from a single file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default config settings
            default_config = {
                "appearance": {
                    "background_theme": "dark",
                    "enhanced_effects": True
                },
                "gameplay": {
                    "player_position": "left",
                    "debug_mode": False
                },
                "audio": {
                    "music_on": True
                }
            }
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            # Write default config to file
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    except Exception as e:
        print(f"Error loading config: {e}")
        # Return default config if there's an error
        return {
            "appearance": {"background_theme": "dark", "enhanced_effects": True},
            "gameplay": {"player_position": "left", "debug_mode": False},
            "audio": {"music_on": True}
        }

# Function to save all game settings
def save_config(config):
    """Save all game configuration settings to a single file"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# Enhanced high score functions
def load_high_scores():
    """Load high scores with history from file or create default if it doesn't exist"""
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                old_scores = json.load(f)
                
                # Check if this is the old format (directly storing integers)
                if isinstance(old_scores.get("classic"), int) or isinstance(old_scores.get("ai"), int):
                    print("Converting high scores from old format to new format...")
                    
                    # Convert old format to new format
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    new_scores = {
                        "classic": {
                            "scores": [old_scores.get("classic", 0)] if old_scores.get("classic", 0) > 0 else [],
                            "dates": [today] if old_scores.get("classic", 0) > 0 else []
                        },
                        "ai": {
                            "scores": [old_scores.get("ai", 0)] if old_scores.get("ai", 0) > 0 else [],
                            "dates": [today] if old_scores.get("ai", 0) > 0 else []
                        },
                        "vs": {
                            "player": {
                                "scores": [old_scores.get("vs", {}).get("player", 0)] if old_scores.get("vs", {}).get("player", 0) > 0 else [],
                                "dates": [today] if old_scores.get("vs", {}).get("player", 0) > 0 else []
                            },
                            "ai": {
                                "scores": [old_scores.get("vs", {}).get("ai", 0)] if old_scores.get("vs", {}).get("ai", 0) > 0 else [],
                                "dates": [today] if old_scores.get("vs", {}).get("ai", 0) > 0 else []
                            }
                        }
                    }
                    
                    # Save the new format back to the file
                    with open(HIGHSCORE_FILE, 'w') as f2:
                        json.dump(new_scores, f2, indent=2)
                    
                    return new_scores
                else:
                    # Already in new format
                    return old_scores
        else:
            # Create default new format
            high_scores = {
                "classic": {
                    "scores": [],
                    "dates": []
                },
                "ai": {
                    "scores": [],
                    "dates": []
                },
                "vs": {
                    "player": {
                        "scores": [],
                        "dates": []
                    },
                    "ai": {
                        "scores": [],
                        "dates": []
                    }
                }
            }
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
            
            # Create the file with default scores
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump(high_scores, f, indent=2)
            
            return high_scores
    except Exception as e:
        print(f"Error loading high scores: {e}")
        return {
            "classic": {"scores": [], "dates": []},
            "ai": {"scores": [], "dates": []},
            "vs": {"player": {"scores": [], "dates": []}, "ai": {"scores": [], "dates": []}}
        }

def save_high_score(mode, score):
    """Save high score with date to the high scores file"""
    try:
        high_scores = load_high_scores()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        is_new_high = False
        
        # Handle VS mode differently since it has nested structure
        if mode.startswith("vs."):
            # Extract the player type (player/ai) from the mode string
            _, player_type = mode.split(".")
            
            # Get the current scores and dates for this mode
            if "scores" not in high_scores["vs"][player_type]:
                high_scores["vs"][player_type]["scores"] = []
                high_scores["vs"][player_type]["dates"] = []
                
            scores = high_scores["vs"][player_type]["scores"]
            dates = high_scores["vs"][player_type]["dates"]
            
            # Insert the new score in the sorted position
            if not scores or score > scores[0]:
                is_new_high = True
                
            # Insert score in sorted order
            insert_index = 0
            while insert_index < len(scores) and score <= scores[insert_index]:
                insert_index += 1
                
            scores.insert(insert_index, score)
            dates.insert(insert_index, today)
            
            # Keep only the top 10 scores
            if len(scores) > 10:
                scores.pop()
                dates.pop()
                
            high_scores["vs"][player_type]["scores"] = scores
            high_scores["vs"][player_type]["dates"] = dates
        else:
            # Regular modes (classic, ai)
            if "scores" not in high_scores[mode]:
                high_scores[mode]["scores"] = []
                high_scores[mode]["dates"] = []
                
            scores = high_scores[mode]["scores"]
            dates = high_scores[mode]["dates"]
            
            # Check if this is a new high score
            if not scores or score > scores[0]:
                is_new_high = True
                
            # Insert score in sorted order (descending)
            insert_index = 0
            while insert_index < len(scores) and score <= scores[insert_index]:
                insert_index += 1
                
            scores.insert(insert_index, score)
            dates.insert(insert_index, today)
            
            # Keep only the top 10 scores
            if len(scores) > 10:
                scores.pop()
                dates.pop()
                
            high_scores[mode]["scores"] = scores
            high_scores[mode]["dates"] = dates
        
        # Save updated high scores
        os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(high_scores, f, indent=2)
        
        print(f"Successfully saved high score of {score} for mode {mode}")
        return is_new_high
    except Exception as e:
        print(f"Error saving high score: {e}")
        import traceback
        traceback.print_exc()
        return False

# Add this function to display high scores
def high_scores_page():
    global screen
    clock = pygame.time.Clock()
    
    # Load high scores
    high_scores = load_high_scores()
    
    # Prepare UI elements
    button_width = 300
    button_height = 60
    back_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, SCREEN_HEIGHT - 100, button_width, button_height)
    
    # Mode selection buttons - CHANGE: combine vs_player and vs_ai into one option
    mode_buttons = {
        "classic": pygame.Rect(220, 150, 280, 60),
        "ai": pygame.Rect(520, 150, 280, 60),
        "vs_mode": pygame.Rect(820, 150, 280, 60)  # Single Player vs AI tab
    }
    
    # Track current selected mode
    current_mode = "classic"
    
    # Animation step
    step = 0
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient()
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size("High Scores")[0]) // 2
        glowing_text(screen, "High Scores", title_font, title_x, 30, YELLOW, step)
        
        # Draw mode selection buttons
        for mode, rect in mode_buttons.items():
            # Determine display name based on the mode
            if mode == "classic":
                display_name = "Classic Mode"
            elif mode == "ai":
                display_name = "AI Mode"
            else:  # vs_mode
                display_name = "Player vs AI"
            
            # Highlight selected mode
            base_color = (60, 100, 200) if mode == current_mode else (50, 50, 80)
            hover_color = (100, 150, 250) if mode == current_mode else (80, 80, 120)
            
            draw_button(screen, rect, display_name, footer_font, base_color, hover_color, mouse_pos)
        
        # Draw scores for the current mode
        if (current_mode in ["classic", "ai"]):
            # Regular modes display unchanged
            scores = high_scores.get(current_mode, {}).get("scores", [])
            dates = high_scores.get(current_mode, {}).get("dates", [])
            
            # Draw scores in a nice format - unchanged for classic and AI modes
            header_y = 250
            pygame.draw.rect(screen, (30, 30, 60, 180), pygame.Rect(280, header_y-10, 720, 50), border_radius=10)
            
            # Headers
            rank_text = menu_font.render("Rank", True, (220, 220, 220))
            score_text = menu_font.render("Score", True, (220, 220, 220))
            date_text = menu_font.render("Date", True, (220, 220, 220))
            
            screen.blit(rank_text, (320, header_y))
            screen.blit(score_text, (550, header_y))
            screen.blit(date_text, (750, header_y))
            
            # Draw score entries
            entry_y = header_y + 70
            for i, (score, date) in enumerate(zip(scores, dates)):
                # Background for entry - alternating colors
                bg_color = (40, 40, 70, 180) if i % 2 == 0 else (30, 30, 60, 180)
                pygame.draw.rect(screen, bg_color, pygame.Rect(280, entry_y-5, 720, 40), border_radius=8)
                
                # Medal for top 3
                if i < 3:
                    medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                    pygame.draw.circle(screen, medal_colors[i], (290, entry_y + 15), 15)
                    
                    rank_text = footer_font.render(f"#{i+1}", True, (20, 20, 20))
                    rank_rect = rank_text.get_rect(center=(290, entry_y + 15))
                    screen.blit(rank_text, rank_rect)
                else:
                    rank_text = footer_font.render(f"#{i+1}", True, WHITE)
                    screen.blit(rank_text, (320 - rank_text.get_width()//2, entry_y))
                
                # Score and date
                score_text = footer_font.render(str(score), True, WHITE)
                date_text = footer_font.render(date, True, WHITE)
                
                screen.blit(score_text, (550, entry_y))
                screen.blit(date_text, (750, entry_y))
                
                entry_y += 45
        else:  # vs_mode - NEW UNIFIED DISPLAY
            # Get both player and AI scores
            player_scores = high_scores.get("vs", {}).get("player", {}).get("scores", [])
            player_dates = high_scores.get("vs", {}).get("player", {}).get("dates", [])
            ai_scores = high_scores.get("vs", {}).get("ai", {}).get("scores", [])
            ai_dates = high_scores.get("vs", {}).get("ai", {}).get("dates", [])
            
            # Prepare combined score array with tuples of (score, date, is_player)
            vs_matches = []
            for score, date in zip(player_scores, player_dates):
                vs_matches.append((score, date, True))  # True = Player score
                
            for score, date in zip(ai_scores, ai_dates):
                vs_matches.append((score, date, False))  # False = AI score
                
            # Sort all matches by score (descending)
            vs_matches.sort(key=lambda x: x[0], reverse=True)
            
            # Draw table header
            header_y = 250
            pygame.draw.rect(screen, (30, 30, 60, 180), pygame.Rect(200, header_y-10, 880, 50), border_radius=10)
            
            # Headers
            rank_text = menu_font.render("Rank", True, (220, 220, 220))
            winner_text = menu_font.render("Winner", True, (220, 220, 220))
            score_text = menu_font.render("Score", True, (220, 220, 220))
            date_text = menu_font.render("Date", True, (220, 220, 220))
            
            screen.blit(rank_text, (240, header_y))
            screen.blit(winner_text, (450, header_y))
            screen.blit(score_text, (650, header_y))
            screen.blit(date_text, (830, header_y))
            
            # Draw score entries
            entry_y = header_y + 70
            for i, (score, date, is_player) in enumerate(vs_matches[:10]):  # Show top 10 combined
                # Background for entry
                bg_color = (40, 40, 70, 180) if i % 2 == 0 else (30, 30, 60, 180)
                pygame.draw.rect(screen, bg_color, pygame.Rect(200, entry_y-5, 880, 40), border_radius=8)
                
                # Medal for top 3
                if i < 3:
                    medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                    pygame.draw.circle(screen, medal_colors[i], (240, entry_y + 15), 15)
                    
                    rank_text = footer_font.render(f"#{i+1}", True, (20, 20, 20))
                    rank_rect = rank_text.get_rect(center=(240, entry_y + 15))
                    screen.blit(rank_text, rank_rect)
                else:
                    rank_text = footer_font.render(f"#{i+1}", True, WHITE)
                    screen.blit(rank_text, (240 - rank_text.get_width()//2, entry_y))
                
                # Winner with distinctive colors
                winner_color = (50, 255, 50) if is_player else (50, 150, 255)  # Green for player, blue for AI
                winner_label = "PLAYER" if is_player else "AI"
                winner_text = footer_font.render(winner_label, True, winner_color)
                screen.blit(winner_text, (450, entry_y))
                
                # Score and date
                score_text = footer_font.render(str(score), True, WHITE)
                date_text = footer_font.render(date, True, WHITE)
                
                screen.blit(score_text, (650, entry_y))
                screen.blit(date_text, (830, entry_y))
                
                entry_y += 45
        
        # Show message if no scores
        if ((current_mode in ["classic", "ai"] and not scores) or 
            (current_mode == "vs_mode" and not vs_matches)):
            no_scores_text = menu_font.render("No scores recorded yet!", True, (200, 200, 200))
            screen.blit(no_scores_text, (SCREEN_WIDTH//2 - no_scores_text.get_width()//2, 350))
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back to Menu", menu_font, (100,100,100), (150,150,150), mouse_pos, step)
        
        pygame.display.update()
        
        # Handle events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Back button
                if back_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    return
                
                # Mode selection buttons
                for mode, rect in mode_buttons.items():
                    if rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_mode = mode
                        
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                if click_sound: click_sound.play()
                return
        
        step += 1
        clock.tick(30)

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Serpentis")

# Colors
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GREEN  = (0, 255,   0)
BLUE   = (0,   0, 255)
RED    = (255,   0,   0)
YELLOW = (255, 255,   0)
GRAY   = (200, 200, 200)

# Font loading with error handling
try:
    title_font  = pygame.font.Font("assets/fonts/game_over.ttf", 96)
    menu_font   = pygame.font.Font("assets/fonts/game_over.ttf", 48)
    footer_font = pygame.font.Font("assets/fonts/game_over.ttf", 36)
except FileNotFoundError:
    print("Warning: Font file not found. Using system fonts.")
    title_font  = pygame.font.SysFont("Arial", 96)
    menu_font   = pygame.font.SysFont("Arial", 48)
    footer_font = pygame.font.SysFont("Arial", 36)

# Load assets with error handling
try:
    # Load the click sound from the new location
    click_sound = pygame.mixer.Sound("assets/sounds/ui_click.mp3")
    eat_sound = pygame.mixer.Sound("assets/sounds/eat-food.mp3")
    pygame.mixer.music.load("assets/sounds/bg_music.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
except FileNotFoundError as e:
    print(f"Warning: Sound file not found: {e}")
    click_sound = None
    eat_sound = None

# Load icons
try:
    music_on_icon  = pygame.image.load("assets/images/music_on.png")
    music_off_icon = pygame.image.load("assets/images/music_off.png")
    music_on_icon  = pygame.transform.scale(music_on_icon,  (40, 40))
    music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))
except FileNotFoundError:
    print("Warning: Icon files not found.")
    music_on_icon  = pygame.Surface((40, 40)); music_on_icon.fill(GREEN)
    music_off_icon = pygame.Surface((40, 40)); music_off_icon.fill(RED)

# State variables
music_on         = True
game_speed       = 30
snake_color      = (100, 200, 100)
background_theme = "dark"
debug_mode       = False
enhanced_effects = True  # New global variable for level-up effects

# Dark gradient palettes
dark_gradients = [
    ((0,   0,  40), (10,  10,  70)),
    ((5,  10,  50), (30,   0, 100)),
    ((15,   0,  60), (40,   5,  90)),
    ((0,  20,  80), (25,  25,  60)),
]
current_gradient = 0
next_gradient    = 1
gradient_blend   = 0.0

# Draw a smooth, slowly blending dark gradient background
def draw_smooth_gradient():
    c1 = dark_gradients[current_gradient][0]
    c2 = dark_gradients[current_gradient][1]
    d1 = dark_gradients[next_gradient][0]
    d2 = dark_gradients[next_gradient][1]

    start = tuple(int((1 - gradient_blend) * c1[i] + gradient_blend * d1[i]) for i in range(3))
    end   = tuple(int((1 - gradient_blend) * c2[i] + gradient_blend * d2[i]) for i in range(3))

    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(start[0] * (1 - t) + end[0] * t)
        g = int(start[1] * (1 - t) + end[1] * t)
        b = int(start[2] * (1 - t) + end[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

# Particle for subtle moving background effect
class Particle:
    def __init__(self):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(0, SCREEN_HEIGHT)
        self.r = random.uniform(1, 3)
        self.speed = random.uniform(0.5, 1.5)
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.uniform(0, SCREEN_WIDTH)
    def draw(self):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(self.r))

# Glowing animated title text
def glowing_text(screen, text, font, x, y, base_color, step):
    glow = abs(math.sin(step / 20)) * 180
    color = (
        min(255, base_color[0] + glow),
        min(255, base_color[1] + glow),
        min(255, base_color[2] + glow),
    )
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

# Modern button with hover effect
def draw_button(screen, rect, text, font, base_color, hover_color, mouse_pos):
    is_hover = rect.collidepoint(mouse_pos)
    color = hover_color if is_hover else base_color
    pygame.draw.rect(screen, color, rect, border_radius=12)
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 30))
    screen.blit(shadow, rect.topleft)

    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return is_hover

# Fancy button adds pulsing border on hover
def draw_fancy_button(screen, rect, text, font, base_color, hover_color, mouse_pos, step):
    hovered = draw_button(screen, rect, text, font, base_color, hover_color, mouse_pos)
    if hovered:
        glow_width = int(abs(math.sin(step / 15)) * 4) + 1
        glow_rect  = rect.inflate(10, 10)
        pygame.draw.rect(screen, hover_color, glow_rect, glow_width, border_radius=12)
    return hovered

# Draw a slider for speed control
def draw_slider(screen, x, y, width, min_val, max_val, current_val):
    pygame.draw.line(screen, GRAY, (x, y), (x + width, y), 5)
    slider_pos = x + int((current_val - min_val) / (max_val - min_val) * width)
    pygame.draw.circle(screen, WHITE, (slider_pos, y), 10)
    return slider_pos

def home_page():
    global music_on, screen, current_gradient, next_gradient, gradient_blend, background_theme, debug_mode, enhanced_effects
    
    # Load config when entering the home page
    config = load_config()
    background_theme = config["appearance"]["background_theme"]
    enhanced_effects = config["appearance"]["enhanced_effects"]
    music_on = config["audio"]["music_on"]
    debug_mode = config["gameplay"]["debug_mode"]
    
    # Set music state based on config
    if music_on:
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()
    
    clock = pygame.time.Clock()
    
    # Button layout parameters
    button_width   = 300
    button_height  = 60
    button_spacing = 80
    total_height   = 5 * button_height + 4 * (button_spacing - button_height)
    start_y        = (SCREEN_HEIGHT - total_height) // 2
    
    buttons = {
        "Play Classic": pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y,                 button_width, button_height),
        "Watch AI": pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + button_spacing, button_width, button_height),
        "Player vs AI": pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + 2*button_spacing, button_width, button_height),
        "Settings": pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + 3*button_spacing, button_width, button_height),
        "Quit":     pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + 4*button_spacing, button_width, button_height),
    }
    
    # Add high scores button
    scores_button = pygame.Rect(20, 20, 180, 50)
    music_rect = pygame.Rect(SCREEN_WIDTH - 60, 20, 40, 40)
    
    # Initialize particles
    particles = [Particle() for _ in range(80)]
    step = 0

    # Button gradient colors
    BUTTON_BASE_LEFT = (0, 241, 143)  # #00F18F - Left side of gradient 
    BUTTON_BASE_RIGHT = (0, 161, 250)  # #00A1FA - Right side of gradient
    BUTTON_HOVER_LEFT = (50, 255, 170)  # Slightly lighter version for hover
    BUTTON_HOVER_RIGHT = (50, 180, 255)  # Slightly lighter version for hover

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background gradient
        draw_smooth_gradient()
        # Draw particles
        for p in particles:
            p.update()
            p.draw()
        
        # Draw glowing title (centered)
        title_text = "AI Serpentis"
        title_surface = title_font.render(title_text, True, YELLOW)
        title_x = (SCREEN_WIDTH - title_surface.get_width()) // 2
        glowing_text(screen, title_text, title_font, title_x, 80, YELLOW, step)
        
        # Draw high scores button
        scores_text = footer_font.render("High Scores", True, WHITE)
        pygame.draw.rect(screen, (50, 80, 150), scores_button, border_radius=8)
        # Add trophy icon or glow effect to make it more visible
        glow_width = int(abs(math.sin(step / 15)) * 3) + 1
        pygame.draw.rect(screen, (100, 150, 250), scores_button, glow_width, border_radius=8)
        screen.blit(scores_text, (scores_button.x + 10, scores_button.y + 12))
        
        # Draw fancy buttons
        for name, rect in buttons.items():
            # Create gradient button surfaces
            is_hovered = rect.collidepoint(mouse_pos)
            
            # Choose gradient colors based on hover state
            left_color = BUTTON_HOVER_LEFT if is_hovered else BUTTON_BASE_LEFT
            right_color = BUTTON_HOVER_RIGHT if is_hovered else BUTTON_BASE_RIGHT
            
            # Create button surface with gradient
            button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            
            # Draw horizontal gradient
            for x in range(rect.width):
                ratio = x / rect.width
                r = int(left_color[0] * (1 - ratio) + right_color[0] * ratio)
                g = int(left_color[1] * (1 - ratio) + right_color[1] * ratio)
                b = int(left_color[2] * (1 - ratio) + right_color[2] * ratio)
                pygame.draw.line(button_surface, (r, g, b), (x, 0), (x, rect.height))
            
            # Apply rounded corners using a mask
            rounded_rect = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(rounded_rect, (255, 255, 255), (0, 0, rect.width, rect.height), border_radius=12)
            button_surface.blit(rounded_rect, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Add a slight shadow for depth
            shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 30))
            shadow_rect = shadow.get_rect(topleft=(rect.x + 2, rect.y + 2))
            screen.blit(shadow, shadow_rect)
            
            # Draw the gradient button
            screen.blit(button_surface, rect)
            
            # Add pulsing glow effect when hovered
            if is_hovered:
                glow_width = int(abs(math.sin(step / 15)) * 4) + 1
                glow_rect = rect.inflate(10, 10)
                # Use a gradient for the glow as well
                pygame.draw.rect(screen, BUTTON_HOVER_RIGHT, glow_rect, glow_width, border_radius=12)
            
            # Add button text
            text_surface = menu_font.render(name, True, WHITE)
            text_rect = text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)
        
        # Music toggle icon
        screen.blit(music_on_icon if music_on else music_off_icon, music_rect.topleft)
        
        # Draw footer (centered)
        footer_surf = footer_font.render("The Snake Game Reimagined v2.0", True, (200, 200, 200))
        footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        screen.blit(footer_surf, footer_rect)
        
        pygame.display.update()
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                # Save config before quitting
                config["audio"]["music_on"] = music_on
                save_config(config)
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = e.pos
                if buttons["Play Classic"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    play_classic_game()
                elif buttons["Watch AI"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    watch_ai_play()
                elif buttons["Player vs AI"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    from src.game.player_vs_ai import player_vs_ai
                    player_vs_ai()
                elif buttons["Settings"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    settings_page()
                elif buttons["Quit"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    # Save config before quitting
                    config["audio"]["music_on"] = music_on
                    save_config(config)
                    pygame.quit()
                    sys.exit()
                elif music_rect.collidepoint(pos):
                    if click_sound: click_sound.play()
                    music_on = not music_on
                    config["audio"]["music_on"] = music_on
                    if music_on:
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.stop()
                elif scores_button.collidepoint(pos):
                    if click_sound: click_sound.play()
                    high_scores_page()
        
        # Advance gradient blend very slowly
        gradient_blend += 0.0001
        if gradient_blend >= 1.0:
            gradient_blend   = 0.0
            current_gradient = next_gradient
            next_gradient    = (next_gradient + 1) % len(dark_gradients)
        
        step += 1
        clock.tick(30)

def play_classic_game():
    global snake_color, background_theme, screen, game_speed, enhanced_effects
    
    # Initialize game with customized settings
    game = SnakeGame()
    
    # Apply the enhanced effects setting
    game.enhanced_effects = enhanced_effects
    
    # Load high scores 
    high_scores = load_high_scores()
    
    # Handle new format correctly
    if isinstance(high_scores.get("classic"), dict):
        classic_scores = high_scores.get("classic", {}).get("scores", [])
        classic_high_score = max(classic_scores) if classic_scores else 0
    else:
        # Legacy format fallback
        classic_high_score = high_scores.get("classic", 0)
    
    # Initialize game with customized settings
    game = SnakeGame()
    
    # Initialize with current customization settings
    # If using random theme, the snake theme is freshly chosen each game
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)  # Use the theme setter method
    
    # For compatibility with older code
    game.snake_color = game.snake_theme.head_color
    
    while True:
        over, score = game.play_step()
        if over:
            print(f"Game Over! Your Score: {score}")
            
            # Check if this is a new high score
            is_new_high = save_high_score("classic", score)
            
            # Show game over screen
            try:
                font_large = pygame.font.Font("assets/fonts/game_over.ttf", 72)
                font_small = pygame.font.Font("assets/fonts/game_over.ttf", 36)
                font_medal = pygame.font.Font("assets/fonts/game_over.ttf", 48)  # Font for high score celebration
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.font.SysFont("Arial", 72)
                font_small = pygame.font.SysFont("Arial", 36)
                font_medal = pygame.font.SysFont("Arial", 48)
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))
            score_text = font_small.render(f"Your Score: {score}", True, WHITE)
            high_score_text = font_small.render(f"High Score: {max(classic_high_score, score)}", True, YELLOW)
            continue_text = font_small.render("Press any key to continue", True, (200, 200, 200))
            
            # Prepare new high score celebration if applicable
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, (255, 215, 0))  # Gold color
                
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 100))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2))
            high_score_rect = high_score_text.get_rect(center=(game.width//2, game.height//2 + 50))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 150))
            
            if is_new_high:
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 100))
            
            # Create dark overlay
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(high_score_text, high_score_rect)
            if is_new_high:
                game.display.blit(new_record_text, new_record_rect)
            game.display.blit(continue_text, continue_rect)
            pygame.display.update()
            
            # Wait for key press
            waiting = True
            animation_step = 0
            clock = pygame.time.Clock()
            while waiting:
                animation_step += 1
                
                # Animate high score text if it's a new record
                if is_new_high and animation_step % 10 == 0:
                    # Redraw just the high score with pulsing effect
                    overlay_rect = pygame.Rect(new_record_rect.left - 20, new_record_rect.top - 10, 
                                            new_record_rect.width + 40, new_record_rect.height + 20)
                    pygame.draw.rect(game.display, (0, 0, 0, 180), overlay_rect)
                    
                    # Pulsing effect using sine wave
                    pulse = abs(math.sin(animation_step / 10)) * 50
                    glow_color = (255, 215, 0 + pulse)  # Pulsing gold
                    new_record_text = font_medal.render("NEW HIGH SCORE!", True, glow_color)
                    game.display.blit(new_record_text, new_record_rect)
                    pygame.display.update(overlay_rect)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if click_sound: click_sound.play()
                        waiting = False
                clock.tick(30)
            break

    # Return to main menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def watch_ai_play():
    global snake_color, background_theme, screen, debug_mode, enhanced_effects
    model = Linear_QNet(11, 256, 3)
    
    # Try multiple model loading paths with better error handling
    try:
        # Look in different possible locations for the model
        model_paths = ["data/models/model.pth", "model_snapshots/model.pth", 
                        "data/checkpoints/checkpoint_model.pth"]
        model_loaded = False
        
        for path in model_paths:
            if os.path.exists(path):
                model.load_state_dict(torch.load(path))
                model_loaded = True
                print(f"Model loaded successfully from {path}")
                break
                
        if not model_loaded:
            print("Warning: No pre-trained model found. Using untrained model.")
        
        model.eval()  # Set model to evaluation mode
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Initialize game with customized settings
    game = SnakeGameAI(width=1280, height=720)
    
    # Apply the enhanced effects setting
    game.enhanced_effects = enhanced_effects
    
    # Get a fresh random theme if random is selected
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)
    
    # For compatibility
    game.snake_color = game.snake_theme.head_color
    
    # Get the historical record from the training data (READ ONLY)
    training_record = 0
    try:
        checkpoint_file = os.path.join("training_checkpoints", "training_state.json")
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                state = json.load(f)
                training_record = state.get('record', 0)
    except Exception as e:
        print(f"Error loading training record: {e}")
    
    # Load the AI gameplay high score (separate from training data)
    high_scores = load_high_scores()
    
    # Handle the new high score format properly
    ai_high_score = 0  # Default value
    if isinstance(high_scores.get("ai"), dict):
        # New format - scores are in an array
        ai_scores = high_scores.get("ai", {}).get("scores", [])
        ai_high_score = max(ai_scores) if ai_scores else 0
    else:
        # Old format (direct integer)
        ai_high_score = high_scores.get("ai", 0)
    
    # Use the higher of training record and AI high score for display
    display_record = max(training_record, ai_high_score)
    game.record = display_record  # Set the record to show
    
    game.viewing_mode = True  # Set a new flag to indicate viewer mode
    
    # Increase frame limit to prevent premature endings
    game.frame_limit_multiplier = 1000  # Very lenient frame limit for viewing
    game.debug_mode = debug_mode  # Pass debug mode to the game
    
    # Initialize agent with the model
    agent = Agent()
    agent.model = model
    agent.epsilon = 0  # No exploration, pure exploitation
    
    # Game loop
    while True:
        state = agent.get_state(game)
        move = agent.get_action(state)
        
        # Process the move
        reward, done, score = game.play_step(move)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    done = True  # Exit on escape key
                elif event.key == pygame.K_p:  # Pause
                    if click_sound: click_sound.play()
                    paused = True
                    
                    # Create appropriate overlay based on the theme
                    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
                    overlay_color = (0, 0, 0, 120) if game.background_theme == "dark" else (255, 255, 255, 120)
                    overlay.fill(overlay_color)
                    game.display.blit(overlay, (0, 0))
                    
                    # Use game's font and appropriate color for the theme
                    if game.background_theme == "dark":
                        pause_color = WHITE
                    else:
                        pause_color = (20, 20, 100)  # Dark blue
                    
                    pause_text = game.sub_font.render('PAUSED - Press P to continue', True, pause_color)
                    game.display.blit(pause_text, (game.width//2 - pause_text.get_width()//2, game.height//2))
                    pygame.display.update()
                    
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_p:
                                paused = False
                            elif pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_ESCAPE:
                                done = True
                                paused = False
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                        pygame.time.wait(100)
        
        if done:
            print(f"AI Game Over! Final Score: {score}")
            
            # Save the score regardless of whether it's the highest
            # The save_high_score function will handle sorting and keeping top 10
            is_new_high = save_high_score("ai", score)
            
            # Update ai_high_score if this is higher
            if score > ai_high_score:
                ai_high_score = score
            
            # Show game over screen with score
            try:
                font_large = pygame.font.Font("assets/fonts/game_over.ttf", 72)
                font_small = pygame.font.Font("assets/fonts/game_over.ttf", 36)
                font_medal = pygame.font.Font("assets/fonts/game_over.ttf", 48)  # For high score celebration
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.font.SysFont("Arial", 72)
                font_small = pygame.font.SysFont("Arial", 36)
                font_medal = pygame.font.SysFont("Arial", 48)
            
            # Dynamic colors based on theme
            if game.background_theme == "dark":
                text_color = WHITE
                secondary_color = (200, 200, 200)
            else:
                text_color = (20, 20, 100)  # Dark blue
                secondary_color = (80, 80, 80)  # Dark gray
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"AI Score: {score}", True, text_color)
            
            # Use the updated ai_high_score for display
            best_record = max(training_record, ai_high_score)
            record_text = font_small.render(f"Record: {best_record}", True, text_color)
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 80))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2))
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 50))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 120))
            
            # Create appropriate overlay for the current theme
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(record_text, record_rect)
            
            # Add celebration if this is a new viewer high score
            if is_new_high:
                new_record_text = font_medal.render("NEW AI HIGH SCORE!", True, (255, 215, 0))  # Gold color
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 85))
                game.display.blit(new_record_text, new_record_rect)
            
            game.display.blit(continue_text, continue_rect)
            pygame.display.update()
            
            # Wait for key press
            waiting = True
            animation_step = 0
            while waiting:
                animation_step += 1
                
                # Animate high score text if it's a new record
                if is_new_high and animation_step % 10 == 0:
                    # Redraw just the high score with pulsing effect
                    overlay_rect = pygame.Rect(new_record_rect.left - 20, new_record_rect.top - 10, 
                                            new_record_rect.width + 40, new_record_rect.height + 20)
                    pygame.draw.rect(game.display, overlay_color[:3] + (180,), overlay_rect)
                    
                    # Pulsing effect using sine wave
                    pulse = abs(math.sin(animation_step / 10)) * 50
                    glow_color = (255, 215, 0 + pulse)  # Pulsing gold
                    new_record_text = font_medal.render("NEW VIEWER HIGH SCORE!", True, glow_color)
                    game.display.blit(new_record_text, new_record_rect)
                    pygame.display.update(overlay_rect)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if click_sound: click_sound.play()
                        waiting = False
                pygame.time.wait(100)
            break
    
    # Return to menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def settings_page():
    global snake_color, background_theme, screen, debug_mode, enhanced_effects
    
    # Load the current config at the start
    config_file = "statics/game_settings.json"
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Create default config if it doesn't exist
            config = {
                "appearance": {
                    "background_theme": background_theme,
                    "enhanced_effects": enhanced_effects
                },
                "gameplay": {
                    "player_position": get_player_position(),
                    "debug_mode": debug_mode
                },
                "audio": {
                    "music_on": music_on
                }
            }
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
    except:
        # Default config if there's an error
        config = {
            "appearance": {"background_theme": "dark", "enhanced_effects": True},
            "gameplay": {"player_position": "left", "debug_mode": False},
            "audio": {"music_on": True}
        }
    
    # Function to save settings immediately when they're changed
    def save_settings_immediately():
        # Update config with current settings
        config["appearance"]["background_theme"] = background_theme
        config["appearance"]["enhanced_effects"] = enhanced_effects
        config["gameplay"]["debug_mode"] = debug_mode
        config["gameplay"]["player_position"] = get_player_position()
        
        # Save to file
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    import math  # Add math import for ceil function
    
    clock = pygame.time.Clock()
    step = 0
    button_width = 300
    button_height = 60
    button_spacing = 80
    
    # Create a scroll area for all options
    scroll_y = 0
    scroll_velocity = 0  # For smoother scrolling
    max_scroll_y = 0
    
    # Keep track of current page (0 = general, 1 = snake themes, 2 = food themes)
    current_page = 0
    
    # Get all available themes
    snake_themes = customization.get_all_snake_themes()
    food_themes = customization.get_all_food_themes()
    
    # Create buttons for all pages
    general_button = pygame.Rect((SCREEN_WIDTH//2 - button_width*1.5)//1, 120, button_width, button_height)
    snake_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 120, button_width, button_height)
    food_button = pygame.Rect(SCREEN_WIDTH//2 + button_width//2, 120, button_width, button_height)
    
    # General page buttons (Theme buttons)
    dark_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 200, button_width, button_height)
    light_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 280, button_width, button_height)
    debug_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 360, button_width, button_height)
    vs_position_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 440, button_width, button_height)
    enhanced_effects_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 520, button_width, button_height)
    
    # Back button
    back_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, SCREEN_HEIGHT - 100, button_width, button_height)
    
    # Create theme preview rects
    preview_size = 180  
    preview_margin = 20 
    preview_cols = 3
    preview_width = preview_cols * (preview_size + preview_margin) - preview_margin
    
    # Create a clipping mask for the content area
    content_area = pygame.Rect(0, 200, SCREEN_WIDTH, SCREEN_HEIGHT - 320)
    content_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 320), pygame.SRCALPHA)
    
    # Track button and mouse states
    mouse_pressed = False
    mouse_pos = (0, 0)
    
    while True:
        # Mouse state tracking for responsive clicks
        prev_mouse_pressed = mouse_pressed
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()
        
        draw_smooth_gradient()
        
        # Settings title
        title_x = (SCREEN_WIDTH - title_font.size("Settings")[0]) // 2
        glowing_text(screen, "Settings", title_font, title_x, 30, YELLOW, step)
        
        # Draw navigation tabs
        pygame.draw.rect(screen, (30, 30, 60), pygame.Rect(0, 110, SCREEN_WIDTH, button_height + 20))
        
        # Highlight the active tab
        active_tab_color = (60, 100, 200)
        inactive_tab_color = (40, 40, 80)
        
        draw_button(screen, general_button, "General", menu_font, 
                    active_tab_color if current_page == 0 else inactive_tab_color, (100, 150, 255), mouse_pos)
        draw_button(screen, snake_button, "Snake Theme", menu_font, 
                    active_tab_color if current_page == 1 else inactive_tab_color, (100, 150, 255), mouse_pos)
        draw_button(screen, food_button, "Food Theme", menu_font,
                    active_tab_color if current_page == 2 else inactive_tab_color, (100, 150, 255), mouse_pos)
        
        # Apply smooth scroll with velocity and damping
        if abs(scroll_velocity) > 0.5:
            scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping factor
        else:
            scroll_velocity = 0
        
        # Clamp scroll position to valid range
        scroll_y = max(0, min(max_scroll_y, scroll_y))
        
        # Process mouse wheel events and handle events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Handle tab navigation
                if e.button == 1:  # Left mouse button
                    if general_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_page = 0
                        scroll_y = 0
                        scroll_velocity = 0
                    elif snake_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_page = 1
                        scroll_y = 0
                        scroll_velocity = 0
                    elif food_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_page = 2
                        scroll_y = 0
                        scroll_velocity = 0
                    
                    # General page buttons
                    if current_page == 0:
                        if dark_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            background_theme = "dark"
                            save_settings_immediately()  # Save immediately after change
                            
                        elif light_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            background_theme = "light"
                            save_settings_immediately()  # Save immediately after change
                            
                        elif debug_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            debug_mode = not debug_mode
                            save_settings_immediately()  # Save immediately after change
                            
                        elif vs_position_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            # Toggle position between left and right
                            new_position = "left" if get_player_position() == "right" else "right"
                            save_player_position(new_position)
                            save_settings_immediately()  # Save immediately after change
                            
                        elif enhanced_effects_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            enhanced_effects = not enhanced_effects
                            save_settings_immediately()  # Save immediately after change
                    
                    # Back button
                    if back_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        save_config(config)
                        return
                
                # Mouse wheel scrolling with smoother velocity
                elif e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                # Save settings before exiting with ESC key
                save_config(config)
                return
                
        # Draw content based on current page
        if current_page == 0:
            # General settings page
            # Add border around the selected theme button
            selected_border = pygame.Rect(0, 0, button_width + 8, button_height + 8)
            if background_theme == "dark":
                selected_border.center = dark_button.center
                pygame.draw.rect(screen, (80, 200, 120), selected_border, 3, border_radius=14)
            else:
                selected_border.center = light_button.center
                pygame.draw.rect(screen, (80, 200, 120), selected_border, 3, border_radius=14)
                
            draw_button(screen, dark_button, "Theme: Dark", menu_font,
                    (50,50,80) if background_theme == "dark" else (30,30,50),
                    (80,80,120), mouse_pos)
            draw_button(screen, light_button, "Theme: Light", menu_font,
                    (200,200,220) if background_theme == "light" else (150,150,170),
                    (230,230,250), mouse_pos)
                    
            # Debug mode toggle button
            debug_label = "Debug: ON" if debug_mode else "Debug: OFF"
            debug_color = (100, 200, 100) if debug_mode else (200, 100, 100)
            draw_button(screen, debug_button, debug_label, menu_font, debug_color, (150, 150, 150), mouse_pos)
            
            # VS Player Position setting
            vs_position = get_player_position()
            vs_position_text = f"Player Position: {vs_position.title()}"
            
            # Draw the button
            if vs_position_button.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (150, 150, 150), vs_position_button, border_radius=5)
            else:
                pygame.draw.rect(screen, (100, 100, 100), vs_position_button, border_radius=5)
            
            text_surface = menu_font.render(vs_position_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(vs_position_button.centerx, vs_position_button.centery))
            screen.blit(text_surface, text_rect)
            
            # Enhanced effects toggle button
            enhanced_label = "Level-Up Effects: Enhanced" if enhanced_effects else "Level-Up Effects: Simple"
            enhanced_color = (100, 200, 100) if enhanced_effects else (200, 100, 100)
            draw_button(screen, enhanced_effects_button, enhanced_label, menu_font, enhanced_color, (150, 150, 150), mouse_pos)

        elif current_page == 1:
            # Clear the content surface for proper clipping
            content_surface.fill((0,0,0,0))
            
            # Snake themes page
            current_snake = customization.current_snake_theme
            
            # Calculate how many theme previews we need to show
            preview_rows = math.ceil(len(snake_themes) / preview_cols)
            content_height = preview_rows * (preview_size + preview_margin) - preview_margin
            max_scroll_y = max(0, content_height - content_area.height)
        
            # Draw snake theme previews onto content_surface
            y_pos = 0  # Relative to content surface
            x_pos = (SCREEN_WIDTH - preview_width) // 2
            
            # Calculate the adjusted mouse position once for the entire content area
            content_mouse_pos = (
                mouse_pos[0], 
                mouse_pos[1] - content_area.top + scroll_y
            )
            
            for i, (key, theme) in enumerate(snake_themes.items()):
                row = i // preview_cols
                col = i % preview_cols
                
                theme_x = x_pos + col * (preview_size + preview_margin)
                theme_y = y_pos + row * (preview_size + preview_margin) - scroll_y
                
                # Only draw if visible in the content area
                if (theme_y + preview_size > 0 and theme_y < content_area.height):
                    # Create preview rect
                    preview_rect = pygame.Rect(theme_x, theme_y, preview_size, preview_size)
                    
                    # Draw theme preview
                    pygame.draw.rect(content_surface, (30, 30, 60), preview_rect, border_radius=10)
                    
                    # Draw selection indicator if this is the current theme
                    if key == current_snake:
                        pygame.draw.rect(content_surface, (80, 200, 120), preview_rect, 4, border_radius=10)
                    
                    # Check hover using the content_mouse_pos - this is fixed now
                    if preview_rect.collidepoint(content_mouse_pos):
                        pygame.draw.rect(content_surface, (150, 150, 180), preview_rect, 2, border_radius=10)
                    
                    # Draw theme name
                    name_text = menu_font.render(theme.name, True, WHITE)
                    name_rect = name_text.get_rect(center=(preview_rect.centerx, preview_rect.top + 30))
                    content_surface.blit(name_text, name_rect)
                    
                    # Draw snake preview
                    snake_segments = [(
                        preview_rect.centerx + (j-5) * 15, 
                        preview_rect.centery
                    ) for j in range(10)]
                    
                    for j, pos in enumerate(snake_segments):
                        color = theme.get_segment_color(j)
                        pygame.draw.rect(content_surface, color, (pos[0]-7, pos[1]-7, 15, 15))
                        
                    # Add select button if not selected
                    if key != current_snake:
                        select_button = pygame.Rect(
                            preview_rect.centerx - 60, 
                            preview_rect.bottom - 40, 
                            120, 30
                        )
                        
                        # Fix the coordinate conversion for screen_button
                        screen_button = pygame.Rect(
                            select_button.left,
                            select_button.top + content_area.top - scroll_y,  # Correct adjustment for scroll position
                            select_button.width,
                            select_button.height
                        )
                        
                        # Draw button on content surface with hover effect
                        # Use content_mouse_pos for hover detection
                        base_color = (60, 120, 60)
                        hover_color = (80, 180, 80)
                        button_color = hover_color if select_button.collidepoint(content_mouse_pos) else base_color
                        pygame.draw.rect(content_surface, button_color, select_button, border_radius=8)
                        
                        text_surface = footer_font.render("Select", True, WHITE)
                        text_rect = text_surface.get_rect(center=select_button.center)
                        content_surface.blit(text_surface, text_rect)
                        
                        # Handle click on select button
                        if mouse_pressed and not prev_mouse_pressed and screen_button.collidepoint(mouse_pos):
                            if click_sound: click_sound.play()
                            customization.set_snake_theme(key)
                            # Also update the snake_color for compatibility
                            snake_color = theme.head_color
            
            # Blit the content surface to the screen with proper clipping
            screen.blit(content_surface, (0, content_area.top))

        elif current_page == 2:
            # Clear the content surface for proper clipping
            content_surface.fill((0,0,0,0))
            
            # Food themes page
            current_food = customization.current_food_theme
            
            # Calculate how many theme previews we need to show
            preview_rows = math.ceil(len(food_themes) / preview_cols)
            content_height = preview_rows * (preview_size + preview_margin) - preview_margin
            max_scroll_y = max(0, content_height - content_area.height)
            
            # Draw food theme previews onto content_surface
            y_pos = 0  # Relative to content surface
            x_pos = (SCREEN_WIDTH - preview_width) // 2
            
            # Calculate the adjusted mouse position once for the entire content area
            content_mouse_pos = (
                mouse_pos[0],
                mouse_pos[1] - content_area.top + scroll_y
            )
            
            for i, (key, theme) in enumerate(food_themes.items()):
                row = i // preview_cols
                col = i % preview_cols
                
                theme_x = x_pos + col * (preview_size + preview_margin)
                theme_y = y_pos + row * (preview_size + preview_margin) - scroll_y
                
                # Only draw if visible in the content area
                if (theme_y + preview_size > 0 and theme_y < content_area.height):
                    # Create preview rect
                    preview_rect = pygame.Rect(theme_x, theme_y, preview_size, preview_size)
                    
                    # Draw theme preview
                    pygame.draw.rect(content_surface, (30, 30, 60), preview_rect, border_radius=10)
                    
                    # Draw selection indicator if this is the current theme
                    if key == current_food:
                        pygame.draw.rect(content_surface, (80, 200, 120), preview_rect, 4, border_radius=10)
                    
                    # Check hover using the adjusted content_mouse_pos
                    if preview_rect.collidepoint(content_mouse_pos):
                        pygame.draw.rect(content_surface, (150, 150, 180), preview_rect, 2, border_radius=10)
                    
                    # Draw theme name
                    name_text = menu_font.render(theme.name, True, WHITE)
                    name_rect = name_text.get_rect(center=(preview_rect.centerx, preview_rect.top + 30))
                    content_surface.blit(name_text, name_rect)
                    
                    # Draw food preview
                    food_color = theme.get_food_color(step)
                    food_radius = 25
                    pygame.draw.circle(content_surface, food_color, 
                                    (preview_rect.centerx, preview_rect.centery), food_radius)
                    
                    # If it's a random color theme, draw some samples
                    if theme.random_colors:
                        for j, color in enumerate(theme.color_options[:5]):
                            small_radius = 10
                            x_offset = (j - 2) * 25
                            pygame.draw.circle(content_surface, color,
                                            (preview_rect.centerx + x_offset, 
                                            preview_rect.centery + 50), small_radius)
                                        
                    # Add select button if not selected
                    if key != current_food:
                        select_button = pygame.Rect(
                            preview_rect.centerx - 60, 
                            preview_rect.bottom - 40, 
                            120, 30
                        )
                        
                        # Fix the coordinate conversion for screen_button
                        screen_button = pygame.Rect(
                            select_button.left,
                            select_button.top + content_area.top - scroll_y,  # Correct adjustment for scroll position
                            select_button.width,
                            select_button.height
                        )
                        
                        # Draw button on content surface with hover effect
                        base_color = (60, 120, 60)
                        hover_color = (80, 180, 80)
                        button_color = hover_color if select_button.collidepoint(content_mouse_pos) else base_color
                        pygame.draw.rect(content_surface, button_color, select_button, border_radius=8)
                        
                        text_surface = footer_font.render("Select", True, WHITE)
                        text_rect = text_surface.get_rect(center=select_button.center)
                        content_surface.blit(text_surface, text_rect)
                        
                        # Handle click on select button
                        if mouse_pressed and not prev_mouse_pressed and screen_button.collidepoint(mouse_pos):
                            if click_sound: click_sound.play()
                            customization.set_food_theme(key)
            
            # Blit the content surface to the screen with proper clipping
            screen.blit(content_surface, (0, content_area.top))
        
        # Back button
        draw_fancy_button(screen, back_button, "Back to Menu", menu_font, (100,100,100), (150,150,150), mouse_pos, step)
        
        # Draw scrollbar for pages that need it
        if current_page in (1, 2) and max_scroll_y > 0:
            scrollbar_height = max(30, int(content_area.height * content_area.height / (content_area.height + max_scroll_y)))
            scrollbar_y = content_area.top + int((content_area.height - scrollbar_height) * (scroll_y / max_scroll_y))
            pygame.draw.rect(screen, (80, 80, 100), 
                            (SCREEN_WIDTH - 15, content_area.top, 10, content_area.height), 
                            border_radius=5)
            pygame.draw.rect(screen, (150, 150, 200), 
                            (SCREEN_WIDTH - 15, scrollbar_y, 10, scrollbar_height), 
                            border_radius=5)
        
        pygame.display.update()
        step += 1
        clock.tick(60)  # Higher framerate for smoother scrolling

# Add this function after your other global functions
def save_all_settings():
    """Save all settings when program exits"""
    global music_on, background_theme, debug_mode, enhanced_effects
    
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

if __name__ == "__main__":
    home_page()
