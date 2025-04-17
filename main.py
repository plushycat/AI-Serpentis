import pygame
import torch
import sys
import math
import os
from model import Linear_QNet
from snake_game import SnakeGame
from snake_ai import SnakeGameAI
from agent import Agent

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Serpentis")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# Font loading with error handling
try:
    title_font = pygame.font.Font("statics/game_over.ttf", 96)
    menu_font = pygame.font.Font("statics/game_over.ttf", 48)
    footer_font = pygame.font.Font("statics/game_over.ttf", 36)
except FileNotFoundError:
    print("Warning: Font file not found. Using system fonts.")
    title_font = pygame.font.SysFont("Arial", 96)
    menu_font = pygame.font.SysFont("Arial", 48)
    footer_font = pygame.font.SysFont("Arial", 36)

# Load assets with error handling
try:
    click_sound = pygame.mixer.Sound("statics/eat-food.mp3")
    pygame.mixer.music.load("statics/bg_music.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
except FileNotFoundError:
    print("Warning: Sound file not found.")
    click_sound = None

# Load icons
try:
    music_on_icon = pygame.image.load("statics/music_on.png")
    music_off_icon = pygame.image.load("statics/music_off.png")
    # Scale icons to fit
    music_on_icon = pygame.transform.scale(music_on_icon, (40, 40))
    music_off_icon = pygame.transform.scale(music_off_icon, (40, 40))
except FileNotFoundError:
    print("Warning: Icon files not found.")
    # Create placeholder icons
    music_on_icon = pygame.Surface((40, 40))
    music_on_icon.fill(GREEN)
    music_off_icon = pygame.Surface((40, 40))
    music_off_icon.fill(RED)

# State variables
music_on = True
game_speed = 30  # Standardized speed
snake_color = (100, 200, 100)  # Default snake color
background_theme = "dark"  # Default background theme

# Dark gradient palettes
dark_gradients = [
    ((0, 0, 40), (10, 10, 70)),    # midnight blue → deep indigo
    ((5, 10, 50), (30, 0, 100)),   # navy → purple
    ((15, 0, 60), (40, 5, 90)),    # dark violet → dusk
    ((0, 20, 80), (25, 25, 60)),   # dark teal → muted blue
]
current_gradient = 0
next_gradient = 1
gradient_blend = 0.0

# Draw a smooth, slowly blending dark gradient background
def draw_smooth_gradient():
    c1 = dark_gradients[current_gradient][0]
    c2 = dark_gradients[current_gradient][1]
    d1 = dark_gradients[next_gradient][0]
    d2 = dark_gradients[next_gradient][1]

    start = tuple(int((1 - gradient_blend) * c1[i] + gradient_blend * d1[i]) for i in range(3))
    end = tuple(int((1 - gradient_blend) * c2[i] + gradient_blend * d2[i]) for i in range(3))

    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(start[0] * (1 - t) + end[0] * t)
        g = int(start[1] * (1 - t) + end[1] * t)
        b = int(start[2] * (1 - t) + end[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

# Glowing animated title text function as provided in your code snippet
def glowing_text(screen, text, font, x, y, base_color, step):
    glow = abs(math.sin(step / 20)) * 180
    color = (
        min(255, base_color[0] + glow),
        min(255, base_color[1] + glow),
        min(255, base_color[2] + glow),
    )
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

# Modern button with hover/glow effect
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

# Draw a slider for speed control
def draw_slider(screen, x, y, width, min_val, max_val, current_val):
    pygame.draw.line(screen, GRAY, (x, y), (x + width, y), 5)  # Slider track
    slider_pos = x + int((current_val - min_val) / (max_val - min_val) * width)
    pygame.draw.circle(screen, WHITE, (slider_pos, y), 10)  # Slider knob
    return slider_pos

def home_page():
    global music_on, screen, current_gradient, next_gradient, gradient_blend
    clock = pygame.time.Clock()
    
    # Ensure Pygame display is initialized
    if not pygame.get_init() or pygame.display.get_surface() is None:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Serpentis")

    # Center-aligned buttons
    button_width = 300
    button_height = 60
    button_spacing = 80
    
    # Calculate starting Y position to center buttons vertically
    total_buttons_height = 4 * button_height + 3 * (button_spacing - button_height)
    start_y = (SCREEN_HEIGHT - total_buttons_height) // 2

    buttons = {
        "Play Classic": pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y, button_width, button_height),
        "Watch AI": pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + button_spacing, button_width, button_height),
        "Settings": pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + 2 * button_spacing, button_width, button_height),
        "Quit": pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + 3 * button_spacing, button_width, button_height),
    }
    
    music_rect = pygame.Rect(SCREEN_WIDTH - 60, 20, 40, 40)
    
    step = 0  # Animation step

    while True:
        try:
            mouse_pos = pygame.mouse.get_pos()
            
            # Draw background
            draw_smooth_gradient()
            
            # Draw title with glowing effect - centered horizontally
            title_text = "AI Serpentis"
            title_surface = title_font.render(title_text, True, YELLOW)  # Temporary surface to get width
            title_width = title_surface.get_width()
            title_x = (SCREEN_WIDTH - title_width) // 2
            glowing_text(screen, title_text, title_font, title_x, 80, YELLOW, step)
            
            # Draw buttons
            button_colors = {
                "Play Classic": ((0, 150, 0), GREEN),  # Base, hover
                "Watch AI": ((0, 0, 150), BLUE),
                "Settings": ((150, 150, 0), YELLOW),
                "Quit": ((150, 0, 0), RED)
            }
            
            for name, rect in buttons.items():
                draw_button(screen, rect, name, menu_font, 
                            button_colors[name][0], button_colors[name][1], mouse_pos)
            
            # Music toggle icon
            screen.blit(music_on_icon if music_on else music_off_icon, music_rect.topleft)
            
            # Footer - centered
            footer_surf = footer_font.render("The Snake Game Reimagined v2.0", True, (200, 200, 200))
            footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
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
                        if click_sound:
                            click_sound.play()
                        play_classic_game()
                    elif buttons["Watch AI"].collidepoint(pos):
                        if click_sound:
                            click_sound.play()
                        watch_ai_play()
                    elif buttons["Settings"].collidepoint(pos):
                        if click_sound:
                            click_sound.play()
                        settings_page()
                    elif buttons["Quit"].collidepoint(pos):
                        if click_sound:
                            click_sound.play()
                        pygame.quit()
                        sys.exit()
                    elif music_rect.collidepoint(pos):
                        music_on = not music_on
                        try:
                            if music_on:
                                pygame.mixer.music.play(-1)
                            else:
                                pygame.mixer.music.stop()
                        except:
                            pass
            
            # Advance gradient blend very slowly
            gradient_blend += 0.0001
            if gradient_blend >= 1.0:
                gradient_blend = 0.0
                current_gradient = next_gradient
                next_gradient = (next_gradient + 1) % len(dark_gradients)
            
            step += 1
            clock.tick(30)
        except pygame.error as e:
            print(f"Error in home_page: {e}")
            # Reinitialize pygame
            pygame.quit()
            pygame.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

def play_classic_game():
    global snake_color, background_theme, screen
    
    # Initialize the game with settings
    game = SnakeGame()
    game.snake_color = snake_color
    game.background_theme = background_theme
    
    while True:
        try:
            over, score = game.play_step()
            if over:
                print(f"Game Over! Your Score: {score}")
                break
        except pygame.error as e:
            print(f"Error in play_classic_game: {e}")
            break
    
    # Reinitialize the screen for the main menu
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Serpentis")
    except pygame.error as e:
        print(f"Error reinitializing screen: {e}")
        pygame.quit()
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

def watch_ai_play():
    """Launches the AI-controlled Snake game using the pre-trained model."""
    global snake_color, background_theme, screen
    
    # Load the trained model
    model = Linear_QNet(11, 256, 3)
    try:
        # Try to load model from primary location
        model_path = "model/model.pth"
        if not os.path.exists(model_path):
            model_path = "model_snapshots/model.pth"  # Fallback location
            
        model.load_state_dict(torch.load(model_path))
        model.eval()
    except FileNotFoundError:
        print("Error: Pre-trained model file not found.")
        return
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Initialize the AI game
    try:
        game = SnakeGameAI(width=1280, height=720)
        game.snake_color = snake_color  # Apply selected color
        game.background_theme = background_theme  # Apply selected theme
        
        agent = Agent()
        agent.model = model
        agent.epsilon = 0  # Disable exploration for watching
        
        while True:
            state = agent.get_state(game)
            move = agent.get_action(state)
            _, done, score = game.play_step(move)
            if done:
                print(f"AI Game Over! Final Score: {score}")
                break
    except pygame.error as e:
        print(f"Error in watch_ai_play: {e}")
    except Exception as e:
        print(f"Unexpected error in watch_ai_play: {e}")
    
    # Reinitialize the screen for the main menu
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Serpentis")
    except pygame.error as e:
        print(f"Error reinitializing screen: {e}")
        pygame.quit()
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

def settings_page():
    global snake_color, background_theme, screen, game_speed
    clock = pygame.time.Clock()
    step = 0
    
    # Center-aligned UI elements
    button_width = 300
    button_height = 60
    button_spacing = 80
    
    # Color options
    options = [
        ("Green", (100, 200, 100)),
        ("Blue", (100, 100, 200)),
        ("Red", (200, 100, 100))
    ]
    
    # Option buttons - centered
    color_buttons = [
        pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 200 + i * button_spacing, button_width, button_height)
        for i in range(len(options))
    ]
    
    # Theme buttons - centered
    dark_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 450, button_width, button_height)
    light_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 530, button_width, button_height)
    
    # Speed slider settings - centered
    slider_x = SCREEN_WIDTH//2 - button_width//2
    slider_width = button_width
    min_speed = 10
    max_speed = 60
    dragging_slider = False
    
    # Back button - centered at bottom
    back_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 700, button_width, button_height)
    
    while True:
        try:
            mouse_pos = pygame.mouse.get_pos()
            
            # Draw background
            draw_smooth_gradient()
            
            # Title - centered
            title_text = "Settings"
            title_surface = title_font.render(title_text, True, YELLOW)
            title_width = title_surface.get_width()
            title_x = (SCREEN_WIDTH - title_width) // 2
            glowing_text(screen, title_text, title_font, title_x, 80, YELLOW, step)
            
            # Color buttons
            for i, ((name, color), rect) in enumerate(zip(options, color_buttons)):
                is_selected = snake_color == color
                button_color = tuple(min(255, c + 50) for c in color) if is_selected else color
                hover_color = tuple(min(255, c + 80) for c in color)
                
                draw_button(screen, rect, f"Snake: {name}", menu_font, 
                           button_color, hover_color, mouse_pos)
            
            # Theme buttons
            is_dark = background_theme == "dark"
            draw_button(screen, dark_button, "Theme: Dark", menu_font,
                       (50, 50, 80) if is_dark else (30, 30, 50),
                       (80, 80, 120), mouse_pos)
            
            draw_button(screen, light_button, "Theme: Light", menu_font,
                       (200, 200, 220) if not is_dark else (150, 150, 170),
                       (230, 230, 250), mouse_pos)
            
            # Speed slider
            speed_text = menu_font.render(f"Game Speed: {game_speed}", True, WHITE)
            speed_text_rect = speed_text.get_rect(center=(SCREEN_WIDTH//2, 600))
            screen.blit(speed_text, speed_text_rect)
            
            slider_pos = draw_slider(screen, slider_x, 650, slider_width, min_speed, max_speed, game_speed)
            
            # Back button
            draw_button(screen, back_button, "Back to Menu", menu_font, (100, 100, 100), (150, 150, 150), mouse_pos)
            
            pygame.display.update()
            
            # Event handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if e.type == pygame.MOUSEBUTTONDOWN:
                    pos = e.pos
                    # Handle color selection
                    for i, ((name, color), rect) in enumerate(zip(options, color_buttons)):
                        if rect.collidepoint(pos):
                            snake_color = color
                            if click_sound:
                                click_sound.play()
                    
                    # Handle theme selection
                    if dark_button.collidepoint(pos):
                        background_theme = "dark"
                        if click_sound:
                            click_sound.play()
                    elif light_button.collidepoint(pos):
                        background_theme = "light"
                        if click_sound:
                            click_sound.play()
                    
                    # Handle slider
                    if abs(pos[0] - slider_pos) < 20 and abs(pos[1] - 650) < 20:
                        dragging_slider = True
                    
                    # Back button
                    if back_button.collidepoint(pos):
                        if click_sound:
                            click_sound.play()
                        return
                
                if e.type == pygame.MOUSEMOTION and dragging_slider:
                    # Update slider position and game_speed
                    pos_ratio = max(0, min(1, (e.pos[0] - slider_x) / slider_width))
                    game_speed = int(min_speed + pos_ratio * (max_speed - min_speed))
                
                if e.type == pygame.MOUSEBUTTONUP:
                    dragging_slider = False
                
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    return
            
            step += 1
            clock.tick(30)
        except pygame.error as e:
            print(f"Error in settings_page: {e}")
            return

if __name__ == "__main__":
    running = True
    while running:
        try:
            # Ensure Pygame is initialized
            pygame.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("AI Serpentis")
            
            home_page()
            running = False  # Exit the loop normally
        except pygame.error as e:
            print(f"Pygame error: {e}")
            pygame.quit()
            pygame.init()
        except Exception as e:
            print(f"Unexpected error: {e}")
            running = False
    
    pygame.quit()
