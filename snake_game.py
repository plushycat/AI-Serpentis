import pygame
import random
from enum import Enum
from collections import namedtuple
from utils import draw_gradient  # Import the correct draw_gradient function

pygame.init()
pygame.mixer.init()

# colors
WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE = (0, 0, 255)
BLACK = (0,0,0)
GREEN = (0, 255, 0)

BLOCK_SIZE = 20
SPEED = 100

# Directions
RIGHT = 1
LEFT = 2
UP = 3
DOWN = 4

Point = namedtuple('Point', 'x, y')

font_path = "statics/game_over.ttf"  
font = pygame.font.Font(font_path, 60)  



# rgb colors
WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)

BLOCK_SIZE = 20
SPEED = 20

class SnakeGame:
    def __init__(self, width=1280, height=720, record=0, avg=0, iteration=0):
        self.width = width
        self.height = height
        self.score = 0
        self.eat_sound = pygame.mixer.Sound('statics/eat-food.mp3')
        self.game_over_sound = pygame.mixer.Sound('statics/game-over.mp3')
        self.snake_color = GREEN  # Default snake color
        self.background_theme = "dark"  # Default background theme
        
        # Init display
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Game')
        self.clock = pygame.time.Clock()
        
        # Init game state
        self.direction = RIGHT
        self.head = Point(self.width / 2, self.height / 2)
        self.snake = [self.head]
        self.food = None
        self._place_food()

    def _place_food(self):
        x = random.randint(0, (self.width - BLOCK_SIZE ) // BLOCK_SIZE ) * BLOCK_SIZE 
        y = random.randint(0, (self.height - BLOCK_SIZE ) // BLOCK_SIZE ) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()
        
    def play_step(self):
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):  # Left arrow or 'A'
                    self.direction = LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):  # Right arrow or 'D'
                    self.direction = RIGHT
                elif event.key in (pygame.K_UP, pygame.K_w):  # Up arrow or 'W'
                    self.direction = UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):  # Down arrow or 'S'
                    self.direction = DOWN

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
            self._place_food()
        else:
            self.snake.pop()

        # Update UI and clock
        self._update_ui()
        self.clock.tick(30)  # Fixed frame rate
        return False, self.score
    
    def _is_collision(self):
        # Check if the snake hits itself
        if self.head in self.snake[1:]:
            self.game_over_sound.play()
            return True
        return False

        
    def _update_ui(self):
        if self.background_theme == "dark":
            draw_gradient(self.display, (0, 0, 50), (0, 0, 0), self.width, self.height)
        else:
            draw_gradient(self.display, (200, 200, 200), (255, 255, 255), self.width, self.height)

        # Draw snake with gradient effect
        for i, point in enumerate(self.snake):
            # Calculate gradient color for each segment
            r = max(0, min(255, self.snake_color[0] - i * 10))
            g = max(0, min(255, self.snake_color[1] - i * 10))
            b = max(0, min(255, self.snake_color[2] - i * 10))
            segment_color = (r, g, b)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food
        pygame.draw.circle(self.display, (255, 0, 0), (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Display score
        score_text = font.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(score_text, [0, 0])

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

            

if __name__ == '__main__':
    game = SnakeGame()
    
    # game loop
    while True:
        game_over, score = game.play_step()
        
        if game_over == True:
            break
        
    print('Final Score', game.score)
        
        
    pygame.quit()