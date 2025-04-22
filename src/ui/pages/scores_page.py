import pygame
import sys
import math
from src.utils.scores import load_high_scores
from src.utils.input_utils import is_screenshot_key

# Import shared globals instead of from home_page
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, background_theme,
    click_sound, screen, title_font, menu_font, footer_font,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT
)

def high_scores_page():
    """Display high scores for all game modes"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    step = 0
    
    # Load high scores
    high_scores = load_high_scores()
    
    # Define categories and their display names
    categories = {
        "classic": "Classic Mode",
        "fibonacci": "Fibonacci Mode",
        "ai": "AI (Classic)",
        "fibonacci_ai": "AI (Fibonacci)",
        "vs": "Player vs AI"
    }
    
    # Define available modes for each category
    modes = {
        "classic": ["scores"],
        "fibonacci": ["scores", "fib_values"],
        "ai": ["scores"],
        "fibonacci_ai": ["scores", "fib_values"],
        "vs": ["player", "ai"]
    }
    
    # Define display names for modes
    mode_names = {
        "scores": "Food Score",
        "fib_values": "Fibonacci Score",
        "player": "Player Scores",
        "ai": "AI Scores"
    }
    
    # Start with classic mode selected
    current_category = "classic"
    current_mode = "scores"  # Default to scores mode
    
    # Scrolling variables
    scroll_y = 0
    scroll_velocity = 0
    max_scroll_y = 0
    
    # Create buttons for categories
    category_buttons = {}
    button_width = 180
    button_spacing = 20
    button_height = 40
    button_x = (SCREEN_WIDTH - (button_width * len(categories) + button_spacing * (len(categories) - 1))) // 2
    
    for i, (category, name) in enumerate(categories.items()):
        category_buttons[category] = pygame.Rect(
            button_x + i * (button_width + button_spacing), 
            120, 
            button_width, 
            button_height
        )
    
    # Create buttons for modes
    mode_buttons = {}
    
    # Back button
    back_button = pygame.Rect(20, 20, 100, 40)
    back_button_color = (180, 60, 60)
    back_button_hover = (220, 80, 80)
    
    # Main loop
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient(screen)
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size("High Scores")[0]) // 2
        glowing_text(screen, "High Scores", title_font, title_x, 30, YELLOW, step)
        
        # Draw category buttons
        for category, rect in category_buttons.items():
            color = (100, 150, 240) if category == current_category else (70, 100, 170)
            hover_color = (150, 200, 255) if category == current_category else (100, 140, 210)
            
            is_hovered = rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, hover_color if is_hovered else color, rect, border_radius=10)
            
            # Add highlight for selected category
            if category == current_category:
                highlight = pygame.Surface((rect.width + 4, rect.height + 4), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (255, 255, 255, 80), 
                              (0, 0, rect.width + 4, rect.height + 4), 2, border_radius=12)
                screen.blit(highlight, (rect.x - 2, rect.y - 2))
            
            cat_text = menu_font.render(categories[category], True, WHITE)
            text_rect = cat_text.get_rect(center=rect.center)
            screen.blit(cat_text, text_rect)
        
        # Draw mode selection buttons if there are multiple modes
        if len(modes[current_category]) > 1:
            # Create mode buttons dynamically
            mode_buttons = {}
            mode_button_width = 150
            mode_button_x = (SCREEN_WIDTH - (mode_button_width * len(modes[current_category]) + 
                           button_spacing * (len(modes[current_category]) - 1))) // 2
            
            for i, mode in enumerate(modes[current_category]):
                mode_buttons[mode] = pygame.Rect(
                    mode_button_x + i * (mode_button_width + button_spacing),
                    180,
                    mode_button_width,
                    button_height
                )
                
                color = (80, 130, 200) if mode == current_mode else (60, 80, 140)
                hover_color = (120, 180, 220) if mode == current_mode else (80, 110, 180)
                
                is_hovered = mode_buttons[mode].collidepoint(mouse_pos)
                pygame.draw.rect(screen, hover_color if is_hovered else color, 
                              mode_buttons[mode], border_radius=8)
                
                # Add highlight for selected mode
                if mode == current_mode:
                    highlight = pygame.Surface((mode_buttons[mode].width + 4, mode_buttons[mode].height + 4), pygame.SRCALPHA)
                    pygame.draw.rect(highlight, (255, 255, 255, 80), 
                                  (0, 0, mode_buttons[mode].width + 4, mode_buttons[mode].height + 4), 2, border_radius=10)
                    screen.blit(highlight, (mode_buttons[mode].x - 2, mode_buttons[mode].y - 2))
                
                mode_text = menu_font.render(mode_names[mode], True, WHITE)
                text_rect = mode_text.get_rect(center=mode_buttons[mode].center)
                screen.blit(mode_text, text_rect)
        
        # Draw scores for selected category and mode
        content_area = pygame.Rect(SCREEN_WIDTH//2 - 300, 250, 600, 400)
        
        # Apply scroll
        content_scroll_y = max(0, min(max_scroll_y, scroll_y))
        
        # Create content surface
        content_surface = pygame.Surface((content_area.width, content_area.height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0))
        
        # Draw content based on category and mode
        y_pos = 20 - content_scroll_y
        
        # Handle vs mode differently
        if current_category == "vs" and current_mode in ["player", "ai"]:
            if current_mode in high_scores.get("vs", {}):
                scores = high_scores["vs"][current_mode]["scores"]
                dates = high_scores["vs"][current_mode]["dates"]
                
                # Draw header
                header_text = menu_font.render("Score", True, (255, 220, 100))
                date_text = menu_font.render("Date", True, (255, 220, 100))
                
                content_surface.blit(header_text, (50, y_pos))
                content_surface.blit(date_text, (350, y_pos))
                y_pos += 50
                
                # Draw scores
                for i, (score, date) in enumerate(zip(scores, dates)):
                    if i < 10:  # Limit to top 10
                        score_text = footer_font.render(f"{score}", True, WHITE)
                        date_text = footer_font.render(f"{date}", True, WHITE)
                        
                        # Add medal for top 3
                        if i < 3:
                            medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                            pygame.draw.circle(content_surface, medal_colors[i], (25, y_pos + 12), 10)
                        
                        rank_text = footer_font.render(f"{i+1}.", True, WHITE)
                        content_surface.blit(rank_text, (10 if i >= 3 else 50, y_pos))
                        content_surface.blit(score_text, (100, y_pos))
                        content_surface.blit(date_text, (350, y_pos))
                        y_pos += 40
                
                # No scores message
                if not scores:
                    no_scores_text = footer_font.render("No scores recorded yet.", True, WHITE)
                    content_surface.blit(no_scores_text, (content_area.width//2 - no_scores_text.get_width()//2, 50))
        else:
            # Standard category handling
            if current_category in high_scores and current_mode == "scores":
                scores = high_scores[current_category]["scores"]
                dates = high_scores[current_category]["dates"]
                
                # Draw header
                header_text = menu_font.render("Score", True, (255, 220, 100))
                date_text = menu_font.render("Date", True, (255, 220, 100))
                
                content_surface.blit(header_text, (50, y_pos))
                content_surface.blit(date_text, (350, y_pos))
                y_pos += 50
                
                # Draw scores
                for i, (score, date) in enumerate(zip(scores, dates)):
                    if i < 10:  # Limit to top 10
                        score_text = footer_font.render(f"{score}", True, WHITE)
                        date_text = footer_font.render(f"{date}", True, WHITE)
                        
                        # Add medal for top 3
                        if i < 3:
                            medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                            pygame.draw.circle(content_surface, medal_colors[i], (25, y_pos + 12), 10)
                        
                        rank_text = footer_font.render(f"{i+1}.", True, WHITE)
                        content_surface.blit(rank_text, (10 if i >= 3 else 50, y_pos))
                        content_surface.blit(score_text, (100, y_pos))
                        content_surface.blit(date_text, (350, y_pos))
                        y_pos += 40
                
                # No scores message
                if not scores:
                    no_scores_text = footer_font.render("No scores recorded yet.", True, WHITE)
                    content_surface.blit(no_scores_text, (content_area.width//2 - no_scores_text.get_width()//2, 50))
            
            # Handle Fibonacci values
            elif current_category in high_scores and current_mode == "fib_values":
                if "fib_values" in high_scores[current_category]:
                    fib_values = high_scores[current_category]["fib_values"]
                    dates = high_scores[current_category]["dates"]
                    
                    # Draw header
                    header_text = menu_font.render("Fibonacci Sum", True, (255, 220, 100))
                    date_text = menu_font.render("Date", True, (255, 220, 100))
                    
                    content_surface.blit(header_text, (50, y_pos))
                    content_surface.blit(date_text, (350, y_pos))
                    y_pos += 50
                    
                    # Draw fibonacci values
                    for i, (fib, date) in enumerate(zip(fib_values, dates)):
                        if i < 10:  # Limit to top 10
                            fib_text = footer_font.render(f"{fib}", True, WHITE)
                            date_text = footer_font.render(f"{date}", True, WHITE)
                            
                            # Add medal for top 3
                            if i < 3:
                                medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                                pygame.draw.circle(content_surface, medal_colors[i], (25, y_pos + 12), 10)
                            
                            rank_text = footer_font.render(f"{i+1}.", True, WHITE)
                            content_surface.blit(rank_text, (10 if i >= 3 else 50, y_pos))
                            content_surface.blit(fib_text, (100, y_pos))
                            content_surface.blit(date_text, (350, y_pos))
                            y_pos += 40
                    
                    # No scores message
                    if not fib_values:
                        no_scores_text = footer_font.render("No Fibonacci scores recorded yet.", True, WHITE)
                        content_surface.blit(no_scores_text, (content_area.width//2 - no_scores_text.get_width()//2, 50))
        
        # Calculate max scroll
        max_scroll_y = max(0, y_pos + content_scroll_y - content_area.height + 50)
        
        # Draw content
        screen.blit(content_surface, content_area)
        
        # Draw scrollbar if needed
        if max_scroll_y > 0:
            # Draw scrollbar track
            scrollbar_track = pygame.Rect(content_area.right + 10, content_area.top, 8, content_area.height)
            pygame.draw.rect(screen, (60, 60, 80), scrollbar_track, border_radius=4)
            
            # Draw scrollbar thumb - size based on content ratio
            thumb_height = max(30, int(content_area.height * content_area.height / (content_area.height + max_scroll_y)))
            thumb_pos = content_area.top + int((content_area.height - thumb_height) * content_scroll_y / max_scroll_y)
            pygame.draw.rect(screen, (120, 120, 160), 
                          (scrollbar_track.x, thumb_pos, scrollbar_track.width, thumb_height), 
                          border_radius=4)
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back", menu_font, back_button_color, back_button_hover, mouse_pos, step)
        
        # Update display
        pygame.display.update()
        
        # Handle events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                # Back button
                if back_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    return
                
                # Category selection
                for category, rect in category_buttons.items():
                    if rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_category = category
                        current_mode = modes[category][0]  # Select first mode by default
                        scroll_y = 0  # Reset scroll position
                
                # Mode selection
                for mode, rect in mode_buttons.items():
                    if rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_mode = mode
                        scroll_y = 0  # Reset scroll position
                
                # Mouse wheel scrolling
                if e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
            
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    return
                elif e.key == pygame.K_UP:
                    scroll_velocity -= 15
                elif e.key == pygame.K_DOWN:
                    scroll_velocity += 15
                elif e.key == pygame.K_PAGEUP:
                    scroll_velocity -= 60
                elif e.key == pygame.K_PAGEDOWN:
                    scroll_velocity += 60
                elif e.key == pygame.K_HOME:
                    scroll_y = 0
                elif e.key == pygame.K_END:
                    scroll_y = max_scroll_y
        
        # Apply smooth scrolling with momentum
        if abs(scroll_velocity) > 0.1:
            scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping
        else:
            scroll_velocity = 0
            
        # Clamp scrolling boundaries
        if scroll_y < 0:
            scroll_y = 0
            scroll_velocity = 0
        elif scroll_y > max_scroll_y:
            scroll_y = max_scroll_y
            scroll_velocity = 0
            
        step += 1
        clock.tick(60)