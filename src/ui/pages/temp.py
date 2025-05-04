import pygame
import sys
import math

from src.ui.components import (
    draw_smooth_gradient, glowing_text, draw_button, draw_fancy_button,
    Particle, YELLOW, WHITE
)

# Import shared globals
from src.ui.shared_globals import (
    SCREEN_WIDTH, SCREEN_HEIGHT, snake_color, background_theme,
    enhanced_effects, debug_mode, music_on, click_sound,
    music_loaded, music_on_icon, music_off_icon, settings_icon, quit_icon,
    current_gradient, next_gradient, gradient_blend,
    title_font, menu_font, footer_font, screen,
    BUTTON_BASE_LEFT, BUTTON_BASE_RIGHT,
    BUTTON_HOVER_LEFT, BUTTON_HOVER_RIGHT,
    dark_gradients, help_icon, scores_icon
)

from src.utils.config import load_config, save_config
from src.utils.sound_manager import sound_manager

# Import game modules at function level to avoid circular imports
def get_game_modules():
    """Import and return game modules dynamically to avoid circular imports"""
    from src.ui.game.classic_game import play_classic_game
    from src.ui.game.fibonacci_game import play_fibonacci_game
    from src.ui.game.ai_viewer import watch_ai_play, watch_fibonacci_ai_play
    from src.game.player_vs_ai import player_vs_ai
    from src.ui.pages.scores_page import high_scores_page
    from src.ui.pages.settings_page import settings_page
    from src.ui.pages.info_page import show_info_page
    
    return {
        "play_classic_game": play_classic_game,
        "play_fibonacci_game": play_fibonacci_game,
        "watch_ai_play": watch_ai_play,
        "watch_fibonacci_ai_play": watch_fibonacci_ai_play,
        "player_vs_ai": player_vs_ai,
        "high_scores_page": high_scores_page, 
        "settings_page": settings_page,
        "show_info_page": show_info_page
    }

def home_page():
    """Main home page/menu function with mobile-style card animation"""
    global music_on, background_theme, enhanced_effects, debug_mode
    global current_gradient, next_gradient, gradient_blend
    global settings_icon, quit_icon  # Add this line
    
    # Import game modules dynamically
    modules = get_game_modules()
    
    # Load config when entering the home page
    config = load_config()
    background_theme = config["appearance"]["background_theme"]
    enhanced_effects = config["appearance"]["enhanced_effects"]
    music_on = config["audio"]["music_on"]
    debug_mode = config["gameplay"]["debug_mode"]
    
    # Play music ONCE - the sound manager will now track if it's already started
    sound_manager.play_music()
    
    clock = pygame.time.Clock()
    
    # Set up buttons with gameplay options only
    buttons = [
        {"text": "Play Classic Mode", "action": modules["play_classic_game"]},
        {"text": "Play Fibonacci Mode", "action": modules["play_fibonacci_game"]},
        {"text": "Player vs AI", "action": modules["player_vs_ai"]},
        {"text": "Watch AI (Classic)", "action": modules["watch_ai_play"]},
        {"text": "Watch AI (Fibonacci)", "action": modules["watch_fibonacci_ai_play"]}
    ]
    
    # Add utility buttons in bottom right
    button_spacing = 20
    button_size = 56
    margin = 30
    
    # Position buttons in bottom right with spacing
    settings_button = pygame.Rect(
        SCREEN_WIDTH - margin - button_size - button_spacing - button_size,  # Moved left
        SCREEN_HEIGHT - margin - button_size,
        button_size, button_size
    )
    quit_button = pygame.Rect(
        SCREEN_WIDTH - margin - button_size,  # Moved right
        SCREEN_HEIGHT - margin - button_size,
        button_size, button_size
    )
    
    # UI elements
    music_rect = pygame.Rect(SCREEN_WIDTH - 76, 20, 56, 56)  
    scores_button = pygame.Rect(SCREEN_WIDTH - 152, 20, 56, 56) 
    help_button = pygame.Rect(SCREEN_WIDTH - 228, 20, 56, 56)
    
    # Central position for the cards - moved up before arrows use it
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    
    # Navigation arrows - larger and more visible
    arrow_width = 40
    arrow_height = 70
    left_arrow_rect = pygame.Rect(60, center_y - arrow_height//2, arrow_width, arrow_height)
    right_arrow_rect = pygame.Rect(SCREEN_WIDTH - 60 - arrow_width, center_y - arrow_height//2, arrow_width, arrow_height)
    
    # Initialize particles for background
    particles = [Particle() for _ in range(80)]
    step = 0
    
    # Track which menu item is currently centered
    current_page = 0
    target_page = 0
    page_offset = 0.0  # For smooth page transitions
    
    # Animation settings for mobile-style transitions
    animation_active = False
    animation_time = 0.0
    animation_direction = 0
    animation_duration = 16  # Slightly reduced for faster overall animation
    
    # Card dimensions - reduced size for better proportions
    card_size = 320  # Size of main card (square) - reduced from 400
    
    # Scale settings for cards
    focused_scale = 1.0      # Current card is full size
    unfocused_scale = 0.7    # Adjacent cards are 70% size
    
    # Positioning settings - tighter spacing between cards
    card_spacing = 200       # Reduced from 220 for better proportion with smaller cards
    
    # Central position for the cards
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    
    # Pre-render static elements
    footer_surf = footer_font.render("The Snake Game Reimagined v2.0", True, (200, 200, 200))
    footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
    
    # Prerender button labels
    button_labels = []
    for button in buttons:
        text_surface = menu_font.render(button["text"], True, WHITE)
        button_labels.append(text_surface)
    
    # Cache card surfaces
    card_surfaces = [None] * len(buttons)
    shadow_surfaces = [None] * len(buttons)
    
    # Animation timing variables
    selection_pulse = 0
    glow_pulse = 0
    arrow_pulse = 0
    
    # Page indicator variables
    indicator_radius = 8
    indicator_spacing = 20
    indicator_y = SCREEN_HEIGHT - 70
    
    # Main loop
    while True:
        frame_start_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        
        # Update background effects
        draw_smooth_gradient(screen, current_gradient, next_gradient, gradient_blend)
        
        # Update and draw particles
        for particle in particles:
            particle.update()
            particle.draw(screen)
        
        # Draw title with glow effect - use step variable like in legacy version
        title_text = "AI Serpentis"
        title_x = (SCREEN_WIDTH - title_font.size(title_text)[0]) // 2
        glowing_text(screen, title_text, title_font, title_x, 80, YELLOW, step)
        
        # Number of buttons/items in the carousel
        num_buttons = len(buttons)
        
        # Handle page animation with improved spring physics
        if animation_active:
            animation_time += 2.0 / animation_duration  # Faster initial movement (increased from 1.5)
            
            if animation_time >= 1.0:
                # Animation complete - snap exactly to target page
                animation_active = False
                animation_time = 0.0
                current_page = target_page
                page_offset = 0.0
            else:
                # Enhanced spring-like easing with even faster startup
                progress = animation_time
                
                # Modified curve with immediate movement
                if progress < 0.6:  # Reduced from 0.7 to accelerate earlier portion
                    # Accelerated first part with immediate start
                    t = progress / 0.6
                    # Modified ease out cubic that starts moving immediately
                    ease_factor = 1 - (1-t) * (1-t) * (1-t) * 0.8  # Added multiplier to increase effect
                    page_offset = animation_direction * (1 - ease_factor)
                else:
                    # Enhanced bounce at end
                    t = (progress - 0.6) / 0.4
                    bounce = math.sin(t * math.pi) * 0.08
                    page_offset = animation_direction * bounce
        
        # Create surfaces for cards if needed
        for i in range(num_buttons):
            if card_surfaces[i] is None:
                # Create card surface
                card_surface = pygame.Surface((card_size, card_size), pygame.SRCALPHA)
                
                # Fill with enhanced gradient
                for x in range(card_size):
                    ratio = x / card_size
                    cubic_ratio = ratio * ratio * (3 - 2 * ratio)  # Smooth interpolation
                    r = int(BUTTON_BASE_LEFT[0] * (1 - cubic_ratio) + BUTTON_BASE_RIGHT[0] * cubic_ratio)
                    g = int(BUTTON_BASE_LEFT[1] * (1 - cubic_ratio) + BUTTON_BASE_RIGHT[1] * cubic_ratio)
                    b = int(BUTTON_BASE_LEFT[2] * (1 - cubic_ratio) + BUTTON_BASE_RIGHT[2] * cubic_ratio)
                    pygame.draw.line(card_surface, (r, g, b), (x, 0), (x, card_size))
                
                # Add stronger inner border highlight
                pygame.draw.rect(card_surface, (255, 255, 255, 40), 
                            (5, 5, card_size-10, card_size-10), 2, border_radius=15)
                
                # Make it rounded
                rounded_rect = pygame.Surface((card_size, card_size), pygame.SRCALPHA)
                pygame.draw.rect(rounded_rect, (255, 255, 255), (0, 0, card_size, card_size), border_radius=20)
                card_surface.blit(rounded_rect, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                card_surfaces[i] = card_surface
                
                # Create enhanced shadow for depth effect - using multiple layers
                shadow = pygame.Surface((card_size+30, card_size+30), pygame.SRCALPHA)
                # Outer softer shadow
                pygame.draw.rect(shadow, (0, 0, 0, 20), (5, 5, card_size+20, card_size+20), border_radius=28)
                # Inner stronger shadow
                pygame.draw.rect(shadow, (0, 0, 0, 40), (0, 0, card_size+20, card_size+20), border_radius=25)
                shadow_surfaces[i] = shadow
        
        # Prepare to draw cards
        cards_to_draw = []
        
        # Calculate which cards to show based on current page with wraparound
        visible_indices = []
        # Always show current page and adjacent pages (with wraparound)
        for offset in range(-2, 3):  # Show -2, -1, 0, 1, 2 relative to current page
            page_idx = (current_page + offset) % num_buttons
            visible_indices.append((offset, page_idx))
        
        # Process cards for display with improved mobile-style positioning
        for offset, idx in visible_indices:
            # Skip cards that would be too far from view
            if abs(offset) > 2:
                continue
                
            # Calculate position offset based on animation
            effective_offset = offset + page_offset
            
            # Calculate scale based on distance from center (mobile-style)
            # Center card is full size, others are smaller with smoother falloff
            if abs(effective_offset) < 0.1:
                scale = focused_scale  # Center card
            else:
                # Further cards get progressively smaller with cubic falloff
                distance_factor = min(1.0, abs(effective_offset))
                cubic_factor = distance_factor * distance_factor * (3 - 2 * distance_factor)
                scale = focused_scale - ((focused_scale - unfocused_scale) * cubic_factor)
            
            # Calculate horizontal position with improved overlap
            # This creates proper card positioning for mobile-like paging
            card_x = center_x + effective_offset * card_spacing
            
            # Apply scale to the card
            scaled_size = int(card_size * scale)
            displayed_card = pygame.transform.smoothscale(card_surfaces[idx], (scaled_size, scaled_size))
            
            # Scale and position shadow with improved depth
            shadow_size = int((card_size + 30) * scale)
            displayed_shadow = pygame.transform.smoothscale(shadow_surfaces[idx], (shadow_size, shadow_size))
            
            # Set card transparency based on distance from center - improved curve
            alpha_factor = 1.0 - (min(1.5, abs(effective_offset)) / 1.5)
            alpha_factor = alpha_factor * alpha_factor  # Quadratic falloff for more natural fade
            alpha = int(255 * alpha_factor)
            
            if alpha < 255:
                temp = displayed_card.copy()
                temp.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
                displayed_card = temp
            
            # Position card and shadow with enhanced parallax effect
            # More natural depth curve
            parallax_factor = abs(effective_offset) * abs(effective_offset) * 0.8  # Quadratic falloff
            parallax_y_offset = parallax_factor * 20  # Increased from 15 to 20
            card_y = center_y + parallax_y_offset
            
            # Create rectangles for positioning
            card_rect = displayed_card.get_rect(center=(card_x, card_y))
            
            # Enhanced shadow positioning for better depth perception
            shadow_offset_x = scale * 4 * (1 + abs(effective_offset) * 0.5)
            shadow_offset_y = scale * 8 * (1 + abs(effective_offset) * 0.5)
            shadow_rect = displayed_shadow.get_rect(center=(card_x + shadow_offset_x, card_y + shadow_offset_y))
            
            # Calculate z-order for proper stacking (center card on top)
            # Enhanced to ensure cards never have z-fighting
            z_order = 1000 - int(abs(effective_offset) * 400) - offset  # Adding offset ensures consistent ordering
            
            # Add to drawing list
            cards_to_draw.append({
                "shadow": displayed_shadow,
                "shadow_rect": shadow_rect,
                "card": displayed_card,
                "rect": card_rect,
                "text": button_labels[idx],
                "scale": scale,
                "idx": idx,
                "z_order": z_order,
                "alpha": alpha,
                "offset": effective_offset
            })
            
            # Only center card is clickable
            if abs(effective_offset) < 0.5:
                buttons[idx]["rect"] = card_rect
            else:
                buttons[idx]["rect"] = None
        
        # Sort cards by z-order for proper layering
        cards_to_draw.sort(key=lambda x: x["z_order"])
        
        # Draw cards in z-order (back to front)
        for card_data in cards_to_draw:
            # Draw shadow
            screen.blit(card_data["shadow"], card_data["shadow_rect"])
            
            # Draw card
            screen.blit(card_data["card"], card_data["rect"])
            
            # Add inward animation effect for center card on hover
            if abs(card_data["offset"]) < 0.5 and card_data["rect"].collidepoint(mouse_pos):
                # Create inward animation effect - outline moving inward
                pulse_factor = (math.sin(step / 8) + 1) / 2  # 0 to 1 range
                # Start with larger rectangle and animate inward
                inner_rect_size = int(10 + 10 * pulse_factor)
                
                # Draw multiple inward-moving outlines with thicker lines
                # Use grayish white color matching the card border
                outline_color = (23, 26, 24)  # Light gray matching card edge
                
                for i in range(3):
                    inset = inner_rect_size - (i * 3)
                    if inset > 0:
                        inward_rect = card_data["rect"].inflate(-inset, -inset)
                        # Increased thickness from 2 to 4 pixels
                        pygame.draw.rect(screen, outline_color, inward_rect, 4, border_radius=18)
            
            # Draw text with improved scaling
            text = card_data["text"]
            if card_data["scale"] < 1.0:
                scaled_text = pygame.transform.smoothscale(
                    text, 
                    (int(text.get_width() * card_data["scale"]), 
                     int(text.get_height() * card_data["scale"]))
                )
            else:
                scaled_text = text
                
            # Scale the text alpha to match the card
            if card_data["alpha"] < 255:
                temp_text = scaled_text.copy()
                temp_text.fill((255, 255, 255, card_data["alpha"]), None, pygame.BLEND_RGBA_MULT)
                scaled_text = temp_text
                
            text_rect = scaled_text.get_rect(center=card_data["rect"].center)
            screen.blit(scaled_text, text_rect)
        
        # Draw navigation arrows on the sides
        # Left arrow with pulsating effect
        left_hover = left_arrow_rect.collidepoint(mouse_pos)
        pulse_factor = 0.7 + abs(math.sin(arrow_pulse)) * 0.3  # Pulsate between 0.7 and 1.0 intensity
        
        if left_hover:
            left_color = (255, 255, 255)  # Bright white on hover
            left_outline_color = (120, 180, 255)  # Light blue outline on hover
            outline_thickness = 2
        else:
            # Normal state with pulse
            intensity = int(220 * pulse_factor)
            left_color = (intensity, intensity, intensity)  # Pulsating white/gray
            left_outline_color = None
            outline_thickness = 0
        
        # Draw left arrow
        arrow_points = [
            (left_arrow_rect.left + left_arrow_rect.width * 0.8, left_arrow_rect.top),
            (left_arrow_rect.left, left_arrow_rect.centery),
            (left_arrow_rect.left + left_arrow_rect.width * 0.8, left_arrow_rect.bottom)
        ]
        pygame.draw.polygon(screen, left_color, arrow_points)
        
        # Draw outline if hovering
        if left_outline_color:
            pygame.draw.polygon(screen, left_outline_color, arrow_points, outline_thickness)
        
        # Right arrow with pulsating effect
        right_hover = right_arrow_rect.collidepoint(mouse_pos)
        
        if right_hover:
            right_color = (255, 255, 255)  # Bright white on hover
            right_outline_color = (120, 180, 255)  # Light blue outline on hover
            outline_thickness = 2
        else:
            # Normal state with pulse
            intensity = int(220 * pulse_factor)
            right_color = (intensity, intensity, intensity)  # Pulsating white/gray
            right_outline_color = None
            outline_thickness = 0
        
        # Draw right arrow
        arrow_points = [
            (right_arrow_rect.right - right_arrow_rect.width * 0.8, right_arrow_rect.top),
            (right_arrow_rect.right, right_arrow_rect.centery),
            (right_arrow_rect.right - right_arrow_rect.width * 0.8, right_arrow_rect.bottom)
        ]
        pygame.draw.polygon(screen, right_color, arrow_points)
        
        # Draw outline if hovering
        if right_outline_color:
            pygame.draw.polygon(screen, right_outline_color, arrow_points, outline_thickness)
        
        # Draw page indicators (dots) centered beneath cards with pulse animation
        indicator_start_x = center_x - (num_buttons-1) * indicator_spacing // 2
        for i in range(num_buttons):
            # Active page has different color/size with subtle pulse
            if i == current_page:
                pulse = abs(math.sin(selection_pulse)) * 0.2 + 0.8  # 0.8 to 1.0 range
                color = (int(255 * pulse), int(255 * pulse), int(255 * pulse))
                radius = indicator_radius + int(abs(math.sin(selection_pulse)) * 1.5)
            else:
                color = (150, 150, 150)
                radius = indicator_radius - 2
                
            # Draw indicator dot
            pygame.draw.circle(
                screen, 
                color, 
                (indicator_start_x + i * indicator_spacing, indicator_y),
                radius
            )
        
        # Draw utility buttons at the top right
        scores_icon_rect = scores_icon.get_rect(center=scores_button.center)
        screen.blit(scores_icon, scores_icon_rect)
        if scores_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (80, 120, 200), scores_button, 2, border_radius=7)

        help_icon_rect = help_icon.get_rect(center=help_button.center)
        screen.blit(help_icon, help_icon_rect)
        if help_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (80, 120, 200), help_button, 2, border_radius=7)

        music_icon = music_on_icon if music_on else music_off_icon
        music_icon_rect = music_icon.get_rect(center=music_rect.center)
        screen.blit(music_icon, music_icon_rect)
        if music_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (80, 120, 200), music_rect, 2, border_radius=7)
        
        # Draw settings and quit buttons in the bottom right - standardized style
        # Settings button (matching top button hover style)
        settings_hover = settings_button.collidepoint(mouse_pos)
        if settings_hover:
            pygame.draw.rect(screen, (80, 120, 200), settings_button, 2, border_radius=7)
        
        # Create fallback icons if they're not available
        if settings_icon is None:
            # Create a simple gear icon as fallback
            settings_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(settings_icon, (200, 200, 220), (20, 20), 18)
            pygame.draw.circle(settings_icon, (50, 70, 100), (20, 20), 10)
        
        if quit_icon is None:
            # Create a simple X icon as fallback
            quit_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.line(quit_icon, (220, 100, 100), (10, 10), (30, 30), 5)
            pygame.draw.line(quit_icon, (220, 100, 100), (30, 10), (10, 30), 5)
        
        # Now use the icons (using same sizing as top buttons)
        settings_icon_rect = settings_icon.get_rect(center=settings_button.center)
        screen.blit(settings_icon, settings_icon_rect)
        
        # Quit button (matching top button hover style)
        quit_hover = quit_button.collidepoint(mouse_pos)
        if quit_hover:
            # Use same blue outline as other buttons for consistency
            pygame.draw.rect(screen, (80, 120, 200), quit_button, 2, border_radius=7)
        
        quit_icon_rect = quit_icon.get_rect(center=quit_button.center)
        screen.blit(quit_icon, quit_icon_rect)
        
        # Draw keyboard/swipe instructions
        hint_text = "LEFT/RIGHT: Navigate - SPACE: Select"
        hint_surf = footer_font.render(hint_text, True, (170, 170, 170))
        hint_rect = hint_surf.get_rect(midbottom=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
        screen.blit(hint_surf, hint_rect)
        
        # Draw footer
        screen.blit(footer_surf, footer_rect)
        
        pygame.display.update()
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                # Save config before quitting
                config["audio"]["music_on"] = music_on
                save_config(config)
                pygame.quit()
                sys.exit()
                
            # Mouse dragging for mobile-like swiping
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Only process clicks for mouse buttons 1-3 (not scroll wheel)
                if e.button <= 3:  # Exclude scroll wheel (buttons 4 and 5)
                    pos = e.pos
                    
                    # Handle utility buttons
                    if music_rect.collidepoint(pos):
                        if click_sound: click_sound.play()
                        music_on = not music_on
                        config["audio"]["music_on"] = music_on
                        if music_on:
                            pygame.mixer.music.play(-1)
                        else:
                            pygame.mixer.music.stop()
                            
                    elif scores_button.collidepoint(pos):
                        if click_sound: click_sound.play()
                        modules["high_scores_page"]()
                        
                    elif help_button.collidepoint(pos):
                        if click_sound: click_sound.play()
                        modules["show_info_page"]()
                    
                    # Handle bottom right utility buttons
                    elif settings_button.collidepoint(pos):
                        if click_sound: click_sound.play()
                        modules["settings_page"]()
                        
                    elif quit_button.collidepoint(pos):
                        if click_sound: click_sound.play()
                        # Save config before quitting
                        config["audio"]["music_on"] = music_on
                        save_config(config)
                        pygame.quit()
                        sys.exit()
                    
                    # Handle arrow navigation
                    elif left_arrow_rect.collidepoint(pos) and not animation_active:
                        if click_sound: click_sound.play()
                        animation_active = True
                        animation_time = 0.05  # Start with non-zero time for immediate movement
                        animation_direction = -1  
                        target_page = (current_page - 1) % num_buttons
                        # Add stronger immediate visual feedback
                        page_offset = -0.15  # Increased from -0.05 for immediate visible movement
                    
                    elif right_arrow_rect.collidepoint(pos) and not animation_active:
                        if click_sound: click_sound.play()
                        animation_active = True
                        animation_time = 0.05  # Start with non-zero time for immediate movement
                        animation_direction = 1 
                        target_page = (current_page + 1) % num_buttons
                        # Add stronger immediate visual feedback
                        page_offset = 0.15  # Increased from 0.05 for immediate visible movement
                    
                    # Handle card selection - only active during non-animation
                    else:
                        if not animation_active:
                            idx = current_page
                            if buttons[idx].get("rect") and buttons[idx]["rect"].collidepoint(pos):
                                if click_sound: click_sound.play()
                                buttons[idx]["action"]()
                    
                    # Store drag starting point for swipe detection
                    if e.button == 1:  # Left mouse button
                        drag_start = pos[0]
                        is_dragging = True
            
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1 and 'is_dragging' in locals() and is_dragging:
                    # Calculate swipe distance
                    if 'drag_start' in locals():
                        swipe_distance = e.pos[0] - drag_start
                        
                        # Only trigger page change if swipe was significant
                        if abs(swipe_distance) > 50 and not animation_active:
                            if click_sound: click_sound.play()
                            
                            # Swipe navigation
                            if swipe_distance > 0:  # Right swipe (previous page)
                                target_page = (current_page - 1) % num_buttons
                                animation_direction = 1
                                page_offset = 0.15  # Stronger initial feedback
                                animation_time = 0.05  # Start with non-zero time
                            else:  # Left swipe (next page)
                                target_page = (current_page + 1) % num_buttons
                                animation_direction = -1
                                page_offset = -0.15  # Stronger initial feedback
                                animation_time = 0.05  # Start with non-zero time
                                
                            animation_active = True
                            animation_time = 0.0
                    
                    is_dragging = False
            
            # Keyboard navigation
            if e.type == pygame.KEYDOWN and not animation_active:
                if e.key == pygame.K_LEFT:
                    if click_sound: click_sound.play()
                    animation_active = True
                    animation_time = 0.05  # Start with non-zero time
                    animation_direction = 1
                    target_page = (current_page - 1) % num_buttons
                    page_offset = 0.15  # Stronger initial feedback
                    
                elif e.key == pygame.K_RIGHT:
                    if click_sound: click_sound.play()
                    animation_active = True
                    animation_time = 0.05  # Start with non-zero time
                    animation_direction = -1
                    target_page = (current_page + 1) % num_buttons
                    page_offset = -0.15  # Stronger initial feedback
                    
                elif e.key == pygame.K_RETURN or e.key == pygame.K_SPACE:
                    if click_sound: click_sound.play()
                    buttons[current_page]["action"]()
        
        # Update animation pulses
        selection_pulse += 0.08
        glow_pulse += 0.03
        arrow_pulse += 0.05
        
        # Advance gradient blend
        gradient_blend += 0.0001
        if gradient_blend >= 1.0:
            gradient_blend = 0.0
            current_gradient = next_gradient
            next_gradient = (next_gradient + 1) % len(dark_gradients)
        
        step += 1
        
        # Control frame rate for smooth animation
        elapsed = pygame.time.get_ticks() - frame_start_time
        if elapsed < 33:  # Target ~30 FPS
            pygame.time.delay(33 - elapsed)
            
        clock.tick(30)