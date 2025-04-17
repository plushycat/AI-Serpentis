import pygame, random, os
from enum import Enum
from collections import namedtuple
import numpy as np
from utils import draw_gradient 

pygame.init()
pygame.mixer.init()

# Define color constants
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0, 0, 0)

# Define block size and game speed
BLOCK_SIZE = 20
SPEED = 40

# Direction constants
RIGHT = 1
LEFT = 2
UP = 3
DOWN = 4

# Point data structure to store x, y coordinates
Point = namedtuple('Point', 'x, y')

# Load font for displaying text
font_path = "statics/game_over.ttf"  
font = pygame.font.Font(font_path, 60)  

class SnakeGameAI:
    """
    A class to represent the Snake Game with AI integration.
    Handles game logic, rendering, and user interactions.
    """

    def __init__(self, width=640, height=480, record=0, avg=0, iteration=0):
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
        self.eat_sound = pygame.mixer.Sound('statics/eat-food.mp3')  # Sound for eating food
        self.game_over_sound = pygame.mixer.Sound('statics/game-over.mp3')  # Sound for game over
        
        # Use the width and height parameters to set up the display
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Game')  # Set the game title
        self.clock = pygame.time.Clock()
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
        # Pause functionality
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Press 'P' to pause
                    paused = True
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_p:
                                paused = False

        self.frame_iteration += 1

        # Handle quitting the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Move the snake
        self._move(action) 
        self.snake.insert(0, self.head)  # Update the snake's position
        
        reward = 0
        game_over = False

        # Check for collisions or exceeding the frame limit
        if self.is_collision() or self.frame_iteration > 100 * len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # Check if the snake eats food
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
            self.eat_sound.play()
        else:
            self.snake.pop()

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
        draw_gradient(self.display, (0, 0, 50), (0, 0, 0), self.width, self.height)  # Draw gradient background

        # Draw the snake with a gradient effect
        for i, point in enumerate(self.snake):
            r = 0
            g = max(0, min(255, 255 - i * 10))  
            b = max(0, min(255, i * 10))        
            color = (r, g, b)
            pygame.draw.rect(self.display, color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw the food
        pygame.draw.circle(self.display, (255, 0, 0), (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        # Display score, record, average, and iteration
        score_text = font.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(score_text, [0, 0])

        record_text = font.render(f"Record: {self.record}", True, WHITE)
        self.display.blit(record_text, [self.width - record_text.get_width(), 0])

        avg_text = font.render(f"Average: {self.avg}", True, WHITE)
        self.display.blit(avg_text, [0, 25])

        iter_text = font.render(f"Iteration: {self.iteration}", True, WHITE)
        self.display.blit(iter_text, [self.width - iter_text.get_width(), 25])

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