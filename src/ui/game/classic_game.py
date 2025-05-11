import pygame
import math
import sys
from src.game.snake_game import SnakeGame
from src.game.customization import customization
from src.utils.scores import load_high_scores, save_high_score
from src.utils.input_utils import is_screenshot_key

# updated settings manager
from src.utils.settings_manager import get_setting
game_speed = get_setting("gameplay", "classic_speed", 10)  # Default 10
# Import shared globals instead of from home_page
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, snake_color, background_theme,
    enhanced_effects, click_sound, screen, title_font, menu_font, footer_font
)

def play_classic_game():
    """Play the classic Snake Game"""
        # Set window title at the beginning
    pygame.display.set_caption("AI Serpentis: Classic Mode")

    from src.utils.sound_manager import sound_manager
    sound_manager.refresh_settings()
    
    from src.utils.settings_manager import get_setting
    game_speed = get_setting("gameplay", "classic_speed", 10)
    current_theme = get_setting("appearance", "background_theme", "dark")
    
    # Initialize game with customized settings
    game = SnakeGame(speed=game_speed)
    
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
    game.set_theme(current_theme)  # Use the theme loaded directly from config
    
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
            
            # Select colors based on theme
            if game.background_theme == "dark":
                text_color = (255, 255, 255)  # White for dark theme
                secondary_color = (180, 180, 180)  # Light gray
                celebration_color = (255, 215, 0)  # Gold for dark theme
            else:
                text_color = (0, 100, 0)  # Dark green for light theme
                secondary_color = (60, 60, 60)  # Dark gray
                celebration_color = (0, 150, 0)  # Green for light theme

            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"Your Score: {score}", True, text_color)
            record_text = font_small.render(f"Record: {max(classic_high_score, score)}", True, text_color)
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Prepare new high score celebration if applicable
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, celebration_color)  # Celebration color based on theme
                
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 100))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2))
            
            # Use a simple integer for the high score display
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 50))
            
            if is_new_high:
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 100))
                
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 150))
            
            # Create overlay for game over screen
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
    pygame.display.set_caption("AI Serpentis")
    return