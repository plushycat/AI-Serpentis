import pygame
import math
import sys
from datetime import datetime
from src.game.fibonacci_snake import FibonacciSnakeGame
from src.game.customization import customization
from src.utils.scores import load_high_scores, save_fibonacci_high_score
from src.utils.input_utils import is_screenshot_key
from src.utils.config import load_config

# Import shared globals (without SPEED which doesn't exist)
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, snake_color,  # Remove SPEED from here
    enhanced_effects, click_sound, screen, title_font, menu_font, footer_font
)

# Define SPEED locally if not in shared_globals
SPEED = 10  # Default value, adjust as needed

def play_fibonacci_game():
    # Get config
    config = load_config()
    background_theme = config["appearance"]["background_theme"]
    game_speed = config["gameplay"].get("fibonacci_speed", 8)  # Use fibonacci_speed setting
    
    # Initialize game with customized settings and configured speed
    game = FibonacciSnakeGame(speed=game_speed)
    
    # Apply the background theme and other settings
    game.background_theme = background_theme
    game.enhanced_effects = enhanced_effects
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    
    # Load high scores
    high_scores = load_high_scores()
    
    # Initialize high score variables
    fibonacci_high_score = 0
    fibonacci_high_fib = 0
    
    # Extract high scores
    try:
        if isinstance(high_scores, dict) and "fibonacci" in high_scores:
            if isinstance(high_scores["fibonacci"], dict) and "scores" in high_scores["fibonacci"]:
                scores_list = high_scores["fibonacci"]["scores"]
                if scores_list and isinstance(scores_list, list) and len(scores_list) > 0:
                    fibonacci_high_score = max(scores_list)
            
            if isinstance(high_scores["fibonacci"], dict) and "fib_values" in high_scores["fibonacci"]:
                fib_list = high_scores["fibonacci"]["fib_values"]
                if fib_list and isinstance(fib_list, list) and len(fib_list) > 0:
                    fibonacci_high_fib = max(fib_list)
    except Exception as e:
        print(f"Error processing high scores: {e}")
    
    # Set record in game object - use tuple format (food_count, fib_value)
    game.record = (fibonacci_high_score, fibonacci_high_fib)
    
    # For compatibility with older code
    game.snake_color = game.snake_theme.head_color
    
    while True:
        over, score_info = game.play_step()
        
        if over:
            # Handle both tuple and integer return formats
            if isinstance(score_info, tuple) and len(score_info) == 2:
                score, fib_score = score_info
            else:
                # Old format with just score
                score = score_info
                # Calculate fibonacci sum if possible
                fib_score = game.fib_score if hasattr(game, 'fib_score') else 0
            
            print(f"Game Over! Score: {score}, Fibonacci Sum: {fib_score}")
            
            # Check if this is a new high score for either metric
            is_new_high_score = score > fibonacci_high_score
            is_new_high_fib = fib_score > fibonacci_high_fib
            
            # Save scores and check if it's a new high score
            save_fibonacci_high_score(score, fib_score)
            
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
            
            # Select colors based on theme
            if game.background_theme == "dark":
                text_color = (255, 255, 255)  # White
                secondary_color = (180, 180, 180)  # Light gray
                celebration_color = (255, 215, 0)  # Gold for dark theme
            else:
                text_color = (0, 100, 0)  # Dark green
                secondary_color = (60, 60, 60)  # Dark gray
                celebration_color = (0, 150, 0)  # Green for light theme
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"Food Score: {score}", True, text_color)
            fib_score_text = font_small.render(f"Fibonacci Sum: {fib_score}", True, text_color)
            
            # Record displays
            score_record_text = font_small.render(f"Food Record: {max(fibonacci_high_score, score)}", True, text_color)
            fib_record_text = font_small.render(f"Fib Record: {max(fibonacci_high_fib, fib_score)}", True, text_color)
            
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 150))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2 - 80))
            fib_score_rect = fib_score_text.get_rect(center=(game.width//2, game.height//2 - 40))
            score_record_rect = score_record_text.get_rect(center=(game.width//2, game.height//2 + 0))
            fib_record_rect = fib_record_text.get_rect(center=(game.width//2, game.height//2 + 40))
            
            # Position new high score text if applicable
            if is_new_high_score or is_new_high_fib:
                new_record_text = font_medal.render(
                    f"NEW {'HIGH SCORE' if is_new_high_score else 'FIBONACCI RECORD'}!", True, celebration_color)
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 100))
            
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 160))
            
            # Create overlay for game over screen
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(fib_score_text, fib_score_rect)
            game.display.blit(score_record_text, score_record_rect)
            game.display.blit(fib_record_text, fib_record_rect)
            
            # Add celebration if this is a new high score
            if is_new_high_score or is_new_high_fib:
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
                if (is_new_high_score or is_new_high_fib) and animation_step % 10 == 0:
                    # Redraw just the high score with pulsing effect
                    overlay_rect = pygame.Rect(new_record_rect.left - 20, new_record_rect.top - 10, 
                                            new_record_rect.width + 40, new_record_rect.height + 20)
                    pygame.draw.rect(game.display, overlay_color[:3] + (180,), overlay_rect)
                    
                    # Pulsing effect using sine wave
                    pulse = abs(math.sin(animation_step / 10)) * 50
                    glow_color = celebration_color
                    new_record_text = font_medal.render(
                        f"NEW {'HIGH SCORE' if is_new_high_score else 'FIBONACCI RECORD'}!", True, glow_color)
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