import pygame
from utils import draw_gradient 
from src.game.snake_game import SnakeGame, BLOCK_SIZE, SPEED

class FibonacciSnakeGame(SnakeGame):
    def __init__(self, width=1280, height=720, display_surface=None):
        # Call parent constructor to initialize the game
        super().__init__(width, height, display_surface)
        
        # Initialize Fibonacci sequence values
        self.fib_current = 1  # First value in sequence
        self.fib_next = 1     # Second value
        self.growth_pending = 0  # Track segments still to be added
        
        # Track total Fibonacci segments added
        self.total_fibonacci_growth = 0
        
        # Update caption for this game mode
        pygame.display.set_caption('Snake Game - Fibonacci Mode')
    
    def play_step(self):
        self.frame_iteration += 1
        
        # Handle user input (reuse parent code)
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
                    pause_color = (255, 255, 255) if self.background_theme == "dark" else (0, 0, 100)
                    
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

        # Check for collisions
        if self._is_collision():
            # Return score and total fibonacci growth when game ends
            return True, (self.score, self.total_fibonacci_growth)

        # Check if the snake eats food
        if self.head == self.food:
            self.eat_sound.play()
            self.score += 1
            self._place_food()
            
            # Fibonacci growth - add current Fibonacci number to pending growth
            self.growth_pending += self.fib_current
            
            # Track total growth from Fibonacci sequence
            self.total_fibonacci_growth += self.fib_current
            
            # Update Fibonacci sequence for next food
            temp = self.fib_current
            self.fib_current = self.fib_next
            self.fib_next = temp + self.fib_next
            
            # Play level up sound every 10 points
            if self.score % 10 == 0 and self.score > 0:
                if hasattr(self, 'level_up_sound') and self.level_up_sound:
                    self.level_up_sound.play()
                    self._show_level_up()
        else:
            # Only remove tail segment if we don't have pending growth
            if self.growth_pending <= 0:
                self.snake.pop()
            else:
                self.growth_pending -= 1
            
            # Update food color if it's a rainbow theme
            if self.food_theme.random_colors and self.frame_iteration % 60 == 0:
                self.food_theme.new_random_color()

        # Update UI and clock
        self._update_ui()
        self.clock.tick(SPEED)
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
            # Light theme colors
            main_text_color = (0, 0, 100)      # Dark blue
            high_score_color = (180, 100, 0)   # Dark orange
            controls_color = (80, 80, 80)      # Dark gray

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
        
        # Display total growth stat
        growth_stat = self.sub_font.render(f"Total Growth: {self.total_fibonacci_growth}", True, main_text_color)
        growth_stat_rect = growth_stat.get_rect(topright=(self.width - 10, 60))
        self.display.blit(growth_stat, growth_stat_rect)
        
        # Draw just the high score value directly using self.record
        if hasattr(self, 'record'):
            if isinstance(self.record, tuple):
                # Display both food and segments in high score
                high_score_text = self.sub_font.render(f"High Score: {self.record[0]} ({self.record[1]} segments)", True, high_score_color)
            else:
                # Fallback for backward compatibility
                high_score_text = self.sub_font.render(f"High Score: {self.record}", True, high_score_color)
            high_score_rect = high_score_text.get_rect(topright=(self.width - 10, 10))
            self.display.blit(high_score_text, high_score_rect)
        
        # Add controls help text at bottom left with dynamic color
        controls_text = self.small_font.render("ESC - Back to Menu | P - Pause | Arrow Keys/WASD - Move", True, controls_color)
        self.display.blit(controls_text, [10, self.height - 30])
        
        # Add Fibonacci-specific UI elements - CENTERED version
        theme_color = (255, 215, 0) if self.background_theme == "dark" else (180, 100, 0)  # Gold/amber
        
        # Display next growth value - CENTERED with new format
        fib_text = self.main_font.render(f"NEXT: +{self.fib_current}", True, theme_color)
        fib_text_rect = fib_text.get_rect(center=(self.width//2, 40))
        self.display.blit(fib_text, fib_text_rect)
        
        # Only call flip once
        pygame.display.flip()