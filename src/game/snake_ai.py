import pygame, random, os
from enum import Enum
from collections import namedtuple
import numpy as np
from utils import draw_gradient
from src.game.customization import customization

pygame.init()
pygame.mixer.init()

# Define color constants
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)  # Add this line to define the missing YELLOW constant

# Define block size and game speed
BLOCK_SIZE = 20
SPEED = 30  # Standardized speed

# Direction constants
RIGHT = 1
LEFT = 2
UP = 3
DOWN = 4

# Point data structure to store x, y coordinates
Point = namedtuple('Point', 'x, y')

# Load font for displaying text
font_path = "assets/fonts/game_over.ttf"
font = pygame.font.Font(font_path, 60)

class SnakeGameAI:
    """
    A class to represent the Snake Game with AI integration.
    Handles game logic, rendering, and user interactions.
    """

    def __init__(self, width=640, height=480, record=0, avg=0, iteration=0, display_surface=None):
        """
        Initializes the game with specified dimensions and statistics.

        Args:
        width: Width of the game window.
        height: Height of the game window.
        record: Highest score achieved.
        avg: Average score.
        iteration: Current training iteration.
        """
        self.width = width
        self.height = height
        self.record = record
        self.avg = avg
        self.iteration = iteration
        self.eat_sound = pygame.mixer.Sound('assets/sounds/eat-food.mp3')
        self.game_over_sound = pygame.mixer.Sound('assets/sounds/game-over.mp3')
        # Add level up sound
        try:
            self.level_up_sound = pygame.mixer.Sound('assets/sounds/level_up.mp3')
        except:
            print("Warning: Level up sound file not found")
            self.level_up_sound = None
        
        # Using customization for snake appearance
        self.snake_theme = customization.get_current_snake_theme()
        self.food_theme = customization.get_current_food_theme()
        
        # Keep for compatibility
        self.snake_color = self.snake_theme.head_color
        self.background_theme = "dark"  # Default background theme
        
        self.frame_limit_multiplier = 500  # Increased frame limit - customizable parameter
        self.recent_positions = []  # Track recent positions to detect loops
        self.loop_detection_length = 20  # How many recent positions to check for loops
        self.debug_mode = False  # Add debug mode flag
        self.viewing_mode = False  # Add a new flag to indicate if we're in viewing mode (spectating AI)
        self.enhanced_effects = True  # Default to enhanced effects
        
        # Use the width and height parameters to set up the display
        if display_surface is None:
            self.display = pygame.display.set_mode((width, height))
        else:
            self.display = display_surface
        pygame.display.set_caption('Snake Game - AI Mode')
        self.clock = pygame.time.Clock()
        
        # Add standardized fonts with proper error handling
        try:
            self.main_font = pygame.font.Font("assets/fonts/game_over.ttf", 60)  # Main font for score display
            self.sub_font = pygame.font.Font("assets/fonts/game_over.ttf", 48)   # Smaller font for other displays
            self.small_font = pygame.font.Font("assets/fonts/game_over.ttf", 36) # Small font for debug info
        except FileNotFoundError:
            print("Warning: Main font file not found. Using system fonts.")
            self.main_font = pygame.font.SysFont("Arial", 60)
            self.sub_font = pygame.font.SysFont("Arial", 48)
            self.small_font = pygame.font.SysFont("Arial", 36)

        self.reset()

    def reset(self):
        """
        Resets the game state for a new game or iteration.
        """
        self.direction = RIGHT
        self.head = Point(self.width/2, self.height/2)  # Start snake at center
        self.snake = [self.head]  # Initialize the snake
        self.score = 0
        self.food = None
        self._place_food()
        self.frame_iteration = 0  # Track frames for performance

    def _place_food(self):
        """
        Places food at a random location on the grid.
        Ensures the food does not spawn on the snake.
        """
        x = random.randint(0, (self.width-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.height-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        
        # Generate a new random food color if that feature is enabled
        if self.food_theme.random_colors:
            self.food_theme.new_random_color()
            
        if self.food in self.snake:  # Prevent food spawning on the snake
            self._place_food()

    def play_step(self, action):
        """
        Executes a single step of the game.

        Args:
        action: The action taken by the AI (array: [straight, right turn, left turn]).

        Returns:
        reward: Reward for the current action.
        game_over: Boolean indicating if the game is over.
        score: Current score.
        """
        self.frame_iteration += 1
        
        # Consolidated event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
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
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                quit()

        # Move the snake
        self._move(action) 
        self.snake.insert(0, self.head)  # Update the snake's position
        
        # Keep track of recent head positions for loop detection
        self.recent_positions.append((self.head.x, self.head.y))
        if len(self.recent_positions) > self.loop_detection_length:
            self.recent_positions.pop(0)
        
        reward = 0
        game_over = False

        # Check for collisions - adding debug information
        if self.is_collision():
            game_over = True
            reward = -10
            self.game_over_sound.play()
            print(f"AI Game Over: Collision detected")
            return reward, game_over, self.score
        
        # Check for timeout - using customizable frame limit multiplier
        # Only applies this strict timeout if the snake is not growing
        # when it has score > 10 (established snake)
        if self.score > 10 and self.frame_iteration > self.frame_limit_multiplier * len(self.snake):
            game_over = True
            reward = -10
            print(f"AI Game Over: Frame limit exceeded ({self.frame_iteration} > {self.frame_limit_multiplier * len(self.snake)})")
            return reward, game_over, self.score

        # Check if the snake eats food
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
            self.eat_sound.play()
            
            # Play level up sound every 10 points
            if self.score % 10 == 0 and self.score > 0 and reward > 0:
                if hasattr(self, 'level_up_sound') and self.level_up_sound:
                    self.level_up_sound.play()
                    # Also show a level up message if in viewing mode
                    if self.viewing_mode:
                        self._show_level_up()
            
            # Reset frame iteration when food is eaten to prevent timeout
            self.frame_iteration = 0
        else:
            self.snake.pop()
            
            # Calculate distance-based reward to guide the AI toward food
            # Only calculate if we have at least 2 positions in the history
            if len(self.recent_positions) >= 2:
                prev_distance = abs(self.recent_positions[-2][0] - self.food.x) + abs(self.recent_positions[-2][1] - self.food.y)
                curr_distance = abs(self.head.x - self.food.x) + abs(self.head.y - self.food.y)
                
                # Reward moving closer to food, penalize moving away
                if curr_distance < prev_distance:
                    reward = 0.1  # Small positive reward for moving closer to food
                else:
                    reward = -0.1  # Small negative reward for moving away from food

        # Update the display
        self._update_ui()
        self.clock.tick(SPEED)
        return reward, game_over, self.score

    def is_collision(self, pt=None):
        """
        Checks if the snake collides with itself.

        Args:
        pt: The point to check for collision (default: snake head).

        Returns:
        Boolean indicating if a collision occurred.
        """
        if pt is None:
            pt = self.head
        if pt in self.snake[1:]:  # Collision with the snake's body
            self.game_over_sound.play()
            return True

        return False

    def _update_ui(self):
        """
        Updates the game display with the current state.
        """
        # Select background and text colors based on theme
        if self.background_theme == "dark":
            draw_gradient(self.display, (0, 0, 50), (0, 0, 0), self.width, self.height)
            # Dark theme colors
            main_text_color = WHITE
            high_score_color = YELLOW
            controls_color = (180, 180, 180)  # Light gray
            secondary_text_color = (200, 200, 200)  # Light gray for secondary text
        else:
            draw_gradient(self.display, (200, 200, 200), (255, 255, 255), self.width, self.height)
            # Light theme colors
            main_text_color = (20, 20, 100)  # Dark blue
            high_score_color = (180, 100, 0)  # Dark orange
            controls_color = (80, 80, 80)  # Dark gray
            secondary_text_color = (100, 100, 100)  # Medium gray for secondary text

        # Draw the snake with custom theme
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw the food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                          (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Different UI for viewer mode vs training mode
        if self.viewing_mode:
            # Simpler UI for viewers - just show Score and Record
            score_text = self.main_font.render(f"AI Score: {self.score}", True, main_text_color)
            record_text = self.main_font.render(f"Record: {self.record}", True, main_text_color)
            
            # Center the score at the top
            score_rect = score_text.get_rect(center=(self.width//2, 30))
            self.display.blit(score_text, score_rect)
            
            # Show record in the top right
            self.display.blit(record_text, [self.width - record_text.get_width() - 10, 10])
            
            # Add controls help text
            controls_text = self.small_font.render("ESC - Back to Menu | P - Pause", True, controls_color)
            self.display.blit(controls_text, [10, self.height - 30])
        else:
            # Full UI for training mode
            score_text = self.main_font.render("Score: " + str(self.score), True, main_text_color)
            self.display.blit(score_text, [0, 0])

            record_text = self.main_font.render(f"Record: {self.record}", True, main_text_color)
            self.display.blit(record_text, [self.width - record_text.get_width(), 0])

            avg_text = self.sub_font.render(f"Average: {self.avg}", True, main_text_color)
            self.display.blit(avg_text, [0, 70])  # Adjusted position to accommodate larger font

            iter_text = self.sub_font.render(f"Iteration: {self.iteration}", True, main_text_color)
            self.display.blit(iter_text, [self.width - iter_text.get_width(), 70])  # Adjusted position

        # If debug mode is on, show additional information
        if self.debug_mode:
            # Show frame count and frame limit
            frame_limit = self.frame_limit_multiplier * len(self.snake)
            debug_text = self.small_font.render(f"Frames: {self.frame_iteration}/{frame_limit}", True, WHITE)
            self.display.blit(debug_text, [0, 120])  # Positioned below other UI elements
            
            # Mark the target food with a flashing indicator
            if self.frame_iteration % 30 < 15:  # Flashing effect
                pygame.draw.circle(self.display, (255, 255, 0), 
                                  (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 20, 2)

        pygame.display.flip()

    def _move(self, action):
        """
        Moves the snake based on the given action.

        Args:
        action: The action taken by the AI (array: [straight, right turn, left turn]).
        """
        clock_wise = [RIGHT, DOWN, LEFT, UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):  # No change in direction
            new_dir = clock_wise[idx]
        elif np.array_equal(action, [0, 1, 0]):  # Turn right
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]
        else:  # Turn left ([0, 0, 1])
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]

        self.direction = new_dir

        # Update the head's position
        x = self.head.x
        y = self.head.y

        if self.direction == RIGHT:
            x += BLOCK_SIZE
        elif self.direction == LEFT:
            x -= BLOCK_SIZE
        elif self.direction == DOWN:
            y += BLOCK_SIZE
        elif self.direction == UP:
            y -= BLOCK_SIZE

        # Handle wrapping around the screen
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

    def _show_level_up(self):
        """Show an enhanced level up animation with colored translucent overlay"""
        # Create semi-transparent overlay for better visibility
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if self.enhanced_effects:
            # Enhanced effects with colored overlay (like in player_vs_ai)
            if self.background_theme == "dark":
                overlay_color = (255, 255, 0, 80)  # Yellow semi-transparent for dark mode
                text_color = (255, 255, 0)  # Bright yellow
            else:
                overlay_color = (0, 100, 0, 80)  # Green semi-transparent for light mode
                text_color = (0, 120, 0)  # Dark green
        else:
            # Simple overlay (original style)
            overlay_color = (0, 0, 0, 100) if self.background_theme == "dark" else (255, 255, 255, 100)
            text_color = (255, 255, 0) if self.background_theme == "dark" else (0, 100, 0)
            
        overlay.fill(overlay_color)
        self.display.blit(overlay, (0, 0))
        
        # Level up message
        level_text = self.main_font.render(f"LEVEL UP!", True, text_color)
        self.display.blit(level_text, 
                        (self.width//2 - level_text.get_width()//2, 
                         self.height//2 - level_text.get_height()//2))
        
        pygame.display.update()
        # Pause briefly so the player can see the level up message
        pygame.time.delay(500)