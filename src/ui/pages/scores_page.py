import pygame
import sys
import math
import datetime
from src.utils.scores import load_high_scores
from src.utils.input_utils import is_screenshot_key

# Import shared globals
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, background_theme,
    click_sound, screen, title_font, menu_font, footer_font,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT,
    dark_gradients
)

# Import components
from src.ui.components import (
    draw_smooth_gradient, draw_fancy_button, draw_button, glowing_text,
    WHITE, YELLOW
)

def high_scores_page():
    """Display high scores page"""
    # Set window title
    pygame.display.set_caption("AI Serpentis: High Scores")
    global screen
    clock = pygame.time.Clock()
    
    # Resort scores only when viewing the page
    from src.utils.scores import resort_all_high_scores
    high_scores = resort_all_high_scores()
    
    # More compact UI elements
    button_width = 250
    button_height = 50
    back_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, SCREEN_HEIGHT - 80, button_width, button_height)
    
    # Use standard fonts from shared_globals instead of custom fonts
    
    # Wider mode selection buttons with tabbed layout for 5 buttons
    mode_button_width = 200
    mode_buttons_total_width = mode_button_width * 5 + 20 * 4  # 5 buttons with 20px gaps
    mode_start_x = (SCREEN_WIDTH - mode_buttons_total_width) // 2
    
    mode_buttons = {
        "classic": pygame.Rect(mode_start_x, 120, mode_button_width, 45),
        "fibonacci": pygame.Rect(mode_start_x + mode_button_width + 20, 120, mode_button_width, 45),
        "ai": pygame.Rect(mode_start_x + (mode_button_width + 20) * 2, 120, mode_button_width, 45),
        "fibonacci_ai": pygame.Rect(mode_start_x + (mode_button_width + 20) * 3, 120, mode_button_width, 45),
        "vs_mode": pygame.Rect(mode_start_x + (mode_button_width + 20) * 4, 120, mode_button_width, 45),
    }
    
    # Display names for mode buttons
    mode_display_names = {
        "classic": "Classic Mode",
        "fibonacci": "Fibonacci Mode",
        "ai": "AI (Classic)",
        "fibonacci_ai": "AI (Fibonacci)",
        "vs_mode": "Player VS AI"
    }
    
    # Track current selected mode
    current_mode = "classic"
    
    # Add scrolling functionality
    scroll_y = 0
    scroll_velocity = 0
    max_scroll_y = 0
    
    # Make better use of screen space with wider content area
    header_height = 40
    content_area = pygame.Rect(80, 180 + header_height, SCREEN_WIDTH - 160, 460 - header_height)
    content_surface = pygame.Surface((content_area.width, 2000), pygame.SRCALPHA)
    
    # Define column positions as percentages of content width for consistent alignment
    col_positions = {
        "rank": 0.05,        # 5% from left
        "score": 0.30,       # 30% from left
        "winner": 0.25,      # 25% from left (only for vs_mode)
        "food": 0.25,        # 25% from left (only for fibonacci)
        "fib": 0.55,         # 55% from left
        "date": 0.80         # 80% from left (moved right for more space)
    }
    
    # Define consistent button colors
    back_button_color = (180, 60, 60)
    back_button_hover = (220, 80, 80)
    
    # Tab styling
    tab_inactive = (60, 80, 120)
    tab_active = (100, 140, 220)
    tab_hover = (80, 120, 180)
    
    # Animation step
    step = 0
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient(screen)
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size("High Scores")[0]) // 2
        glowing_text(screen, "High Scores", title_font, title_x, 30, YELLOW, step)
        
        # Draw mode selection buttons with improved tab styling
        pygame.draw.rect(screen, (30, 30, 60), pygame.Rect(0, 110, SCREEN_WIDTH, 65))  # Tab bar background
        
        for mode, button in mode_buttons.items():
            is_current = mode == current_mode
            color = tab_active if is_current else tab_inactive
            hover_color = tab_active if is_current else tab_hover
            
            draw_button(screen, button, mode_display_names[mode], footer_font, 
                    color, hover_color, mouse_pos)
        
        # Apply smooth scrolling with inertia
        if abs(scroll_velocity) > 0.5:
            scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping factor
        else:
            scroll_velocity = 0
        
        # Clear content surface
        content_surface.fill((0, 0, 0, 0))
        
        # Calculate actual column positions in pixels
        col_pixels = {
            "rank": int(content_area.width * col_positions["rank"]),
            "score": int(content_area.width * col_positions["score"]),
            "winner": int(content_area.width * col_positions["winner"]),
            "food": int(content_area.width * col_positions["food"]),
            "fib": int(content_area.width * col_positions["fib"]),
            "date": int(content_area.width * col_positions["date"])
        }
        
        # Draw header background with rounded corners
        header_bg = pygame.Rect(content_area.left, content_area.top - header_height - 5, 
                                content_area.width, header_height)
        pygame.draw.rect(screen, (40, 40, 80), header_bg, border_radius=10)
        
        # Prepare header texts with footer_font (36pt) - matching old_main.py
        header_texts = {
            "rank": footer_font.render("Rank", True, (220, 220, 220)),
            "score": footer_font.render("Score", True, (220, 220, 220)),
            "winner": footer_font.render("Winner", True, (220, 220, 220)),
            "food": footer_font.render("Food", True, (220, 220, 220)),
            "fib": footer_font.render("Fibonacci Sum", True, (220, 220, 220)),
            "date": footer_font.render("Date", True, (220, 220, 220))
        }
        
        # Draw headers based on current mode
        if current_mode in ["classic", "ai"]:
            # Classic and AI modes: Rank, Score, Date
            screen.blit(header_texts["rank"], (content_area.left + col_pixels["rank"] - header_texts["rank"].get_width()//2, 
                                            header_bg.centery - header_texts["rank"].get_height()//2))
            screen.blit(header_texts["score"], (content_area.left + col_pixels["score"] - header_texts["score"].get_width()//2, 
                                            header_bg.centery - header_texts["score"].get_height()//2))
            screen.blit(header_texts["date"], (content_area.left + col_pixels["date"] - header_texts["date"].get_width()//2, 
                                            header_bg.centery - header_texts["date"].get_height()//2))
            
            # Get data for current mode
            scores = high_scores.get(current_mode, {}).get("scores", [])
            dates = high_scores.get(current_mode, {}).get("dates", [])
            
            # Calculate max scroll
            entries_height = max(40, len(scores) * 40)  # Standard row height from old_main.py
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
                    
                    # Score and date - centered in their columns with footer_font (36pt)
                    score_text = footer_font.render(str(score), True, WHITE)
                    date_text = footer_font.render(short_date, True, (180, 180, 180))
                    
                    score_rect = score_text.get_rect(center=(col_pixels["score"], entry_y + 20))
                    date_rect = date_text.get_rect(center=(col_pixels["date"], entry_y + 20))
                    
                    content_surface.blit(score_text, score_rect)
                    content_surface.blit(date_text, date_rect)
                
                entry_y += 40  # Standard spacing from old_main.py
                
        elif current_mode in ["fibonacci", "fibonacci_ai"]:
            # Fibonacci modes: Rank, Food, Fibonacci Sum, Date
            screen.blit(header_texts["rank"], (content_area.left + col_pixels["rank"] - header_texts["rank"].get_width()//2, 
                                            header_bg.centery - header_texts["rank"].get_height()//2))
            screen.blit(header_texts["food"], (content_area.left + col_pixels["food"] - header_texts["food"].get_width()//2, 
                                            header_bg.centery - header_texts["food"].get_height()//2))
            screen.blit(header_texts["fib"], (content_area.left + col_pixels["fib"] - header_texts["fib"].get_width()//2, 
                                            header_bg.centery - header_texts["fib"].get_height()//2))
            screen.blit(header_texts["date"], (content_area.left + col_pixels["date"] - header_texts["date"].get_width()//2, 
                                            header_bg.centery - header_texts["date"].get_height()//2))
            
            # Get data
            scores = high_scores.get(current_mode, {}).get("scores", [])
            fib_values = high_scores.get(current_mode, {}).get("fib_values", [])
            dates = high_scores.get(current_mode, {}).get("dates", [])
            
            # Calculate max scroll
            entries_height = max(40, len(scores) * 40)  # Standard row height
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
                    
                    # Display values with footer_font (36pt)
                    score_text = footer_font.render(str(score), True, WHITE)
                    fib_text = footer_font.render(str(fib_value), True, (255, 215, 0))
                    date_text = footer_font.render(short_date, True, (180, 180, 180))
                    
                    score_rect = score_text.get_rect(center=(col_pixels["food"], entry_y + 20))
                    fib_rect = fib_text.get_rect(center=(col_pixels["fib"], entry_y + 20))
                    date_rect = date_text.get_rect(center=(col_pixels["date"], entry_y + 20))
                    
                    content_surface.blit(score_text, score_rect)
                    content_surface.blit(fib_text, fib_rect)  # Fixed: was incorrectly using fib_rect as the surface
                    content_surface.blit(date_text, date_rect)
                
                entry_y += 40  # Standard spacing from old_main.py
                
        else:  # vs_mode
            # VS mode: Rank, Winner, Score, Date
            screen.blit(header_texts["rank"], (content_area.left + col_pixels["rank"] - header_texts["rank"].get_width()//2, 
                                            header_bg.centery - header_texts["rank"].get_height()//2))
            screen.blit(header_texts["winner"], (content_area.left + col_pixels["winner"] - header_texts["winner"].get_width()//2, 
                                            header_bg.centery - header_texts["winner"].get_height()//2))
            screen.blit(header_texts["score"], (content_area.left + col_pixels["score"] - header_texts["score"].get_width()//2, 
                                            header_bg.centery - header_texts["score"].get_height()//2))
            screen.blit(header_texts["date"], (content_area.left + col_pixels["date"] - header_texts["date"].get_width()//2, 
                                            header_bg.centery - header_texts["date"].get_height()//2))
            
            # Only get vs_mode data, not vs (which is deprecated)
            player_scores = high_scores.get("vs_mode", {}).get("player", {}).get("scores", [])
            player_dates = high_scores.get("vs_mode", {}).get("player", {}).get("dates", [])
            ai_scores = high_scores.get("vs_mode", {}).get("ai", {}).get("scores", [])
            ai_dates = high_scores.get("vs_mode", {}).get("ai", {}).get("dates", [])
            
            # Combine scores
            vs_matches = []
            for score, date in zip(player_scores, player_dates):
                vs_matches.append((score, date, True))  # True = Player score
                
            for score, date in zip(ai_scores, ai_dates):
                vs_matches.append((score, date, False))  # False = AI score
                
            # Sort all matches by score (descending)
            vs_matches.sort(key=lambda x: x[0], reverse=True)
            # Limit to top 10 overall
            vs_matches = vs_matches[:10]
            
            # Calculate max scroll
            entries_height = max(40, len(vs_matches) * 40)  # Standard row height
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
                    
                    # Winner indicator with footer_font (36pt)
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
                    
                    # Score and date with footer_font (36pt)
                    score_text = footer_font.render(str(score), True, WHITE)
                    date_text = footer_font.render(short_date, True, (180, 180, 180))
                    
                    score_rect = score_text.get_rect(center=(col_pixels["score"], entry_y + 20))
                    date_rect = date_text.get_rect(center=(col_pixels["date"], entry_y + 20))
                    
                    content_surface.blit(score_text, score_rect)
                    content_surface.blit(date_text, date_rect)
                
                entry_y += 40  # Standard spacing from old_main.py
        
        # Show message if no scores with menu_font (48pt) - matching old_main.py
        if ((current_mode in ["classic", "ai", "fibonacci", "fibonacci_ai"] and 
            not high_scores.get(current_mode, {}).get("scores", [])) or 
            (current_mode == "vs_mode" and not vs_matches)):
            no_scores_text = menu_font.render("No scores recorded yet!", True, (200, 200, 200))
            no_scores_rect = no_scores_text.get_rect(center=(content_area.width // 2, 150))
            content_surface.blit(no_scores_text, no_scores_rect)
        
        # Blit the content surface with proper clipping
        screen.blit(content_surface, (content_area.topleft), 
                (0, 0, content_area.width, content_area.height))
        
        # Draw scrollbar if needed
        has_content = ((current_mode in ["classic", "ai", "fibonacci", "fibonacci_ai"] and 
                    high_scores.get(current_mode, {}).get("scores", [])) or 
                    (current_mode == "vs_mode" and vs_matches))
                    
        if max_scroll_y > 0 and has_content:
            # Calculate scrollbar position and size
            scrollbar_height = max(30, int(content_area.height * content_area.height / (content_area.height + max_scroll_y)))
            scrollbar_y = content_area.top + int((content_area.height - scrollbar_height) * min(1, scroll_y / max_scroll_y))
            
            # Draw scrollbar track
            pygame.draw.rect(screen, (60, 60, 80), 
                        (content_area.right + 10, content_area.top, 8, content_area.height), 
                        border_radius=4)
                        
            # Draw scrollbar thumb - using exact style from old_main.py
            pygame.draw.rect(screen, (120, 120, 160), 
                        (content_area.right + 10, scrollbar_y, 8, scrollbar_height), 
                        border_radius=4)
        
        # Draw back button with footer_font (36pt) - matching old_main.py
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
                    pygame.display.set_caption("AI Serpentis")
                    return
                
                # Mode selection buttons
                for mode, rect in mode_buttons.items():
                    if rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_mode = mode
                        scroll_y = 0  # Reset scroll position when switching modes
                        scroll_velocity = 0
                
                # Mouse wheel scrolling
                if e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
                        
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    pygame.display.set_caption("AI Serpentis")
                    return
                # Add keyboard scrolling
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