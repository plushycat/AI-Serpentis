import pygame
import sys
import math
import datetime
import json
import torch
import os
from src.game.snake_ai import SnakeGameAI
from src.game.fibonacci_ai import FibonacciGameAI
from src.ai.agent import Agent
from src.ai.transfer_fibonacci_ai import TransferredFibonacciAgent
from src.game.customization import customization
from src.utils.scores import load_high_scores, save_high_score
from src.utils.input_utils import is_screenshot_key
from src.utils.config import load_config, save_config  # Add this import

# Import shared globals instead of from home_page
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, snake_color, background_theme,
    enhanced_effects, debug_mode, click_sound, screen, title_font, menu_font, footer_font
)

# File paths
HIGHSCORE_FILE = "data/stats/highscores.json"
CONFIG_FILE = "statics/game_settings.json"  # Add this constant
WHITE = (255, 255, 255)

# Helper function to ensure debug_mode is up-to-date
def get_current_debug_mode():
    """Get the current debug mode setting from config file"""
    global debug_mode
    try:
        config = load_config()
        if config and "gameplay" in config and "debug_mode" in config["gameplay"]:
            debug_mode = config["gameplay"]["debug_mode"]
    except Exception as e:
        print(f"Error loading debug mode setting: {e}")
    return debug_mode

# Helper function to save debug mode changes
def save_debug_mode_setting(new_value):
    """Save the debug mode setting to config file"""
    global debug_mode
    try:
        config = load_config()
        if config and "gameplay" in config:
            config["gameplay"]["debug_mode"] = new_value
            save_config(config)
            debug_mode = new_value
    except Exception as e:
        print(f"Error saving debug mode setting: {e}")

def watch_ai_play():
    """Watch the trained AI play classic Snake"""
    global background_theme, screen, debug_mode, enhanced_effects
    
    # Get latest debug mode setting from config
    debug_mode = get_current_debug_mode()
    
    # Load theme from config
    config = load_config()
    background_theme = config.get("appearance", {}).get("background_theme", "dark")
    
    # Initialize the AI agent
    agent = Agent()
    
    # Initialize game with 1280x720 resolution for better viewing
    game = SnakeGameAI(width=1280, height=720)
    game.viewing_mode = True  # Enable viewer mode UI
    game.background_theme = background_theme  # Set the theme
    
    # Apply customization settings
    game.enhanced_effects = enhanced_effects
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)
    game.debug_mode = debug_mode  # Initial debug mode state
    
    # For compatibility
    game.snake_color = game.snake_theme.head_color
    
    # Find and load the best available model
    model_path = ""
    model_dir = "data/models"
    checkpoint_dir = "data/checkpoints"
    
    try:
        # First try to load trained models
        if os.path.exists(os.path.join(model_dir, "model.pth")):
            model_path = os.path.join(model_dir, "model.pth")
            
        # If no model found, try checkpoint
        elif os.path.exists(os.path.join(checkpoint_dir, "checkpoint_model.pth")):
            model_path = os.path.join(checkpoint_dir, "checkpoint_model.pth")
            
        if not model_path:
            print("No trained AI model found. Please train one first.")
            return
            
        print(f"Loading AI model: {os.path.basename(model_path)}")
        agent.model.load_state_dict(torch.load(model_path))
        agent.epsilon = 0  # No random moves when watching
        
    except Exception as e:
        print(f"Error loading AI model: {e}")
        return
    
    # Load high scores
    high_scores = load_high_scores()
    
    # Ensure we have an ai category
    if "ai" not in high_scores:
        high_scores["ai"] = {
            "scores": [],
            "dates": []
        }
        
    # Get high score
    ai_high_score = 0
    
    if high_scores["ai"]["scores"] and len(high_scores["ai"]["scores"]) > 0:
        ai_high_score = max(high_scores["ai"]["scores"])
        
    # Set the record in the game
    game.record = ai_high_score
    
    # Very high frame limit for AI viewing
    game.frame_limit_multiplier = 1000
        
    print("Watching AI play. Press ESC to exit, P to pause.")
    
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
                elif event.key == pygame.K_p:
                    if click_sound: click_sound.play()
                    paused = True
                    
                    # Create pause overlay
                    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120))  # Semi-transparent black
                    game.display.blit(overlay, (0, 0))
                    
                    # Draw pause text
                    pause_text = game.sub_font.render('PAUSED - Press P to continue', True, WHITE)
                    game.display.blit(pause_text, (game.width//2 - pause_text.get_width()//2, game.height//2))
                    pygame.display.update()
                    
                    # Pause loop
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
                
                # Add debug mode toggle with SPACE key
                elif event.key == pygame.K_SPACE:
                    debug_mode = not debug_mode  # Toggle global debug mode
                    game.debug_mode = debug_mode  # Update game's debug mode
                    # Save the changed setting
                    save_debug_mode_setting(debug_mode)
                    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
        
        # If game over, save score and show game over screen
        if done:
            # Save scores
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            is_new_high = False
            
            # Check for new high score
            if score > ai_high_score:
                ai_high_score = score
                is_new_high = True
            
            # Save the score
            high_scores["ai"]["scores"].append(score)
            high_scores["ai"]["dates"].append(current_date)
            
            # Keep only the top 10 scores
            if len(high_scores["ai"]["scores"]) > 10:
                # Sort by score and keep top 10
                combined = list(zip(high_scores["ai"]["scores"], high_scores["ai"]["dates"]))
                combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
                combined = combined[:10]  # Keep top 10
                
                high_scores["ai"]["scores"] = [item[0] for item in combined]
                high_scores["ai"]["dates"] = [item[1] for item in combined]
            
            # Save high scores to file
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump(high_scores, f, indent=4)
                
            print(f"Game over! Score: {score}")
            
            # Show game over screen
            try:
                font_large = pygame.font.Font("assets/fonts/game_over.ttf", 72)
                font_small = pygame.font.Font("assets/fonts/game_over.ttf", 36)
                font_medal = pygame.font.Font("assets/fonts/game_over.ttf", 48)
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.font.SysFont("Arial", 72)
                font_small = pygame.font.SysFont("Arial", 36)
                font_medal = pygame.font.SysFont("Arial", 48)
                
            # Dynamic colors based on theme
            if game.background_theme == "dark":
                text_color = WHITE
                secondary_color = (180, 180, 180)  # Light gray
                celebration_color = (255, 215, 0)  # Gold for dark theme
            else:
                text_color = (20, 20, 100)  # Dark blue
                secondary_color = (80, 80, 80)  # Dark gray
                celebration_color = (0, 120, 50)  # Green for light theme
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"Score: {score}", True, text_color)
            record_text = font_small.render(f"Record: {ai_high_score}", True, text_color)
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 100))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2 - 20))
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 40))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 120))
            
            # Create overlay for game over screen
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(record_text, record_rect)
            
            # Add celebration if this is a new high score
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, celebration_color)
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 80))
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
                    
                    # Create glow effect with RGB components
                    if game.background_theme == "dark":
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
            break
            
    # Return to menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def watch_fibonacci_ai_play():
    """Watch the transferred Fibonacci AI play"""
    global snake_color, background_theme, screen, debug_mode, enhanced_effects
    
    # Get latest debug mode setting from config
    debug_mode = get_current_debug_mode()
    
    # Load theme from config
    config = load_config()
    background_theme = config.get("appearance", {}).get("background_theme", "dark")
    
    # Initialize agent
    agent = TransferredFibonacciAgent()
    
    # Initialize game with 1280x720 resolution for better viewing
    game = FibonacciGameAI(width=1280, height=720)
    game.viewing_mode = True  # Enable viewer mode UI
    game.background_theme = background_theme  # Set the theme
    
    # Apply customization settings
    game.enhanced_effects = enhanced_effects
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.set_theme(background_theme)
    game.debug_mode = debug_mode  # Initial debug mode state
    
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
    game.record = (fibonacci_ai_high_score, fibonacci_ai_fib_record)  # Pass as tuple
    
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
                elif event.key == pygame.K_p:
                    if click_sound: click_sound.play()
                    paused = True
                    
                    # Create pause overlay
                    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120))  # Semi-transparent black
                    game.display.blit(overlay, (0, 0))
                    
                    # Draw pause text
                    pause_text = game.sub_font.render('PAUSED - Press P to continue', True, WHITE)
                    game.display.blit(pause_text, (game.width//2 - pause_text.get_width()//2, game.height//2))
                    pygame.display.update()
                    
                    # Pause loop
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
                
                # Add debug mode toggle with SPACE key
                elif event.key == pygame.K_SPACE:
                    debug_mode = not debug_mode  # Toggle global debug mode 
                    game.debug_mode = debug_mode  # Update game's debug mode
                    # Save the changed setting
                    save_debug_mode_setting(debug_mode)
                    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
        
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
                combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
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
                font_large = pygame.font.SysFont("Arial", 72)
                font_small = pygame.font.SysFont("Arial", 36)
                font_medal = pygame.font.SysFont("Arial", 48)
                
            # Dynamic colors based on theme
            if game.background_theme == "dark":
                text_color = WHITE
                secondary_color = (180, 180, 180)  # Light gray
                celebration_color = (255, 215, 0)  # Gold for dark theme
            else:
                text_color = (20, 20, 100)  # Dark blue
                secondary_color = (80, 80, 80)  # Dark gray
                celebration_color = (0, 120, 50)  # Green for light theme
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"Score: {score}", True, text_color)
            fib_score_text = font_small.render(f"Fibonacci Sum: {game.fib_score}", True, text_color)
            record_text = font_small.render(f"Record: {fibonacci_ai_high_score} | {fibonacci_ai_fib_record}", True, text_color)
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
                    
                    # Create glow effect with RGB components
                    if game.background_theme == "dark":
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
            break
            
    # Return to menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")