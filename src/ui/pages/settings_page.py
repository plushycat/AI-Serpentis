import pygame
import sys
import math
import json
import os
from src.game.customization import customization
from src.utils.input_utils import is_screenshot_key
from src.utils.settings_manager import get_setting, set_setting, get_config, save_config
from src.ui.pages.settings_help_page import show_settings_help
from src.utils.sound_manager import sound_manager, play_click

# Import shared globals
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, background_theme, enhanced_effects,
    debug_mode, screen, title_font, menu_font, footer_font,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT,
    dark_gradients, music_on, update_theme, help_icon,
    music_on_icon, music_off_icon, scores_icon  # Add these icons
)

# Import UI components
from src.ui.components import (
    draw_smooth_gradient, draw_fancy_button, draw_button, glowing_text,
    WHITE, YELLOW
)

from src.game.player_vs_ai import get_player_position, save_player_position

# Add import for high scores page navigation
from src.ui.pages.scores_page import high_scores_page

def settings_page():
    """Display and manage game settings with sidebar navigation"""
    global background_theme, debug_mode, enhanced_effects
    
    # UPDATED: Always use sound manager as source of truth
    # Don't rely on config file for current state
    music_on = sound_manager.music_on
    sound_effects_on = sound_manager.sound_effects_on
    click_sounds_on = sound_manager.click_sounds_on
    master_volume = sound_manager.master_volume
    music_volume = sound_manager.music_volume
    sound_effects_volume = sound_manager.sound_effects_volume
    
    # Load other settings from config
    config_file = "statics/game_settings.json"
    
    try:
        background_theme = get_setting("appearance", "background_theme", "dark")
        enhanced_effects = get_setting("appearance", "enhanced_effects", True)
        debug_mode = get_setting("gameplay", "debug_mode", False)
        classic_speed = get_setting("gameplay", "classic_speed", 10)
        fibonacci_speed = get_setting("gameplay", "fibonacci_speed", 8)
    except Exception as e:
        print(f"Error loading config: {e}")
        # Default values
        background_theme = "dark"
        enhanced_effects = True
        debug_mode = False
        classic_speed = 10
        fibonacci_speed = 8
    
    # Define save_settings_immediately to use the sound manager for audio settings
    def save_settings_immediately():
        """Save settings and synchronize with SoundManager"""
        print(f"Saving audio settings: music={music_on}, sfx={sound_effects_on}, clicks={click_sounds_on}, " +
            f"volumes: master={master_volume:.2f}, music={music_volume:.2f}, sfx={sound_effects_volume:.2f}")
        
        # Update sound manager settings
        sound_manager.music_on = music_on
        sound_manager.sound_effects_on = sound_effects_on
        sound_manager.click_sounds_on = click_sounds_on
        sound_manager.master_volume = master_volume
        sound_manager.music_volume = music_volume
        sound_manager.sound_effects_volume = sound_effects_volume
        
        # Apply settings to hear changes immediately
        sound_manager.apply_settings()
        
        # Save all settings at once
        set_setting("appearance", "background_theme", background_theme)
        set_setting("appearance", "enhanced_effects", enhanced_effects)
        set_setting("gameplay", "debug_mode", debug_mode)
        set_setting("gameplay", "player_position", get_player_position())
        set_setting("gameplay", "classic_speed", classic_speed)
        set_setting("gameplay", "fibonacci_speed", fibonacci_speed)
        
        # Call sound manager's save_settings() to save audio settings
        sound_manager.save_settings()
        
        print("Settings saved successfully")
        return True
    
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
    col_dark_button = pygame.Rect(col_button_x, content_start_y + 60, col_button_width, button_height)  # From 80 to 60
    col_light_button = pygame.Rect(col_button_x, content_start_y + 60 + button_height + 15, col_button_width, button_height)  # Spacing reduced from 20 to 15
    
    # Right column buttons - DEFINE BEFORE EVENT HANDLING  
    col_button_x = right_col_x + (col_width - col_button_width) // 2
    col_debug_button = pygame.Rect(col_button_x, content_start_y + 60, col_button_width, button_height)  # From 80 to 60
    col_vs_button = pygame.Rect(col_button_x, content_start_y + 60 + button_height + 15, col_button_width, button_height)  # Spacing reduced
    col_effects_button = pygame.Rect(col_button_x, content_start_y + 60 + (button_height + 15) * 2, col_button_width, button_height)  # Spacing reduced
    
    # Back button positioned at bottom right with more spacing - smaller height and lower position
    back_button_width = 160
    back_button_height = 45  # Reduced height for better appearance
    back_button = pygame.Rect(SCREEN_WIDTH - back_button_width - page_margin, SCREEN_HEIGHT - 65, back_button_width, back_button_height)
    
    # Help button - keep in bottom left corner
    help_button_size = 56  # Match home page size
    help_button = pygame.Rect(SCREEN_WIDTH - 228, 20, help_button_size, help_button_size)  # Match home page position
    
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
    
    # Define slider dimensions
    slider_width = 300
    slider_height = 8
    slider_knob_radius = 8  # For circle knobs if needed
    slider_spacing = 80  # Spacing between sliders
    
    # Audio settings buttons and sliders
    music_button = pygame.Rect(button_x, content_start_y + 80, button_width, button_height)
    effects_button = pygame.Rect(button_x, content_start_y + 80 + button_height + button_spacing, button_width, button_height)
    
    # Create Rect objects for sliders
    master_slider = pygame.Rect(
        button_x + (button_width - slider_width) // 2,
        content_start_y + 200,
        slider_width,
        slider_height
    )
    
    music_slider = pygame.Rect(
        button_x + (button_width - slider_width) // 2,
        content_start_y + 200 + slider_spacing,
        slider_width,
        slider_height
    )
    
    effects_slider = pygame.Rect(
        button_x + (button_width - slider_width) // 2,
        content_start_y + 200 + slider_spacing * 2,
        slider_width,
        slider_height
    )
    
    # Define the group containers early (before they're used in checkbox positioning)
    master_group = pygame.Rect(0, 0, 100, 100)  # Initial size, will be updated later
    music_group = pygame.Rect(0, 0, 100, 160)   # Initial size, will be updated later
    effects_group = pygame.Rect(0, 0, 100, 160) # Initial size, will be updated later

    # Define checkbox dimensions and styling
    checkbox_size = 24
    checkbox_text_spacing = 10
    checkbox_checked_color = (100, 200, 100)
    checkbox_unchecked_color = (60, 60, 80)
    checkbox_border_color = (120, 120, 160)
    
    # Define checkboxes alongside other UI elements
    music_checkbox = pygame.Rect(0, 0, checkbox_size, checkbox_size)
    effects_checkbox = pygame.Rect(0, 0, checkbox_size, checkbox_size)
    click_checkbox = pygame.Rect(0, 0, checkbox_size, checkbox_size)
    
    # Update checkbox positions
    music_checkbox.x = music_group.left + 20
    music_checkbox.y = music_group.top + 50

    effects_checkbox.x = effects_group.left + 20
    effects_checkbox.y = effects_group.top + 50

    click_checkbox.x = effects_group.left + 20
    click_checkbox.y = effects_group.top + 80
    
    # Function to draw a checkbox
    def draw_checkbox(screen, rect, is_checked, label, font):
        # Draw the checkbox
        pygame.draw.rect(screen, checkbox_border_color, rect, 2, border_radius=4)
        if is_checked:
            inner_rect = rect.inflate(-8, -8)
            pygame.draw.rect(screen, checkbox_checked_color, inner_rect, border_radius=3)
        
        # Draw the label
        label_surface = font.render(label, True, (220, 220, 220))
        screen.blit(label_surface, (rect.right + checkbox_text_spacing, rect.centery - label_surface.get_height() // 2))
    
    # Add this helper function to draw slider triangles
    def draw_slider_triangles(screen, slider_rect, color=(150, 150, 150)):
        """Draw triangle indicators at each end of a slider"""
        # Left triangle (min) - points right - toward slider
        left_triangle = [
            (slider_rect.left - 10, slider_rect.centery),      # Tip points right
            (slider_rect.left - 5, slider_rect.centery - 6),   # Top of base
            (slider_rect.left - 5, slider_rect.centery + 6)    # Bottom of base
        ]
        pygame.draw.polygon(screen, color, left_triangle)
        
        # Right triangle (max) - points left - toward slider
        right_triangle = [
            (slider_rect.right + 10, slider_rect.centery),     # Tip points left
            (slider_rect.right + 5, slider_rect.centery - 6),  # Top of base
            (slider_rect.right + 5, slider_rect.centery + 6)   # Bottom of base
        ]
        pygame.draw.polygon(screen, color, right_triangle)
    
    active_slider = None
    
    # Update knob dimensions - make them wider
    knob_width = 6  # Increased from 4 to 6 for better visibility
    knob_height = 20
    
    # In settings_page function, add a new variable to hold game speed
    game_speed = get_setting("gameplay", "game_speed", 10)  # Default 10 if not found

    # In the initialization section, load both speeds
    classic_speed = get_setting("gameplay", "classic_speed", 10)
    fibonacci_speed = get_setting("gameplay", "fibonacci_speed", 8)

    # Define wider speed range
    min_speed = 5
    max_speed = 30  # Increased from 20 to 30

    # Create separate sliders for both speed settings
    classic_speed_group = pygame.Rect(content_start_x + 20, col_effects_button.bottom + 15, content_width - 40, 90)  # From 20 to 15
    fibonacci_speed_group = pygame.Rect(content_start_x + 20, classic_speed_group.bottom + 10, content_width - 40, 90)  # From 15 to 10

    # Setup both sliders
    classic_speed_slider = pygame.Rect(classic_speed_group.left + 30, classic_speed_group.top + 55, classic_speed_group.width - 100, slider_height)
    fibonacci_speed_slider = pygame.Rect(fibonacci_speed_group.left + 30, fibonacci_speed_group.top + 55, fibonacci_speed_group.width - 100, slider_height)

    # Add utility buttons in top right (matching home page)
    button_size = 56
    help_button_size = 56  # Match home page size
    help_button = pygame.Rect(SCREEN_WIDTH - 228, 20, help_button_size, help_button_size)  # Match home page position

    # Add music toggle and scores buttons
    music_rect = pygame.Rect(SCREEN_WIDTH - 76, 20, button_size, button_size)
    scores_button = pygame.Rect(SCREEN_WIDTH - 152, 20, button_size, button_size)

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
                            play_click()
                            current_category = i
                    
                    # Handle appearance sub-tabs
                    if current_category == 0:
                        for i, button in enumerate(subtab_buttons):
                            if button.collidepoint(event.pos):
                                play_click()
                                appearance_subtab = i
                    
                    # Gameplay buttons
                    if current_category == 1:
                        # First check for any button in the gameplay section
                        if col_dark_button.collidepoint(event.pos):  # Changed from 'elif' to 'if'
                            play_click()
                            background_theme = "dark"
                            update_theme("dark")
                            save_settings_immediately()
                            
                        elif col_light_button.collidepoint(event.pos):
                            play_click()
                            background_theme = "light"
                            update_theme("light")
                            save_settings_immediately()
                        
                        elif col_debug_button.collidepoint(event.pos):
                            play_click()
                            debug_mode = not debug_mode
                            
                            # Update shared_globals module directly
                            import src.ui.shared_globals
                            src.ui.shared_globals.debug_mode = debug_mode
                            
                            save_settings_immediately()
                        
                        elif col_vs_button.collidepoint(event.pos):
                            play_click()
    
                            # Get current position and toggle it
                            current_position = get_player_position()
                            new_position = "left" if current_position == "right" else "right"
                            
                            # Use only one save method - the function from player_vs_ai is more robust
                            success = save_player_position(new_position)
                            if not success:
                                print(f"Warning: Failed to save player position: {new_position}")
                            
                            print(f"Player position changed: {current_position} → {new_position}")
                        
                        elif col_effects_button.collidepoint(event.pos):
                            play_click()
                            enhanced_effects = not enhanced_effects
                            
                            # Update shared_globals module directly
                            import src.ui.shared_globals
                            src.ui.shared_globals.enhanced_effects = enhanced_effects
                            
                            save_settings_immediately()
                        
                        # Check slider interactions specifically for gameplay category
                        if current_category == 1:  # Only check these sliders when on Gameplay tab
                            # Classic speed slider - improved hit area
                            classic_slider_area = pygame.Rect(
                                classic_speed_slider.left - 15,
                                classic_speed_slider.top - 20,
                                classic_speed_slider.width + 30,
                                40
                            )
                            if classic_slider_area.collidepoint(event.pos):
                                active_slider = "classic_speed"
                                # Calculate speed immediately on click for instant feedback
                                rel_x = max(0, min(event.pos[0] - classic_speed_slider.left, classic_speed_slider.width))
                                classic_speed = min_speed + int((rel_x / classic_speed_slider.width) * (max_speed - min_speed))
                                classic_speed = max(min_speed, min(max_speed, classic_speed))
                            
                            # Fibonacci speed slider - improved hit area
                            fibonacci_slider_area = pygame.Rect(
                                fibonacci_speed_slider.left - 15,
                                fibonacci_speed_slider.top - 20,
                                fibonacci_speed_slider.width + 30,
                                40
                            )
                            if fibonacci_slider_area.collidepoint(event.pos):
                                active_slider = "fibonacci_speed"
                                # Calculate speed immediately on click for instant feedback
                                rel_x = max(0, min(event.pos[0] - fibonacci_speed_slider.left, fibonacci_speed_slider.width))
                                fibonacci_speed = min_speed + int((rel_x / fibonacci_speed_slider.width) * (max_speed - min_speed))
                                fibonacci_speed = max(min_speed, min(max_speed, fibonacci_speed))
                    
                    # Audio settings
                    elif current_category == 2:
                        # Music toggle checkbox
                        if music_checkbox.collidepoint(event.pos):
                            music_on = not music_on
                            # Apply change immediately
                            if music_on and music_volume > 0:
                                try:
                                    pygame.mixer.music.play(-1)
                                    pygame.mixer.music.set_volume(master_volume * music_volume)
                                except Exception as e:
                                    print(f"Error playing music: {e}")
                            else:
                                try:
                                    pygame.mixer.music.stop()
                                except Exception as e:
                                    print(f"Error stopping music: {e}")
                            # Save the setting immediately
                            save_settings_immediately()
                            
                            # Play click sound feedback if enabled
                            if click_sounds_on:
                                play_click()
                        
                        # Sound effects toggle checkbox
                        elif effects_checkbox.collidepoint(event.pos):
                            sound_effects_on = not sound_effects_on
                            save_settings_immediately()
                            
                            # Play click sound only if turning ON
                            if sound_effects_on:
                                play_click()
                        
                        # UI Click sounds toggle checkbox
                        elif click_checkbox.collidepoint(event.pos):
                            click_sounds_on = not click_sounds_on
                            
                            # Update config
                            set_setting("audio", "click_sounds_on", click_sounds_on)
                            save_settings_immediately()
                            
                            # Play click sound only if turning ON
                            if click_sounds_on:
                                play_click()
                        
                        # Handle slider dragging
                        elif pygame.mouse.get_pressed()[0]:
                            pos = pygame.mouse.get_pos()
                            
                            # Master volume slider - increase hit area and make interaction more forgiving
                            if (master_slider.collidepoint(pos) or 
                                pygame.Rect(master_slider.left - 10, master_slider.top - 15, 
                                        master_slider.width + 20, master_slider.height + 30).collidepoint(pos) or
                                (prev_mouse_pressed and master_slider.left - 10 <= pos[0] <= master_slider.right + 10 and 
                                abs(pos[1] - master_slider.centery) < 50)):
                                active_slider = "master"
                            
                            # Music volume slider - only if music is enabled
                            elif music_on and (music_slider.collidepoint(pos) or 
                                pygame.Rect(music_slider.left - 10, music_slider.top - 15, 
                                        music_slider.width + 20, music_slider.height + 30).collidepoint(pos) or
                                (prev_mouse_pressed and music_slider.left - 10 <= pos[0] <= music_slider.right + 10 and 
                                abs(pos[1] - music_slider.centery) < 50)):
                                active_slider = "music"
                            
                            # Sound effects volume slider - only if sound effects are enabled
                            elif sound_effects_on and (effects_slider.collidepoint(pos) or \
                                (prev_mouse_pressed and effects_slider.left <= pos[0] <= effects_slider.right and 
                                abs(pos[1] - effects_slider.centery) < 40)):
                                active_slider = "effects"
                            
                            # Add to the event handling section where active_slider is set
                            elif classic_speed_slider.collidepoint(pos) or \
                                (prev_mouse_pressed and classic_speed_slider.left - 10 <= pos[0] <= classic_speed_slider.right + 10 and 
                                abs(pos[1] - classic_speed_slider.centery) < 50):
                                active_slider = "classic_speed"
                                
                            elif fibonacci_speed_slider.collidepoint(pos) or \
                                (prev_mouse_pressed and fibonacci_speed_slider.left - 10 <= pos[0] <= fibonacci_speed_slider.right + 10 and 
                                abs(pos[1] - fibonacci_speed_slider.centery) < 50):
                                active_slider = "fibonacci_speed"
                    
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
                        play_click()
                        save_settings_immediately()
                        return
                    
                    elif help_button.collidepoint(event.pos):
                        play_click()
                        # Map each tab to the correct help page index
                        if current_category == 0:  # Appearance
                            # If in Appearance category, show either Snake or Food theme help
                            show_settings_help(appearance_subtab + 1)  # 1=Snake themes, 2=Food themes
                        elif current_category == 1:  # Gameplay
                            show_settings_help(0)  # 0=Gameplay settings
                        elif current_category == 2:  # Audio
                            show_settings_help(3)  # 3=Audio settings
                    
                    # Handle music toggle
                    if music_rect.collidepoint(event.pos):
                        play_click()
                        sound_manager.toggle_music()
                        music_on = sound_manager.music_on
                        
                    # Handle scores button
                    if scores_button.collidepoint(event.pos):
                        play_click()
                        high_scores_page()  # Navigate to scores page
            
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and active_slider:  # Left button pressed
                    pos = pygame.mouse.get_pos()
                    
                    if active_slider == "master":
                        # Calculate volume based on x position with clamping
                        new_x = min(max(pos[0], master_slider.left), master_slider.right)
                        master_volume = (new_x - master_slider.left) / master_slider.width
                        # Apply volume without saving
                        if music_on:
                            try:
                                pygame.mixer.music.set_volume(master_volume * music_volume)
                            except Exception as e:
                                print(f"Error setting volume: {e}")
                        # Don't save during dragging
                        
                    elif active_slider == "music" and music_on:
                        # Calculate volume based on x position with clamping
                        new_x = min(max(pos[0], music_slider.left), music_slider.right)
                        music_volume = (new_x - music_slider.left) / music_slider.width
                        # Apply volume without saving
                        try:
                            pygame.mixer.music.set_volume(master_volume * music_volume)
                        except Exception as e:
                            print(f"Error setting music volume: {e}")
                        # Don't save during dragging
                        
                    elif active_slider == "effects" and sound_effects_on:
                        # Calculate volume based on x position with clamping
                        new_x = min(max(pos[0], effects_slider.left), effects_slider.right)
                        sound_effects_volume = (new_x - effects_slider.left) / effects_slider.width
                        # Don't save during dragging
                    
                    # Handle slider dragging for the new sliders
                    elif active_slider == "classic_speed":
                        # Calculate speed based on x position with clamping
                        new_x = min(max(pos[0], classic_speed_slider.left), classic_speed_slider.right)
                        classic_speed = min_speed + int((new_x - classic_speed_slider.left) / classic_speed_slider.width * (max_speed - min_speed))
                        classic_speed = max(min_speed, min(max_speed, classic_speed))

                    elif active_slider == "fibonacci_speed":
                        # Calculate speed based on x position with clamping
                        new_x = min(max(pos[0], fibonacci_speed_slider.left), fibonacci_speed_slider.right)
                        fibonacci_speed = min_speed + int((new_x - fibonacci_speed_slider.left) / fibonacci_speed_slider.width * (max_speed - min_speed))
                        fibonacci_speed = max(min_speed, min(max_speed, fibonacci_speed))
            
            if event.type == pygame.MOUSEBUTTONUP:
                if active_slider:
                    # Always save regardless of which slider was active
                    save_settings_immediately()
                    print(f"Settings saved after adjusting {active_slider}")
                    active_slider = None
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                save_settings_immediately()
                return
        
        # When mouse is released, save the settings
        if prev_mouse_pressed and not mouse_pressed:
            if active_slider == "classic_speed":
                set_setting("gameplay", "classic_speed", classic_speed)
                save_settings_immediately()
            elif active_slider == "fibonacci_speed":
                set_setting("gameplay", "fibonacci_speed", fibonacci_speed)
                save_settings_immediately()
            active_slider = None

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
            screen.blit(section_title, (left_col_x, content_start_y + 20))  # From 30 to 20
            
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
            screen.blit(section_title, (right_col_x, content_start_y + 20))  # From 30 to 20
            
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
            
            # Game Speed Slider
            speed_group = pygame.Rect(content_start_x + 20, col_effects_button.bottom + 20, content_width - 40, 90)
            pygame.draw.rect(screen, (30, 30, 55), speed_group, border_radius=12)

            # Speed title
            speed_title = menu_font.render("Game Speed", True, (220, 220, 220))
            screen.blit(speed_title, (speed_group.left + 20, speed_group.top + 15))

            # Speed slider
            speed_slider = pygame.Rect(speed_group.left + 30, speed_group.top + 55, speed_group.width - 100, slider_height)
            pygame.draw.rect(screen, (60, 60, 80), speed_slider, border_radius=4)
            filled_width = int(speed_slider.width * ((game_speed - 5) / 15))  # Scale from 5-20 to 0-1
            filled_slider = pygame.Rect(speed_slider.left, speed_slider.top, filled_width, slider_height)
            pygame.draw.rect(screen, (100, 160, 240), filled_slider, border_radius=4)

            # Draw knob
            knob_x = speed_slider.left + filled_width
            knob_rect = pygame.Rect(knob_x - knob_width//2, speed_slider.centery - knob_height//2, 
                                knob_width, knob_height)
            pygame.draw.rect(screen, (140, 200, 255), knob_rect, border_radius=2)

            # Draw slider triangles
            draw_slider_triangles(screen, speed_slider)

            # Draw speed text
            speed_label = footer_font.render(f"{game_speed} FPS", True, (180, 180, 180))
            right_edge_space = content_area.right - speed_slider.right - 15 - speed_label.get_width()
            if right_edge_space < 20:
                screen.blit(speed_label, (speed_slider.right - speed_label.get_width(), speed_slider.top - 25))
            else:
                screen.blit(speed_label, (speed_slider.right + 15, speed_slider.top - 4))  # Changed from 25 to 15

            # Add slider interaction for speed
            if speed_slider.collidepoint(mouse_pos) and mouse_pressed and not prev_mouse_pressed:
                # Calculate speed value between 5-20 based on click position
                rel_x = mouse_pos[0] - speed_slider.left
                game_speed = 5 + int((rel_x / speed_slider.width) * 15)
                game_speed = max(5, min(20, game_speed))  # Clamp between 5-20
                
                # Save immediately
                set_setting("gameplay", "game_speed", game_speed)
                save_settings_immediately()
            
            # Draw both speed groups
            pygame.draw.rect(screen, (30, 30, 55), classic_speed_group, border_radius=12)
            pygame.draw.rect(screen, (30, 30, 55), fibonacci_speed_group, border_radius=12)
            
            # Classic Speed title and slider
            speed_title = menu_font.render("Classic Game Speed", True, (220, 220, 220))
            screen.blit(speed_title, (classic_speed_group.left + 20, classic_speed_group.top + 15))
            
            # Calculate filled width normalized to range
            filled_width = int(classic_speed_slider.width * ((classic_speed - min_speed) / (max_speed - min_speed)))
            filled_slider = pygame.Rect(classic_speed_slider.left, classic_speed_slider.top, filled_width, slider_height)
            
            # Draw slider components
            pygame.draw.rect(screen, (60, 60, 80), classic_speed_slider, border_radius=4)
            pygame.draw.rect(screen, (100, 160, 240), filled_slider, border_radius=4)
            draw_slider_triangles(screen, classic_speed_slider)
            
            # Draw knob
            knob_x = classic_speed_slider.left + filled_width
            knob_rect = pygame.Rect(knob_x - knob_width//2, classic_speed_slider.centery - knob_height//2, knob_width, knob_height)
            pygame.draw.rect(screen, (140, 200, 255), knob_rect, border_radius=2)
            
            # Draw speed text
            speed_label = footer_font.render(f"{classic_speed} FPS", True, (180, 180, 180))
            right_edge_space = content_area.right - classic_speed_slider.right - 15 - speed_label.get_width()
            if right_edge_space < 20:
                screen.blit(speed_label, (classic_speed_slider.right - speed_label.get_width(), classic_speed_slider.top - 25))
            else:
                screen.blit(speed_label, (classic_speed_slider.right + 15, classic_speed_slider.top - 4))
            
            # Fibonacci Speed title and slider
            fib_speed_title = menu_font.render("Fibonacci Game Speed", True, (220, 220, 220))
            screen.blit(fib_speed_title, (fibonacci_speed_group.left + 20, fibonacci_speed_group.top + 15))
            
            # Calculate filled width normalized to range
            filled_width = int(fibonacci_speed_slider.width * ((fibonacci_speed - min_speed) / (max_speed - min_speed)))
            filled_slider = pygame.Rect(fibonacci_speed_slider.left, fibonacci_speed_slider.top, filled_width, slider_height)
            
            # Draw slider components
            pygame.draw.rect(screen, (60, 60, 80), fibonacci_speed_slider, border_radius=4)
            pygame.draw.rect(screen, (100, 160, 240), filled_slider, border_radius=4)
            draw_slider_triangles(screen, fibonacci_speed_slider)
            
            # Draw knob
            knob_x = fibonacci_speed_slider.left + filled_width
            knob_rect = pygame.Rect(knob_x - knob_width//2, fibonacci_speed_slider.centery - knob_height//2, knob_width, knob_height)
            pygame.draw.rect(screen, (140, 200, 255), knob_rect, border_radius=2)
            
            # Draw speed text
            speed_label = footer_font.render(f"{fibonacci_speed} FPS", True, (180, 180, 180))
            right_edge_space = content_area.right - fibonacci_speed_slider.right - 15 - speed_label.get_width()
            if right_edge_space < 20:
                screen.blit(speed_label, (fibonacci_speed_slider.right - speed_label.get_width(), fibonacci_speed_slider.top - 25))
            else:
                screen.blit(speed_label, (fibonacci_speed_slider.right + 15, fibonacci_speed_slider.top - 4))
            
        elif current_category == 2:
            # Audio settings with improved layout
            section_title = menu_font.render("Audio Settings", True, (200, 200, 200))
            screen.blit(section_title, (content_start_x + 20, content_start_y + 20))  # Moved up 10px
            
            # Define consistent spacing with reduced heights
            section_spacing = 20  # Reduced from 40
            group_spacing = 15    # Reduced from 120
            
            # Update settings groups with more compact positions
            master_group.x = content_start_x + 20
            master_group.y = content_start_y + 55  # Moved up 15px
            master_group.width = content_width - 40
            master_group.height = 90  # Increased from 80 to 90 for more space
            
            music_group.x = content_start_x + 20
            music_group.y = master_group.bottom + 15  # Reduced gap between sections
            music_group.width = content_width - 40
            music_group.height = 140  # Reduced from 160
            
            effects_group.x = content_start_x + 20
            effects_group.y = music_group.bottom + 15  # Reduced gap between sections
            effects_group.width = content_width - 40
            effects_group.height = 160  # Increased from 140 to 160 for more bottom space
            
            # Draw settings groups with slightly more subtle backgrounds
            pygame.draw.rect(screen, (30, 30, 55), master_group, border_radius=12)
            pygame.draw.rect(screen, (30, 30, 55), music_group, border_radius=12)
            pygame.draw.rect(screen, (30, 30, 55), effects_group, border_radius=12)
            
            # Master volume section
            group_title = menu_font.render("Master Volume", True, (220, 220, 220))
            screen.blit(group_title, (master_group.left + 20, master_group.top + 15))
            
            # Master volume slider with fixed width - INCREASED GAP HERE
            master_slider.top = master_group.top + 55  # Increased from 45 to 55 for more space between title and slider
            master_slider.left = master_group.left + 30
            master_slider.width = master_group.width - 100  # Fixed width
            
            # Draw slider with better visual appearance
            pygame.draw.rect(screen, (60, 60, 80), master_slider, border_radius=4)
            filled_width = int(master_slider.width * master_volume)
            filled_slider = pygame.Rect(master_slider.left, master_slider.top, filled_width, slider_height)
            pygame.draw.rect(screen, (100, 160, 240), filled_slider, border_radius=4)
            
            # Draw rectangular knob instead of circle
            knob_x = master_slider.left + int(master_slider.width * master_volume)
            knob_rect = pygame.Rect(knob_x - knob_width//2, master_slider.centery - knob_height//2, 
                                  knob_width, knob_height)
            pygame.draw.rect(screen, (140, 200, 255), knob_rect, border_radius=2)
            
            # Draw slider triangles
            draw_slider_triangles(screen, master_slider)
            
            # Draw percentage text AFTER the slider and triangles
            vol_label = footer_font.render(f"{int(master_volume * 100)}%", True, (180, 180, 180))
            screen.blit(vol_label, (master_slider.right + 25, master_slider.top - 4))
            
            # Music section
            group_title = menu_font.render("Background Music", True, (220, 220, 220))
            screen.blit(group_title, (music_group.left + 20, music_group.top + 15))
            
            # Create checkbox for music
            music_checkbox.x = music_group.left + 20
            music_checkbox.y = music_group.top + 50
            draw_checkbox(screen, music_checkbox, music_on, "Enable Background Music", footer_font)
            
            # Music volume controls (only shown if music is enabled)
            if music_on:
                
                # For Music slider section
                # Position music slider with fixed width
                music_slider.top = music_group.top + 95
                music_slider.left = music_group.left + 30
                music_slider.width = music_group.width - 100  # Fixed width
                
                # Draw slider
                pygame.draw.rect(screen, (60, 60, 80), music_slider, border_radius=4)
                filled_width = int(music_slider.width * music_volume)
                filled_slider = pygame.Rect(music_slider.left, music_slider.top, filled_width, slider_height)
                pygame.draw.rect(screen, (100, 160, 240), filled_slider, border_radius=4)
                
                # Draw rectangular knob instead of circle
                knob_x = music_slider.left + int(music_slider.width * music_volume)
                knob_rect = pygame.Rect(knob_x - knob_width//2, music_slider.centery - knob_height//2, 
                                        knob_width, knob_height)
                pygame.draw.rect(screen, (140, 200, 255), knob_rect, border_radius=2)
                
                # Draw slider triangles
                draw_slider_triangles(screen, music_slider)
                
                # Draw percentage text AFTER the slider and triangles
                vol_label = footer_font.render(f"{int(music_volume * 100)}%", True, (180, 180, 180))
                screen.blit(vol_label, (music_slider.right + 25, music_slider.top - 4))
            
            # Sound Effects section
            group_title = menu_font.render("Sound Effects", True, (220, 220, 220))
            screen.blit(group_title, (effects_group.left + 20, effects_group.top + 15))
            
            # Create checkbox for sound effects
            effects_checkbox.x = effects_group.left + 20
            effects_checkbox.y = effects_group.top + 50
            draw_checkbox(screen, effects_checkbox, sound_effects_on, "Enable Sound Effects", footer_font)
            
            # Create separate checkbox for click sounds
            click_checkbox.x = effects_group.left + 20
            click_checkbox.y = effects_group.top + 80
            draw_checkbox(screen, click_checkbox, click_sounds_on, "Enable UI Click Sounds", footer_font)
            
            # Sound effects volume controls (only shown if enabled)
            if sound_effects_on:
                # Position effects slider with fixed width
                effects_slider.top = effects_group.top + 120
                effects_slider.left = effects_group.left + 30
                effects_slider.width = effects_group.width - 100  # Fixed width
                
                # Draw slider background and fill
                pygame.draw.rect(screen, (60, 60, 80), effects_slider, border_radius=4)
                filled_width = int(effects_slider.width * sound_effects_volume)
                filled_slider = pygame.Rect(effects_slider.left, effects_slider.top, filled_width, slider_height)
                pygame.draw.rect(screen, (100, 160, 240), filled_slider, border_radius=4)
                
                # Draw rectangular knob instead of circle
                effects_knob_x = effects_slider.left + int(effects_slider.width * sound_effects_volume)
                knob_rect = pygame.Rect(effects_knob_x - knob_width//2, effects_slider.centery - knob_height//2, 
                                    knob_width, knob_height)
                pygame.draw.rect(screen, (140, 200, 255), knob_rect, border_radius=2)
                
                # Draw triangles
                draw_slider_triangles(screen, effects_slider)
                
                # Draw percentage text AFTER the slider and triangles
                vol_label = footer_font.render(f"{int(sound_effects_volume * 100)}%", True, (180, 180, 180))
                screen.blit(vol_label, (effects_slider.right + 25, effects_slider.top - 4))
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Back to Menu", menu_font, 
                        back_button_color, back_button_hover, mouse_pos, step)
        
        # Draw help button (using same style as home page)
        if help_icon is not None:
            help_icon_rect = help_icon.get_rect(center=help_button.center)
            screen.blit(help_icon, help_icon_rect)
        else:
            # Fallback if icon is missing
            pygame.draw.rect(screen, (80, 100, 180), help_button, 0, border_radius=7)
            fallback_text = menu_font.render("?", True, WHITE)
            text_rect = fallback_text.get_rect(center=help_button.center)
            screen.blit(fallback_text, text_rect)
        
        # Add hover effect matching home page
        if help_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (80, 120, 200), help_button, 2, border_radius=7)
        
        # Draw music toggle button
        if music_on and music_on_icon:
            music_icon_rect = music_on_icon.get_rect(center=music_rect.center)
            screen.blit(music_on_icon, music_icon_rect)
        elif not music_on and music_off_icon:
            music_icon_rect = music_off_icon.get_rect(center=music_rect.center)
            screen.blit(music_off_icon, music_icon_rect)
        else:
            # Fallback if icon is missing
            pygame.draw.rect(screen, (80, 100, 180), music_rect, 0, border_radius=7)
            fallback_text = menu_font.render("M", True, WHITE)
            text_rect = fallback_text.get_rect(center=music_rect.center)
            screen.blit(fallback_text, text_rect)

        # Draw scores button
        if scores_icon:
            scores_icon_rect = scores_icon.get_rect(center=scores_button.center)
            screen.blit(scores_icon, scores_icon_rect)
        else:
            # Fallback if icon is missing
            pygame.draw.rect(screen, (80, 100, 180), scores_button, 0, border_radius=7)
            fallback_text = menu_font.render("S", True, WHITE)
            text_rect = fallback_text.get_rect(center=scores_button.center)
            screen.blit(fallback_text, text_rect)

        # Add hover effects for utility buttons
        if music_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (80, 120, 200), music_rect, 2, border_radius=7)
        if scores_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (80, 120, 200), scores_button, 2, border_radius=7)

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
                play_click()
                prev_theme = current_theme
                customization.set_snake_theme(key)
                
                # Log the theme change
                import datetime, sys
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Snake theme changed: {prev_theme} → {key}")
                sys.stdout.flush()
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
                play_click()
                prev_theme = current_theme
                customization.set_food_theme(key)
                
                # Log the theme change
                import datetime, sys
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Food theme changed: {prev_theme} → {key}")
                sys.stdout.flush()
                return True
    
    return False


def get_current_theme():
    """Get the current background theme from config file"""
    try:
        config = load_config()
        if config and "appearance" in config and "background_theme" in config["appearance"]:
            return config["appearance"]["background_theme"]
    except Exception as e:
        print(f"Error loading theme setting: {e}")
    return "dark"  # Default fallback