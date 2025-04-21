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
from src.game.player_vs_ai import player_vs_ai
from src.game.fibonacci_snake import FibonacciSnakeGame
from src.ai.agent import Agent
from src.game.player_vs_ai import get_player_position, save_player_position
from src.game.customization import customization
import datetime
import atexit
from src.utils.input_utils import is_screenshot_key

# Define all fonts after pygame is initialized
pygame.init()
# Fallback if font file doesn't exist
try:
    title_font = pygame.font.Font("assets/fonts/game_over.ttf", 96)
    menu_font = pygame.font.Font("assets/fonts/game_over.ttf", 36)
    footer_font = pygame.font.Font("assets/fonts/game_over.ttf", 24)
except FileNotFoundError:
    print("Warning: Font files not found. Using system fonts.")
    title_font = pygame.font.SysFont("Arial", 96)
    menu_font = pygame.font.SysFont("Arial", 36)
    footer_font = pygame.font.SysFont("Arial", 24)
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
                
                # Convert from old format if needed
                if isinstance(old_scores.get("classic"), int) or isinstance(old_scores.get("ai"), int):
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
                            "player": {"scores": [], "dates": []},
                            "ai": {"scores": [], "dates": []}
                        }
                    }
                    with open(HIGHSCORE_FILE, 'w') as f2:
                        json.dump(new_scores, f2, indent=2)
                    return new_scores
                else:
                    # Already in new format
                    return old_scores
        else:
            # Create default new format
            high_scores = {
                "classic": {"scores": [], "dates": []},
                "ai": {"scores": [], "dates": []},
                "vs": {"player": {"scores": [], "dates": []}, "ai": {"scores": [], "dates": []}}
            }
            os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
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
            # Regular modes (classic, ai, fibonacci)
            # Make sure the mode exists
            if mode not in high_scores:
                high_scores[mode] = {"scores": [], "dates": []}
                
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

def save_fibonacci_high_score(food_score, next_fib_value):
    """Save Fibonacci high score with both food count and next Fibonacci number"""
    try:
        high_scores = load_high_scores()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        is_new_high = False
        
        # Make sure fibonacci category exists with all required fields
        if "fibonacci" not in high_scores:
            high_scores["fibonacci"] = {
                "scores": [],     # Food eaten count
                "fib_values": [], # Corresponding next Fibonacci values
                "dates": []       # Dates when scores were achieved
            }
        
        # Ensure all required keys exist
        if "scores" not in high_scores["fibonacci"]:
            high_scores["fibonacci"]["scores"] = []
        if "fib_values" not in high_scores["fibonacci"]:
            high_scores["fibonacci"]["fib_values"] = []
        if "dates" not in high_scores["fibonacci"]:
            high_scores["fibonacci"]["dates"] = []
            
        scores = high_scores["fibonacci"]["scores"]
        fib_values = high_scores["fibonacci"]["fib_values"]
        dates = high_scores["fibonacci"]["dates"]
        
        # Check if this is a new high score - primarily based on food count
        if not scores or food_score > max(scores):
            is_new_high = True
        
        # Insert score in sorted order (by food count first)
        insert_index = 0
        while insert_index < len(scores) and food_score <= scores[insert_index]:
            insert_index += 1
            
        scores.insert(insert_index, food_score)
        fib_values.insert(insert_index, next_fib_value)
        dates.insert(insert_index, today)
        
        # Keep only the top 10 scores
        if len(scores) > 10:
            scores.pop(10)
            fib_values.pop(10)
            dates.pop(10)
            
        # Save updated high scores
        os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(high_scores, f, indent=2)
        
        print(f"Successfully saved Fibonacci score: {food_score} | {next_fib_value}")
        return is_new_high
    except Exception as e:
        print(f"Error saving Fibonacci high score: {e}")
        import traceback
        traceback.print_exc()
        return False

# Add this function to display high scores
def high_scores_page():
    global screen
    clock = pygame.time.Clock()
    
    # Load high scores
    high_scores = load_high_scores()
    
    # Back button
    button_width = 250
    button_height = 50
    back_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, SCREEN_HEIGHT - 80, button_width, button_height)
    
    # Define categories and modes
    categories = ["Player", "AI", "VS Mode"]
    modes = {
        "Player": ["Classic", "Fibonacci"],
        "AI": ["Classic", "Fibonacci"],
        "VS Mode": ["Overall"]
    }
    
    # Track selected category and mode
    current_category = "Player"
    current_mode = "Classic"
    
    # Mode to data mapping
    mode_to_data_key = {
        "Player-Classic": "classic",
        "Player-Fibonacci": "fibonacci", 
        "AI-Classic": "ai",
        "AI-Fibonacci": "fibonacci_ai",
        "VS Mode-Overall": "vs_mode"
    }
    
    # Set up scrolling
    scroll_y = 0
    scroll_velocity = 0
    max_scroll_y = 0
    
    # Content area dimensions
    header_height = 40
    content_area = pygame.Rect(100, 250 + header_height, SCREEN_WIDTH - 200, 390 - header_height)
    content_surface = pygame.Surface((content_area.width, 2000), pygame.SRCALPHA)
    
    # Column positions as percentages
    col_positions = {
        "rank": 0.05,        # 5% from left
        "score": 0.30,       # 30% from left
        "winner": 0.25,      # 25% from left (only for vs_mode)
        "food": 0.25,        # 25% from left (only for fibonacci)
        "fib": 0.55,         # 55% from left (only for fibonacci)
        "date": 0.75         # 75% from left
    }
    
    # Button colors
    back_button_color = (180, 60, 60)
    back_button_hover = (220, 80, 80)
    category_btn_color = (70, 90, 130)
    category_btn_hover = (90, 110, 150)
    category_btn_active = (110, 130, 170)
    mode_btn_color = (60, 80, 120)
    mode_btn_hover = (80, 100, 140)
    mode_btn_active = (100, 120, 200)
    
    # Animation step
    step = 0
    
    # Calculate button positions and sizes
    category_btn_width = 320
    category_btn_height = 50
    category_btn_y = 120
    
    mode_btn_width = 150
    mode_btn_height = 40
    mode_btn_y = 190
    
    # Create category buttons with equal spacing
    category_spacing = (SCREEN_WIDTH - (category_btn_width * len(categories))) // (len(categories) + 1)
    category_buttons = {}
    for i, category in enumerate(categories):
        x = category_spacing + i * (category_btn_width + category_spacing)
        category_buttons[category] = pygame.Rect(x, category_btn_y, category_btn_width, category_btn_height)
    
    # Create mode buttons (will be positioned dynamically based on selected category)
    mode_buttons = {}
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient()
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size("High Scores")[0]) // 2
        glowing_text(screen, "High Scores", title_font, title_x, 30, YELLOW, step)
        
        # Draw category selection buttons
        for category, button in category_buttons.items():
            is_current = category == current_category
            color = category_btn_active if is_current else category_btn_color
            hover_color = category_btn_active if is_current else category_btn_hover
            
            # Draw fancy button with larger font for categories
            draw_fancy_button(screen, button, category, menu_font, color, hover_color, mouse_pos, step)
        
        # Position mode buttons based on current category
        available_modes = modes[current_category]
        mode_spacing = (SCREEN_WIDTH - (mode_btn_width * len(available_modes))) // (len(available_modes) + 1)
        mode_buttons.clear()
        for i, mode in enumerate(available_modes):
            x = mode_spacing + i * (mode_btn_width + mode_spacing)
            mode_buttons[mode] = pygame.Rect(x, mode_btn_y, mode_btn_width, mode_btn_height)
        
        # Draw mode selection buttons
        for mode, button in mode_buttons.items():
            is_current = mode == current_mode
            color = mode_btn_active if is_current else mode_btn_color
            hover_color = mode_btn_active if is_current else mode_btn_hover
            
            draw_fancy_button(screen, button, mode, footer_font, color, hover_color, mouse_pos, step)
        
        # Apply smooth scrolling with inertia
        if abs(scroll_velocity) > 0.5:
            scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping factor
        else:
            scroll_velocity = 0
        
        # Clear content surface
        content_surface.fill((0, 0, 0, 0))
        
        # Get data key for current selection
        data_key = mode_to_data_key.get(f"{current_category}-{current_mode}")
        
        # Calculate column positions in pixels
        col_pixels = {key: int(content_area.width * pos) for key, pos in col_positions.items()}
        
        # Draw header background with gradient effect
        header_bg = pygame.Rect(content_area.left, content_area.top - header_height - 5, 
                             content_area.width, header_height)
        # Create gradient header background
        header_surface = pygame.Surface((header_bg.width, header_bg.height), pygame.SRCALPHA)
        for y in range(header_bg.height):
            alpha = 255 - int(170 * (y / header_bg.height))  # Fade from solid to semi-transparent
            pygame.draw.line(header_surface, (60, 80, 150, alpha), 
                          (0, y), (header_bg.width, y))
        
        # Add glossy reflection effect
        reflection_height = header_bg.height // 2
        for y in range(reflection_height):
            alpha = 70 * (1 - y / reflection_height)  # Fade the reflection
            pygame.draw.line(header_surface, (255, 255, 255, int(alpha)), 
                          (0, y), (header_bg.width, y))
        
        # Apply border radius to header using a mask
        header_mask = pygame.Surface((header_bg.width, header_bg.height), pygame.SRCALPHA)
        pygame.draw.rect(header_mask, (255, 255, 255), 
                      (0, 0, header_bg.width, header_bg.height), border_radius=12)
        header_surface.blit(header_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        screen.blit(header_surface, header_bg)
        
        # Add subtle bottom border to header
        pygame.draw.line(screen, (100, 140, 200), 
                      (header_bg.left, header_bg.bottom - 1), 
                      (header_bg.right, header_bg.bottom - 1), 2)
        
        # Prepare header texts with improved styling
        header_texts = {
            "rank": footer_font.render("RANK", True, (240, 240, 240)),
            "score": footer_font.render("SCORE", True, (240, 240, 240)),
            "winner": footer_font.render("WINNER", True, (240, 240, 240)),
            "food": footer_font.render("FOOD", True, (240, 240, 240)),
            "fib": footer_font.render("FIB VALUE", True, (240, 240, 240)),
            "date": footer_font.render("DATE", True, (240, 240, 240))
        }
        
        # Display content based on current category and mode
        if data_key == "classic" or data_key == "ai":
            # Regular score display for Classic modes (Player or AI)
            # Add icons/indicators for columns
            rank_icon = "🏆"
            score_icon = "🎮"
            date_icon = "📅"
            
            # Draw the column headers
            screen.blit(header_texts["rank"], (content_area.left + col_pixels["rank"] - header_texts["rank"].get_width()//2, 
                    header_bg.centery - header_texts["rank"].get_height()//2))
            screen.blit(header_texts["score"], (content_area.left + col_pixels["score"] - header_texts["score"].get_width()//2, 
                    header_bg.centery - header_texts["score"].get_height()//2))
            screen.blit(header_texts["date"], (content_area.left + col_pixels["date"] - header_texts["date"].get_width()//2, 
                    header_bg.centery - header_texts["date"].get_height()//2))
            
            # Draw subtle column dividers
            for col in ["score", "date"]:
                x = content_area.left + col_pixels[col] - 40
                pygame.draw.line(screen, (100, 120, 180, 120), 
                              (x, header_bg.top + 5), 
                              (x, header_bg.bottom - 5), 1)
            
            # Get data
            scores = high_scores.get(data_key, {}).get("scores", [])
            dates = high_scores.get(data_key, {}).get("dates", [])
            
            # Calculate max scroll
            entries_height = max(40, len(scores) * 40)
            max_scroll_y = max(0, entries_height - content_area.height)
            
            # Draw entries
            entry_y = 0 - scroll_y
            
            for i, (score, date) in enumerate(zip(scores, dates)):
                if -50 <= entry_y <= content_area.height + 50:
                    # Alternating background colors
                    bg_color = (40, 40, 70, 180) if i % 2 == 0 else (30, 30, 60, 180)
                    pygame.draw.rect(content_surface, bg_color, 
                                pygame.Rect(0, entry_y, content_area.width, 40), border_radius=8)
                    
                    # Rank with medal for top 3
                    if i < 3:
                        medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                        pygame.draw.circle(content_surface, medal_colors[i], 
                                        (col_pixels["rank"], entry_y + 20), 15)
                        rank_text = footer_font.render(f"#{i+1}", True, (20, 20, 20))
                        rank_rect = rank_text.get_rect(center=(col_pixels["rank"], entry_y + 20))
                        content_surface.blit(rank_text, rank_rect)
                    else:
                        rank_text = footer_font.render(f"#{i+1}", True, WHITE)
                        rank_rect = rank_text.get_rect(center=(col_pixels["rank"], entry_y + 20))
                        content_surface.blit(rank_text, rank_rect)
                    
                    # Format date
                    try:
                        parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                        short_date = parsed_date.strftime("%b %d")
                    except ValueError:
                        short_date = date
                    
                    # Score and date - centered in their columns
                    score_text = footer_font.render(str(score), True, WHITE)
                    date_text = footer_font.render(short_date, True, (180, 180, 180))
                    
                    score_rect = score_text.get_rect(center=(col_pixels["score"], entry_y + 20))
                    date_rect = date_text.get_rect(center=(col_pixels["date"], entry_y + 20))
                    
                    content_surface.blit(score_text, score_rect)
                    content_surface.blit(date_text, date_rect)
                
                entry_y += 40
                
        elif data_key == "fibonacci" or data_key == "fibonacci_ai":
            # Fibonacci modes (Player or AI)
            screen.blit(header_texts["rank"], (content_area.left + col_pixels["rank"], 
                                          header_bg.centery - header_texts["rank"].get_height()//2))
            screen.blit(header_texts["food"], (content_area.left + col_pixels["food"], 
                                          header_bg.centery - header_texts["food"].get_height()//2))
            screen.blit(header_texts["fib"], (content_area.left + col_pixels["fib"], 
                                         header_bg.centery - header_texts["fib"].get_height()//2))
            screen.blit(header_texts["date"], (content_area.left + col_pixels["date"], 
                                          header_bg.centery - header_texts["date"].get_height()//2))
            
            # Get data
            scores = high_scores.get(data_key, {}).get("scores", [])
            fib_values = high_scores.get(data_key, {}).get("fib_values", [])
            dates = high_scores.get(data_key, {}).get("dates", [])
            
            # Calculate max scroll
            entries_height = max(40, len(scores) * 40)
            max_scroll_y = max(0, entries_height - content_area.height)
            
            # Draw entries
            entry_y = 0 - scroll_y
            
            for i, (score, date) in enumerate(zip(scores, dates[:len(scores)])):
                if -50 <= entry_y <= content_area.height + 50:
                    bg_color = (40, 40, 70, 180) if i % 2 == 0 else (30, 30, 60, 180)
                    pygame.draw.rect(content_surface, bg_color, 
                                pygame.Rect(0, entry_y, content_area.width, 40), border_radius=8)
                    
                    # Rank with medal
                    if i < 3:
                        medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
                        pygame.draw.circle(content_surface, medal_colors[i], 
                                        (col_pixels["rank"], entry_y + 20), 15)
                        rank_text = footer_font.render(f"#{i+1}", True, (20, 20, 20))
                        rank_rect = rank_text.get_rect(center=(col_pixels["rank"], entry_y + 20))
                        content_surface.blit(rank_text, rank_rect)
                    else:
                        rank_text = footer_font.render(f"#{i+1}", True, WHITE)
                        rank_rect = rank_text.get_rect(center=(col_pixels["rank"], entry_y + 20))
                        content_surface.blit(rank_text, rank_rect)
                    
                    # Format date
                    try:
                        parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                        short_date = parsed_date.strftime("%b %d")
                    except ValueError:
                        short_date = date
                    
                    # Get fibonacci value
                    fib_value = fib_values[i] if i < len(fib_values) else "?"
                    
                    # Display values
                    score_text = footer_font.render(str(score), True, WHITE)
                    fib_text = footer_font.render(str(fib_value), True, (255, 215, 0))
                    date_text = footer_font.render(short_date, True, (180, 180, 180))
                    
                    score_rect = score_text.get_rect(center=(col_pixels["food"], entry_y + 20))
                    fib_rect = fib_text.get_rect(center=(col_pixels["fib"], entry_y + 20))
                    date_rect = date_text.get_rect(center=(col_pixels["date"], entry_y + 20))
                    
                    content_surface.blit(score_text, score_rect)
                    content_surface.blit(fib_text, fib_rect)
                    content_surface.blit(date_text, date_rect)
                
                entry_y += 40
                
        elif data_key == "vs_mode":
            # VS Mode
            screen.blit(header_texts["rank"], (content_area.left + col_pixels["rank"], 
                                          header_bg.centery - header_texts["rank"].get_height()//2))
            screen.blit(header_texts["winner"], (content_area.left + col_pixels["winner"], 
                                             header_bg.centery - header_texts["winner"].get_height()//2))
            screen.blit(header_texts["score"], (content_area.left + col_pixels["score"], 
                                           header_bg.centery - header_texts["score"].get_height()//2))
            screen.blit(header_texts["date"], (content_area.left + col_pixels["date"], 
                                          header_bg.centery - header_texts["date"].get_height()//2))
            
            # Get data
            player_scores = high_scores.get("vs", {}).get("player", {}).get("scores", [])
            player_dates = high_scores.get("vs", {}).get("player", {}).get("dates", [])
            ai_scores = high_scores.get("vs", {}).get("ai", {}).get("scores", [])
            ai_dates = high_scores.get("vs", {}).get("ai", {}).get("dates", [])
            
            # Combine scores
            vs_matches = []
            for score, date in zip(player_scores, player_dates):
                vs_matches.append((score, date, True))  # True = Player score
                
            for score, date in zip(ai_scores, ai_dates):
                vs_matches.append((score, date, False))  # False = AI score
                
            # Sort and limit to top 10
            vs_matches.sort(key=lambda x: x[0], reverse=True)
            vs_matches = vs_matches[:10]
            
            # Calculate max scroll
            entries_height = max(40, len(vs_matches) * 40)
            max_scroll_y = max(0, entries_height - content_area.height)
            
            # Draw entries
            entry_y = 0 - scroll_y
            
            for i, (score, date, is_player) in enumerate(vs_matches[:40]):
                if -50 <= entry_y <= content_area.height + 50:
                    bg_color = (40, 40, 70, 180) if i % 2 == 0 else (30, 30, 60, 180)
                    pygame.draw.rect(content_surface, bg_color, 
                                pygame.Rect(0, entry_y, content_area.width, 40), border_radius=8)
                    
                    # Rank with medal
                    if i < 3:
                        medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
                        pygame.draw.circle(content_surface, medal_colors[i], 
                                        (col_pixels["rank"], entry_y + 20), 15)
                        rank_text = footer_font.render(f"#{i+1}", True, (20, 20, 20))
                        rank_rect = rank_text.get_rect(center=(col_pixels["rank"], entry_y + 20))
                        content_surface.blit(rank_text, rank_rect)
                    else:
                        rank_text = footer_font.render(f"#{i+1}", True, WHITE)
                        rank_rect = rank_text.get_rect(center=(col_pixels["rank"], entry_y + 20))
                        content_surface.blit(rank_text, rank_rect)
                    
                    # Winner indicator
                    winner_color = (50, 255, 50) if is_player else (50, 150, 255)  # Green for player, blue for AI
                    winner_label = "PLAYER" if is_player else "AI"
                    winner_text = footer_font.render(winner_label, True, winner_color)
                    winner_rect = winner_text.get_rect(center=(col_pixels["winner"], entry_y + 20))
                    content_surface.blit(winner_text, winner_rect)
                    
                    # Format date
                    try:
                        parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                        short_date = parsed_date.strftime("%b %d")
                    except ValueError:
                        short_date = date
                    
                    # Score and date
                    score_text = footer_font.render(str(score), True, WHITE)
                    date_text = footer_font.render(short_date, True, (180, 180, 180))
                    
                    score_rect = score_text.get_rect(center=(col_pixels["score"], entry_y + 20))
                    date_rect = date_text.get_rect(center=(col_pixels["date"], entry_y + 20))
                    
                    content_surface.blit(score_text, score_rect)
                    content_surface.blit(date_text, date_rect)
                
                entry_y += 40
        
        # Show message if no scores
        if ((data_key in ["classic", "ai"] and not high_scores.get(data_key, {}).get("scores", [])) or
            (data_key == "vs_mode" and not vs_matches) or
            (data_key in ["fibonacci", "fibonacci_ai"] and not high_scores.get(data_key, {}).get("scores", []))):
            no_scores_text = menu_font.render("No scores recorded yet!", True, (200, 200, 200))
            no_scores_rect = no_scores_text.get_rect(center=(content_area.width // 2, 150))
            content_surface.blit(no_scores_text, no_scores_rect)
        
        # Blit content with clipping
        screen.blit(content_surface, (content_area.topleft), 
                (0, 0, content_area.width, content_area.height))
        
        # Draw scrollbar if needed
        has_content = ((data_key in ["classic", "ai"] and high_scores.get(data_key, {}).get("scores", [])) or 
                    (data_key == "vs_mode" and vs_matches) or
                    (data_key in ["fibonacci", "fibonacci_ai"] and high_scores.get(data_key, {}).get("scores", [])))
                    
        if max_scroll_y > 0 and has_content:
            scrollbar_height = max(30, int(content_area.height * content_area.height / (content_area.height + max_scroll_y)))
            scrollbar_y = content_area.top + int((content_area.height - scrollbar_height) * min(1, scroll_y / max_scroll_y))
            
            # Draw scrollbar track
            pygame.draw.rect(screen, (60, 60, 80), 
                        (content_area.right + 10, content_area.top, 8, content_area.height), 
                        border_radius=4)
                        
            # Draw scrollbar thumb
            pygame.draw.rect(screen, (120, 120, 160), 
                        (content_area.right + 10, scrollbar_y, 8, scrollbar_height), 
                        border_radius=4)
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back to Menu", footer_font, back_button_color, back_button_hover, mouse_pos, step)
        
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
                
                # Category selection
                for category, rect in category_buttons.items():
                    if rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_category = category
                        current_mode = modes[category][0]  # Select first mode in category
                        scroll_y = 0  # Reset scroll position
                        scroll_velocity = 0
                
                # Mode selection
                for mode, rect in mode_buttons.items():
                    if rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_mode = mode
                        scroll_y = 0  # Reset scroll position
                        scroll_velocity = 0
                
                # Mouse wheel scrolling
                if e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
                        
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    return
                # Keyboard scrolling
                elif e.key == pygame.K_UP:
                    scroll_velocity -= 15
                elif e.key == pygame.K_DOWN:
                    scroll_velocity += 15
                elif e.key == pygame.K_PAGEUP:
                    scroll_velocity -= 45
                elif e.key == pygame.K_PAGEDOWN:
                    scroll_velocity += 45
                elif e.key == pygame.K_HOME:
                    scroll_y = 0  # Jump to top
                elif e.key == pygame.K_END:
                    scroll_y = max_scroll_y  # Jump to bottom
        
        # Clamp scroll position
        if max_scroll_y > 0:
            scroll_y = max(0, min(max_scroll_y, scroll_y))
        else:
            scroll_y = 0
        
        step += 1
        clock.tick(60)

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Serpenti_c")

# Colors
WHITE  = (255, 255, 255)
GREEN  = (0, 255, 0)     
RED    = (255, 0, 0)     
YELLOW = (255, 255, 0)  # Add this line

# Load icons and music with better error handling
try:
    # Load icons
    music_on_icon = pygame.image.load("assets/images/sound-on.png")
    music_off_icon = pygame.image.load("assets/images/sound-off.png")
    music_on_icon = pygame.transform.scale(music_on_icon, (40, 40))
    music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))
    
    # Load and prepare background music
    pygame.mixer.music.load("assets/sounds/background-music.mp3")
    click_sound = pygame.mixer.Sound("assets/sounds/click.wav")
    music_loaded = True  # Flag to track if music was loaded successfully
except Exception as e:
    print(f"Warning: Resource files not found. {e}")
    # Create fallback icons
    music_on_icon = pygame.Surface((40, 40))
    music_off_icon = pygame.Surface((40, 40))
    music_on_icon.fill(GREEN)
    music_off_icon.fill(RED)
    
    # Create dummy sound objects
    click_sound = None
    music_loaded = False  # Mark music as not loaded
    # Initialize mixer anyway for potential future loads
    pygame.mixer.init()

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
            # Add the reset code here:
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
    if music_on and music_loaded:  # Only play if music was loaded successfully
        try:
            pygame.mixer.music.play(-1)
        except pygame.error:
            print("Warning: Unable to play music.")
    else:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
    
    clock = pygame.time.Clock()
    
    buttons = [
        {"text": "Play Classic Mode", "action": play_classic_game, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 180, 400, 60)},
        {"text": "Play Fibonacci Mode", "action": play_fibonacci_game, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 250, 400, 60)},
        {"text": "Player vs AI", "action": player_vs_ai, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 320, 400, 60)},
        {"text": "Watch AI (Classic)", "action": watch_ai_play, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 390, 400, 60)},
        {"text": "Watch AI (Fibonacci)", "action": watch_fibonacci_ai_play, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 460, 400, 60)},
        {"text": "Settings", "action": settings_page, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 530, 400, 60)},
        {"text": "Quit", "action": sys.exit, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 600, 400, 60)}
    ]
    
    #high score button
    scores_button = pygame.Rect(20, 20, 120, 40)
    music_rect = pygame.Rect(SCREEN_WIDTH - 60, 20, 40, 40)
    
    # Help button
    help_button_size = 40
    help_button = pygame.Rect(20, SCREEN_HEIGHT - 60, help_button_size, help_button_size)
    help_color = (80, 100, 180)
    help_hover = (120, 140, 220)
    
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
        
        # Draw high scores button with a more subtle, compact design
        scores_text = footer_font.render("Scores", True, WHITE)  # Shorter text
        
        # Create a more subtle gradient effect
        scores_surface = pygame.Surface((scores_button.width, scores_button.height), pygame.SRCALPHA)
        
        # More subtle colors that complement the UI
        scores_color = (40, 60, 100)  # Darker, more subtle blue base color
        scores_hover_color = (60, 90, 150)  # Subtle hover color
        
        # Choose color based on hover state
        button_color = scores_hover_color if scores_button.collidepoint(mouse_pos) else scores_color
        
        # Draw button with rounded corners - smaller radius for the smaller button
        pygame.draw.rect(scores_surface, button_color, 
                    (0, 0, scores_button.width, scores_button.height), border_radius=6)
        
        # Add a slight shadow with adjusted size
        shadow = pygame.Surface((scores_button.width, scores_button.height), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 30))
        shadow_rect = shadow.get_rect(topleft=(scores_button.x + 2, scores_button.y + 2))
        screen.blit(shadow, shadow_rect)
        
        # Draw the button
        screen.blit(scores_surface, scores_button)
        
        # Add pulsing glow effect (smaller for this button)
        glow_width = int(abs(math.sin(step / 15)) * 2) + 1  # Reduced from 3 to 2
        glow_rect = scores_button.inflate(4, 4)  # Smaller inflation (4px instead of 6px)
        pygame.draw.rect(screen, (80, 120, 200), glow_rect, glow_width, border_radius=6)
        
        # Center the text properly inside the button
        text_rect = scores_text.get_rect(center=scores_button.center)
        screen.blit(scores_text, text_rect)  # Use scores_text as the surface to blit
        
        # Draw fancy buttons
        for button in buttons:
            rect = button["rect"]
            name = button["text"]
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
        
        # Draw help button (question mark)
        pygame.draw.rect(screen, help_hover if help_button.collidepoint(mouse_pos) else help_color, 
                      help_button, border_radius=20)
        question_text = menu_font.render("?", True, WHITE)
        question_rect = question_text.get_rect(center=help_button.center)
        screen.blit(question_text, question_rect)
        
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
                for button in buttons:
                    if button["rect"].collidepoint(pos):
                        if click_sound: click_sound.play()
                        button["action"]()
                if music_rect.collidepoint(pos):
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
                elif help_button.collidepoint(pos):
                    if click_sound: click_sound.play()
                    show_info_page()
        
        # Advance gradient blend very slowly
        gradient_blend += 0.0001
        if gradient_blend >= 1.0:
            gradient_blend = 0.0
            current_gradient = next_gradient
            next_gradient = (next_gradient + 1) % len(dark_gradients)
        
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
    
    # DEBUG: Print what we loaded to see the issue
    print("Loaded high scores:", high_scores)
    
    # Make absolutely sure we get a numeric value
    classic_high_score = 0  # Default as fallback
    
    # Extra defensive code to ensure we get just an integer
    try:
        if isinstance(high_scores, dict) and "classic" in high_scores:
            if isinstance(high_scores["classic"], dict) and "scores" in high_scores["classic"]:
                scores_list = high_scores["classic"]["scores"]
                if scores_list and isinstance(scores_list, list):
                    # Find the highest number in the list
                    highest = 0
                    for s in scores_list:
                        try:
                            if isinstance(s, (int, float)) and s > highest:
                                highest = s
                        except:
                            pass
                    classic_high_score = highest
            elif isinstance(high_scores["classic"], (int, float)):
                classic_high_score = high_scores["classic"]
    except Exception as e:
        print(f"Error processing high scores: {e}")
        classic_high_score = 0
    
    # Force it to be an integer no matter what
    classic_high_score = int(classic_high_score)
    
    print(f"Final classic_high_score: {classic_high_score} (type: {type(classic_high_score)})")
    
    # Set the record in the game object
    game.record = classic_high_score
    
    # Initialize with current customization settings
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)
    
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
                font_large = pygame.SysFont("Arial", 72)
                font_small = pygame.SysFont("Arial", 36)
                font_medal = pygame.SysFont("Arial", 48)
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))
            score_text = font_small.render(f"Your Score: {score}", True, WHITE)
            continue_text = font_small.render("Press any key to continue", True, (200, 200, 200))
            
            # Prepare new high score celebration if applicable
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, (255, 215, 0))  # Gold color
                
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 100))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2))
            
            # Use a simple integer for the high score display
            highest_score = max(classic_high_score, score)
            # Theme-specific high score color
            if game.background_theme == "dark":
                high_score_color = YELLOW
            else:
                high_score_color = (0, 0, 128)  # DARK BLUE for light theme
            record_text = font_small.render(f"High Score: {highest_score}", True, high_score_color)
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 50))
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
            game.display.blit(record_text, record_rect)
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
                    glow_color = (255, 215, 0)  # Pulsing gold
                    new_record_text = font_medal.render("NEW HIGH SCORE!", True, glow_color)
                    game.display.blit(new_record_text, new_record_rect)
                    pygame.display.update(overlay_rect)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        # Ignore screenshot keys
                        if is_screenshot_key(event.key):
                            continue
                            
                        if click_sound: click_sound.play()
                        waiting = False
                clock.tick(30)
            break

    # Return to main menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def play_fibonacci_game():
    global snake_color, background_theme, screen, enhanced_effects
    
    # Import SPEED directly from snake_game module
    from src.game.snake_game import SPEED
    
    # Calculate slower speed (60% of normal speed = 40% slower)
    fibonacci_speed = int(SPEED * 0.6)
    
    # Initialize game with customized settings and slower speed
    game = FibonacciSnakeGame(speed=fibonacci_speed)
    
    # Apply the enhanced effects setting
    game.enhanced_effects = enhanced_effects
    
    # Load high scores 
    high_scores = load_high_scores()
    
    # Make sure we have a fibonacci category with the right structure
    if "fibonacci" not in high_scores:
        high_scores["fibonacci"] = {
            "scores": [],
            "segments": [],
            "dates": []
        }
    
    # Ensure all required keys exist
    if "scores" not in high_scores["fibonacci"]:
        high_scores["fibonacci"]["scores"] = []
    if "segments" not in high_scores["fibonacci"]:
        high_scores["fibonacci"]["segments"] = []
    if "dates" not in high_scores["fibonacci"]:
        high_scores["fibonacci"]["dates"] = []
    
    # Get highest score for fibonacci mode
    fibonacci_high_score = (0, 0)  # (food_score, fib_value)

    if high_scores["fibonacci"]["scores"] and len(high_scores["fibonacci"]["scores"]) > 0:
        # Find the entry with highest food score
        highest_idx = 0
        highest_food = 0
        
        for i, score in enumerate(high_scores["fibonacci"]["scores"]):
            if score > highest_food:
                highest_food = score
                highest_idx = i
                
        # Get the corresponding fib value
        if "fib_values" in high_scores["fibonacci"] and len(high_scores["fibonacci"]["fib_values"]) > highest_idx:
            fib_value = high_scores["fibonacci"]["fib_values"][highest_idx]
            fibonacci_high_score = (highest_food, fib_value)
        else:
            # Calculate the Fibonacci value if not stored
            fib_value = game.get_fibonacci_at_position(highest_food)
            fibonacci_high_score = (highest_food, fib_value)
    
    # Set the record in the game object
    game.record = fibonacci_high_score
    
    # Initialize with current customization settings
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)
    
    # For compatibility with older code
    game.snake_color = game.snake_theme.head_color
    
    while True:
        over, result = game.play_step()
        if over:
            if isinstance(result, tuple) and len(result) == 2:
                # New format with (score, fib_value)
                score, fib_value = result
            else:
                # Old format with just score
                score = result
                # Calculate the Fibonacci value
                fib_value = game.get_fibonacci_at_position(score)
            
            print(f"Game Over! Food: {score} | Fib: {fib_value}")
            
            # Save high score with food count and Fibonacci number
            is_new_high = save_fibonacci_high_score(score, fib_value)
            
            # Show game over screen
            try:
                font_large = pygame.font.Font("assets/fonts/game_over.ttf", 72)
                font_small = pygame.font.Font("assets/fonts/game_over.ttf", 36)
                font_medal = pygame.font.Font("assets/fonts/game_over.ttf", 48)
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.SysFont("Arial", 72)
                font_small = pygame.SysFont("Arial", 36)
                font_medal = pygame.SysFont("Arial", 48)
            
            # Game over screen texts with theme-based colors
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            
            # Use theme-specific colors for regular text
            if game.background_theme == "dark":
                main_text_color = (255, 255, 255)  # WHITE for dark theme
                high_score_color = (255, 255, 0)   # YELLOW for dark theme
                secondary_color = (180, 180, 180)  # Light gray
                celebration_color = (255, 215, 0)  # Gold color
            else:
                main_text_color = (0, 120, 0)      # Rich green for light theme
                high_score_color = (0, 0, 128)     # DARK BLUE for light theme
                secondary_color = (60, 60, 60)     # Dark gray
                celebration_color = (0, 120, 50)   # Green with blue tint
            
            # Use the theme colors for all text elements
            score_text = font_small.render(f"Score: {score}  |  {fib_value}", True, main_text_color)
            growth_text = font_small.render(f"Total Growth: {game.total_fibonacci_growth}", True, main_text_color)
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Use high score color for record text
            if isinstance(fibonacci_high_score, tuple) and len(fibonacci_high_score) == 2:
                highest_food = max(fibonacci_high_score[0], score)
                highest_fib = max(fibonacci_high_score[1], fib_value)
                record_text = font_small.render(f"High Score: {highest_food}  |  {highest_fib}", True, high_score_color)
            else:
                record_text = font_small.render(f"High Score: {max(fibonacci_high_score, score)}", True, high_score_color)
            
            # New high score text with celebration color
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, celebration_color)
                
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 120))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2 - 30))
            growth_rect = growth_text.get_rect(center=(game.width//2, game.height//2 + 20))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 150))
            
            # Show high score
            if isinstance(fibonacci_high_score, tuple) and len(fibonacci_high_score) == 2:
                highest_food = max(fibonacci_high_score[0], score)
                highest_fib = max(fibonacci_high_score[1], fib_value)
                record_text = font_small.render(f"High Score: {highest_food}  |  {highest_fib}", True, high_score_color)
            else:
                record_text = font_small.render(f"High Score: {max(fibonacci_high_score, score)}", True, high_score_color)
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 70))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 150))
            
            if is_new_high:
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 110))
            
            # Create dark overlay
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(growth_text, growth_rect)
            game.display.blit(record_text, record_rect)
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
                    pygame.draw.rect(game.display, overlay_color[:3] + (180,), overlay_rect)
                    
                    # Pulsing effect using sine wave
                    pulse = abs(math.sin(animation_step / 10)) * 50
                    glow_color = celebration_color
                    new_record_text = font_medal.render("NEW HIGH SCORE!", True, glow_color)
                    game.display.blit(new_record_text, new_record_rect)
                    pygame.display.update(overlay_rect)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        # Ignore screenshot keys
                        if is_screenshot_key(event.key):
                            continue
                            
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
                font_large = pygame.SysFont("Arial", 72)
                font_small = pygame.SysFont("Arial", 36)
                font_medal = pygame.SysFont("Arial", 48)
            
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
                        # Ignore screenshot keys
                        if is_screenshot_key(event.key):
                            continue
                            
                        if click_sound: click_sound.play()
                        waiting = False
                pygame.time.wait(100)
            break
    
    # Return to menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def watch_fibonacci_ai_play():
    """Watch the transferred Fibonacci AI play in the main GUI"""
    global snake_color, background_theme, screen, debug_mode, enhanced_effects
    
    # Initialize agent
    from src.ai.transfer_fibonacci_ai import TransferredFibonacciAgent
    agent = TransferredFibonacciAgent()
    
    # Initialize game with 1280x720 resolution for better viewing
    from src.game.fibonacci_ai import FibonacciGameAI
    game = FibonacciGameAI(width=1280, height=720)
    game.viewing_mode = True  # Enable viewer mode UI
    
    # Apply customization settings
    game.enhanced_effects = enhanced_effects
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)
    game.debug_mode = debug_mode
    
    # For compatibility
    game.snake_color = game.snake_theme.head_color
    
    # Find and load the best available model
    model_path = ""
    model_dir = "data/models"
    checkpoint_dir = "data/checkpoints"
    
    try:
        # First try finetuned models
        model_files = [f for f in os.listdir(model_dir) if f.startswith('fibonacci_transferred_model_finetuned_')]
        
        if model_files:
            # Get the one with the highest game count
            try:
                model_file = max(model_files, key=lambda x: int(x.split('_')[-2]))
                model_path = os.path.join(model_dir, model_file)
            except:
                # If parsing fails, just take the first one
                model_path = os.path.join(model_dir, model_files[0])
        
        # Then try base transferred model
        if not model_path:
            base_model = os.path.join(model_dir, "fibonacci_transferred_model.pth")
            if os.path.exists(base_model):
                model_path = base_model
        
        # Finally try checkpoint model
        if not model_path:
            checkpoint_model = os.path.join(checkpoint_dir, "fibonacci_transferred_checkpoint_model.pth")
            if os.path.exists(checkpoint_model):
                model_path = checkpoint_model
                
        if not model_path or not os.path.exists(model_path):
            print("No Fibonacci AI model found. Please train or transfer a model first.")
            return
            
        print(f"Loading Fibonacci AI model: {os.path.basename(model_path)}")
        agent.model.load_state_dict(torch.load(model_path))
        agent.epsilon = 0  # No random moves when watching
        
    except Exception as e:
        print(f"Error loading Fibonacci AI model: {e}")
        return
    
    # Load high scores
    high_scores = load_high_scores()
    
    # Ensure we have a fibonacci_ai category
    if "fibonacci_ai" not in high_scores:
        high_scores["fibonacci_ai"] = {
            "scores": [],
            "fib_values": [],
            "dates": []
        }
        
    # Get high score
    fibonacci_ai_high_score = 0
    fibonacci_ai_fib_record = 0
    
    if high_scores["fibonacci_ai"]["scores"] and len(high_scores["fibonacci_ai"]["scores"]) > 0:
        fibonacci_ai_high_score = max(high_scores["fibonacci_ai"]["scores"])
        
    if "fib_values" in high_scores["fibonacci_ai"] and high_scores["fibonacci_ai"]["fib_values"]:
        fibonacci_ai_fib_record = max(high_scores["fibonacci_ai"]["fib_values"])
        
    # Set the record in the game
    game.record = fibonacci_ai_high_score
    
    # Very high frame limit for watching
    game.frame_limit_multiplier = 1000
        
    print("Watching Fibonacci AI play. Press ESC to exit, P to pause.")
    
    # Game loop
    done = False
    paused = False
    
    while not done:
        # Get current state
        state = agent.get_state(game)
        
        # Get AI move
        final_move = agent.get_action(state)
        
        # Perform move and get new state
        reward, done, score = game.play_step(final_move)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    done = True
                elif event.key == pygame.K_p:  # Pause
                    if click_sound: click_sound.play()
                    paused = True
                    
                    # Create overlay for pause screen
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
        
        # If game over, save score and show game over screen
        if done:
            # Save scores
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            is_new_high = False
            is_new_fib_high = False
            
            # Check for new high score
            if score > fibonacci_ai_high_score:
                fibonacci_ai_high_score = score
                is_new_high = True
                
            # Check for new Fibonacci record
            if game.fib_score > fibonacci_ai_fib_record:
                fibonacci_ai_fib_record = game.fib_score
                is_new_fib_high = True
            
            # Save the score and Fibonacci value
            high_scores["fibonacci_ai"]["scores"].append(score)
            high_scores["fibonacci_ai"]["fib_values"].append(game.fib_score)
            high_scores["fibonacci_ai"]["dates"].append(current_date)
            
            # Keep only the top 10 scores
            if len(high_scores["fibonacci_ai"]["scores"]) > 10:
                # Sort by score and keep top 10
                scores = high_scores["fibonacci_ai"]["scores"]
                fib_values = high_scores["fibonacci_ai"]["fib_values"]
                dates = high_scores["fibonacci_ai"]["dates"]
                
                combined = list(zip(scores, fib_values, dates))
                combined.sort(reverse(True), key=lambda x: x[0])  # Sort by score
                combined = combined[:10]  # Keep top 10
                
                high_scores["fibonacci_ai"]["scores"] = [item[0] for item in combined]
                high_scores["fibonacci_ai"]["fib_values"] = [item[1] for item in combined]
                high_scores["fibonacci_ai"]["dates"] = [item[2] for item in combined]
            
            # Save high scores to file
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump(high_scores, f, indent=4)
                
            print(f"Game over! Score: {score}, Fibonacci Sum: {game.fib_score}")
            
            # Show game over screen
            try:
                font_large = pygame.font.Font("assets/fonts/game_over.ttf", 72)
                font_small = pygame.font.Font("assets/fonts/game_over.ttf", 36)
                font_medal = pygame.font.Font("assets/fonts/game_over.ttf", 48)
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.SysFont("Arial", 72)
                font_small = pygame.SysFont("Arial", 36)
                font_medal = pygame.SysFont("Arial", 48)
                
            # Dynamic colors based on theme
            if game.background_theme == "dark":
                text_color = WHITE
                secondary_color = (200, 200, 200)
                celebration_color = (255, 215, 0)  # Gold for dark theme
            else:
                text_color = (20, 20, 100)  # Dark blue
                secondary_color = (80, 80, 80)  # Dark gray
                celebration_color = (0, 120, 50)  # Green for light theme
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"Score: {score}", True, text_color)
            fib_score_text = font_small.render(f"Fibonacci Sum: {game.fib_score}", True, text_color)
            record_text = font_small.render(f"Record: {fibonacci_ai_high_score}", True, text_color)
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 120))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2 - 40))
            fib_score_rect = fib_score_text.get_rect(center=(game.width//2, game.height//2 + 10))
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 60))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 140))
            
            # Create overlay for game over screen
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(fib_score_text, fib_score_rect)
            game.display.blit(record_text, record_rect)
            
            # Add celebration if this is a new high score
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, celebration_color)
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 100))
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
                    if isinstance(celebration_color, tuple) and len(celebration_color) >= 3:
                        # Adjust brightness based on pulse
                        glow_r = min(255, celebration_color[0] + pulse)
                        glow_g = min(255, celebration_color[1] + pulse)
                        glow_b = min(255, celebration_color[2] + pulse)
                        glow_color = (glow_r, glow_g, glow_b)
                    else:
                        glow_color = celebration_color
                        
                    new_record_text = font_medal.render("NEW HIGH SCORE!", True, glow_color)
                    game.display.blit(new_record_text, new_record_rect)
                    pygame.display.update(overlay_rect)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        # Ignore screenshot keys
                        if is_screenshot_key(event.key):
                            continue
                            
                        if click_sound: click_sound.play()
                        waiting = False
                pygame.time.wait(100)
            
            # Reset the game
            game.reset()
            
    # Return to menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def settings_page():
    global snake_color, background_theme, screen, debug_mode, enhanced_effects, music_on
    
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
        config["audio"]["music_on"] = music_on
        
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
    
    # Help button - moved to bottom left
    help_button_size = 40
    help_button = pygame.Rect(60, SCREEN_HEIGHT - 60, help_button_size, help_button_size)
    help_color = (80, 100, 180)
    help_hover = (120, 140, 220)
    
    # Create theme preview rects
    preview_size = 180  
    preview_margin = 20 
    preview_cols = 3
    
    # Create a clipping mask for the content area
    content_area = pygame.Rect(0, 200, SCREEN_WIDTH, SCREEN_HEIGHT - 320)
    content_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 320), pygame.SRCALPHA)
    
    # Track button and mouse states
    mouse_pressed = False
    mouse_pos = (0, 0)
    
    # Define consistent button colors
    standard_button_color = (60, 100, 180)  # Blue-ish base color
    standard_button_hover = (100, 150, 250)  # Lighter blue for hover
    
    toggle_on_color = (100, 200, 100)  # Green for ON state
    toggle_off_color = (200, 100, 100)  # Red for OFF state
    
    back_button_color = (180, 60, 60)  # Reddish for exit button
    back_button_hover = (220, 80, 80)  # Lighter red for hover

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
                    
                    # Add help button handler
                    elif help_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        show_settings_help(current_page)  # Pass the current page to show relevant help
                
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
                
            # Use standardized colors for theme buttons
            draw_button(screen, dark_button, "Theme: Dark", menu_font,
                    standard_button_color, standard_button_hover, mouse_pos)
            draw_button(screen, light_button, "Theme: Light", menu_font,
                    standard_button_color, standard_button_hover, mouse_pos)
                    
            # Debug mode toggle button - keep toggle colors
            debug_label = "Debug: ON" if debug_mode else "Debug: OFF"
            debug_color = toggle_on_color if debug_mode else toggle_off_color
            draw_button(screen, debug_button, debug_label, menu_font, debug_color, (150, 150, 150), mouse_pos)
            
            # VS Player Position setting - use standard colors
            vs_position = get_player_position()
            vs_position_text = f"Player Position: {vs_position.title()}"
            
            # Draw the button with standard colors
            if vs_position_button.collidepoint(mouse_pos):
                pygame.draw.rect(screen, standard_button_hover, vs_position_button, border_radius=5)
            else:
                pygame.draw.rect(screen, standard_button_color, vs_position_button, border_radius=5)
            
            text_surface = menu_font.render(vs_position_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(vs_position_button.centerx, vs_position_button.centery))
            screen.blit(text_surface, text_rect)
            
            # Enhanced effects toggle button - keep toggle colors
            enhanced_label = "Level-Up Effects: Enhanced" if enhanced_effects else "Level-Up Effects: Simple"
            enhanced_color = toggle_on_color if enhanced_effects else toggle_off_color
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
        
        # Back button with distinctive color
        draw_fancy_button(screen, back_button, "Back to Menu", menu_font, back_button_color, back_button_hover, mouse_pos, step)
        
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
        
        # Draw help button (question mark)
        pygame.draw.rect(screen, help_hover if help_button.collidepoint(mouse_pos) else help_color, 
                        help_button, border_radius=20)
        question_text = menu_font.render("?", True, WHITE)
        question_rect = question_text.get_rect(center=help_button.center)
        screen.blit(question_text, question_rect)
        
        pygame.display.update()
        step += 1
        clock.tick(60)  # Higher framerate for smoother scrolling

def show_snake_themes():
    """Show snake theme customization dialog"""
    # This would be a simplified version that just shows snake themes
    # You can implement this later if desired
    pass

def show_food_themes():
    """Show food theme customization dialog"""
    # This would be a simplified version that just shows food themes
    # You can implement this later if desired
    pass

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

def show_info_page():
    """Display an information page with game instructions and credits"""
    global screen
    clock = pygame.time.Clock()
    step = 0
    
    # Layout dimensions
    content_area = pygame.Rect(100, 150, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 250)
    content_scroll_y = 0
    max_scroll_y = 0
    scroll_velocity = 0
    
    # Create scrollable content surface - make it large enough for all content
    content_surface = pygame.Surface((content_area.width, 2000), pygame.SRCALPHA)
    
    # Back button
    back_button = pygame.Rect((SCREEN_WIDTH-250)//2, SCREEN_HEIGHT - 80, 250, 50)
    back_button_color = (180, 60, 60)
    back_button_hover = (220, 80, 80)
    
    # Sections to display
    sections = [
        {
            "title": "Game Modes",
            "content": [
                "• Classic Mode -> Traditional snake game, eat food to grow longer. Fast Snake Speed.",
                "• Fibonacci Mode -> Snake grows according to the Fibonacci sequence. Slow Snake Speed.",
                "• Player vs AI -> Compete against the trained AI in split-screen. Slow Snake Speed.",
                "• Watch AI -> Observe the trained AI play either gamemode."
            ]
        },
        {
            "title": "Controls",
            "content": [
                "• Arrow Keys / WASD -> Control the snake direction",
                "• P -> Pause game",
                "• ESC -> Return to menu",
                "• Space -> Toggle debug overlay (if enabled)"
            ]
        },
        {
            "title": "Fibonacci Mode",
            "content": [
                "In Fibonacci mode, the snake follows the Fibonacci sequence (0, 1, 1, 2, 3, 5, 8, 13...).",
                "For each food eaten:",
                "• First food -> No growth (0)",
                "• Second food -> Grow by 1 segment",
                "• Third food -> Grow by 1 segment",
                "• Fourth food -> Grow by 2 segments",
                "• And so on, following the Fibonacci sequence."
            ]
        },
        {
            "title": "AI Training Info",
            "content": [
                "The AI uses deep reinforcement learning to master snake gameplay.",
                "• It was trained using a Deep Q-Network (DQN)",
                "• Learns to avoid walls, its own body, and collect food efficiently",
                "• The Fibonacci AI was created using transfer learning from the classic AI"
            ]
        },
        {
            "title": "Credits",
            "content": [
                "• Game Design & Development -> HEMANTH SSR (github.com/plushycat)",
                "• Source Repository -> github.com/armin2080/Snake-Game-AI",
                "• Graphics & Sound -> Open-source resources and original assets",
            ]
        }
    ]
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient()
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size("Information")[0]) // 2
        glowing_text(screen, "Information", title_font, title_x, 30, YELLOW, step)
        
        # Apply smooth scrolling with inertia
        if abs(scroll_velocity) > 0.5:
            content_scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping factor
        else:
            scroll_velocity = 0
        
        # Clear content surface
        content_surface.fill((0, 0, 0, 0))
        
        # Draw content sections
        y_pos = 20 - content_scroll_y
        total_height = 0
        
        for section in sections:
            if y_pos + 80 > 0 or y_pos < content_area.height:
                # Section title
                title_text = menu_font.render(section["title"], True, (255, 220, 100))
                content_surface.blit(title_text, (30, y_pos))
                y_pos += 70
                
                # Section content with wrapping
                for line in section["content"]:
                    # Basic text wrapping - split long lines
                    words = line.split()
                    line_parts = []
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + word + " "
                        # Check if adding this word would exceed the width
                        if footer_font.size(test_line)[0] < content_area.width - 80:
                            current_line = test_line
                        else:
                            line_parts.append(current_line)
                            current_line = word + " "
                    
                    # Add the last line
                    if current_line:
                        line_parts.append(current_line)
                    
                    # Render wrapped lines
                    for part in line_parts:
                        if y_pos + 40 > 0 or y_pos < content_area.height:
                            text = footer_font.render(part, True, (220, 220, 220))
                            content_surface.blit(text, (50, y_pos))
                            y_pos += 40
                
                # Add spacing between sections
                y_pos += 30
            else:
                # Skip rendering if section is off-screen, but still account for height
                height_estimate = 70 + len(section["content"]) * 40 + 30
                y_pos += height_estimate
            
            # Track total height for scrolling
            total_height = y_pos + content_scroll_y
        
        # Calculate max scroll - account for content and viewport
        max_scroll_y = max(0, total_height - content_area.height + 50)
        
        # Clip and display content
        screen.blit(content_surface, (content_area.topleft), 
                (0, 0, content_area.width, content_area.height))
        
        # Draw content area border
        pygame.draw.rect(screen, (60, 60, 100), content_area, 2, border_radius=12)
        
        # Draw scrollbar if needed
        if max_scroll_y > 0:
            scrollbar_height = max(30, int(content_area.height * content_area.height / (content_area.height + max_scroll_y)))
            scrollbar_y = content_area.top + int((content_area.height - scrollbar_height) * min(1, content_scroll_y / max_scroll_y))
            
            # Draw scrollbar track
            pygame.draw.rect(screen, (60, 60, 80), 
                        (content_area.right + 10, content_area.top, 8, content_area.height), 
                        border_radius=4)
                        
            # Draw scrollbar thumb
            pygame.draw.rect(screen, (120, 120, 160), 
                        (content_area.right + 10, scrollbar_y, 8, scrollbar_height), 
                        border_radius=4)
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back", menu_font, back_button_color, back_button_hover, mouse_pos, step)
        
        pygame.display.update()
        
        # Handle events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:  # Left click
                    if back_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        return
                
                # Mouse wheel scrolling
                if e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
                        
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    return
                # Keyboard scrolling
                elif e.key == pygame.K_UP:
                    scroll_velocity -= 15
                elif e.key == pygame.K_DOWN:
                    scroll_velocity += 15
                elif e.key == pygame.K_PAGEUP:
                    scroll_velocity -= 45
                elif e.key == pygame.K_PAGEDOWN:
                    scroll_velocity += 45
                elif e.key == pygame.K_HOME:
                    content_scroll_y = 0  # Jump to top
                elif e.key == pygame.K_END:
                    content_scroll_y = max_scroll_y  # Jump to bottom
        
        # Clamp scroll position
        if max_scroll_y > 0:
            content_scroll_y = max(0, min(max_scroll_y, content_scroll_y))
        else:
            content_scroll_y = 0
        
        step += 1
        clock.tick(60)

def show_settings_help(current_page=0):
    """Display help information about settings options"""
    global screen
    clock = pygame.time.Clock()
    step = 0
    
    # Layout dimensions
    content_area = pygame.Rect(100, 150, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 250)
    content_scroll_y = 0
    max_scroll_y = 0
    scroll_velocity = 0
    
    # Create scrollable content surface
    content_surface = pygame.Surface((content_area.width, 2000), pygame.SRCALPHA)
    
    # Back button
    back_button = pygame.Rect((SCREEN_WIDTH-250)//2, SCREEN_HEIGHT - 80, 250, 50)
    back_button_color = (180, 60, 60)
    back_button_hover = (220, 80, 80)
    
    # Define help sections based on the current page
    general_sections = [
        {
            "title": "Theme Settings",
            "content": [
                "• Dark Theme: Black background.",
                "• Light Theme: White background."
            ]
        },
        {
            "title": "Debug Mode",
            "content": [
                "• ON: Shows AI vision and decision-making information when watching AI play",
                "• OFF: Normal gameplay without technical overlays",
                "• Toggle with SPACE key during AI gameplay"
            ]
        },
        {
            "title": "Player Position",
            "content": [
                "• Controls the side of the player screen in Player VS AI Mode:",
                "• Either to the left, or to the right of the split screen."
            ]
        },
        {
            "title": "Level-Up Effects",
            "content": [
                "• Enhanced: Show flashy color overlay visual effect every 10 food collected.",
                "• Simple: Minimal visual effects for user preference."
            ]
        }
    ]

    # Choose which sections to display based on current page
    if current_page == 0:
        sections = general_sections
        page_title = "General Settings Help"
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient()
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size(page_title)[0]) // 2
        glowing_text(screen, page_title, title_font, title_x, 30, YELLOW, step)
        
        # Apply smooth scrolling with inertia
        if abs(scroll_velocity) > 0.5:
            content_scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping factor
        else:
            scroll_velocity = 0
        
        # Clear content surface
        content_surface.fill((0, 0, 0, 0))
        
        # Draw content sections
        y_pos = 20 - content_scroll_y
        total_height = 0
        
        for section in sections:
            if y_pos + 80 > 0 or y_pos < content_area.height:
                # Section title
                title_text = menu_font.render(section["title"], True, (255, 220, 100))
                content_surface.blit(title_text, (30, y_pos))
                y_pos += 70
                
                # Section content with wrapping
                for line in section["content"]:
                    # Basic text wrapping - split long lines
                    words = line.split()
                    line_parts = []
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + word + " "
                        # Check if adding this word would exceed the width
                        if footer_font.size(test_line)[0] < content_area.width - 80:
                            current_line = test_line
                        else:
                            line_parts.append(current_line)
                            current_line = word + " "
                    
                    # Add the last line
                    if current_line:
                        line_parts.append(current_line)
                    
                    # Render wrapped lines
                    for part in line_parts:
                        if y_pos + 40 > 0 or y_pos < content_area.height:
                            text = footer_font.render(part, True, (220, 220, 220))
                            content_surface.blit(text, (50, y_pos))
                            y_pos += 40
                
                # Add spacing between sections
                y_pos += 30
            else:
                # Skip rendering if section is off-screen, but still account for height
                height_estimate = 70 + len(section["content"]) * 40 + 30
                y_pos += height_estimate
            
            # Track total height for scrolling
            total_height = y_pos + content_scroll_y
        
        # Calculate max scroll - account for content and viewport
        max_scroll_y = max(0, total_height - content_area.height + 50)
        
        # Clip and display content
        screen.blit(content_surface, (content_area.topleft), 
                (0, 0, content_area.width, content_area.height))
        
        # Draw content area border
        pygame.draw.rect(screen, (60, 60, 100), content_area, 2, border_radius=12)
        
        # Draw scrollbar if needed
        if max_scroll_y > 0:
            scrollbar_height = max(30, int(content_area.height * content_area.height / (content_area.height + max_scroll_y)))
            scrollbar_y = content_area.top + int((content_area.height - scrollbar_height) * min(1, content_scroll_y / max_scroll_y))
            
            # Draw scrollbar track
            pygame.draw.rect(screen, (60, 60, 80), 
                        (content_area.right + 10, content_area.top, 8, content_area.height), 
                        border_radius=4)
                        
            # Draw scrollbar thumb
            pygame.draw.rect(screen, (120, 120, 160), 
                        (content_area.right + 10, scrollbar_y, 8, scrollbar_height), 
                        border_radius=4)
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back", menu_font, back_button_color, back_button_hover, mouse_pos, step)
        
        pygame.display.update()
        
        # Handle events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:  # Left click
                    if back_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        return
                
                # Mouse wheel scrolling
                if e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
                        
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    return
                # Keyboard scrolling
                elif e.key == pygame.K_UP:
                    scroll_velocity -= 15
                elif e.key == pygame.K_DOWN:
                    scroll_velocity += 15
                elif e.key == pygame.K_PAGEUP:
                    scroll_velocity -= 45
                elif e.key == pygame.K_PAGEDOWN:
                    scroll_velocity += 45
                elif e.key == pygame.K_HOME:
                    content_scroll_y = 0  # Jump to top
                elif e.key == pygame.K_END:
                    content_scroll_y = max_scroll_y  # Jump to bottom
        
        # Clamp scroll position
        if max_scroll_y > 0:
            content_scroll_y = max(0, min(max_scroll_y, content_scroll_y))
        else:
            content_scroll_y = 0
        
        step += 1
        clock.tick(60)

if __name__ == "__main__":
    home_page()
