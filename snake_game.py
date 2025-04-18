import pygame
import random
from enum import Enum
from collections import namedtuple
from customization import customization
from utils import draw_gradient  # Import the correct draw_gradient function
import os
import json

pygame.init()
pygame.mixer.init()

# Colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Game settings
BLOCK_SIZE = 20
SPEED = 30  # Standardized speed

# Directions
RIGHT = 1
LEFT = 2
UP = 3
DOWN = 4

Point = namedtuple('Point', 'x, y')

# Font settings
font_path = "statics/game_over.ttf"
font = pygame.font.Font(font_path, 60)

class SnakeGame:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.score = 0
        self.eat_sound = pygame.mixer.Sound('statics/eat-food.mp3')
        self.game_over_sound = pygame.mixer.Sound('statics/game-over.mp3')
        # Add level up sound
        try:
            self.level_up_sound = pygame.mixer.Sound('statics/level_up.mp3')
        except:
            print("Warning: Level up sound file not found")
            self.level_up_sound = None
        
        # Using customization for snake appearance
        self.snake_theme = customization.get_current_snake_theme()
        self.food_theme = customization.get_current_food_theme()
        
        # Keep for compatibility
        self.snake_color = self.snake_theme.head_color
        self.background_theme = "dark"  # Default background theme
        
        # Init display
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Game - Classic Mode')
        self.clock = pygame.time.Clock()
        self.frame_iteration = 0  # Track frame count for animations
        
        # Add standardized fonts with proper error handling
        try:
            self.main_font = pygame.font.Font("statics/game_over.ttf", 60)  # Main font for score display
            self.sub_font = pygame.font.Font("statics/game_over.ttf", 48)   # Smaller font for other displays
            self.small_font = pygame.font.Font("statics/game_over.ttf", 36) # Small font for debug info
        except FileNotFoundError:
            print("Warning: Main font file not found. Using system fonts.")
            self.main_font = pygame.font.SysFont("Arial", 60)
            self.sub_font = pygame.font.SysFont("Arial", 48)
            self.small_font = pygame.font.SysFont("Arial", 36)
        
        # Initialize snake position and direction
        self.direction = RIGHT
        self.head = Point(self.width // 2, self.height // 2)
        self.snake = [
            self.head,
            Point(self.head.x - BLOCK_SIZE, self.head.y),
            Point(self.head.x - (2 * BLOCK_SIZE), self.head.y)
        ]
        self.food = None
        self._place_food()

    def _place_food(self):
        x = random.randint(0, (self.width - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE 
        y = random.randint(0, (self.height - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()
        
    def play_step(self):
        self.frame_iteration += 1
        
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Press 'P' to pause
                    paused = True
                    
                    # Create semi-transparent overlay for better contrast
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120) if self.background_theme == "dark" else (255, 255, 255, 120))
                    self.display.blit(overlay, (0, 0))
                    
                    # Dynamic text color based on theme
                    pause_color = WHITE if self.background_theme == "dark" else (0, 0, 100)
                    
                    pause_text = self.sub_font.render('PAUSED - Press P to continue', True, pause_color)
                    self.display.blit(pause_text, (self.width//2 - pause_text.get_width()//2, self.height//2))
                    pygame.display.update()
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_p:
                                paused = False
                            elif pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_ESCAPE:
                                pygame.quit()
                                quit()
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                quit()
                        pygame.time.wait(100)
                elif event.key in (pygame.K_LEFT, pygame.K_a):  # Left arrow or 'A'
                    if self.direction != RIGHT:  # Prevent 180-degree turns
                        self.direction = LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):  # Right arrow or 'D'
                    if self.direction != LEFT:  # Prevent 180-degree turns
                        self.direction = RIGHT
                elif event.key in (pygame.K_UP, pygame.K_w):  # Up arrow or 'W'
                    if self.direction != DOWN:  # Prevent 180-degree turns
                        self.direction = UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):  # Down arrow or 'S'
                    if self.direction != UP:  # Prevent 180-degree turns
                        self.direction = DOWN
                elif event.key == pygame.K_ESCAPE:  # Escape key to quit
                    return True, self.score

        # Move the snake
        self._move(self.direction)
        self.snake.insert(0, self.head)

        # Check for collisions
        if self._is_collision():
            return True, self.score

        # Check if the snake eats food
        if self.head == self.food:
            self.eat_sound.play()
            self.score += 1
            self._place_food()  # This will generate a new random color if needed
            
            # Play level up sound every 10 points
            if self.score % 10 == 0 and self.score > 0:
                if hasattr(self, 'level_up_sound') and self.level_up_sound:
                    self.level_up_sound.play()
                    
                    # Create semi-transparent overlay for better visibility
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay_color = (0, 0, 0, 100) if self.background_theme == "dark" else (255, 255, 255, 100)
                    overlay.fill(overlay_color)
                    self.display.blit(overlay, (0, 0))
                    
                    # Level up message with dynamic color based on theme
                    level_color = YELLOW if self.background_theme == "dark" else (0, 100, 0)  # Yellow for dark mode, dark green for light mode
                    level_text = self.main_font.render(f"LEVEL UP!", True, level_color)
                    self.display.blit(level_text, 
                                    (self.width//2 - level_text.get_width()//2, 
                                    self.height//2 - level_text.get_height()//2))
                    pygame.display.update()
                    # Pause briefly so the player can see the level up message
                    pygame.time.delay(500)
        else:
            self.snake.pop()
            
            # Update food color if it's a rainbow theme
            # This is the key fix - update the food color even when not eating
            if self.food_theme.random_colors and self.frame_iteration % 60 == 0:
                self.food_theme.new_random_color()

        # Update UI and clock
        self._update_ui()
        self.clock.tick(SPEED)  # Use standardized frame rate
        return False, self.score
    
    def _is_collision(self):
        # Check if the snake hits itself
        if self.head in self.snake[1:]:
            self.game_over_sound.play()
            print(f"Game Over: Snake collision")
            return True
        return False
        
    def _update_ui(self):
        # Apply background based on theme
        if self.background_theme == "dark":
            draw_gradient(self.display, (0, 0, 50), (0, 0, 0), self.width, self.height)
            # Dark theme colors
            main_text_color = WHITE
            high_score_color = YELLOW
            controls_color = (180, 180, 180)  # Light gray
        else:
            draw_gradient(self.display, (200, 200, 200), (255, 255, 255), self.width, self.height)
            # Light theme colors
            main_text_color = (0, 0, 100)  # Dark blue
            high_score_color = (180, 100, 0)  # Dark orange
            controls_color = (80, 80, 80)  # Dark gray

        # Draw snake with custom theme
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                          (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Display score with consistent font and dynamic color
        score_text = self.main_font.render("Score: " + str(self.score), True, main_text_color)
        self.display.blit(score_text, [0, 0])
        
        # Try to load and display high score with dynamic color
        try:
            high_score_file = "statics/highscores.json"
            if os.path.exists(high_score_file):
                with open(high_score_file, 'r') as f:
                    high_scores = json.load(f)
                    classic_high = high_scores.get('classic', 0)
                    high_score_text = self.sub_font.render(f"High Score: {classic_high}", True, high_score_color)
                    self.display.blit(high_score_text, [self.width - high_score_text.get_width() - 10, 10])
        except:
            pass  # Skip if there's an issue loading the high score
        
        # Add controls help text at bottom left with dynamic color
        controls_text = self.small_font.render("ESC - Back to Menu | P - Pause | Arrow Keys/WASD - Move", True, controls_color)
        self.display.blit(controls_text, [10, self.height - 30])

        pygame.display.flip()
        
    def _move(self, direction):
        x = self.head.x
        y = self.head.y
        
        if direction == RIGHT:
            x += BLOCK_SIZE
        elif direction == LEFT:
            x -= BLOCK_SIZE
        elif direction == DOWN:
            y += BLOCK_SIZE
        elif direction == UP:
            y -= BLOCK_SIZE

        # Wrap around the borders
        x %= self.width
        y %= self.height

        self.head = Point(x, y)

    def set_theme(self, theme):
        """
        Updates the background theme.
        Args:
        theme: String indicating the theme ("dark" or "light").
        """
        self.background_theme = theme

if __name__ == '__main__':
    game = SnakeGame()
    
    # game loop
    while True:
        game_over, score = game.play_step()
        
        if game_over:
            break
        
    print('Final Score', game.score)
    pygame.quit()