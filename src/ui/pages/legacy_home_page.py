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
    music_loaded, music_on_icon, music_off_icon,
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
    """Main home page/menu function"""
    global music_on, background_theme, enhanced_effects, debug_mode
    global current_gradient, next_gradient, gradient_blend
    
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
    
    # Set up buttons
    buttons = [
        {"text": "Play Classic Mode", "action": modules["play_classic_game"], 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 180, 400, 60)},
        {"text": "Play Fibonacci Mode", "action": modules["play_fibonacci_game"], 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 250, 400, 60)},
        {"text": "Player vs AI", "action": modules["player_vs_ai"], 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 320, 400, 60)},
        {"text": "Watch AI (Classic)", "action": modules["watch_ai_play"], 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 390, 400, 60)},
        {"text": "Watch AI (Fibonacci)", "action": modules["watch_fibonacci_ai_play"], 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 460, 400, 60)},
        {"text": "Settings", "action": modules["settings_page"], 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 530, 400, 60)},
        {"text": "Quit", "action": sys.exit, 
            "rect": pygame.Rect(SCREEN_WIDTH//2 - 200, 600, 400, 60)}
    ]
    
    # UI elements - increased from 48 to 56
    music_rect = pygame.Rect(SCREEN_WIDTH - 76, 20, 56, 56)  # Keep music icon position 
    scores_button = pygame.Rect(SCREEN_WIDTH - 152, 20, 56, 56)  # To the left of music
    help_button = pygame.Rect(SCREEN_WIDTH - 228, 20, 56, 56)  # To the left of scores

    # Help button - define once outside the loop with correct size
    help_button_size = 50  # Larger size for better visibility 
    help_color = (80, 100, 180)
    help_hover = (120, 140, 220)
    
    # Initialize particles
    particles = [Particle() for _ in range(80)]
    step = 0

    # Pre-render static elements to reduce flickering
    title_text = "AI Serpentis"
    
    # Use the shared footer_font instead of hardcoded size
    footer_surf = footer_font.render("The Snake Game Reimagined v2.0", True, (200, 200, 200))
    footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
    
    # Pre-render button labels to avoid creating them every frame
    button_labels = []
    for button in buttons:
        # Use menu_font instead of hardcoded size
        text_surface = menu_font.render(button["text"], True, WHITE)
        button_labels.append(text_surface)
    
    # Cache button surfaces
    button_surfaces = [None] * len(buttons)
    shadow_surfaces = [None] * len(buttons)
    
    # Main loop
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Update background effects
        draw_smooth_gradient(screen, current_gradient, next_gradient, gradient_blend)
        
        # Update and draw particles
        for particle in particles:
            particle.update()
            particle.draw(screen)
        
        # Draw title using the glowing_text function from components.py
        title_text = "AI Serpentis"
        title_x = (SCREEN_WIDTH - title_font.size(title_text)[0]) // 2
        glowing_text(screen, title_text, title_font, title_x, 80, YELLOW, step)
                
        # Draw main menu buttons
        for i, button in enumerate(buttons):
            rect = button["rect"]
            name = button["text"]
            is_hovered = rect.collidepoint(mouse_pos)
            
            # Choose gradient colors based on hover state
            left_color = BUTTON_HOVER_LEFT if is_hovered else BUTTON_BASE_LEFT
            right_color = BUTTON_HOVER_RIGHT if is_hovered else BUTTON_BASE_RIGHT
            
            # Create gradient button
            if button_surfaces[i] is None:
                button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                for x in range(rect.width):
                    ratio = x / rect.width
                    r = int(left_color[0] * (1 - ratio) + right_color[0] * ratio)
                    g = int(left_color[1] * (1 - ratio) + right_color[1] * ratio)
                    b = int(left_color[2] * (1 - ratio) + right_color[2] * ratio)
                    pygame.draw.line(button_surface, (r, g, b), (x, 0), (x, rect.height))
                rounded_rect = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(rounded_rect, (255, 255, 255), (0, 0, rect.width, rect.height), border_radius=12)
                button_surface.blit(rounded_rect, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                button_surfaces[i] = button_surface
            
            # Add shadow for depth
            if shadow_surfaces[i] is None:
                shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 30))
                shadow_surfaces[i] = shadow
            
            shadow_rect = shadow_surfaces[i].get_rect(topleft=(rect.x + 2, rect.y + 2))
            screen.blit(shadow_surfaces[i], shadow_rect)
            
            # Draw button
            screen.blit(button_surfaces[i], rect)
            
            # Add hover glow effect
            if is_hovered:
                glow_width = int(abs(math.sin(step / 15)) * 4) + 1
                glow_rect = rect.inflate(10, 10)
                pygame.draw.rect(screen, BUTTON_HOVER_RIGHT, glow_rect, glow_width, border_radius=12)
            
            # Add button text
            text_rect = button_labels[i].get_rect(center=rect.center)
            screen.blit(button_labels[i], text_rect)
        
        # Draw scores button - center the icon in the button rect
        scores_icon_rect = scores_icon.get_rect(center=scores_button.center)
        screen.blit(scores_icon, scores_icon_rect)
        if scores_button.collidepoint(mouse_pos):
            # Add glow effect on hover - adjusted for 52x52 icons
            glow_rect = scores_button.inflate(8, 8)
            glow_width = int(abs(math.sin(step / 15)) * 2) + 1
            pygame.draw.rect(screen, (80, 120, 200), glow_rect, glow_width, border_radius=7)

        # Draw help button - center the icon in the button rect 
        help_icon_rect = help_icon.get_rect(center=help_button.center)
        screen.blit(help_icon, help_icon_rect)
        if help_button.collidepoint(mouse_pos):
            # Add glow effect on hover - adjusted for 52x52 icons
            glow_rect = help_button.inflate(8, 8)
            glow_width = int(abs(math.sin(step / 15)) * 2) + 1
            pygame.draw.rect(screen, (80, 120, 200), glow_rect, glow_width, border_radius=7)

        # Draw music toggle icon - center the icon in the button rect
        music_icon = music_on_icon if music_on else music_off_icon
        music_icon_rect = music_icon.get_rect(center=music_rect.center)
        screen.blit(music_icon, music_icon_rect)
        if music_rect.collidepoint(mouse_pos):
            # Add glow effect on hover - adjusted for 52x52 icons
            glow_rect = music_rect.inflate(8, 8)
            glow_width = int(abs(math.sin(step / 15)) * 2) + 1
            pygame.draw.rect(screen, (80, 120, 200), glow_rect, glow_width, border_radius=7)
        
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
            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = e.pos
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
                    
                # For main menu buttons
                for button in buttons:
                    if button["rect"].collidepoint(pos):
                        if click_sound: click_sound.play()
                        button["action"]()
        
        # Advance gradient blend very slowly
        gradient_blend += 0.0001
        if gradient_blend >= 1.0:
            gradient_blend = 0.0
            current_gradient = next_gradient
            next_gradient = (next_gradient + 1) % len(dark_gradients)
        
        step += 1
        clock.tick(30)
        
            
    return text_surface