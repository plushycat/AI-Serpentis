import pygame
import sys
import math
from src.utils.input_utils import is_screenshot_key
from src.ui.components import (
    draw_smooth_gradient, draw_fancy_button, glowing_text, WHITE, YELLOW
)

# Import shared globals
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, click_sound, 
    screen, title_font, menu_font, footer_font
)

def show_settings_help(current_page=0):
    """Display help information about settings options"""
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
    
    # Replace diamond with simple dash
    bullet = "-"  # Simple dash instead of diamond symbol
    
    # Define help sections based on the current page
    gameplay_sections = [
        {
            "title": "Background Theme",
            "content": [
                f"{bullet} Dark Theme: Black background",
                f"{bullet} Light Theme: White background"
            ]
        },
        {
            "title": "Gameplay Settings",
            "content": [
                f"{bullet} Debug Mode: Shows AI vision during AI gameplay",
                f"{bullet} Player Position: Left/right side in VS Mode",
                f"{bullet} Level-Up Effects: Visual effects when growing"
            ]
        },
        {
            "title": "Controls",
            "content": [
                f"{bullet} Arrow Keys / WASD: Move snake",
                f"{bullet} P: Pause game",
                f"{bullet} ESC: Return to menu"
            ]
        }
    ]
    
    snake_theme_sections = [
        {
            "title": "Snake Themes",
            "content": [
                f"{bullet} Click any theme preview to select it",
                f"{bullet} Green border shows current selection",
                f"{bullet} Changes apply immediately"
            ]
        }
    ]
    
    food_theme_sections = [
        {
            "title": "Food Themes",
            "content": [
                f"{bullet} Click any food preview to select it",
                f"{bullet} Some themes have color-changing effects",
                f"{bullet} Green border shows current selection"
            ]
        }
    ]
    
    audio_sections = [
        {
            "title": "Audio Settings",
            "content": [
                f"{bullet} Music: Toggle background music on/off",
                f"{bullet} Settings apply immediately"
            ]
        }
    ]
    
    # Choose which sections to display based on current page
    if current_page == 0:  # Gameplay settings
        sections = gameplay_sections
        page_title = "Gameplay Settings"
    elif current_page == 1:  # Snake theme settings
        sections = snake_theme_sections
        page_title = "Snake Themes"
    elif current_page == 2:  # Food theme settings
        sections = food_theme_sections
        page_title = "Food Themes"
    elif current_page == 3:  # Audio settings
        sections = audio_sections
        page_title = "Audio Settings"
    else:  # Default to gameplay if an invalid page is requested
        sections = gameplay_sections
        page_title = "Settings Help"

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background
        draw_smooth_gradient(screen)
        
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
                # Section title - use title_font instead of menu_font for larger headings
                title_text = title_font.render(section["title"], True, (255, 220, 100))
                content_surface.blit(title_text, (30, y_pos))
                y_pos += 90  # Increased from 70 to 90 to accommodate larger heading
                
                # Section content with wrapping
                for line in section["content"]:
                    # Basic text wrapping - split long lines
                    words = line.split()
                    line_parts = []
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + word + " "
                        # Use menu_font instead of footer_font for larger text
                        if menu_font.size(test_line)[0] < content_area.width - 80:
                            current_line = test_line
                        else:
                            line_parts.append(current_line)
                            current_line = word + " "
                    
                    # Add the last line
                    if current_line:
                        line_parts.append(current_line)
                    
                    # Render wrapped lines with menu_font for larger text
                    for part in line_parts:
                        if y_pos + 50 > 0 or y_pos < content_area.height:
                            # Using menu_font instead of footer_font for larger text
                            text = menu_font.render(part, True, (220, 220, 220))
                            content_surface.blit(text, (50, y_pos))
                            y_pos += 50  # Increased from 40 to 50 for larger font
                
                # Add spacing between sections
                y_pos += 30
            else:
                # Skip rendering if section is off-screen, but still account for height
                height_estimate = 70 + len(section["content"]) * 50 + 30  # Adjusted for larger font
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
                elif is_screenshot_key(e):
                    # Take screenshot
                    timestamp = pygame.time.get_ticks()
                    pygame.image.save(screen, f"screenshot_{timestamp}.png")
        
        # Clamp scroll position
        if max_scroll_y > 0:
            content_scroll_y = max(0, min(max_scroll_y, content_scroll_y))
        else:
            content_scroll_y = 0
        
        step += 1
        clock.tick(60)