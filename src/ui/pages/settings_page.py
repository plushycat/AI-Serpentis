import pygame
import sys
import math
import json
import os
from src.game.customization import customization
from src.utils.input_utils import is_screenshot_key
from src.utils.config import load_config, save_config

# Import shared globals instead of from home_page
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, background_theme, enhanced_effects,
    debug_mode, click_sound, screen, title_font, menu_font, footer_font,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT
)

def settings_page():
    """Display and manage game settings"""
    global music_on, background_theme, debug_mode, enhanced_effects
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis - Settings")
    clock = pygame.time.Clock()
    
    # Load config
    config = load_config()
    
    # Initial settings
    try:
        snake_theme_index = customization.get_current_snake_theme_index()
    except AttributeError:
        # Fallback if method doesn't exist - just use the first theme
        snake_theme_index = 0
        
    try:
        food_theme_index = customization.get_current_food_theme_index()
    except AttributeError:
        # Fallback if method doesn't exist - just use the first theme
        food_theme_index = 0
        
    player_position = "left"  # Default
    
    if "gameplay" in config and "player_position" in config["gameplay"]:
        player_position = config["gameplay"]["player_position"]
    
    # Page navigation
    pages = ["General", "Customization", "Advanced"]
    current_page = 0
    
    # Tabs for page navigation
    tab_width = 180
    tab_height = 50
    tab_spacing = 20
    tab_y = 120
    tab_buttons = []
    
    for i, page in enumerate(pages):
        tab_x = SCREEN_WIDTH // 2 - (tab_width * len(pages) + tab_spacing * (len(pages) - 1)) // 2 + i * (tab_width + tab_spacing)
        tab_buttons.append(pygame.Rect(tab_x, tab_y, tab_width, tab_height))
    
    # Back button
    back_button = pygame.Rect((SCREEN_WIDTH-250)//2, SCREEN_HEIGHT - 80, 250, 50)
    back_button_color = (180, 60, 60)
    back_button_hover = (220, 80, 80)
    
    # Scrolling settings
    scroll_y = 0
    scroll_velocity = 0
    
    # Animation step
    step = 0
    
    # Help button
    help_button_size = 40
    help_button = pygame.Rect(20, SCREEN_HEIGHT - 60, help_button_size, help_button_size)
    help_color = (80, 100, 180)
    help_hover = (120, 140, 220)
    
    # Info button in bottom right
    info_button_size = 40
    info_button = pygame.Rect(SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60, info_button_size, info_button_size)
    info_color = (60, 110, 180) 
    info_hover = (100, 150, 220)
    
    # Main loop
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw base
        draw_smooth_gradient(screen)
        
        # Draw title
        title_text = "Settings"
        title_x = (SCREEN_WIDTH - title_font.size(title_text)[0]) // 2
        glowing_text(screen, title_text, title_font, title_x, 30, YELLOW, step)
        
        # Draw tabs
        for i, tab_rect in enumerate(tab_buttons):
            is_current = i == current_page
            is_hovered = tab_rect.collidepoint(mouse_pos)
            
            color = (100, 150, 240) if is_current else (70, 100, 170)
            hover_color = (150, 200, 255) if is_current else (100, 140, 210)
            
            pygame.draw.rect(screen, hover_color if is_hovered else color, tab_rect, border_radius=10)
            
            # Add highlight for current tab
            if is_current:
                highlight = pygame.Surface((tab_rect.width + 4, tab_rect.height + 4), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (255, 255, 255, 80), 
                              (0, 0, tab_rect.width + 4, tab_rect.height + 4), 2, border_radius=12)
                screen.blit(highlight, (tab_rect.x - 2, tab_rect.y - 2))
            
            tab_text = menu_font.render(pages[i], True, WHITE)
            text_rect = tab_text.get_rect(center=tab_rect.center)
            screen.blit(tab_text, text_rect)
        
        # Draw page content based on current_page
        content_area = pygame.Rect(SCREEN_WIDTH//2 - 350, tab_y + tab_height + 30, 700, SCREEN_HEIGHT - tab_y - tab_height - 150)
        
        # General Settings
        if current_page == 0:
            # Music toggle
            setting_y = content_area.y + 30 - scroll_y
            music_text = menu_font.render("Music", True, WHITE)
            screen.blit(music_text, (content_area.x + 20, setting_y))
            
            music_toggle_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            toggle_color = (0, 200, 0) if music_on else (200, 0, 0)
            hover = music_toggle_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, toggle_color, music_toggle_rect, border_radius=20)
            
            toggle_state = menu_font.render("ON" if music_on else "OFF", True, WHITE)
            toggle_rect = toggle_state.get_rect(center=music_toggle_rect.center)
            screen.blit(toggle_state, toggle_rect)
            
            # Background theme
            setting_y += 80
            theme_text = menu_font.render("Background Theme", True, WHITE)
            screen.blit(theme_text, (content_area.x + 20, setting_y))
            
            dark_rect = pygame.Rect(content_area.right - 240, setting_y, 100, 40)
            light_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            
            # Draw theme buttons
            dark_hover = dark_rect.collidepoint(mouse_pos)
            light_hover = light_rect.collidepoint(mouse_pos)
            
            dark_color = (100, 100, 240) if background_theme == "dark" else (60, 60, 100)
            light_color = (240, 100, 100) if background_theme == "light" else (100, 60, 60)
            
            pygame.draw.rect(screen, (80, 80, 220) if dark_hover else dark_color, dark_rect, border_radius=10)
            pygame.draw.rect(screen, (220, 80, 80) if light_hover else light_color, light_rect, border_radius=10)
            
            # Add highlight to current theme
            if background_theme == "dark":
                pygame.draw.rect(screen, (255, 255, 255), dark_rect, 2, border_radius=10)
            else:
                pygame.draw.rect(screen, (255, 255, 255), light_rect, 2, border_radius=10)
            
            dark_text = menu_font.render("Dark", True, WHITE)
            dark_text_rect = dark_text.get_rect(center=dark_rect.center)
            screen.blit(dark_text, dark_text_rect)
            
            light_text = menu_font.render("Light", True, WHITE)
            light_text_rect = light_text.get_rect(center=light_rect.center)
            screen.blit(light_text, light_text_rect)
            
            # Visual effects toggle
            setting_y += 80
            effects_text = menu_font.render("Enhanced Effects", True, WHITE)
            screen.blit(effects_text, (content_area.x + 20, setting_y))
            
            effects_toggle_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            toggle_color = (0, 200, 0) if enhanced_effects else (200, 0, 0)
            hover = effects_toggle_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, toggle_color, effects_toggle_rect, border_radius=20)
            
            toggle_state = menu_font.render("ON" if enhanced_effects else "OFF", True, WHITE)
            toggle_rect = toggle_state.get_rect(center=effects_toggle_rect.center)
            screen.blit(toggle_state, toggle_rect)
            
            # Player position for VS mode
            setting_y += 80
            position_text = menu_font.render("Player Position (VS Mode)", True, WHITE)
            screen.blit(position_text, (content_area.x + 20, setting_y))
            
            left_rect = pygame.Rect(content_area.right - 240, setting_y, 100, 40)
            right_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            
            # Draw position buttons
            left_hover = left_rect.collidepoint(mouse_pos)
            right_hover = right_rect.collidepoint(mouse_pos)
            
            left_color = (100, 200, 100) if player_position == "left" else (60, 120, 60)
            right_color = (100, 200, 100) if player_position == "right" else (60, 120, 60)
            
            pygame.draw.rect(screen, (120, 220, 120) if left_hover else left_color, left_rect, border_radius=10)
            pygame.draw.rect(screen, (120, 220, 120) if right_hover else right_color, right_rect, border_radius=10)
            
            # Add highlight to current position
            if player_position == "left":
                pygame.draw.rect(screen, (255, 255, 255), left_rect, 2, border_radius=10)
            else:
                pygame.draw.rect(screen, (255, 255, 255), right_rect, 2, border_radius=10)
            
            left_text = menu_font.render("Left", True, WHITE)
            left_text_rect = left_text.get_rect(center=left_rect.center)
            screen.blit(left_text, left_text_rect)
            
            right_text = menu_font.render("Right", True, WHITE)
            right_text_rect = right_text.get_rect(center=right_rect.center)
            screen.blit(right_text, right_text_rect)
        
        # Customization Settings
        elif current_page == 1:
            # Snake Theme
            setting_y = content_area.y + 30 - scroll_y
            snake_text = menu_font.render("Snake Theme", True, WHITE)
            screen.blit(snake_text, (content_area.x + 20, setting_y))
            
            # Draw theme selector
            theme_width = 80
            theme_height = 40
            theme_spacing = 20
            total_width = (theme_width + theme_spacing) * len(customization.snake_themes)
            theme_x = content_area.x + (content_area.width - total_width) // 2
            
            for i, theme in enumerate(customization.snake_themes):
                theme_rect = pygame.Rect(theme_x + i * (theme_width + theme_spacing), setting_y + 60, theme_width, theme_height)
                is_selected = i == snake_theme_index
                is_hovered = theme_rect.collidepoint(mouse_pos)
                
                # Draw theme preview
                if theme.name == "Random":
                    # Special handling for Random theme - diagonal split
                    pygame.draw.rect(screen, (200, 60, 60), theme_rect, border_radius=10)
                    points = [(theme_rect.left, theme_rect.top), 
                             (theme_rect.right, theme_rect.top),
                             (theme_rect.right, theme_rect.bottom)]
                    pygame.draw.polygon(screen, (60, 200, 60), points)
                else:
                    # Draw using theme color
                    pygame.draw.rect(screen, theme.head_color, theme_rect, border_radius=10)
                
                # Add highlight for selected theme
                if is_selected:
                    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(theme_rect.x - 4, theme_rect.y - 4, 
                                                                      theme_rect.width + 8, theme_rect.height + 8), 
                                  2, border_radius=14)
                
                # Show theme name on hover
                if is_hovered:
                    name_surface = footer_font.render(theme.name, True, WHITE)
                    name_rect = name_surface.get_rect(center=(theme_rect.centerx, theme_rect.bottom + 20))
                    screen.blit(name_surface, name_rect)
            
            # Food Theme
            setting_y += 160
            food_text = menu_font.render("Food Theme", True, WHITE)
            screen.blit(food_text, (content_area.x + 20, setting_y))
            
            # Draw food theme selector
            theme_x = content_area.x + (content_area.width - total_width) // 2
            
            for i, theme in enumerate(customization.food_themes):
                theme_rect = pygame.Rect(theme_x + i * (theme_width + theme_spacing), setting_y + 60, theme_width, theme_height)
                is_selected = i == food_theme_index
                is_hovered = theme_rect.collidepoint(mouse_pos)
                
                # Draw theme preview based on type
                if theme.name == "Rainbow":
                    # Special rainbow gradient
                    rainbow_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130), (238, 130, 238)]
                    segment_width = theme_rect.width / len(rainbow_colors)
                    
                    for j, color in enumerate(rainbow_colors):
                        segment_rect = pygame.Rect(theme_rect.x + j * segment_width, theme_rect.y, 
                                                segment_width, theme_rect.height)
                        pygame.draw.rect(screen, color, segment_rect)
                    
                    # Round the corners by drawing an alpha mask
                    mask = pygame.Surface((theme_rect.width, theme_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(mask, (255, 255, 255), (0, 0, theme_rect.width, theme_rect.height), 
                                  border_radius=10)
                    
                    # Create temporary surface to apply the mask
                    temp = pygame.Surface((theme_rect.width, theme_rect.height), pygame.SRCALPHA)
                    temp.blit(screen.subsurface(theme_rect), (0, 0))
                    temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    
                    # Clear the original area and blit the masked surface
                    pygame.draw.rect(screen, (0, 0, 0, 0), theme_rect)
                    screen.blit(temp, theme_rect)
                else:
                    # Regular food theme
                    pygame.draw.rect(screen, theme.get_food_color(0), theme_rect, border_radius=10)
                
                # Add highlight for selected theme
                if is_selected:
                    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(theme_rect.x - 4, theme_rect.y - 4, 
                                                                      theme_rect.width + 8, theme_rect.height + 8), 
                                  2, border_radius=14)
                
                # Show theme name on hover
                if is_hovered:
                    name_surface = footer_font.render(theme.name, True, WHITE)
                    name_rect = name_surface.get_rect(center=(theme_rect.centerx, theme_rect.bottom + 20))
                    screen.blit(name_surface, name_rect)
        
        # Advanced Settings
        elif current_page == 2:
            # Debug Mode
            setting_y = content_area.y + 30 - scroll_y
            debug_text = menu_font.render("Debug Mode", True, WHITE)
            screen.blit(debug_text, (content_area.x + 20, setting_y))
            
            debug_toggle_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            toggle_color = (0, 200, 0) if debug_mode else (200, 0, 0)
            hover = debug_toggle_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, toggle_color, debug_toggle_rect, border_radius=20)
            
            toggle_state = menu_font.render("ON" if debug_mode else "OFF", True, WHITE)
            toggle_rect = toggle_state.get_rect(center=debug_toggle_rect.center)
            screen.blit(toggle_state, toggle_rect)
            
            # Reset Scores
            setting_y += 80
            reset_text = menu_font.render("Reset High Scores", True, WHITE)
            screen.blit(reset_text, (content_area.x + 20, setting_y))
            
            reset_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            reset_color = (200, 60, 60)
            hover = reset_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (240, 80, 80) if hover else reset_color, reset_rect, border_radius=10)
            
            reset_button_text = menu_font.render("Reset", True, WHITE)
            reset_text_rect = reset_button_text.get_rect(center=reset_rect.center)
            screen.blit(reset_button_text, reset_text_rect)
            
            # Warning text
            warning = footer_font.render("Warning: This will permanently erase all high scores!", True, (255, 180, 180))
            screen.blit(warning, (content_area.x + 20, setting_y + 50))
            
            # Delete AI Models
            setting_y += 120
            models_text = menu_font.render("Delete AI Models", True, WHITE)
            screen.blit(models_text, (content_area.x + 20, setting_y))
            
            models_rect = pygame.Rect(content_area.right - 120, setting_y, 100, 40)
            models_color = (200, 60, 60)
            hover = models_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (240, 80, 80) if hover else models_color, models_rect, border_radius=10)
            
            models_button_text = menu_font.render("Delete", True, WHITE)
            models_text_rect = models_button_text.get_rect(center=models_rect.center)
            screen.blit(models_button_text, models_text_rect)
            
            # Warning text
            warning = footer_font.render("Warning: This will permanently delete all trained AI models!", True, (255, 180, 180))
            screen.blit(warning, (content_area.x + 20, setting_y + 50))
        
        # Draw divider between content and buttons
        pygame.draw.line(screen, (100, 100, 150), 
                      (content_area.x, content_area.bottom + 10), 
                      (content_area.right, content_area.bottom + 10), 3)
        
        # Draw back button
        draw_fancy_button(screen, back_button, "Save & Back", menu_font, back_button_color, back_button_hover, mouse_pos, step)
        
        # Draw help button (question mark)
        pygame.draw.rect(screen, help_hover if help_button.collidepoint(mouse_pos) else help_color, 
                      help_button, border_radius=20)
        question_text = menu_font.render("?", True, WHITE)
        question_rect = question_text.get_rect(center=help_button.center)
        screen.blit(question_text, question_rect)
        
        # Draw info button (i icon) in bottom right
        pygame.draw.rect(screen, info_hover if info_button.collidepoint(mouse_pos) else info_color, 
                      info_button, border_radius=20)
        info_text = menu_font.render("i", True, WHITE)
        info_rect = info_text.get_rect(center=info_button.center)
        screen.blit(info_text, info_rect)
        
        # Update display
        pygame.display.update()
        
        # Handle events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                # Save settings before quitting
                _save_settings(config, music_on, background_theme, debug_mode, enhanced_effects,
                             snake_theme_index, food_theme_index, player_position)
                pygame.quit()
                sys.exit()
                
            elif e.type == pygame.MOUSEBUTTONDOWN:
                # Handle tab navigation
                for i, button in enumerate(tab_buttons):
                    if button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_page = i
                        scroll_y = 0
                
                # Back button
                if back_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    # Save all settings
                    _save_settings(config, music_on, background_theme, debug_mode, enhanced_effects,
                                 snake_theme_index, food_theme_index, player_position)
                    return
                
                # Help button handler
                elif help_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    show_settings_help(current_page)  # Show help for current page
                
                # Info button handler
                elif info_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    from src.ui.pages.info_page import show_info_page
                    show_info_page()
                
                # Page-specific interactions
                if current_page == 0:  # General settings
                    # Music toggle
                    if music_toggle_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        music_on = not music_on
                        config["audio"]["music_on"] = music_on
                        
                        # Update music state
                        if music_on:
                            try:
                                pygame.mixer.music.play(-1)
                            except:
                                print("Could not play music")
                        else:
                            try:
                                pygame.mixer.music.stop()
                            except:
                                print("Could not stop music")
                    
                    # Background theme
                    elif dark_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        background_theme = "dark"
                        config["appearance"]["background_theme"] = background_theme
                    elif light_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        background_theme = "light"
                        config["appearance"]["background_theme"] = background_theme
                    
                    # Enhanced effects
                    elif effects_toggle_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        enhanced_effects = not enhanced_effects
                        config["appearance"]["enhanced_effects"] = enhanced_effects
                    
                    # Player position
                    elif left_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        player_position = "left"
                        config["gameplay"]["player_position"] = player_position
                        set_player_position(player_position)
                    elif right_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        player_position = "right"
                        config["gameplay"]["player_position"] = player_position
                        set_player_position(player_position)
                
                elif current_page == 1:  # Customization
                    # Snake theme selection
                    theme_width = 80
                    theme_height = 40
                    theme_spacing = 20
                    total_width = (theme_width + theme_spacing) * len(customization.snake_themes)
                    theme_x = content_area.x + (content_area.width - total_width) // 2
                    
                    for i in range(len(customization.snake_themes)):
                        theme_rect = pygame.Rect(theme_x + i * (theme_width + theme_spacing), 
                                             content_area.y + 90 - scroll_y, theme_width, theme_height)
                        if theme_rect.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            snake_theme_index = i
                            customization.set_snake_theme(snake_theme_index)
                            break
                    
                    # Food theme selection
                    theme_y = content_area.y + 250 - scroll_y
                    for i in range(len(customization.food_themes)):
                        theme_rect = pygame.Rect(theme_x + i * (theme_width + theme_spacing), 
                                             theme_y, theme_width, theme_height)
                        if theme_rect.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            food_theme_index = i
                            customization.set_food_theme(food_theme_index)
                            break
                
                elif current_page == 2:  # Advanced
                    # Debug toggle
                    if debug_toggle_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        debug_mode = not debug_mode
                        config["gameplay"]["debug_mode"] = debug_mode
                    
                    # Reset scores
                    elif reset_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        confirm = confirm_dialog("Reset High Scores", 
                                             "Are you sure you want to reset all high scores?",
                                             "This action cannot be undone.")
                        if confirm:
                            reset_high_scores()
                    
                    # Delete AI models
                    elif models_rect.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        confirm = confirm_dialog("Delete AI Models", 
                                             "Are you sure you want to delete all AI models?",
                                             "This will remove all trained neural networks.")
                        if confirm:
                            delete_ai_models()
                
                # Mouse wheel scrolling
                if e.button == 4:  # Scroll up
                    scroll_velocity -= 15
                elif e.button == 5:  # Scroll down
                    scroll_velocity += 15
            
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    # Save all settings
                    _save_settings(config, music_on, background_theme, debug_mode, enhanced_effects,
                                 snake_theme_index, food_theme_index, player_position)
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
                    scroll_y = 500  # Approximate max scroll
        
        # Apply smooth scrolling
        if abs(scroll_velocity) > 0.1:
            scroll_y += scroll_velocity
            scroll_velocity *= 0.9  # Damping factor
        else:
            scroll_velocity = 0
        
        # Clamp scroll position
        scroll_y = max(0, min(500, scroll_y))  # Arbitrary max value
        
        step += 1
        clock.tick(60)

def _save_settings(config, music_on, background_theme, debug_mode, enhanced_effects,
                  snake_theme_index, food_theme_index, player_position):
    """Save all settings to the config file"""
    # Save all settings
    config["audio"]["music_on"] = music_on
    config["appearance"]["background_theme"] = background_theme
    config["appearance"]["enhanced_effects"] = enhanced_effects
    config["gameplay"]["debug_mode"] = debug_mode
    config["gameplay"]["player_position"] = player_position
    
    # Save to file
    save_config(config)
    
    # Save theme preferences to customization system
    customization.set_snake_theme(snake_theme_index)
    customization.set_food_theme(food_theme_index)
    customization.save_preferences()

def show_settings_help(page_index):
    """Show context-specific help for the settings page"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # Get help content for the specific page
    if page_index == 0:
        title = "General Settings Help"
        content = [
            "• Music: Toggle background music on/off",
            "• Background Theme: Choose between dark and light modes",
            "• Enhanced Effects: Enable or disable visual effects and animations",
            "• Player Position: Set your side of the screen for Player vs AI mode"
        ]
    elif page_index == 1:
        title = "Customization Help"
        content = [
            "• Snake Theme: Choose from various snake color schemes",
            "• Random theme will generate a new color each game",
            "• Food Theme: Select the appearance of food items",
            "• Rainbow food will cycle through colors as you play"
        ]
    else:  # page_index == 2
        title = "Advanced Settings Help"
        content = [
            "• Debug Mode: Shows additional information during gameplay",
            "• Reset High Scores: Permanently delete all saved high scores",
            "• Delete AI Models: Remove trained neural network models",
            "• Use these options with caution - actions cannot be undone"
        ]
    
    # Dark overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    
    # Create help dialog
    dialog_width = 600
    dialog_height = 400
    dialog_x = (SCREEN_WIDTH - dialog_width) // 2
    dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
    
    # Close button
    close_button = pygame.Rect(dialog_x + dialog_width - 120, dialog_y + dialog_height - 60, 100, 40)
    
    step = 0
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw blurred background
        screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(screen, (40, 45, 80), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=15)
        pygame.draw.rect(screen, (60, 70, 120), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=15)
        
        # Draw title
        title_surf = menu_font.render(title, True, (255, 220, 100))
        screen.blit(title_surf, (dialog_x + (dialog_width - title_surf.get_width()) // 2, dialog_y + 30))
        
        # Draw content
        content_y = dialog_y + 100
        for line in content:
            line_surf = footer_font.render(line, True, WHITE)
            screen.blit(line_surf, (dialog_x + 40, content_y))
            content_y += 40
        
        # Draw close button
        close_hover = close_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (180, 60, 60) if not close_hover else (220, 80, 80), 
                      close_button, border_radius=10)
        close_text = footer_font.render("Close", True, WHITE)
        close_rect = close_text.get_rect(center=close_button.center)
        screen.blit(close_text, close_rect)
        
        pygame.display.update()
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if close_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    return
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE or e.key == pygame.K_RETURN:
                    if click_sound: click_sound.play()
                    return
        
        step += 1
        clock.tick(60)

def confirm_dialog(title, message, warning=None):
    """Show a confirmation dialog and return True if confirmed"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # Dark overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    
    # Create dialog
    dialog_width = 500
    dialog_height = 300
    dialog_x = (SCREEN_WIDTH - dialog_width) // 2
    dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
    
    # Buttons
    yes_button = pygame.Rect(dialog_x + 80, dialog_y + dialog_height - 80, 120, 50)
    no_button = pygame.Rect(dialog_x + dialog_width - 80 - 120, dialog_y + dialog_height - 80, 120, 50)
    
    step = 0
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw blurred background
        screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(screen, (40, 45, 80), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=15)
        pygame.draw.rect(screen, (180, 60, 60), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=15)
        
        # Draw title
        title_surf = menu_font.render(title, True, (255, 100, 100))
        screen.blit(title_surf, (dialog_x + (dialog_width - title_surf.get_width()) // 2, dialog_y + 30))
        
        # Draw message
        message_surf = footer_font.render(message, True, WHITE)
        screen.blit(message_surf, (dialog_x + (dialog_width - message_surf.get_width()) // 2, dialog_y + 100))
        
        # Draw warning if provided
        if warning:
            warning_surf = footer_font.render(warning, True, (255, 180, 180))
            screen.blit(warning_surf, (dialog_x + (dialog_width - warning_surf.get_width()) // 2, dialog_y + 150))
        
        # Draw buttons
        yes_hover = yes_button.collidepoint(mouse_pos)
        no_hover = no_button.collidepoint(mouse_pos)
        
        pygame.draw.rect(screen, (180, 60, 60) if not yes_hover else (220, 80, 80), 
                      yes_button, border_radius=10)
        pygame.draw.rect(screen, (60, 100, 180) if not no_hover else (80, 140, 220), 
                      no_button, border_radius=10)
        
        yes_text = menu_font.render("Yes", True, WHITE)
        yes_rect = yes_text.get_rect(center=yes_button.center)
        screen.blit(yes_text, yes_rect)
        
        no_text = menu_font.render("No", True, WHITE)
        no_rect = no_text.get_rect(center=no_button.center)
        screen.blit(no_text, no_rect)
        
        pygame.display.update()
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if yes_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    return True
                elif no_button.collidepoint(e.pos):
                    if click_sound: click_sound.play()
                    return False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    return False
                elif e.key == pygame.K_RETURN:
                    if click_sound: click_sound.play()
                    return True
        
        step += 1
        clock.tick(60)

def reset_high_scores():
    """Reset all high scores"""
    highscore_file = "data/stats/highscores.json"
    
    try:
        # Create a new empty high scores file
        if not os.path.exists(os.path.dirname(highscore_file)):
            os.makedirs(os.path.dirname(highscore_file))
        
        # Create default structure
        high_scores = {
            "classic": {"scores": [], "dates": []},
            "ai": {"scores": [], "dates": []},
            "fibonacci": {"scores": [], "fib_values": [], "dates": []},
            "fibonacci_ai": {"scores": [], "fib_values": [], "dates": []},
            "vs": {
                "player": {"scores": [], "dates": []},
                "ai": {"scores": [], "dates": []},
                "matches": []
            }
        }
        
        # Write to file
        import json
        with open(highscore_file, 'w') as f:
            json.dump(high_scores, f, indent=4)
            
        print("High scores reset successfully")
    except Exception as e:
        print(f"Error resetting high scores: {e}")

def delete_ai_models():
    """Delete all AI models"""
    model_dirs = ["data/models", "data/checkpoints"]
    
    try:
        for dir_path in model_dirs:
            if os.path.exists(dir_path):
                # Delete all files in directory
                for file in os.listdir(dir_path):
                    if file.endswith('.pth') or file.endswith('.json'):
                        os.remove(os.path.join(dir_path, file))
                print(f"Deleted AI models in {dir_path}")
            else:
                print(f"Directory {dir_path} does not exist")
    except Exception as e:
        print(f"Error deleting AI models: {e}")