import pygame
import torch
import sys
import math
from model import Linear_QNet
from snake_game import SnakeGame
from watch_ai import watch_ai_play as watch_ai_play_external
from utils import draw_gradient
from snake_ai import SnakeGameAI
from agent import Agent
# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game Menu")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# Fonts
title_font = pygame.font.Font("statics/game_over.ttf", 72)
menu_font = pygame.font.Font("statics/game_over.ttf", 36)
footer_font = pygame.font.SysFont("statics/game_over.ttf", 18)

# Load icons and sounds
click_sound = pygame.mixer.Sound("statics/eat-food.mp3")
pygame.mixer.music.load("statics/bg_music.mp3")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

# Load icons and scale them to fit the screen size
music_on_icon = pygame.image.load("statics/music_on.png")
music_off_icon = pygame.image.load("statics/music_off.png")

# Scale icons to 40x40 pixels (or adjust based on your needs)
ICON_SIZE = int(SCREEN_WIDTH * 0.05)  # 5% of the screen width
music_on_icon = pygame.transform.scale(music_on_icon, (ICON_SIZE, ICON_SIZE))
music_off_icon = pygame.transform.scale(music_off_icon, (ICON_SIZE, ICON_SIZE))

music_on = True  # Music state toggle

# Global speed variable
game_speed = 40  # Default speed for both player and AI

snake_color = GREEN  # Default snake color
background_theme = "dark"  # Default background theme

# Draw a gradient background
def draw_gradient(display, color1, color2, width, height):
    """
    Draws a vertical gradient on the display.

    Args:
    display: Pygame display object.
    color1: Starting color of the gradient (RGB tuple).
    color2: Ending color of the gradient (RGB tuple).
    width: Width of the gradient area.
    height: Height of the gradient area.
    """
    for i in range(height):
        r = color1[0] + (color2[0] - color1[0]) * i // height
        g = color1[1] + (color2[1] - color1[1]) * i // height
        b = color1[2] + (color2[2] - color1[2]) * i // height
        pygame.draw.line(display, (r, g, b), (0, i), (width, i))

# Corrected call to draw_gradient
draw_gradient(screen, (0, 0, 50), (0, 0, 0), SCREEN_WIDTH, SCREEN_HEIGHT)

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
    global music_on, screen  # Declare global variables
    clock = pygame.time.Clock()

    # Ensure Pygame display is initialized
    if not pygame.get_init() or pygame.display.get_surface() is None:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake Game Menu")

    # Buttons
    play_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 200, 300, 50)
    ai_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 300, 300, 50)
    quit_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 400, 300, 50)
    settings_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 500, 300, 50)
    music_rect = pygame.Rect(SCREEN_WIDTH - ICON_SIZE - 20, 20, ICON_SIZE, ICON_SIZE)  # Adjusted for scaled icons

    step = 0  # Animation step

    while True:
        # Ensure display is still initialized
        if not pygame.get_init() or pygame.display.get_surface() is None:
            pygame.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Snake Game Menu")
            
        mouse_pos = pygame.mouse.get_pos()
        draw_gradient(screen, (0, 0, 50), (50, 0, 100), SCREEN_WIDTH, SCREEN_HEIGHT)

        glowing_text(screen, "AI Serpentis", title_font, SCREEN_WIDTH // 2 - 300, 100, YELLOW, step)

        # Buttons
        hover_play = draw_button(screen, play_button, "Play Classic Snake Game", menu_font, (0, 150, 0), GREEN, mouse_pos)
        hover_ai = draw_button(screen, ai_button, "Watch AI Play Snake Game", menu_font, (0, 0, 150), BLUE, mouse_pos)
        hover_quit = draw_button(screen, quit_button, "Quit", menu_font, (150, 0, 0), RED, mouse_pos)
        hover_settings = draw_button(screen, settings_button, "Settings", menu_font, (150, 150, 0), YELLOW, mouse_pos)

        # Music toggle icon
        screen.blit(music_on_icon if music_on else music_off_icon, music_rect.topleft)

        # Footer
        footer = footer_font.render("The Snake Game Reimagined v2.0", True, WHITE)
        screen.blit(footer, (10, SCREEN_HEIGHT - 30))

        pygame.display.update()  # Refresh the display

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    click_sound.play()
                    play_classic_game()
                elif ai_button.collidepoint(event.pos):
                    click_sound.play()
                    watch_ai_play()  # Call our local function
                elif quit_button.collidepoint(event.pos):
                    click_sound.play()
                    pygame.quit()
                    sys.exit()
                elif settings_button.collidepoint(event.pos):
                    click_sound.play()
                    settings_page()
                elif music_rect.collidepoint(event.pos):
                    music_on = not music_on  # Toggle music state
                    if music_on:
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.stop()

        step += 1
        clock.tick(30)

def play_classic_game():
    global game_speed, snake_color, background_theme, screen
    game = SnakeGame()
    game.snake_color = snake_color
    game.background_theme = background_theme
    
    while True:
        game_over, score = game.play_step()
        if game_over:
            print(f"Game Over! Your Score: {score}")
            break
    
    # Reinitialize the screen for the main menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake Game Menu")

def watch_ai_play():
    """Launches the AI-controlled Snake game using the pre-trained model."""
    global screen
    
    # Load the trained model
    model = Linear_QNet(11, 256, 3)
    try:
        model.load_state_dict(torch.load("model/model.pth"))
    except FileNotFoundError:
        print("Error: Pre-trained model file not found.")
        return
    model.eval()

    # Initialize the AI game
    game = SnakeGameAI(width=1280, height=720)  # Set the resolution explicitly to 1280x720
    game.background_theme = background_theme  # Use selected background theme
    agent = Agent()
    agent.model = model  # Use the loaded model

    while True:
        # Get the current state of the game
        state_old = agent.get_state(game)

        # Use the model to decide the next move
        final_move = agent.get_action(state_old)

        # Perform the action and observe the result
        reward, done, score = game.play_step(final_move)

        # If the game is over, print the score and exit the loop
        if done:
            print(f"AI Game Over! Final Score: {score}")
            break

    # Reinitialize the screen for the main menu
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake Game Menu")

def settings_page():
    global snake_color, background_theme, screen
    clock = pygame.time.Clock()

    # Buttons for snake color
    green_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150, 300, 50)
    blue_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 230, 300, 50)
    red_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 310, 300, 50)

    # Buttons for background theme
    dark_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 390, 300, 50)
    light_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 470, 300, 50)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BLACK)

        glowing_text(screen, "Settings", title_font, SCREEN_WIDTH // 2 - 150, 50, YELLOW, 0)

        # Draw buttons
        draw_button(screen, green_button, "Snake Color: Green", menu_font, (0, 150, 0), GREEN, mouse_pos)
        draw_button(screen, blue_button, "Snake Color: Blue", menu_font, (0, 0, 150), BLUE, mouse_pos)
        draw_button(screen, red_button, "Snake Color: Red", menu_font, (150, 0, 0), RED, mouse_pos)
        draw_button(screen, dark_button, "Background: Dark", menu_font, (50, 50, 50), GRAY, mouse_pos)
        draw_button(screen, light_button, "Background: Light", menu_font, (200, 200, 200), WHITE, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if green_button.collidepoint(event.pos):
                    snake_color = GREEN
                elif blue_button.collidepoint(event.pos):
                    snake_color = BLUE
                elif red_button.collidepoint(event.pos):
                    snake_color = RED
                elif dark_button.collidepoint(event.pos):
                    background_theme = "dark"
                elif light_button.collidepoint(event.pos):
                    background_theme = "light"
                return  # Return to the main menu

        clock.tick(30)

if __name__ == "__main__":
    running = True
    while running:
        try:
            # Ensure Pygame is initialized
            pygame.init()
            # Set up the display
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Snake Game Menu")

            # Call the home page
            home_page()
            running = False  # Exit if home_page completes normally
        except pygame.error as e:
            print(f"Pygame error: {e}")
            # Reinitialize Pygame
            pygame.quit()
            pygame.init()
        except Exception as e:
            print(f"Unexpected error: {e}")
            running = False
    
    pygame.quit()
