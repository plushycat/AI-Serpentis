import pygame
import random
import os
import json
import math
import torch
import numpy as np
from collections import namedtuple
from enum import Enum

from src.ai.model import Linear_QNet
from src.ai.agent import Agent
# Update import to use Direction from snake_game directly
from src.game.snake_game import SnakeGame, Point, RIGHT, LEFT, UP, DOWN, BLOCK_SIZE, SPEED
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization

# Create a special SnakeGame subclass for VS mode
class VSPlayerGame(SnakeGame):
    """A modified SnakeGame that accepts external direction input and has minimal UI"""
    
    def __init__(self, width=640, height=480, speed=SPEED, display_surface=None):
        """Initialize with speed parameter"""
        super().__init__(width=width, height=height, display_surface=display_surface)
        self.speed = speed  # Store speed attribute explicitly
    
    def play_step(self, direction=None):
        """Modified play_step that accepts external direction input"""
        self.frame_iteration += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = True
                    
                    # Create semi-transparent overlay
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
                            elif pause_event.type == pygame.QUIT:
                                pygame.quit()
                                quit()
                        pygame.time.delay(100)

        # Apply external direction if provided
        if direction is not None:
            self.direction = direction
            
        # Move the snake in the current direction
        self._move(self.direction)
        self.snake.insert(0, self.head)

        # Check for collisions
        if self._is_collision():
            if hasattr(self, 'game_over_sound') and self.game_over_sound:
                self.game_over_sound.play()
            return True, self.score
        
        # Check if the snake eats food
        if self.head == self.food:
            if hasattr(self, 'eat_sound') and self.eat_sound:
                self.eat_sound.play()
            self.score += 1
            self._place_food()  # This will generate a new random color if needed
            
            # Play level up sound every 10 points
            if self.score % 10 == 0 and self.score > 0:
                if hasattr(self, 'level_up_sound') and self.level_up_sound:
                    self.level_up_sound.play()
        else:
            self.snake.pop()
            
            # Update food color if it's a rainbow theme
            if self.food_theme.random_colors and self.frame_iteration % 60 == 0:
                self.food_theme.new_random_color()
        
        # Override parent's _update_ui with our own minimal version
        self._update_ui_simple()
        self.clock.tick(self.speed)
        return False, self.score
    
    def _update_ui_simple(self):
        """A minimal UI update that skips drawing scores and other elements"""
        # Apply background based on theme
        if self.background_theme == "dark":
            self.display.fill((0, 0, 20))  # Very dark blue
        else:
            self.display.fill((240, 240, 240))  # Very light gray

        # Draw snake with custom theme - only essential game elements
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                         (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        pygame.display.flip()

# Create a special SnakeGameAI subclass for VS mode
class VSAIGame(SnakeGameAI):
    """A modified SnakeGameAI with minimal UI for use in split-screen"""
    
    def __init__(self, width=640, height=480, display_surface=None):
        super().__init__(width=width, height=height, display_surface=display_surface)
    
    def _update_ui(self):
        """Override to provide minimal UI"""
        # Apply background based on theme
        if self.background_theme == "dark":
            self.display.fill((0, 0, 20))  # Very dark blue
        else:
            self.display.fill((240, 240, 240))  # Very light gray

        # Draw snake with custom theme
        for i, point in enumerate(self.snake):
            segment_color = self.snake_theme.get_segment_color(i)
            pygame.draw.rect(self.display, segment_color, pygame.Rect(point.x, point.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw food with custom theme
        food_color = self.food_theme.get_food_color(self.frame_iteration)
        pygame.draw.circle(self.display, food_color, 
                         (self.food.x + BLOCK_SIZE // 2, self.food.y + BLOCK_SIZE // 2), 10)

        pygame.display.flip()

# For high score handling
def load_high_scores():
    """Load high scores from file or create default if it doesn't exist"""
    highscore_file = "data/stats/highscores.json"
    try:
        if os.path.exists(highscore_file):
            with open(highscore_file, 'r') as f:
                return json.load(f)
        else:
            # Default high scores
            high_scores = {
                "classic": 0,
                "ai": 0,
                "vs": {"player": 0, "ai": 0}
            }
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(highscore_file), exist_ok=True)
            # Create the file with default scores
            with open(highscore_file, 'w') as f:
                json.dump(high_scores, f)
            return high_scores
    except Exception as e:
        print(f"Error loading high scores: {e}")
        return {"classic": 0, "ai": 0, "vs": {"player": 0, "ai": 0}}

def save_vs_high_score(player_type, score):
    """Save high score for vs mode if it's a new record"""
    highscore_file = "data/stats/highscores.json"
    try:
        high_scores = load_high_scores()
        
        # Update if it's a new high score
        if score > high_scores.get("vs", {}).get(player_type, 0):
            if "vs" not in high_scores:
                high_scores["vs"] = {}
            high_scores["vs"][player_type] = score
            
            # Save updated high scores
            with open(highscore_file, 'w') as f:
                json.dump(high_scores, f)
            return True  # Indicates this is a new high score
        return False
    except Exception as e:
        print(f"Error saving high score: {e}")
        return False

def draw_simple_score(surface, p_score, ai_score, total_width, font):
    """Draw a clean, simple scoreboard showing only player and AI scores"""
    # Draw player score on left side
    player_txt = font.render(f"{p_score}", True, (255, 255, 255))
    surface.blit(player_txt, (total_width//4 - player_txt.get_width()//2, 20))
    
    # Draw AI score on right side
    ai_txt = font.render(f"{ai_score}", True, (255, 255, 255))
    surface.blit(ai_txt, (total_width*3//4 - ai_txt.get_width()//2, 20))

def player_vs_ai():
    """Main function for the split-screen player vs AI mode"""
    pygame.init()
    
    # 1) Set up window dimensions
    game_w, game_h = 640, 480
    screen_width = game_w * 2
    screen_height = game_h + 60  # Add just a bit of space for controls at bottom
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("AI Serpentis - Player vs AI")
    
    # Create black background for the entire screen
    screen.fill((0, 0, 0))
    
    # Create a persistent background for the score area to prevent flickering
    score_area = pygame.Surface((screen_width, 60))
    score_area.fill((0, 0, 35))  # Dark blue background
    pygame.draw.line(score_area, (100, 100, 150), (screen_width//2, 0), (screen_width//2, 60), 2)
    
    # 2) Create two sub-surfaces for the games
    left_surf = screen.subsurface(pygame.Rect(0, 60, game_w, game_h))
    right_surf = screen.subsurface(pygame.Rect(game_w, 60, game_w, game_h))
    
    # Load fonts with error handling
    try:
        main_font = pygame.font.Font("assets/fonts/game_over.ttf", 48)  # Larger, cleaner score font
        small_font = pygame.font.Font("assets/fonts/game_over.ttf", 20)  # Smaller font for controls
    except FileNotFoundError:
        print("Warning: Font file not found. Using system fonts.")
        main_font = pygame.font.SysFont("Arial", 48)  
        small_font = pygame.font.SysFont("Arial", 20)
    
    # Load sounds with error handling
    try:
        eat_sound = pygame.mixer.Sound("assets/sounds/eat-food.mp3")
        game_over_sound = pygame.mixer.Sound("assets/sounds/game-over.wav")
        level_up_sound = pygame.mixer.Sound("assets/sounds/level-up.wav")
    except:
        print("Warning: Sound file(s) not found.")
        eat_sound = None
        game_over_sound = None
        level_up_sound = None
    
    # Setup AI agent model
    model = Linear_QNet(11, 256, 3)
    
    # Try multiple model loading paths with better error handling
    try:
        # Look in different possible locations for the model
        model_paths = ["data/models/model.pth", "model_snapshots/model.pth", 
                      "data/checkpoints/checkpoint_model.pth"]
        model_loaded = False
        
        for path in model_paths:
            if os.path.exists(path):
                model.load_state_dict(torch.load(path))
                model_loaded = True
                print(f"Model loaded successfully from {path}")
                break
                
        if not model_loaded:
            print("Warning: No pre-trained model found. Using untrained model.")
        
        model.eval()  # Set model to evaluation mode
    except Exception as e:
        print(f"Error loading model: {e}")
    
    # Initialize agent with model
    agent = Agent()
    agent.model = model
    agent.epsilon = 0  # No exploration, pure exploitation
    
    # 3) Synchronize random seed for fair food placement
    seed = random.randint(1, 10000)  # Generate a random seed
    random.seed(seed)
    
    # 4) Create game instances on the surfaces
    player_game = VSPlayerGame(width=game_w, height=game_h, display_surface=left_surf)
    ai_game = VSAIGame(width=game_w, height=game_h, display_surface=right_surf)
    
    # Apply customization settings to both games
    snake_theme = customization.get_current_snake_theme()
    food_theme = customization.get_current_food_theme()
    
    player_game.snake_theme = snake_theme
    player_game.food_theme = food_theme
    ai_game.snake_theme = snake_theme
    ai_game.food_theme = food_theme
    
    # Game state variables
    player_score = 0
    ai_score = 0
    player_game_over = False
    ai_game_over = False
    final_result_shown = False
    clock = pygame.time.Clock()
    
    # Track player direction
    player_direction = RIGHT
    
    # Game loop
    running = True
    while running:
        # a) Handle shared events and player movement
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                # Handle escape key - return to main menu
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                # Handle pause
                if event.key == pygame.K_p:
                    paused = True
                    
                    # Draw pause overlay
                    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))  # Semi-transparent black
                    screen.blit(overlay, (0, 0))
                    
                    pause_text = main_font.render("PAUSED", True, (255, 255, 255))
                    screen.blit(pause_text, (screen_width//2 - pause_text.get_width()//2, screen_height//2 - 30))
                    
                    continue_text = small_font.render("Press P to continue", True, (200, 200, 200))
                    screen.blit(continue_text, (screen_width//2 - continue_text.get_width()//2, screen_height//2 + 30))
                    
                    pygame.display.flip()
                    
                    # Pause loop
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.QUIT:
                                pygame.quit()
                                return
                            
                            if pause_event.type == pygame.KEYDOWN:
                                if pause_event.key == pygame.K_p:
                                    paused = False
                                elif pause_event.key == pygame.K_ESCAPE:
                                    running = False
                                    paused = False
                        
                        pygame.time.delay(100)
                
                # Player controls - update the player_direction based on keys
                if not player_game_over:
                    if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and player_game.direction != RIGHT:
                        player_direction = LEFT
                    elif (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and player_game.direction != LEFT:
                        player_direction = RIGHT
                    elif (event.key == pygame.K_UP or event.key == pygame.K_w) and player_game.direction != DOWN:
                        player_direction = UP
                    elif (event.key == pygame.K_DOWN or event.key == pygame.K_s) and player_game.direction != UP:
                        player_direction = DOWN
        
        # Draw the score area background
        screen.blit(score_area, (0, 0))
        
        # If both games are over, show final result
        if player_game_over and ai_game_over and not final_result_shown:
            # Determine the winner
            if player_score > ai_score:
                winner_text = "PLAYER WINS!"
                winner_color = (50, 255, 50)  # Green
                save_vs_high_score("player", player_score)
            elif ai_score > player_score:
                winner_text = "AI WINS!"
                winner_color = (50, 50, 255)  # Blue
                save_vs_high_score("ai", ai_score)
            else:
                winner_text = "IT'S A TIE!"
                winner_color = (255, 255, 50)  # Yellow
            
            # Draw semi-transparent overlay
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            # Draw winner text
            winner_surf = main_font.render(winner_text, True, winner_color)
            screen.blit(winner_surf, (screen_width//2 - winner_surf.get_width()//2, screen_height//2 - 30))
            
            # Draw continue text
            continue_surf = small_font.render("Press any key to continue", True, (200, 200, 200))
            screen.blit(continue_surf, (screen_width//2 - continue_surf.get_width()//2, screen_height//2 + 30))
            
            pygame.display.flip()
            final_result_shown = True
            
            # Wait for key press to continue
            waiting_for_key = True
            while waiting_for_key:
                for wait_event in pygame.event.get():
                    if wait_event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    
                    if wait_event.type == pygame.KEYDOWN:
                        if wait_event.key == pygame.K_ESCAPE:
                            running = False
                            waiting_for_key = False
                        else:
                            # Reset games for a new round
                            random.seed(random.randint(1, 10000))
                            player_game = VSPlayerGame(width=game_w, height=game_h, display_surface=left_surf)
                            ai_game = VSAIGame(width=game_w, height=game_h, display_surface=right_surf)
                            
                            # Apply customization again
                            player_game.snake_theme = snake_theme
                            player_game.food_theme = food_theme
                            ai_game.snake_theme = snake_theme
                            ai_game.food_theme = food_theme
                            
                            # Reset game states
                            player_score = 0
                            ai_score = 0
                            player_game_over = False
                            ai_game_over = False
                            final_result_shown = False
                            player_direction = RIGHT  # Reset player direction
                            waiting_for_key = False
                
                pygame.time.delay(100)
            
            continue
        
        # b) Process game steps if not game over
        if not player_game_over:
            # Process player game step with the current player direction
            player_game_over, player_score = player_game.play_step(player_direction)
            
            # Play sounds for player
            if player_score > player_game.score - 1:  # Score increased
                if eat_sound:
                    eat_sound.play()
                if player_score % 10 == 0 and player_score > 0 and level_up_sound:
                    level_up_sound.play()
            
            if player_game_over and game_over_sound:
                game_over_sound.play()
        
        if not ai_game_over:
            # Get AI state and action
            state = agent.get_state(ai_game)
            action = agent.get_action(state)
            
            # Process AI game step
            _, ai_game_over, ai_score = ai_game.play_step(action)
            
            # Play sounds for AI
            if ai_score > ai_game.score - 1:  # Score increased
                if eat_sound:
                    eat_sound.play()
                if ai_score % 10 == 0 and ai_score > 0 and level_up_sound:
                    level_up_sound.play()
            
            if ai_game_over and game_over_sound:
                game_over_sound.play()
        
        # Draw simple score display (just the numbers)
        player_txt = main_font.render(f"{player_score}", True, (255, 255, 255))
        ai_txt = main_font.render(f"{ai_score}", True, (255, 255, 255))
        screen.blit(player_txt, (game_w//2 - player_txt.get_width()//2, 10))
        screen.blit(ai_txt, (screen_width - game_w//2 - ai_txt.get_width()//2, 10))
        
        # Draw simple text labels for player and AI
        player_label = small_font.render("YOU", True, (180, 180, 180))
        ai_label = small_font.render("AI", True, (180, 180, 180))
        screen.blit(player_label, (10, 10))
        screen.blit(ai_label, (screen_width - 40, 10))
        
        # Draw minimal controls text only on player side (bottom right of player area)
        controls_text = small_font.render("ESC - Menu | P - Pause", True, (150, 150, 150))
        screen.blit(controls_text, (game_w - controls_text.get_width() - 10, screen_height - 30))
        
        # Draw game over text if needed
        if player_game_over:
            game_over_surf = main_font.render("GAME OVER", True, (255, 50, 50))
            left_surf.blit(game_over_surf, (game_w//2 - game_over_surf.get_width()//2, game_h//2))
        
        if ai_game_over:
            game_over_surf = main_font.render("GAME OVER", True, (255, 50, 50))
            right_surf.blit(game_over_surf, (game_w//2 - game_over_surf.get_width()//2, game_h//2))
        
        # d) Update display and control frame rate
        pygame.display.flip()
        clock.tick(15)  # Lower frame rate for fair gameplay
    
    # Reset display mode for returning to main menu
    pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("AI Serpentis")

if __name__ == "__main__":
    player_vs_ai()