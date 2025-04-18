import pygame
import torch
import sys
import math
import os
import random
import json  
from model import Linear_QNet
from snake_game import SnakeGame
from snake_ai import SnakeGameAI
from agent import Agent
from customization import customization

def load_high_scores():
    """Load high scores from file or create default if it doesn't exist"""
    highscore_file = "statics/highscores.json"
    try:
        if os.path.exists(highscore_file):
            with open(highscore_file, 'r') as f:
                return json.load(f)
        else:
            # Default high scores
            high_scores = {
                "classic": 0,
                "ai": 0
            }
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(highscore_file), exist_ok=True)
            # Create the file with default scores
            with open(highscore_file, 'w') as f:
                json.dump(high_scores, f)
            return high_scores
    except Exception as e:
        print(f"Error loading high scores: {e}")
        return {"classic": 0, "ai": 0}

def save_high_score(mode, score):
    """Save high score if it's a new record"""
    highscore_file = "statics/highscores.json"
    try:
        high_scores = load_high_scores()
        
        # Update if it's a new high score
        if score > high_scores.get(mode, 0):
            high_scores[mode] = score
            
            # Save updated high scores
            with open(highscore_file, 'w') as f:
                json.dump(high_scores, f)
            return True  # Indicates this is a new high score
        return False
    except Exception as e:
        print(f"Error saving high score: {e}")
        return False

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Serpentis")

# Colors
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GREEN  = (0, 255,   0)
BLUE   = (0,   0, 255)
RED    = (255,   0,   0)
YELLOW = (255, 255,   0)
GRAY   = (200, 200, 200)

# Font loading with error handling
try:
    title_font  = pygame.font.Font("statics/game_over.ttf", 96)
    menu_font   = pygame.font.Font("statics/game_over.ttf", 48)
    footer_font = pygame.font.Font("statics/game_over.ttf", 36)
except FileNotFoundError:
    print("Warning: Font file not found. Using system fonts.")
    title_font  = pygame.font.SysFont("Arial", 96)
    menu_font   = pygame.font.SysFont("Arial", 48)
    footer_font = pygame.font.SysFont("Arial", 36)

# Load assets with error handling
try:
    # Load the click sound from the new location
    click_sound = pygame.mixer.Sound("statics/ui_click.mp3")
    eat_sound = pygame.mixer.Sound("statics/eat-food.mp3")
    pygame.mixer.music.load("statics/bg_music.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
except FileNotFoundError as e:
    print(f"Warning: Sound file not found: {e}")
    click_sound = None
    eat_sound = None

# Load icons
try:
    music_on_icon  = pygame.image.load("statics/music_on.png")
    music_off_icon = pygame.image.load("statics/music_off.png")
    music_on_icon  = pygame.transform.scale(music_on_icon,  (40, 40))
    music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))
except FileNotFoundError:
    print("Warning: Icon files not found.")
    music_on_icon  = pygame.Surface((40, 40)); music_on_icon.fill(GREEN)
    music_off_icon = pygame.Surface((40, 40)); music_off_icon.fill(RED)

# State variables
music_on         = True
game_speed       = 30
snake_color      = (100, 200, 100)
background_theme = "dark"
debug_mode       = False

# Dark gradient palettes
dark_gradients = [
    ((0,   0,  40), (10,  10,  70)),
    ((5,  10,  50), (30,   0, 100)),
    ((15,   0,  60), (40,   5,  90)),
    ((0,  20,  80), (25,  25,  60)),
]
current_gradient = 0
next_gradient    = 1
gradient_blend   = 0.0

# Draw a smooth, slowly blending dark gradient background
def draw_smooth_gradient():
    c1 = dark_gradients[current_gradient][0]
    c2 = dark_gradients[current_gradient][1]
    d1 = dark_gradients[next_gradient][0]
    d2 = dark_gradients[next_gradient][1]

    start = tuple(int((1 - gradient_blend) * c1[i] + gradient_blend * d1[i]) for i in range(3))
    end   = tuple(int((1 - gradient_blend) * c2[i] + gradient_blend * d2[i]) for i in range(3))

    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(start[0] * (1 - t) + end[0] * t)
        g = int(start[1] * (1 - t) + end[1] * t)
        b = int(start[2] * (1 - t) + end[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

# Particle for subtle moving background effect
class Particle:
    def __init__(self):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(0, SCREEN_HEIGHT)
        self.r = random.uniform(1, 3)
        self.speed = random.uniform(0.5, 1.5)
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.uniform(0, SCREEN_WIDTH)
    def draw(self):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(self.r))

# Glowing animated title text
def glowing_text(screen, text, font, x, y, base_color, step):
    glow = abs(math.sin(step / 20)) * 180
    color = (
        min(255, base_color[0] + glow),
        min(255, base_color[1] + glow),
        min(255, base_color[2] + glow),
    )
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

# Modern button with hover effect
def draw_button(screen, rect, text, font, base_color, hover_color, mouse_pos):
    is_hover = rect.collidepoint(mouse_pos)
    color = hover_color if is_hover else base_color
    pygame.draw.rect(screen, color, rect, border_radius=12)
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 30))
    screen.blit(shadow, rect.topleft)

    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return is_hover

# Fancy button adds pulsing border on hover
def draw_fancy_button(screen, rect, text, font, base_color, hover_color, mouse_pos, step):
    hovered = draw_button(screen, rect, text, font, base_color, hover_color, mouse_pos)
    if hovered:
        glow_width = int(abs(math.sin(step / 15)) * 4) + 1
        glow_rect  = rect.inflate(10, 10)
        pygame.draw.rect(screen, hover_color, glow_rect, glow_width, border_radius=12)
    return hovered

# Draw a slider for speed control
def draw_slider(screen, x, y, width, min_val, max_val, current_val):
    pygame.draw.line(screen, GRAY, (x, y), (x + width, y), 5)
    slider_pos = x + int((current_val - min_val) / (max_val - min_val) * width)
    pygame.draw.circle(screen, WHITE, (slider_pos, y), 10)
    return slider_pos

def home_page():
    global music_on, screen, current_gradient, next_gradient, gradient_blend
    clock = pygame.time.Clock()
    
    # Button layout parameters
    button_width   = 300
    button_height  = 60
    button_spacing = 80
    total_height   = 4 * button_height + 3 * (button_spacing - button_height)
    start_y        = (SCREEN_HEIGHT - total_height) // 2
    
    buttons = {
        "Play Classic": pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y,                 button_width, button_height),
        "Watch AI":     pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + button_spacing, button_width, button_height),
        "Settings":     pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + 2*button_spacing, button_width, button_height),
        "Quit":         pygame.Rect((SCREEN_WIDTH - button_width)//2, start_y + 3*button_spacing, button_width, button_height),
    }
    music_rect = pygame.Rect(SCREEN_WIDTH - 60, 20, 40, 40)
    
    # Initialize particles
    particles = [Particle() for _ in range(80)]
    step = 0

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw background gradient
        draw_smooth_gradient()
        # Draw particles
        for p in particles:
            p.update()
            p.draw()
        
        # Draw glowing title (centered)
        title_text = "AI Serpentis"
        title_surface = title_font.render(title_text, True, YELLOW)
        title_x = (SCREEN_WIDTH - title_surface.get_width()) // 2
        glowing_text(screen, title_text, title_font, title_x, 80, YELLOW, step)
        
        # Draw fancy buttons (all same base and hover colors)
        BUTTON_BASE  = (0, 150, 0)
        BUTTON_HOVER = GREEN
        for name, rect in buttons.items():
            draw_fancy_button(screen, rect, name, menu_font, BUTTON_BASE, BUTTON_HOVER, mouse_pos, step)
        
        # Music toggle icon
        screen.blit(music_on_icon if music_on else music_off_icon, music_rect.topleft)
        
        # Draw footer (centered)
        footer_surf = footer_font.render("The Snake Game Reimagined v2.0", True, (200, 200, 200))
        footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        screen.blit(footer_surf, footer_rect)
        
        pygame.display.update()
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = e.pos
                if buttons["Play Classic"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    play_classic_game()
                elif buttons["Watch AI"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    watch_ai_play()
                elif buttons["Settings"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    settings_page()
                elif buttons["Quit"].collidepoint(pos):
                    if click_sound: click_sound.play()
                    pygame.quit()
                    sys.exit()
                elif music_rect.collidepoint(pos):
                    if click_sound: click_sound.play()  # Add click sound for music toggle
                    music_on = not music_on
                    if music_on:
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.stop()
        
        # Advance gradient blend very slowly
        gradient_blend += 0.0001
        if gradient_blend >= 1.0:
            gradient_blend   = 0.0
            current_gradient = next_gradient
            next_gradient    = (next_gradient + 1) % len(dark_gradients)
        
        step += 1
        clock.tick(30)

# Update play_classic_game to correctly apply customizations

def play_classic_game():
    global snake_color, background_theme, screen, game_speed
    
    # Load high scores
    high_scores = load_high_scores()
    classic_high_score = high_scores.get("classic", 0)
    
    # Initialize game with customized settings
    game = SnakeGame()
    
    # Initialize with current customization settings
    game.snake_theme = customization.get_current_snake_theme()
    game.food_theme = customization.get_current_food_theme()
    game.background_theme = background_theme
    
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
                font_large = pygame.font.Font("statics/game_over.ttf", 72)
                font_small = pygame.font.Font("statics/game_over.ttf", 36)
                font_medal = pygame.font.Font("statics/game_over.ttf", 48)  # Font for high score celebration
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.font.SysFont("Arial", 72)
                font_small = pygame.font.SysFont("Arial", 36)
                font_medal = pygame.font.SysFont("Arial", 48)
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))
            score_text = font_small.render(f"Your Score: {score}", True, WHITE)
            high_score_text = font_small.render(f"High Score: {max(classic_high_score, score)}", True, YELLOW)
            continue_text = font_small.render("Press any key to continue", True, (200, 200, 200))
            
            # Prepare new high score celebration if applicable
            if is_new_high:
                new_record_text = font_medal.render("NEW HIGH SCORE!", True, (255, 215, 0))  # Gold color
                
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 100))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2))
            high_score_rect = high_score_text.get_rect(center=(game.width//2, game.height//2 + 50))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 150))
            
            if is_new_high:
                new_record_rect = new_record_text.get_rect(center=(game.width//2, game.height//2 + 100))
            
            # Create dark overlay
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(high_score_text, high_score_rect)
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
                    glow_color = (255, 215, 0 + pulse)  # Pulsing gold
                    new_record_text = font_medal.render("NEW HIGH SCORE!", True, glow_color)
                    game.display.blit(new_record_text, new_record_rect)
                    pygame.display.update(overlay_rect)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if click_sound: click_sound.play()
                        waiting = False
                clock.tick(30)
            break

    # Return to main menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

def watch_ai_play():
    global snake_color, background_theme, screen, debug_mode
    model = Linear_QNet(11, 256, 3)
    
    # Try multiple model loading paths with better error handling
    try:
        # Look in different possible locations for the model
        model_paths = ["model/model.pth", "model_snapshots/model.pth", 
                        "training_checkpoints/checkpoint_model.pth"]
        model_loaded = False
        
        for path in model_paths:
            if os.path.exists(path):
                model.load_state_dict(torch.load(path))
                model_loaded = True
                print(f"Model loaded successfully from {path}")
                break
                
        if not model_loaded:
            print("Warning: No pre-trained model found. Using untrained model.")
        
        model.eval()  # Set model to evaluation mode
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Initialize game with customized settings
    game = SnakeGameAI(width=1280, height=720)
    game.snake_color = snake_color
    game.background_theme = background_theme
    
    # Get the record from training data
    record = 0
    try:
        checkpoint_file = os.path.join("training_checkpoints", "training_state.json")
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                state = json.load(f)
                record = state.get('record', 0)
    except:
        pass
    
    game.record = record  # Set the record to show
    game.viewing_mode = True  # Set a new flag to indicate viewer mode
    
    # Increase frame limit to prevent premature endings
    game.frame_limit_multiplier = 1000  # Very lenient frame limit for viewing
    game.debug_mode = debug_mode  # Pass debug mode to the game
    
    # Initialize agent with the model
    agent = Agent()
    agent.model = model
    agent.epsilon = 0  # No exploration, pure exploitation
    
    # Game loop
    while True:
        state = agent.get_state(game)
        move = agent.get_action(state)
        
        # Process the move
        reward, done, score = game.play_step(move)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if click_sound: click_sound.play()
                    done = True  # Exit on escape key
                elif event.key == pygame.K_p:  # Pause
                    if click_sound: click_sound.play()
                    paused = True
                    
                    # Create appropriate overlay based on the theme
                    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
                    overlay_color = (0, 0, 0, 120) if game.background_theme == "dark" else (255, 255, 255, 120)
                    overlay.fill(overlay_color)
                    game.display.blit(overlay, (0, 0))
                    
                    # Use game's font and appropriate color for the theme
                    if game.background_theme == "dark":
                        pause_color = WHITE
                    else:
                        pause_color = (20, 20, 100)  # Dark blue
                    
                    pause_text = game.sub_font.render('PAUSED - Press P to continue', True, pause_color)
                    game.display.blit(pause_text, (game.width//2 - pause_text.get_width()//2, game.height//2))
                    pygame.display.update()
                    
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_p:
                                paused = False
                            elif pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_ESCAPE:
                                done = True
                                paused = False
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                        pygame.time.wait(100)
        
        if done:
            print(f"AI Game Over! Final Score: {score}")
            # Show game over screen with score - using consistent fonts
            try:
                font_large = pygame.font.Font("statics/game_over.ttf", 72)
                font_small = pygame.font.Font("statics/game_over.ttf", 36)
            except FileNotFoundError:
                print("Warning: Font file not found. Using system fonts.")
                font_large = pygame.font.SysFont("Arial", 72)
                font_small = pygame.font.SysFont("Arial", 36)
            
            # Dynamic colors based on theme
            if game.background_theme == "dark":
                text_color = WHITE
                secondary_color = (200, 200, 200)
            else:
                text_color = (20, 20, 100)  # Dark blue
                secondary_color = (80, 80, 80)  # Dark gray
            
            game_over_text = font_large.render("GAME OVER", True, (255, 50, 50))  # Always red
            score_text = font_small.render(f"AI Score: {score}", True, text_color)
            record_text = font_small.render(f"Record: {max(record, score)}", True, text_color)
            continue_text = font_small.render("Press any key to continue", True, secondary_color)
            
            # Position texts
            game_over_rect = game_over_text.get_rect(center=(game.width//2, game.height//2 - 80))
            score_rect = score_text.get_rect(center=(game.width//2, game.height//2))
            record_rect = record_text.get_rect(center=(game.width//2, game.height//2 + 50))
            continue_rect = continue_text.get_rect(center=(game.width//2, game.height//2 + 120))
            
            # Create appropriate overlay for the current theme
            overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
            overlay_color = (0, 0, 0, 180) if game.background_theme == "dark" else (255, 255, 255, 180)
            overlay.fill(overlay_color)
            game.display.blit(overlay, (0, 0))
            
            # Draw texts
            game.display.blit(game_over_text, game_over_rect)
            game.display.blit(score_text, score_rect)
            game.display.blit(record_text, record_rect)
            game.display.blit(continue_text, continue_rect)
            pygame.display.update()
            
            # Wait for key press
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if click_sound: click_sound.play()
                        waiting = False
                pygame.time.wait(100)
            break
    
    # Return to menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Serpentis")

# Fix the settings page's responsiveness

def settings_page():
    global snake_color, background_theme, screen, game_speed, debug_mode
    clock = pygame.time.Clock()
    step = 0
    button_width = 300
    button_height = 60
    button_spacing = 80
    
    # Create a scroll area for all options
    scroll_y = 0
    max_scroll_y = 0  # Will be calculated based on content
    
    # Keep track of current page (0 = general, 1 = snake themes, 2 = food themes)
    current_page = 0
    
    # Get all available themes
    snake_themes = customization.get_all_snake_themes()
    food_themes = customization.get_all_food_themes()
    
    # Create buttons for all pages
    general_button = pygame.Rect((SCREEN_WIDTH//2 - button_width*1.5)//1, 120, button_width, button_height)
    snake_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 120, button_width, button_height)
    food_button = pygame.Rect(SCREEN_WIDTH//2 + button_width//2, 120, button_width, button_height)
    
    # General page buttons (Theme buttons)
    dark_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 200, button_width, button_height)
    light_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 280, button_width, button_height)
    debug_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, 360, button_width, button_height)
    
    # Back button
    back_button = pygame.Rect((SCREEN_WIDTH-button_width)//2, SCREEN_HEIGHT - 100, button_width, button_height)
    
    # Create theme preview rects
    preview_size = 180
    preview_margin = 20
    preview_cols = 3
    preview_width = preview_cols * (preview_size + preview_margin) - preview_margin
    
    # Track button and mouse states
    mouse_pressed = False
    mouse_pos = (0, 0)
    
    while True:
        # Mouse state tracking for responsive clicks
        prev_mouse_pressed = mouse_pressed
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_released = prev_mouse_pressed and not mouse_pressed
        mouse_pos = pygame.mouse.get_pos()
        
        draw_smooth_gradient()
        
        # Settings title
        title_x = (SCREEN_WIDTH - title_font.size("Settings")[0]) // 2
        glowing_text(screen, "Settings", title_font, title_x, 30, YELLOW, step)
        
        # Draw navigation tabs
        pygame.draw.rect(screen, (30, 30, 60), pygame.Rect(0, 110, SCREEN_WIDTH, button_height + 20))
        
        # Highlight the active tab
        active_tab_color = (60, 100, 200)
        inactive_tab_color = (40, 40, 80)
        
        draw_button(screen, general_button, "General", menu_font, 
                   active_tab_color if current_page == 0 else inactive_tab_color, 
                   (100, 150, 255), mouse_pos)
        draw_button(screen, snake_button, "Snake Theme", menu_font,
                   active_tab_color if current_page == 1 else inactive_tab_color, 
                   (100, 150, 255), mouse_pos)
        draw_button(screen, food_button, "Food Theme", menu_font,
                   active_tab_color if current_page == 2 else inactive_tab_color, 
                   (100, 150, 255), mouse_pos)
                   
        # Content area
        content_area = pygame.Rect(0, 200, SCREEN_WIDTH, SCREEN_HEIGHT - 320)
        
        # Process mouse wheel events for scrolling
        mouse_wheel_up = False
        mouse_wheel_down = False
        
        # Event handling - do this at the beginning of each frame
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
                    elif snake_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_page = 1
                        scroll_y = 0
                    elif food_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        current_page = 2
                        scroll_y = 0
                    
                    # General page buttons
                    if current_page == 0:
                        if dark_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            background_theme = "dark"
                        elif light_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            background_theme = "light"
                        elif debug_button.collidepoint(e.pos):
                            if click_sound: click_sound.play()
                            debug_mode = not debug_mode
                    
                    # Back button
                    if back_button.collidepoint(e.pos):
                        if click_sound: click_sound.play()
                        return
                
                # Mouse wheel scrolling
                elif e.button == 4:  # Scroll up
                    mouse_wheel_up = True
                elif e.button == 5:  # Scroll down
                    mouse_wheel_down = True
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return
        
        # Draw content based on current page
        if current_page == 0:
            # General settings page
            draw_button(screen, dark_button, "Theme: Dark", menu_font,
                      (50,50,80) if background_theme == "dark" else (30,30,50),
                      (80,80,120), mouse_pos)
            draw_button(screen, light_button, "Theme: Light", menu_font,
                      (200,200,220) if background_theme == "light" else (150,150,170),
                      (230,230,250), mouse_pos)
                      
            # Debug mode toggle button
            debug_label = "Debug: ON" if debug_mode else "Debug: OFF"
            debug_color = (100, 200, 100) if debug_mode else (200, 100, 100)
            draw_button(screen, debug_button, debug_label, menu_font, debug_color, (150, 150, 150), mouse_pos)
            
            # Speed slider UI
            speed_txt = menu_font.render(f"Game Speed: {game_speed}", True, WHITE)
            speed_rect = speed_txt.get_rect(center=(SCREEN_WIDTH//2, 460))
            screen.blit(speed_txt, speed_rect)
            
            # Draw slider
            slider_x = (SCREEN_WIDTH-button_width)//2
            slider_w = button_width
            min_s, max_s = 10, 60
            slider_y = 500
            slider_pos = slider_x + int((game_speed - min_s) / (max_s - min_s) * slider_w)
            
            pygame.draw.line(screen, GRAY, (slider_x, slider_y), (slider_x + slider_w, slider_y), 5)
            pygame.draw.circle(screen, WHITE, (slider_pos, slider_y), 10)
            
            # Handle slider drag
            if pygame.mouse.get_pressed()[0]:  # Left mouse button pressed
                if abs(mouse_pos[0] - slider_pos) < 20 and abs(mouse_pos[1] - slider_y) < 20:
                    ratio = max(0, min(1, (mouse_pos[0] - slider_x) / slider_w))
                    game_speed = int(min_s + ratio * (max_s - min_s))
            
        elif current_page == 1:
            # Snake themes page
            current_snake = customization.current_snake_theme
            
            # Calculate how many theme previews we need to show
            preview_rows = (len(snake_themes) + preview_cols - 1) // preview_cols
            content_height = preview_rows * (preview_size + preview_margin) - preview_margin
            max_scroll_y = max(0, content_height - content_area.height)
            
            # Adjust scroll with mouse wheel
            if mouse_wheel_up:
                scroll_y = max(0, scroll_y - 30)
            elif mouse_wheel_down:
                scroll_y = min(max_scroll_y, scroll_y + 30)
            
            # Draw snake theme previews
            y_pos = 220 - scroll_y
            x_pos = (SCREEN_WIDTH - preview_width) // 2
            
            for i, (key, theme) in enumerate(snake_themes.items()):
                row = i // preview_cols
                col = i % preview_cols
                
                theme_x = x_pos + col * (preview_size + preview_margin)
                theme_y = y_pos + row * (preview_size + preview_margin)
                
                # Only draw if visible in the content area
                if (theme_y < content_area.bottom and 
                    theme_y + preview_size > content_area.top):
                    
                    # Create preview rect
                    preview_rect = pygame.Rect(theme_x, theme_y, preview_size, preview_size)
                    
                    # Draw theme preview
                    pygame.draw.rect(screen, (30, 30, 60), preview_rect, border_radius=10)
                    
                    # Draw selection indicator if this is the current theme
                    if key == current_snake:
                        pygame.draw.rect(screen, (80, 200, 120), preview_rect, 4, border_radius=10)
                    elif preview_rect.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, (150, 150, 180), preview_rect, 2, border_radius=10)
                    
                    # Draw theme name
                    name_text = menu_font.render(theme.name, True, WHITE)
                    name_rect = name_text.get_rect(center=(preview_rect.centerx, preview_rect.top + 30))
                    screen.blit(name_text, name_rect)
                    
                    # Draw snake preview
                    snake_segments = [(
                        preview_rect.centerx + (i-5) * 15, 
                        preview_rect.centery
                    ) for i in range(10)]
                    
                    for j, pos in enumerate(snake_segments):
                        color = theme.get_segment_color(j)
                        pygame.draw.rect(screen, color, 
                                       (pos[0]-7, pos[1]-7, 15, 15))
                                       
                    # Add select button if not selected
                    if key != current_snake:
                        select_button = pygame.Rect(
                            preview_rect.centerx - 60, 
                            preview_rect.bottom - 40, 
                            120, 30
                        )
                        draw_button(screen, select_button, "Select", footer_font, 
                                  (60, 120, 60), (80, 180, 80), mouse_pos)
                        
                        # Handle click on select button - improved responsiveness
                        if mouse_pressed and not prev_mouse_pressed and select_button.collidepoint(mouse_pos):
                            if click_sound: click_sound.play()
                            customization.set_snake_theme(key)
                            # Also update the snake_color for compatibility
                            snake_color = theme.head_color

        elif current_page == 2:
            # Food themes page
            current_food = customization.current_food_theme
            
            # Calculate how many theme previews we need to show
            preview_rows = (len(food_themes) + preview_cols - 1) // preview_cols
            content_height = preview_rows * (preview_size + preview_margin) - preview_margin
            max_scroll_y = max(0, content_height - content_area.height)
            
            # Adjust scroll with mouse wheel
            if mouse_wheel_up:
                scroll_y = max(0, scroll_y - 30)
            elif mouse_wheel_down:
                scroll_y = min(max_scroll_y, scroll_y + 30)
            
            # Draw food theme previews
            y_pos = 220 - scroll_y
            x_pos = (SCREEN_WIDTH - preview_width) // 2
            
            for i, (key, theme) in enumerate(food_themes.items()):
                row = i // preview_cols
                col = i % preview_cols
                
                theme_x = x_pos + col * (preview_size + preview_margin)
                theme_y = y_pos + row * (preview_size + preview_margin)
                
                # Only draw if visible in the content area
                if (theme_y < content_area.bottom and 
                    theme_y + preview_size > content_area.top):
                    
                    # Create preview rect
                    preview_rect = pygame.Rect(theme_x, theme_y, preview_size, preview_size)
                    
                    # Draw theme preview
                    pygame.draw.rect(screen, (30, 30, 60), preview_rect, border_radius=10)
                    
                    # Draw selection indicator if this is the current theme
                    if key == current_food:
                        pygame.draw.rect(screen, (80, 200, 120), preview_rect, 4, border_radius=10)
                    elif preview_rect.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, (150, 150, 180), preview_rect, 2, border_radius=10)
                    
                    # Draw theme name
                    name_text = menu_font.render(theme.name, True, WHITE)
                    name_rect = name_text.get_rect(center=(preview_rect.centerx, preview_rect.top + 30))
                    screen.blit(name_text, name_rect)
                    
                    # Draw food preview
                    food_color = theme.get_food_color(step)
                    food_radius = 25
                    pygame.draw.circle(screen, food_color, 
                                     (preview_rect.centerx, preview_rect.centery), food_radius)
                    
                    # If it's a random color theme, draw some samples
                    if theme.random_colors:
                        for j, color in enumerate(theme.color_options[:5]):
                            small_radius = 10
                            x_offset = (j - 2) * 25
                            pygame.draw.circle(screen, color,
                                            (preview_rect.centerx + x_offset, 
                                             preview_rect.centery + 50), small_radius)
                                             
                    # Add select button if not selected
                    if key != current_food:
                        select_button = pygame.Rect(
                            preview_rect.centerx - 60, 
                            preview_rect.bottom - 40, 
                            120, 30
                        )
                        draw_button(screen, select_button, "Select", footer_font, 
                                (60, 120, 60), (80, 180, 80), mouse_pos)
                        
                        # Handle click on select button - improved responsiveness
                        if mouse_pressed and not prev_mouse_pressed and select_button.collidepoint(mouse_pos):
                            if click_sound: click_sound.play()
                            customization.set_food_theme(key)
        
        # Back button
        draw_fancy_button(screen, back_button, "Back to Menu", menu_font, (100,100,100), (150,150,150), mouse_pos, step)
        
        pygame.display.update()
        step += 1
        clock.tick(30)

if __name__ == "__main__":
    home_page()
