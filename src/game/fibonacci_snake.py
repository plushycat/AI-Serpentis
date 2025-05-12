import pygame
from src.utils.sound_manager import play_sound
from utils import draw_gradient 
from src.game.snake_game import SnakeGame, BLOCK_SIZE, SPEED, Point

class FibonacciSnakeGame(SnakeGame):
    def __init__(self, width=1280, height=720, speed=None, display_surface=None):
        # Add this at the beginning of __init__ method
        from src.utils.sound_manager import sound_manager
        sound_manager.refresh_settings()
        
        # Pass speed to parent constructor
        super().__init__(width, height, display_surface, speed=speed)
            # Add this method to set the theme directly
        def set_theme(self, theme):
            """Update the background theme"""
            from src.ui.shared_globals import update_theme
            self.background_theme = theme
            update_theme(theme)  # Sync with global state
        
        # Also set it on this instance for clarity
        self.speed = speed if speed is not None else SPEED
        
        # Override snake initialization - start with just the head
        self.head = Point(self.width // 2, self.height // 2)
        self.snake = [self.head]  # Just the head, no body segments initially
        
        # Initialize Fibonacci sequence values correctly
        self.fibonacci_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]  # Pre-compute sequence
        self.fib_index = 0  # Start at index 0 (value = 0)
        self.growth_pending = 0  # Track segments still to be added
        
        # Track total Fibonacci segments added
        self.total_fibonacci_growth = 0
        
        # Update caption for this game mode
        pygame.display.set_caption('AI Serpentis - Fibonacci Mode')
    
    def play_step(self):
        self.frame_iteration += 1
        
        # Handle user input (reuse parent code)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:  # Changed to support both P and ESC
                    paused = True
                    
                    # Create semi-transparent overlay for better contrast
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120) if self.background_theme == "dark" else (255, 255, 255, 120))
                    self.display.blit(overlay, (0, 0))
                    
                    # Dynamic text color based on theme
                    pause_color = (255, 255, 255) if self.background_theme == "dark" else (0, 0, 100)
                    
                    # Updated pause text with R to resume and ESC to exit instructions
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
                                    # Get current Fibonacci values for score return
                                    current_fib_index = max(0, self.fib_index - 1)
                                    current_fib_value = self.fibonacci_sequence[current_fib_index]
                                    return True, (self.score, current_fib_value)
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                quit()
                        pygame.time.wait(100)
                    
                # Continue with direction handling
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if self.direction != 1:  # RIGHT
                        self.direction = 2  # LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self.direction != 2:  # LEFT
                        self.direction = 1  # RIGHT
                elif event.key in (pygame.K_UP, pygame.K_w):
                    if self.direction != 4:  # DOWN
                        self.direction = 3  # UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if self.direction != 3:  # UP
                        self.direction = 4  # DOWN
                elif event.key == pygame.K_ESCAPE:
                    return True, self.score

        # Move the snake
        self._move(self.direction)
        self.snake.insert(0, self.head)
        
        # Track if we ate food on this step
        ate_food_this_step = False

        # Check for collisions
        if self._is_collision():
            # Return the current food count and the CURRENT Fibonacci value
            current_fib_index = max(0, self.fib_index - 1)
            current_fib_value = self.fibonacci_sequence[current_fib_index]
            return True, (self.score, current_fib_value)

        # Check if the snake eats food
        if self.head == self.food:
            play_sound("eat")  # Changed from self.eat_sound.play()
            self.score += 1
            self._place_food()
            ate_food_this_step = True
            
            # Get current Fibonacci value for growth
            current_fib_value = self.fibonacci_sequence[self.fib_index]
            
            # Fibonacci growth - add current Fibonacci number to pending growth
            self.growth_pending += current_fib_value
            
            # Track total growth from Fibonacci sequence
            self.total_fibonacci_growth += current_fib_value
            
            # Move to next Fibonacci number
            self.fib_index += 1
            # If we exceed pre-computed values, calculate more
            if self.fib_index >= len(self.fibonacci_sequence) - 1:
                next_val = self.fibonacci_sequence[-1] + self.fibonacci_sequence[-2]
                self.fibonacci_sequence.append(next_val)
            
            # Play level up sound every 5 points instead of 10
            if self.score % 5 == 0 and self.score > 0:
                play_sound("level_up")  # Changed from self.level_up_sound.play()
                self._show_level_up()
        
        # Handle tail removal logic
        # For the first food (Fibonacci value 0), we ALWAYS remove the tail
        if ate_food_this_step and self.score == 1:
            # First food was just eaten - always remove tail to maintain original length
            self.snake.pop()
            # We've already accounted for the fact that current_fib_value is 0 
            # by keeping the snake length the same
        elif self.growth_pending <= 0:
            # No pending growth, remove tail
            self.snake.pop()
        else:
            # We have pending growth, keep the tail
            self.growth_pending -= 1
            
        # Update food color if it's a rainbow theme
        if self.food_theme.random_colors and self.frame_iteration % 60 == 0:
            self.food_theme.new_random_color()

        # Update UI and clock
        self._update_ui()
        self.clock.tick(self.speed)  # Use instance speed instead of global SPEED
        return False, self.score
    
    def _update_ui(self):
        # Apply background based on theme
        if self.background_theme == "dark":
            draw_gradient(self.display, (0, 0, 50), (0, 0, 0), self.width, self.height)
            # Dark theme colors
            main_text_color = (255, 255, 255)  # WHITE
            high_score_color = (255, 255, 0)   # YELLOW
            controls_color = (180, 180, 180)   # Light gray
        else:
            draw_gradient(self.display, (200, 200, 200), (255, 255, 255), self.width, self.height)
            # Light theme colors - change to GREEN
            main_text_color = (0, 120, 0)          # Rich green for main text
            high_score_color = (0, 100, 0)         # Slightly darker green for high score
            controls_color = (60, 60, 60)          # Keep dark gray for controls

        # Draw snake with custom theme
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                        (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Get the CURRENT Fibonacci value (the one that was JUST used, not the next one)
        # We need to look at the previous index since fib_index is already pointing to the NEXT value
        current_fib_index = max(0, self.fib_index - 1)  # Ensure we don't go below 0
        current_fib_value = self.fibonacci_sequence[current_fib_index]
        next_fib_value = self.fibonacci_sequence[self.fib_index]  # This is correct

        # Display score with format showing current score and corresponding Fibonacci value
        # This now shows the Fibonacci value JUST USED, not the next one
        score_text = self.main_font.render(f"Score: {self.score} | {current_fib_value}", True, main_text_color)
        self.display.blit(score_text, [10, 10])
        
        # Draw high score if available
        if hasattr(self, 'record') and self.record:
            if isinstance(self.record, tuple) and len(self.record) == 2:
                # Use the format (food_count, fib_value)
                high_score_text = self.sub_font.render(f"High Score: {self.record[0]} | {self.record[1]}", True, high_score_color)
            else:
                # Fallback for old format
                high_score_text = self.sub_font.render(f"High Score: {self.record}", True, high_score_color)
            high_score_rect = high_score_text.get_rect(topright=(self.width - 10, 10))
            self.display.blit(high_score_text, high_score_rect)
        
        # Add controls help text
        controls_text = self.small_font.render("ESC or P - Pause | R - Resume | Arrow Keys/WASD - Move", True, controls_color)
        self.display.blit(controls_text, [10, self.height - 30])
        
        # Calculate exact total length (initial head + all growth)
        total_length = len(self.snake)
        
        # Define colors for the metrics display
        metrics_color = (255, 215, 0) if self.background_theme == "dark" else (0, 120, 50)  # Green with blue tint
        
        # Display Total Length to the left of the Next Growth
        length_text = self.main_font.render(f"Length: {total_length}", True, metrics_color)
        next_growth_text = self.main_font.render(f"NEXT: +{next_fib_value}", True, metrics_color)
        
        # Calculate positions - center them both with spacing between
        total_width = length_text.get_width() + next_growth_text.get_width() + 60  # 60px spacing
        start_x = (self.width - total_width) // 2
        
        # Display metrics side by side
        length_rect = length_text.get_rect(midleft=(start_x, 40))
        next_growth_rect = next_growth_text.get_rect(midleft=(start_x + length_text.get_width() + 60, 40))
        
        self.display.blit(length_text, length_rect)
        self.display.blit(next_growth_text, next_growth_rect)
        
        # Update display
        pygame.display.flip()

    def get_fibonacci_at_position(self, position):
        """Get the Fibonacci number at the given position in the sequence"""
        if position < len(self.fibonacci_sequence):
            return self.fibonacci_sequence[position]
            
        # If position is beyond our pre-computed values, calculate it
        if position <= 0:
            return 0
        elif position == 1 or position == 2:
            return 1
        
        # Generate the Fibonacci sequence up to the desired position
        a, b = 1, 1
        for _ in range(3, position + 1):
            a, b = b, a + b
        return b
