import pygame
import sys
import math
import json
import os
from src.game.customization import customization
from src.utils.input_utils import is_screenshot_key
from src.utils.config import load_config, save_config
from src.ui.pages.settings_help_page import show_settings_help  # Import the help page function

# Import shared globals instead of from home_page
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, background_theme, enhanced_effects,
    debug_mode, click_sound, screen, title_font, menu_font, footer_font,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT,
    dark_gradients, music_on  # Added missing import
)

# Import the missing function
from src.ui.components import (
    draw_smooth_gradient, draw_fancy_button, draw_button, glowing_text,
    WHITE, YELLOW
)

def settings_page():
    """Display and manage game settings"""
    global music_on, background_theme, debug_mode, enhanced_effects
    
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
    
    # Create buttons for all pages with improved spacing
    tab_spacing = 20  # Add spacing between tabs
    total_width = 3 * button_width + 2 * tab_spacing
    start_x = (SCREEN_WIDTH - total_width) // 2
    
    general_button = pygame.Rect(start_x, 120, button_width, button_height)
    snake_button = pygame.Rect(start_x + button_width + tab_spacing, 120, button_width, button_height)
    food_button = pygame.Rect(start_x + 2 * button_width + 2 * tab_spacing, 120, button_width, button_height)
    
    # General page buttons (Theme buttons)
    dark_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 200, button_width, button_height)
    light_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 280, button_width, button_height)
    debug_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 360, button_width, button_height)
    vs_position_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 440, button_width, button_height)
    enhanced_effects_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 520, button_width, button_height)
    
    # Back button
    back_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, SCREEN_HEIGHT - 100, button_width, button_height)
    
    # Help button - add to bottom left corner like on home page
    help_button_size = 50
    help_button = pygame.Rect(20, SCREEN_HEIGHT - 70, help_button_size, help_button_size)
    help_color = (80, 100, 180)
    help_hover = (120, 140, 220)
    
    # Pre-render help button elements
    question_text = menu_font.render("?", True, WHITE)
    help_shadow = pygame.Surface((help_button_size, help_button_size), pygame.SRCALPHA)
    help_shadow.fill((0, 0, 0, 30))
    
    # Create theme preview rects
    preview_size = 180  
    preview_margin = 20 
    preview_cols = 3
    preview_width = preview_cols * (preview_size + preview_margin) - preview_margin
    
    # Create a clipping mask for the content area
    content_area = pygame.Rect(0, 210, SCREEN_WIDTH, SCREEN_HEIGHT - 330)
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
        
        draw_smooth_gradient(screen)
        
        # Settings title with improved vertical spacing
        title_x = (SCREEN_WIDTH - title_font.size("Settings")[0]) // 2
        glowing_text(screen, "Settings", title_font, title_x, 40, YELLOW, step)
        
        # Highlight the active tab (keeping just the button coloring)
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
                    
                    # Help button
                    elif help_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        show_settings_help(current_page)
                
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
                
            # Use theme-specific colors for theme buttons instead of standard colors
            dark_theme_color = (40, 40, 50)  # Dark gray
            dark_theme_hover = (60, 60, 80)  # Slightly lighter dark gray
            
            light_theme_color = (230, 230, 240)  # Very light gray (almost white)
            light_theme_hover = (250, 250, 255)  # White
            
            # Dark theme button with dark colors
            draw_button(screen, dark_button, "Theme: Dark", menu_font,
                    dark_theme_color, dark_theme_hover, mouse_pos)
            
            # Light theme button with light colors - use dark text
            is_hover = light_button.collidepoint(mouse_pos)
            color = light_theme_hover if is_hover else light_theme_color
            pygame.draw.rect(screen, color, light_button, border_radius=12)
            
            # Dark text for light button for better contrast
            text_surface = menu_font.render("Theme: Light", True, (20, 20, 30))
            text_rect = text_surface.get_rect(center=light_button.center)
            screen.blit(text_surface, text_rect)
                    
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
                    
                    # Check hover using the adjusted content_mouse_pos
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
        
        # Draw help button (same style as in home_page.py)
        help_surface = pygame.Surface((help_button.width, help_button.height), pygame.SRCALPHA)
        
        # Change color based on hover state
        current_help_color = help_hover if help_button.collidepoint(mouse_pos) else help_color
        pygame.draw.rect(help_surface, current_help_color, 
                    (0, 0, help_button.width, help_button.height), border_radius=20)
        
        # Add shadow for depth
        screen.blit(help_shadow, (help_button.x + 2, help_button.y + 2))
        screen.blit(help_surface, help_button)
        
        # Add pulsing glow effect
        help_glow_width = int(abs(math.sin(step / 15)) * 2) + 1
        help_glow_rect = help_button.inflate(4, 4)
        pygame.draw.rect(screen, (80, 120, 200), help_glow_rect, help_glow_width, border_radius=20)
        
        # Center the question mark in the button
        question_rect = question_text.get_rect(center=help_button.center)
        screen.blit(question_text, question_rect)
        
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


def get_player_position():
    """Get the current player position for VS mode"""
    config = load_config()
    return config["gameplay"].get("player_position", "left")

def save_player_position(position):
    """Save the player position setting"""
    config = load_config()
    config["gameplay"]["player_position"] = position
    save_config(config)