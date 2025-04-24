import pygame
import sys
import math
import json
import os
from src.game.customization import customization
from src.utils.input_utils import is_screenshot_key
from src.utils.config import load_config, save_config
from src.ui.pages.settings_help_page import show_settings_help

# Import shared globals
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, background_theme, enhanced_effects,
    debug_mode, click_sound, screen, title_font, menu_font, footer_font,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT,
    dark_gradients, music_on
)

# Import UI components
from src.ui.components import (
    draw_smooth_gradient, draw_fancy_button, draw_button, glowing_text,
    WHITE, YELLOW
)

def settings_page():
    """Display and manage game settings with sidebar navigation"""
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
        config["appearance"]["background_theme"] = background_theme
        config["appearance"]["enhanced_effects"] = enhanced_effects
        config["gameplay"]["debug_mode"] = debug_mode
        config["gameplay"]["player_position"] = get_player_position()
        config["audio"]["music_on"] = music_on
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    clock = pygame.time.Clock()
    step = 0
    
    # Improved spacing with consistent margins on both sides
    page_margin = 30  # Increased margin for both sides
    
    # Define sidebar dimensions with proper spacing
    sidebar_left_margin = page_margin  # Left edge margin
    sidebar_width = 220
    sidebar_margin = 20
    sidebar_start_y = 120
    sidebar_button_height = 60
    sidebar_button_spacing = 10
    
    # Define content area dimensions with proper right margin
    content_start_x = sidebar_left_margin + sidebar_width + 32  # Slightly increased spacing between sidebar and content
    content_width = SCREEN_WIDTH - content_start_x - (page_margin + 2)  # Slightly more right margin
    content_start_y = 122  # Moved down slightly
    content_height = SCREEN_HEIGHT - content_start_y - 95  # Slightly more bottom margin
    content_area = pygame.Rect(content_start_x, content_start_y, content_width, content_height)
    
    # Current category (0 = Appearance, 1 = Gameplay, 2 = Audio)
    current_category = 0
    
    # Current appearance sub-tab (0 = Snake Themes, 1 = Food Themes)
    appearance_subtab = 0
    
    # Get all available themes
    snake_themes = customization.get_all_snake_themes()
    food_themes = customization.get_all_food_themes()
    
    # Create sidebar category buttons
    categories = ["Appearance", "Gameplay", "Audio"]
    category_buttons = []
    
    for i, category in enumerate(categories):
        category_buttons.append(
            pygame.Rect(
                sidebar_left_margin + sidebar_margin, 
                sidebar_start_y + i * (sidebar_button_height + sidebar_button_spacing), 
                sidebar_width - (sidebar_margin * 2), 
                sidebar_button_height
            )
        )
    # Create sub-tab buttons for Appearance
    subtab_width = (content_width - 40) // 2
    subtab_buttons = [
        pygame.Rect(content_start_x + 10, content_start_y + 10, subtab_width, 40),
        pygame.Rect(content_start_x + 20 + subtab_width, content_start_y + 10, subtab_width, 40)
    ]
    
    # Create content buttons
    button_width = 360
    button_height = 60
    button_spacing = 20
    button_x = content_start_x + (content_width - button_width) // 2
    
    # Gameplay settings buttons - kept for compatibility
    dark_button = pygame.Rect(button_x, content_start_y + 80, button_width, button_height)
    light_button = pygame.Rect(button_x, content_start_y + 80 + button_height + button_spacing, button_width, button_height)
    debug_button = pygame.Rect(button_x, content_start_y + 80 + (button_height + button_spacing) * 2, button_width, button_height)
    vs_position_button = pygame.Rect(button_x, content_start_y + 80 + (button_height + button_spacing) * 3, button_width, button_height)
    enhanced_effects_button = pygame.Rect(button_x, content_start_y + 80 + (button_height + button_spacing) * 4, button_width, button_height)
    
    # Audio settings button
    music_button = pygame.Rect(button_x, content_start_y + 80, button_width, button_height)
    
    # Define column layout variables for two-column view - DEFINE THESE EARLY
    col_width = (content_width - 60) // 2
    left_col_x = content_start_x + 20
    right_col_x = content_start_x + col_width + 40
    col_button_width = min(col_width - 20, 300)
    
    # Left column buttons - DEFINE BEFORE EVENT HANDLING
    col_button_x = left_col_x + (col_width - col_button_width) // 2
    col_dark_button = pygame.Rect(col_button_x, content_start_y + 80, 
                            col_button_width, button_height)
    col_light_button = pygame.Rect(col_button_x, content_start_y + 80 + button_height + button_spacing, 
                            col_button_width, button_height)
    
    # Right column buttons - DEFINE BEFORE EVENT HANDLING  
    col_button_x = right_col_x + (col_width - col_button_width) // 2
    col_debug_button = pygame.Rect(col_button_x, content_start_y + 80, 
                            col_button_width, button_height)
    col_vs_button = pygame.Rect(col_button_x, content_start_y + 80 + button_height + button_spacing, 
                            col_button_width, button_height)
    col_effects_button = pygame.Rect(col_button_x, content_start_y + 80 + (button_height + button_spacing) * 2, 
                            col_button_width, button_height)
    
    # Back button positioned at bottom right with more spacing - reduced size for better alignment
    back_button_width = 160  # Reduced from 200 to 160 for a smaller button
    back_button = pygame.Rect(SCREEN_WIDTH - back_button_width - page_margin, SCREEN_HEIGHT - 80, back_button_width, button_height)
    
    # Help button - keep in bottom left corner
    help_button_size = 50
    help_button = pygame.Rect(page_margin, SCREEN_HEIGHT - 70, help_button_size, help_button_size)
    help_color = (80, 100, 180)
    help_hover = (120, 140, 220)
    
    # Pre-render help button elements
    question_text = menu_font.render("?", True, WHITE)
    help_shadow = pygame.Surface((help_button_size, help_button_size), pygame.SRCALPHA)
    help_shadow.fill((0, 0, 0, 30))
    
    # Define theme preview dimensions - bigger boxes, 3 per row
    preview_size = 200  # Increased from 160  
    preview_margin = 25  # Increased from 20
    
    # Fix to 3 columns for better layout
    preview_cols = 3
    preview_rows = math.ceil(len(snake_themes) / preview_cols)
    
    # Define consistent button colors
    standard_button_color = (60, 100, 180)  # Blue-ish base color
    standard_button_hover = (100, 150, 250)  # Lighter blue for hover
    
    toggle_on_color = (100, 200, 100)  # Green for ON state
    toggle_off_color = (200, 100, 100)  # Red for OFF state
    
    back_button_color = (180, 60, 60)  # Reddish for exit button
    back_button_hover = (220, 80, 80)  # Lighter red for hover
    
    # Sidebar styling
    sidebar_bg_color = (25, 25, 45, 180)  # Semi-transparent dark blue
    sidebar_active = (50, 50, 80)  # Darker blue for active category
    sidebar_inactive = (35, 35, 65)  # Slightly lighter for inactive
    sidebar_hover = (45, 45, 75)  # Hover state
    sidebar_border = (80, 80, 120)  # Border color
    
    # Subtab styling
    subtab_active = (60, 100, 200)
    subtab_inactive = (40, 40, 80)
    subtab_hover = (80, 120, 220)
    
    # Track mouse state for better interaction
    mouse_pressed = False
    prev_mouse_pressed = False
    
    while True:
        prev_mouse_pressed = mouse_pressed
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient(screen)
        
        # Draw title
        title_x = (SCREEN_WIDTH - title_font.size("Settings")[0]) // 2
        glowing_text(screen, "Settings", title_font, title_x, 40, YELLOW, step)
        
        # Draw sidebar background with proper left margin
        sidebar_rect = pygame.Rect(
            sidebar_left_margin, 
            sidebar_start_y - 10, 
            sidebar_width, 
            SCREEN_HEIGHT - sidebar_start_y + 10 - 85  # Adjusted from 100 to 85 to match content
        )
        pygame.draw.rect(screen, sidebar_bg_color, sidebar_rect, border_radius=15)
        pygame.draw.rect(screen, sidebar_border, sidebar_rect, 2, border_radius=15)
        
        # Draw content area background - taller with proper spacing
        content_bg = pygame.Rect(content_start_x - 15, content_start_y - 15, 
                                content_width + 30, content_height + 30)
        pygame.draw.rect(screen, (25, 25, 45, 120), content_bg, border_radius=15)
        
        # Draw category buttons in sidebar
        for i, (button, category) in enumerate(zip(category_buttons, categories)):
            is_active = i == current_category
            is_hovered = button.collidepoint(mouse_pos)
            
            # Determine button color based on state
            if is_active:
                color = sidebar_active
                # Draw active indicator - vertical bar on right
                indicator_rect = pygame.Rect(
                    button.right - 5, 
                    button.top + 5, 
                    5, 
                    button.height - 10
                )
                pygame.draw.rect(screen, (100, 140, 220), indicator_rect, border_radius=2)
            elif is_hovered:
                color = sidebar_hover
            else:
                color = sidebar_inactive
                
            # Draw button background
            pygame.draw.rect(screen, color, button, border_radius=8)
            
            # Draw button text
            text_surface = menu_font.render(category, True, WHITE)
            text_rect = text_surface.get_rect(center=button.center)
            screen.blit(text_surface, text_rect)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Sidebar category navigation
                    for i, button in enumerate(category_buttons):
                        if button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            current_category = i
                    
                    # Handle appearance sub-tabs
                    if current_category == 0:
                        for i, button in enumerate(subtab_buttons):
                            if button.collidepoint(event.pos):
                                if click_sound: click_sound.play()
                                appearance_subtab = i
                    
                    # Gameplay buttons
                    if current_category == 1:
                        # Check column-specific buttons instead of full-width ones
                        if col_dark_button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            background_theme = "dark"
                            save_settings_immediately()
                            
                        elif col_light_button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            background_theme = "light"
                            save_settings_immediately()
                            
                        elif col_debug_button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            debug_mode = not debug_mode
                            save_settings_immediately()
                            
                        elif col_vs_button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            new_position = "left" if get_player_position() == "right" else "right"
                            save_player_position(new_position)
                            save_settings_immediately()
                            
                        elif col_effects_button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            enhanced_effects = not enhanced_effects
                            save_settings_immediately()
                    
                    # Audio settings
                    elif current_category == 2:
                        if music_button.collidepoint(event.pos):
                            if click_sound: click_sound.play()
                            music_on = not music_on
                            if music_on:
                                try:
                                    pygame.mixer.music.play(-1)
                                except:
                                    pass
                            else:
                                try:
                                    pygame.mixer.music.stop()
                                except:
                                    pass
                            save_settings_immediately()
                    
                    # Snake theme selection
                    if current_category == 0 and appearance_subtab == 0:
                        handle_snake_theme_selection(event.pos, snake_themes, preview_size, preview_margin, 
                                                    preview_cols, content_start_x, content_start_y + 70)
                    
                    # Food theme selection  
                    if current_category == 0 and appearance_subtab == 1:
                        handle_food_theme_selection(event.pos, food_themes, preview_size, preview_margin, 
                                                 preview_cols, content_start_x, content_start_y + 70)
                    
                    # Back and Help buttons
                    if back_button.collidepoint(event.pos):
                        if click_sound: click_sound.play()
                        save_config(config)
                        return
                    
                    elif help_button.collidepoint(event.pos):
                        if click_sound: click_sound.play()
                        # Pass the correct help page index based on current category and subtab
                        if current_category == 0:  # Appearance
                            # If in Appearance category, show either Snake or Food theme help
                            show_settings_help(appearance_subtab + 1)  # 1=Snake themes, 2=Food themes
                        else:
                            # For Gameplay or Audio, just use the category index
                            show_settings_help(current_category)
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                save_config(config)
                return
        
        # Draw content based on current category
        if current_category == 0:
            # Appearance tab with sub-tabs
            for i, (button, label) in enumerate(zip(subtab_buttons, ["Snake Themes", "Food Themes"])):
                is_active = i == appearance_subtab
                is_hovered = button.collidepoint(mouse_pos)
                
                # Determine color based on state
                if is_active:
                    color = subtab_active
                elif is_hovered:
                    color = subtab_hover
                else:
                    color = subtab_inactive
                
                # Draw sub-tab button
                pygame.draw.rect(screen, color, button, border_radius=8)
                text_surf = footer_font.render(label, True, WHITE)
                text_rect = text_surf.get_rect(center=button.center)
                screen.blit(text_surf, text_rect)
            
            # Draw theme previews based on active sub-tab
            if appearance_subtab == 0:
                draw_snake_theme_previews(snake_themes, preview_size, preview_margin, preview_cols, 
                                        content_start_x, content_start_y + 70, mouse_pos)
            else:
                draw_food_theme_previews(food_themes, preview_size, preview_margin, preview_cols, 
                                    content_start_x, content_start_y + 70, mouse_pos)
            
        elif current_category == 1:
            # Gameplay settings - use two-column layout for better space usage
            
            # Left column - Background Theme
            section_title = menu_font.render("Background Theme", True, (200, 200, 200))
            screen.blit(section_title, (left_col_x, content_start_y + 30))
            
            # Draw selected theme indicator
            selected_border = pygame.Rect(0, 0, col_button_width + 8, button_height + 8)
            if background_theme == "dark":
                selected_border.center = col_dark_button.center
                pygame.draw.rect(screen, (80, 200, 120), selected_border, 3, border_radius=14)
            else:
                selected_border.center = col_light_button.center
                pygame.draw.rect(screen, (80, 200, 120), selected_border, 3, border_radius=14)
            
            # Dark theme button
            dark_theme_color = (40, 40, 50)
            dark_theme_hover = (60, 60, 80)
            is_hover = col_dark_button.collidepoint(mouse_pos)
            color = dark_theme_hover if is_hover else dark_theme_color
            pygame.draw.rect(screen, color, col_dark_button, border_radius=12)
            text = menu_font.render("Theme: Dark", True, WHITE)
            text_rect = text.get_rect(center=col_dark_button.center)
            screen.blit(text, text_rect)
            
            # Light theme button
            light_theme_color = (230, 230, 240)
            light_theme_hover = (250, 250, 255)
            is_hover = col_light_button.collidepoint(mouse_pos)
            color = light_theme_hover if is_hover else light_theme_color
            pygame.draw.rect(screen, color, col_light_button, border_radius=12)
            text = menu_font.render("Theme: Light", True, (20, 20, 30))
            text_rect = text.get_rect(center=col_light_button.center)
            screen.blit(text, text_rect)
            
            # Right column - Other gameplay settings
            section_title = menu_font.render("Gameplay Settings", True, (200, 200, 200))
            screen.blit(section_title, (right_col_x, content_start_y + 30))
            
            # Debug mode button
            debug_label = "Debug Mode: ON" if debug_mode else "Debug Mode: OFF"
            debug_color = toggle_on_color if debug_mode else toggle_off_color
            pygame.draw.rect(screen, debug_color, col_debug_button, border_radius=12)
            text = menu_font.render(debug_label, True, WHITE)
            text_rect = text.get_rect(center=col_debug_button.center)
            screen.blit(text, text_rect)
            
            # VS position button
            vs_position = get_player_position()
            vs_position_text = f"Player Position: {vs_position.title()}"
            is_hover = col_vs_button.collidepoint(mouse_pos)
            color = standard_button_hover if is_hover else standard_button_color
            pygame.draw.rect(screen, color, col_vs_button, border_radius=12)
            text = menu_font.render(vs_position_text, True, WHITE)
            text_rect = text.get_rect(center=col_vs_button.center)
            screen.blit(text, text_rect)
            
            # Enhanced effects button
            enhanced_label = "Level-Up Effects: Enhanced" if enhanced_effects else "Level-Up Effects: Simple"
            enhanced_color = toggle_on_color if enhanced_effects else toggle_off_color
            pygame.draw.rect(screen, enhanced_color, col_effects_button, border_radius=12)
            text = menu_font.render(enhanced_label, True, WHITE)
            text_rect = text.get_rect(center=col_effects_button.center)
            screen.blit(text, text_rect)
            
        elif current_category == 2:
            # Audio settings
            section_title = menu_font.render("Audio Settings", True, (200, 200, 200))
            screen.blit(section_title, (content_start_x + 20, content_start_y + 30))
            
            # Music toggle button
            music_label = "Music: ON" if music_on else "Music: OFF"
            music_color = toggle_on_color if music_on else toggle_off_color
            pygame.draw.rect(screen, music_color, music_button, border_radius=12)
            text = menu_font.render(music_label, True, WHITE)
            text_rect = text.get_rect(center=music_button.center)
            screen.blit(text, text_rect)
            
            # Note about future audio settings
            note_text = footer_font.render("More audio settings coming soon!", True, (150, 150, 180))
            screen.blit(note_text, (content_start_x + 20, music_button.bottom + 40))
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back to Menu", menu_font, 
                        back_button_color, back_button_hover, mouse_pos, step)
        
        # Draw help button
        help_surface = pygame.Surface((help_button.width, help_button.height), pygame.SRCALPHA)
        current_help_color = help_hover if help_button.collidepoint(mouse_pos) else help_color
        pygame.draw.rect(help_surface, current_help_color, 
                       (0, 0, help_button.width, help_button.height), border_radius=20)
        
        # Add shadow for help button
        screen.blit(help_shadow, (help_button.x + 2, help_button.y + 2))
        screen.blit(help_surface, help_button)
        
        # Add pulsing glow effect
        help_glow_width = int(abs(math.sin(step / 15)) * 2) + 1
        help_glow_rect = help_button.inflate(4, 4)
        pygame.draw.rect(screen, (80, 120, 200), help_glow_rect, help_glow_width, border_radius=20)
        
        # Center the question mark in the button
        question_rect = question_text.get_rect(center=help_button.center)
        screen.blit(question_text, question_rect)
        
        pygame.display.update()
        step += 1
        clock.tick(60)


def draw_snake_theme_previews(themes, preview_size, preview_margin, cols, start_x, start_y, mouse_pos):
    """Draw snake theme previews in a grid"""
    current_theme = customization.current_snake_theme
    
    # Calculate width of the preview grid
    preview_width = cols * (preview_size + preview_margin) - preview_margin
    x_start = start_x + (SCREEN_WIDTH - start_x - preview_width) // 2
    
    for i, (key, theme) in enumerate(themes.items()):
        row = i // cols
        col = i % cols
        
        x_pos = x_start + col * (preview_size + preview_margin)
        y_pos = start_y + row * (preview_size + preview_margin)
        
        # Create preview rect
        preview_rect = pygame.Rect(x_pos, y_pos, preview_size, preview_size)
        
        # Draw theme preview
        pygame.draw.rect(screen, (30, 30, 60), preview_rect, border_radius=10)
        
        # Draw selection indicator if this is the current theme
        if key == current_theme:
            pygame.draw.rect(screen, (80, 200, 120), preview_rect, 4, border_radius=10)
        
        # Draw theme name
        name_text = footer_font.render(theme.name, True, WHITE)
        name_rect = name_text.get_rect(center=(preview_rect.centerx, preview_rect.top + 30))
        screen.blit(name_text, name_rect)
        
        # Draw snake preview
        snake_segments = [(
            preview_rect.centerx + (j-5) * 15, 
            preview_rect.centery
        ) for j in range(10)]
        
        for j, pos in enumerate(snake_segments):
            color = theme.get_segment_color(j)
            pygame.draw.rect(screen, color, (pos[0]-7, pos[1]-7, 15, 15))
            
        # Add select button if not selected
        if key != current_theme:
            select_button = pygame.Rect(
                preview_rect.centerx - 60, 
                preview_rect.bottom - 40, 
                120, 30
            )
            
            # Fix hover detection by properly checking the mouse position
            is_hover = select_button.collidepoint(mouse_pos)
            button_color = (80, 180, 80) if is_hover else (60, 120, 60)
            
            # Draw button
            pygame.draw.rect(screen, button_color, select_button, border_radius=8)
            text = footer_font.render("Select", True, WHITE)
            text_rect = text.get_rect(center=select_button.center)
            screen.blit(text, text_rect)


def draw_food_theme_previews(themes, preview_size, preview_margin, cols, start_x, start_y, mouse_pos):
    """Draw food theme previews in a grid"""
    current_theme = customization.current_food_theme
    step = pygame.time.get_ticks() // 30  # Animation step
    
    # Calculate width of the preview grid
    preview_width = cols * (preview_size + preview_margin) - preview_margin
    x_start = start_x + (SCREEN_WIDTH - start_x - preview_width) // 2
    
    for i, (key, theme) in enumerate(themes.items()):
        row = i // cols
        col = i % cols
        
        x_pos = x_start + col * (preview_size + preview_margin)
        y_pos = start_y + row * (preview_size + preview_margin)
        
        # Create preview rect
        preview_rect = pygame.Rect(x_pos, y_pos, preview_size, preview_size)
        
        # Draw theme preview
        pygame.draw.rect(screen, (30, 30, 60), preview_rect, border_radius=10)
        
        # Draw selection indicator if this is the current theme
        if key == current_theme:
            pygame.draw.rect(screen, (80, 200, 120), preview_rect, 4, border_radius=10)
        
        # Draw theme name
        name_text = footer_font.render(theme.name, True, WHITE)
        name_rect = name_text.get_rect(center=(preview_rect.centerx, preview_rect.top + 30))
        screen.blit(name_text, name_rect)
        
        # Draw food preview
        food_color = theme.get_food_color(step)
        food_radius = 30  # Slightly larger food preview
        pygame.draw.circle(screen, food_color, 
                        (preview_rect.centerx, preview_rect.centery), food_radius)
        
        # If it's a random color theme, draw some samples
        if theme.random_colors:
            for j, color in enumerate(theme.color_options[:5]):
                small_radius = 12  # Slightly larger sample circles
                x_offset = (j - 2) * 30  # More spacing between samples
                pygame.draw.circle(screen, color,
                                (preview_rect.centerx + x_offset, 
                                preview_rect.centery + 60), small_radius)
                            
        # Add select button if not selected
        if key != current_theme:
            select_button = pygame.Rect(
                preview_rect.centerx - 60, 
                preview_rect.bottom - 40, 
                120, 30
            )
            
            # Fix hover detection by properly checking the mouse position
            is_hover = select_button.collidepoint(mouse_pos)
            button_color = (80, 180, 80) if is_hover else (60, 120, 60)
            
            # Draw button
            pygame.draw.rect(screen, button_color, select_button, border_radius=8)
            text = footer_font.render("Select", True, WHITE)
            text_rect = text.get_rect(center=select_button.center)
            screen.blit(text, text_rect)


def handle_snake_theme_selection(click_pos, themes, preview_size, preview_margin, cols, start_x, start_y):
    """Handle click on snake theme preview"""
    current_theme = customization.current_snake_theme
    
    # Calculate width of the preview grid
    preview_width = cols * (preview_size + preview_margin) - preview_margin
    x_start = start_x + (SCREEN_WIDTH - start_x - preview_width) // 2
    
    for i, (key, theme) in enumerate(themes.items()):
        row = i // cols
        col = i % cols
        
        x_pos = x_start + col * (preview_size + preview_margin)
        y_pos = start_y + row * (preview_size + preview_margin)
        
        # Create preview rect
        preview_rect = pygame.Rect(x_pos, y_pos, preview_size, preview_size)
        
        if key != current_theme:
            select_button = pygame.Rect(
                preview_rect.centerx - 60, 
                preview_rect.bottom - 40, 
                120, 30
            )
            
            if select_button.collidepoint(click_pos):
                if click_sound: click_sound.play()
                customization.set_snake_theme(key)
                return True
    
    return False


def handle_food_theme_selection(click_pos, themes, preview_size, preview_margin, cols, start_x, start_y):
    """Handle click on food theme preview"""
    current_theme = customization.current_food_theme
    
    # Calculate width of the preview grid
    preview_width = cols * (preview_size + preview_margin) - preview_margin
    x_start = start_x + (SCREEN_WIDTH - start_x - preview_width) // 2
    
    for i, (key, theme) in enumerate(themes.items()):
        row = i // cols
        col = i % cols
        
        x_pos = x_start + col * (preview_size + preview_margin)
        y_pos = start_y + row * (preview_size + preview_margin)
        
        # Create preview rect
        preview_rect = pygame.Rect(x_pos, y_pos, preview_size, preview_size)
        
        if key != current_theme:
            select_button = pygame.Rect(
                preview_rect.centerx - 60, 
                preview_rect.bottom - 40, 
                120, 30
            )
            
            if select_button.collidepoint(click_pos):
                if click_sound: click_sound.play()
                customization.set_food_theme(key)
                return True
    
    return False


def get_player_position():
    """Get the current player position for VS mode"""
    config = load_config()
    return config["gameplay"].get("player_position", "left")


def save_player_position(position):
    """Save the player position setting"""
    config = load_config()
    config["gameplay"]["player_position"] = position
    save_config(config)