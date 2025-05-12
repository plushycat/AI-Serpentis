import pygame
import random
from enum import Enum
from collections import namedtuple
from src.game.customization import customization
from utils import draw_gradient 
import os
import json
from src.utils.sound_manager import play_sound
from src.utils.config import load_config

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

# Directions as integer constants (for backward compatibility)
RIGHT = 1
LEFT = 2
UP = 3
DOWN = 4

# Also define Direction as an Enum for cleaner code
class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Point = namedtuple('Point', 'x, y')

# Font settings
font_path = "assets/fonts/game_over.ttf"
font = pygame.font.Font(font_path, 60)

class SnakeGame:
    def __init__(self, width=1280, height=720, display_surface=None, speed=None):
        # Add this at the beginning of __init__ method
        from src.utils.sound_manager import sound_manager
        sound_manager.refresh_settings()
        
        self.width = width
        self.height = height
        
        # Use provided display surface or create a new one
        if display_surface is None:
            self.display = pygame.display.set_mode((width, height))
        else:
            self.display = display_surface

        # Use provided speed or default
        self.speed = speed if speed is not None else SPEED
        
        self.score = 0
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
        
        # Load theme from config
        config = load_config()
        self.background_theme = config.get("appearance", {}).get("background_theme", "dark")
        
        # Init display
        pygame.display.set_caption('AI Serpentis - Classic Mode')
        self.clock = pygame.time.Clock()
        self.frame_iteration = 0  # Track frame count for animations
        
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

        # Add a toggle for enhanced level-up effects
        self.enhanced_effects = True  # Default to enhanced effects

        # Add to your existing initialization
        self.direction_buffer = None
        self.last_direction_change = 0
        self.min_direction_change_interval = 50  # milliseconds

    def _place_food(self):
        """
        Places food at a random location on the grid.
        Ensures the food does not spawn on the snake or text overlay areas.
        """
        # Define forbidden areas (rectangles to avoid)
        forbidden_areas = [
            # Top score area (0-200 x 0-50)
            pygame.Rect(0, 0, 200, 50),
            
            # Top right corner for high score display
            pygame.Rect(self.width - 300, 0, 300, 50),
            
            # Bottom area for controls text
            pygame.Rect(0, self.height - 40, self.width, 40),
            
            # Center area for potential level up messages
            pygame.Rect(self.width//2 - 150, self.height//2 - 50, 300, 100)
        ]
        
        # Fibonacci mode needs additional forbidden areas
        if hasattr(self, 'fibonacci_sequence'):
            # Center top for Fibonacci metrics
            forbidden_areas.append(pygame.Rect(self.width//2 - 250, 0, 500, 60))
        
        # Try to place food in a valid location
        max_attempts = 50  # Prevent infinite recursion
        for _ in range(max_attempts):
            x = random.randint(0, (self.width - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE 
            y = random.randint(0, (self.height - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            food_rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
            
            # Check if food collides with any forbidden area
            if any(food_rect.colliderect(area) for area in forbidden_areas):
                continue  # Try again with new coordinates
                
            # Check if food is on the snake
            potential_food = Point(x, y)
            if potential_food in self.snake:
                continue  # Try again with new coordinates
                
            # We found a valid position
            self.food = potential_food
            
            # Generate a new random food color if that feature is enabled
            if hasattr(self, 'food_theme') and self.food_theme.random_colors:
                self.food_theme.new_random_color()
                
            return
            
        # If we've exhausted attempts, just place it somewhere not on the snake
        # (fallback to original behavior)
        x = random.randint(0, (self.width - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE 
        y = random.randint(0, (self.height - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()  # Last resort recursive call
        
    def play_step(self):
        self.frame_iteration += 1
        current_time = pygame.time.get_ticks()
        
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:  # Either P or ESC pauses
                    paused = True
                    
                    # Create semi-transparent overlay for better contrast
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120) if self.background_theme == "dark" else (255, 255, 255, 120))
                    self.display.blit(overlay, (0, 0))
                    
                    # Dynamic text color based on theme
                    pause_color = WHITE if self.background_theme == "dark" else (0, 0, 100)
                    
                    # Updated pause text with R to resume and ESC to exit
                    pause_text = self.sub_font.render('PAUSED', True, pause_color)
                    resume_text = self.small_font.render('Press R to resume, ESC to exit', True, pause_color)
                    
                    self.display.blit(pause_text, (self.width//2 - pause_text.get_width()//2, self.height//2 - 30))
                    self.display.blit(resume_text, (self.width//2 - resume_text.get_width()//2, self.height//2 + 20))
                    pygame.display.update()
                    
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.KEYDOWN:
                                if pause_event.key == pygame.K_r:  # R to resume
                                    paused = False
                                elif pause_event.key == pygame.K_ESCAPE:  # ESC in pause to exit
                                    return True, self.score  # Return game over and score
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                quit()
                        pygame.time.wait(100)
                
                # Handle direction inputs with buffering
                elif event.key in (pygame.K_LEFT, pygame.K_a) and self.direction != RIGHT:
                    # Don't change immediately, store in buffer
                    self.direction_buffer = LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != LEFT:
                    self.direction_buffer = RIGHT
                elif event.key in (pygame.K_UP, pygame.K_w) and self.direction != DOWN:
                    self.direction_buffer = UP
                elif event.key in (pygame.K_DOWN, pygame.K_s) and self.direction != UP:
                    self.direction_buffer = DOWN
        
        # Apply buffered direction change if enough time has passed
        if self.direction_buffer is not None:
            if current_time - self.last_direction_change >= self.min_direction_change_interval:
                self.direction = self.direction_buffer
                self.direction_buffer = None
                self.last_direction_change = current_time

        # Move the snake
        self._move(self.direction)
        self.snake.insert(0, self.head)

        # Check for collisions
        if self._is_collision():
            return True, self.score

        # Check if the snake eats food
        if self.head == self.food:
            play_sound("eat")  # Changed from self.eat_sound.play()
            self.score += 1
            self._place_food()  # This will generate a new random color if needed
            
            # Play level up sound every 10 points
            if self.score % 10 == 0 and self.score > 0:
                play_sound("level_up")  # Changed from self.level_up_sound.play()
                self._show_level_up()
        else:
            self.snake.pop()
            
            # Update food color if it's a rainbow theme
            # This is the key fix - update the food color even when not eating
            if self.food_theme.random_colors and self.frame_iteration % 60 == 0:
                self.food_theme.new_random_color()

        # Update UI and clock
        self._update_ui()
        self.clock.tick(self.speed)  # Use custom speed if provided
        return False, self.score
    
    def _is_collision(self):
        if self.head in self.snake[1:]:
            # Log more details about the collision
            collision_index = self.snake[1:].index(self.head) + 1
            print(f"Game Over: Snake collision with segment {collision_index}. "
                f"Direction: {self.direction}, Head: {self.head}, "
                f"Collided segment: {self.snake[collision_index]}")
            play_sound("game_over")
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
        
        # Rest of the method remains unchanged...
        # Draw snake with custom theme
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                          (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Display score with theme-appropriate color
        score_text = self.main_font.render("Score: " + str(self.score), True, main_text_color)
        self.display.blit(score_text, [0, 0])
        
        # Draw high score with theme-appropriate color
        if hasattr(self, 'record'):
            high_score_text = self.sub_font.render(f"High Score: {self.record}", True, high_score_color)
            high_score_rect = high_score_text.get_rect(topright=(self.width - 10, 10))
            self.display.blit(high_score_text, high_score_rect)
        
        # Add controls help text with theme-appropriate color
        controls_text = self.small_font.render("ESC or P - Pause | Arrow Keys / WASD - Move", True, controls_color)
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
            text_color = YELLOW if self.background_theme == "dark" else (0, 100, 0)
            
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

    # Add a method to toggle enhanced effects
    def toggle_enhanced_effects(self):
        """Toggle between enhanced and simple level-up effects"""
        self.enhanced_effects = not self.enhanced_effects
        return self.enhanced_effects

    def _draw(self):
        # ... existing drawing code for game elements ...
        
        # Draw score and high score cleanly
        score_text = self.main_font.render(f"Score: {self.score}", True, WHITE)
        self.display.blit(score_text, [10, 10])
        
        # Draw just the high score value in the top right - no date, no extra info
        high_score_text = self.main_font.render(f"High Score: {self.record}", True, YELLOW)
        high_score_rect = high_score_text.get_rect(topright=(self.width - 10, 10))
        self.display.blit(high_score_text, high_score_rect)
        
        # ... rest of drawing code ...

if __name__ == '__main__':
    game = SnakeGame()
    
    # game loop
    while True:
        game_over, score = game.play_step()
        
        if game_over:
            break
        
    print('Final Score', game.score)
    pygame.quit()