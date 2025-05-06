import pygame
import random
import numpy as np
from enum import Enum
from collections import namedtuple
from src.utils.sound_manager import play_sound
from src.game.snake_ai import SnakeGameAI, Point, RIGHT, LEFT, UP, DOWN, BLOCK_SIZE, WHITE, BLACK, RED, BLUE, BLUE2, GREEN, YELLOW
from utils import draw_gradient

# Add GOLD constant since it's used in your code but might not be in snake_ai.py
GOLD = (255, 215, 0)

class FibonacciGameAI(SnakeGameAI):
    """
    Extends the SnakeGameAI class to implement Fibonacci game mechanics.
    The snake grows according to the Fibonacci sequence.
    """
    def __init__(self, width=640, height=480, record=0, avg=0, iteration=0, display_surface=None):
        # Initialize the parent class
        super().__init__(width, height, record, avg, iteration, display_surface)
        
        # Fibonacci-specific attributes - match player mode
        # Start with 0 to match player mode (0-indexed growth)
        self.fibonacci_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        self.fib_index = 0  # Start with index 0 (value 0)
        self.total_fibonacci_growth = 0
        self.fib_score = 0  # Total Fibonacci value collected
        self.viewing_mode = False  # Flag for viewer mode UI
        
    # Add this method to set the theme directly
    def set_theme(self, theme):
        """Update the background theme"""
        self.background_theme = theme
        
    def reset(self):
        """Override reset to include Fibonacci-specific reset logic"""
        super().reset()
        self.fib_index = 0
        self.total_fibonacci_growth = 0
        self.fib_score = 0
        
    def _extend_fibonacci_sequence(self):
        """Extend the Fibonacci sequence if we're about to go beyond the end"""
        if self.fib_index >= len(self.fibonacci_sequence) - 1:
            next_val = self.fibonacci_sequence[-1] + self.fibonacci_sequence[-2]
            self.fibonacci_sequence.append(next_val)
            
    def get_fibonacci_at_position(self, index):
        """Get the Fibonacci value at a specific index, extending if needed"""
        # Safety check for negative indices
        if index < 0:
            return 0
            
        while index >= len(self.fibonacci_sequence):
            self._extend_fibonacci_sequence()
        return self.fibonacci_sequence[index]
    
    def play_step(self, action):
        """Override the play_step method to implement Fibonacci growth mechanics"""
        self.frame_iteration += 1
        
        # Handle events (quit events, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if event.type == pygame.KEYDOWN:
                # Handle pause with both P and ESC
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    paused = True
    
                    # Create semi-transparent overlay for better contrast
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120) if self.background_theme == "dark" else (255, 255, 255, 120))
                    self.display.blit(overlay, (0, 0))
    
                    # Dynamic text color based on theme
                    pause_color = WHITE if self.background_theme == "dark" else (0, 0, 100)
                    
                    # Updated pause text with instructions
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
                                elif pause_event.key == pygame.K_ESCAPE:  # ESC to exit
                                    game_over = True
                                    reward = -10
                                    return reward, game_over, self.score
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                quit()
                        pygame.time.wait(100)
        
        # Move the snake
        self._move(action)
        self.snake.insert(0, self.head)
        
        # Keep track of recent positions for loop detection
        self.recent_positions.append((self.head.x, self.head.y))
        if len(self.recent_positions) > self.loop_detection_length:
            self.recent_positions.pop(0)
        
        reward = 0
        game_over = False
        
        # Check for collisions
        if self.is_collision():
            game_over = True
            reward = -10
            if hasattr(self, 'game_over_sound'):
                self.game_over_sound.play()
            return reward, game_over, self.score
        
        # Check for timeout - using customizable frame limit multiplier
        if self.score > 10 and self.frame_iteration > self.frame_limit_multiplier * len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score
            
        # Check if the snake eats food
        if self.head == self.food:
            # Get current Fibonacci value for growth
            current_fib_value = self.get_fibonacci_at_position(self.fib_index)
            
            # Increment score - this represents food eaten
            self.score += 1
            
            # Add to Fibonacci score - accumulated Fibonacci values
            if self.score == 1:
                # First food adds nothing (matches player mode)
                pass
            else:
                # Add to total Fibonacci sum - this matches player mode behavior
                self.total_fibonacci_growth += current_fib_value
                self.fib_score = self.total_fibonacci_growth
            
            # Reward is proportional to the Fibonacci value
            reward = max(1, current_fib_value) / 10  # Scale down large values
            
            # SPECIAL CASE: For first food (score=1, fib_index=0, value=0), remove tail
            # to match player mode behavior - no growth for first food
            if self.score == 1:
                self.snake.pop()  # Remove the tail to maintain original length
            else:
                # For subsequent values, add exactly that many segments
                for _ in range(current_fib_value):
                    # Add segments to the tail
                    self.snake.append(self.snake[-1])
                    
            # Track total growth
            self.total_fibonacci_growth += current_fib_value
                
            # Play sound effects
            play_sound("eat")  # Changed from self.eat_sound.play()
            
            # Play level up sound every 5 food collected
            if self.score > 0 and self.score % 5 == 0:
                play_sound("level_up")  # Changed from self.level_up_sound.play()
                self._show_level_up()  # This will call our implemented method
                
            # Place new food
            self._place_food()
            
            # Increment Fibonacci index
            self.fib_index += 1
            
            # Reset frame iteration counter to prevent timeout
            self.frame_iteration = 0
        else:
            # If no food eaten, just remove the tail
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
        
        # Update display
        self._update_ui()
        self.clock.tick(10)  # Adjust game speed (can be faster for AI training)
        
        return reward, game_over, self.score
        
    def _update_ui(self):
        """Override to include Fibonacci-specific UI elements"""
        # Select background and text colors based on theme
        if self.background_theme == "dark":
            draw_gradient(self.display, (0, 0, 50), (0, 0, 0), self.width, self.height)
            # Dark theme colors
            main_text_color = WHITE
            high_score_color = GOLD
            controls_color = (180, 180, 180)  # Light gray
        else:
            draw_gradient(self.display, (200, 200, 200), (255, 255, 255), self.width, self.height)
            # Light theme colors
            main_text_color = (0, 120, 0)      # Rich green
            high_score_color = (0, 100, 0)     # Darker green
            controls_color = (60, 60, 60)      # Dark gray

        # Draw snake with custom theme
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                         (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Get the current and next Fibonacci values
        # Current value is the last one used for growth
        current_fib_value = self.get_fibonacci_at_position(max(0, self.fib_index - 1))
        # Next value is what will be used for next growth
        next_fib_value = self.get_fibonacci_at_position(self.fib_index)

        # Different UI for viewer mode vs training mode
        if self.viewing_mode:
            # Simpler UI for viewers - just show Score, Record, and Fibonacci info
            score_text = self.main_font.render(f"Score: {self.score} | {current_fib_value}", True, main_text_color)
            self.display.blit(score_text, [10, 10])
            
            if hasattr(self, 'record') and self.record:
                if isinstance(self.record, tuple) and len(self.record) == 2:
                    # Use the format (food_count, fib_value)
                    record_text = self.main_font.render(f"Record: {self.record[0]} | {self.record[1]}", True, high_score_color)
                else:
                    # Fallback for old format
                    record_text = self.main_font.render(f"Record: {self.record}", True, high_score_color)
                self.display.blit(record_text, [self.width - record_text.get_width() - 10, 10])
            
            # Show next Fibonacci value
            next_growth_text = self.sub_font.render(f"NEXT: +{next_fib_value}", True, main_text_color)
            self.display.blit(next_growth_text, [10, 70])
            
            # Show total length
            length_text = self.sub_font.render(f"Length: {len(self.snake)}", True, main_text_color)
            self.display.blit(length_text, [self.width - length_text.get_width() - 10, 70])
            
            # Show total Fibonacci score
            fib_score_text = self.sub_font.render(f"Fibonacci Sum: {self.fib_score}", True, main_text_color)
            self.display.blit(fib_score_text, [10, 120])
            
            # Add controls help text
            controls_text = self.small_font.render("ESC or P - Pause | R - Resume", True, controls_color)
            self.display.blit(controls_text, [10, self.height - 30])
        else:
            # Full UI for training mode
            score_text = self.main_font.render(f"Score: {self.score} | Fib: {self.fib_score}", True, main_text_color)
            self.display.blit(score_text, [0, 0])

            record_text = self.main_font.render(f"Record: {self.record}", True, main_text_color)
            self.display.blit(record_text, [self.width - record_text.get_width(), 0])

            avg_text = self.sub_font.render(f"Average: {self.avg}", True, main_text_color)
            self.display.blit(avg_text, [0, 70])

            iter_text = self.sub_font.render(f"Iteration: {self.iteration}", True, main_text_color)
            self.display.blit(iter_text, [self.width - iter_text.get_width(), 70])
            
            # Show next Fibonacci value
            next_growth_text = self.sub_font.render(f"NEXT: +{next_fib_value}", True, main_text_color)
            self.display.blit(next_growth_text, [0, 140])

        # If debug mode is on, show additional information
        if self.debug_mode:
            # Show frame count and frame limit
            frame_limit = self.frame_limit_multiplier * len(self.snake)
            debug_text = self.small_font.render(f"Frames: {self.frame_iteration}/{frame_limit}", True, WHITE)
            # Position at bottom right instead of top left
            self.display.blit(debug_text, [self.width - debug_text.get_width() - 10, self.height - 60])
            
            # Mark the target food with a flashing indicator
            if self.frame_iteration % 30 < 15:  # Flashing effect
                pygame.draw.circle(self.display, (255, 255, 0), 
                                  (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 20, 2)

        pygame.display.flip()