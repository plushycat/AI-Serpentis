import pygame
import random
from enum import Enum
from collections import namedtuple

pygame.init()
pygame.mixer.init()

# colors
WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)

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



def draw_gradient(display, color1, color2):
    for i in range(600):  # Assuming window height is 600px
        r = color1[0] + (color2[0] - color1[0]) * i // 600
        g = color1[1] + (color2[1] - color1[1]) * i // 600
        b = color1[2] + (color2[2] - color1[2]) * i // 600
        pygame.draw.line(display, (r, g, b), (0, i), (800, i))  # Adjust to match your window size



# rgb colors
WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)

BLOCK_SIZE = 20
SPEED = 20

class SnakeGame:
    
    def __init__(self, width=640, height=480, record=0, avg=0, iteration=0):
        self.width = width
        self.height = height
        self.score = 0
        self.eat_sound = pygame.mixer.Sound('statics/eat-food.mp3')
        self.game_over_sound = pygame.mixer.Sound('statics/game-over.mp3')
        
        # init display
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Game')
        self.clock = pygame.time.Clock()
        
        # init game state
        self.direction = RIGHT
        
        self.head = Point(self.width/2, self.height/2)
        self.snake = [self.head]
        
        self.score = 0
        self.food = None
        self._place_food()
        
    def _place_food(self):
        x = random.randint(0, (self.width - BLOCK_SIZE ) // BLOCK_SIZE ) * BLOCK_SIZE 
        y = random.randint(0, (self.height - BLOCK_SIZE ) // BLOCK_SIZE ) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()
        
    def play_step(self):
        # 1. collect user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.direction = LEFT
                elif event.key == pygame.K_RIGHT:
                    self.direction = RIGHT
                elif event.key == pygame.K_UP:
                    self.direction = UP
                elif event.key == pygame.K_DOWN:
                    self.direction = DOWN
        
        # 2. move
        self._move(self.direction) # update the head
        self.snake.insert(0, self.head)
        
        # 3. check if game over
        game_over = False
        if self._is_collision():
            game_over = True
            return game_over, self.score
            
        # 4. place new food or just move
        if self.head == self.food:
            self.eat_sound.play()

            self.score += 1
            self._place_food()
        else:
            self.snake.pop()
        
        # 5. update ui and clock
        self._update_ui()
        self.clock.tick(SPEED)
        # 6. return game over and score
        return game_over, self.score
    
    def _is_collision(self):
        # Check if the snake hits itself
        if self.head in self.snake[1:]:
            self.game_over_sound.play()

            
            self.score = 0
            return True
        return False

        
    def _update_ui(self):

        draw_gradient(self.display, (0, 0, 50), (0, 0, 0))  # Dark blue to black gradient        
        
        # Draw snake with gradient effect
        for i, point in enumerate(self.snake):
            # Calculate RGB values and clamp them to the 0-255 range
            r = 0
            g = max(0, min(255, 255 - i * 10))  # Clamp the green value between 0 and 255
            b = max(0, min(255, i * 10))        # Clamp the blue value between 0 and 255

            color = (r, g, b)
            pygame.draw.rect(self.display, color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))
        
        # Add a glow effect
        pygame.draw.circle(self.display, (255, 0, 0), (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)
        pygame.draw.rect(self.display, (200, 0, 0), pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))


            
        pygame.draw.rect(self.display, RED, pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))

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