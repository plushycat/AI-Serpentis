import pygame
import random
import os
import json
import torch
from src.ai.model import Linear_QNet
from src.ai.agent import Agent
from src.game.snake_game import SnakeGame, Point, RIGHT, LEFT, UP, DOWN, BLOCK_SIZE, SPEED
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization
from src.utils.input_utils import is_screenshot_key
from src.utils.scores import save_vs_high_score
from src.utils.sound_manager import sound_manager, play_sound

# Create a special SnakeGame subclass for VS mode
class VSPlayerGame(SnakeGame):
    """A modified SnakeGame that accepts external direction input and has minimal UI"""
    
    def __init__(self, width=640, height=480, speed=SPEED, display_surface=None):
        """Initialize with speed parameter"""
        super().__init__(width, height, display_surface, speed)
        
    def play_step(self, direction=None):
        """Modified play_step that accepts external direction input"""
        # Save current direction
        if direction is not None:
            self.direction = direction
        
        # Move snake
        self._move(self.direction)
        self.snake.insert(0, self.head)
        
        # Check for game over
        game_over = False
        if self._is_collision():
            game_over = True
            # Use sound_manager instead of direct sound
            from src.utils.sound_manager import play_sound
            play_sound("game_over")
            return game_over, self.score
            
        # Check if snake eats food
        if self.head == self.food:
            # Use sound_manager for eat sound
            from src.utils.sound_manager import play_sound
            play_sound("eat")
            
            self.score += 1
            self._place_food()
            
            # Check if level up should be played
            if self.score % 10 == 0 and self.score > 0:
                play_sound("level_up")
        else:
            self.snake.pop()
            
        self._update_ui_simple()
        self.clock.tick(self.speed)
        return game_over, self.score
        
    def _is_collision(self, pt=None):
        """Override collision detection to implement without sound effects"""
        if pt is None:
            pt = self.head
            
        # Hit boundary
        if pt.x > self.width - BLOCK_SIZE or pt.x < 0 or pt.y > self.height - BLOCK_SIZE or pt.y < 0:
            return True
            
        # Hit snake body
        if pt in self.snake[1:]:
            return True
            
        return False

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

class VSAIGameNoFlip(VSAIGame):
    def _update_ui(self):
        """Override to provide minimal UI without display flip"""
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
        # No pygame.display.flip() call here

    def _show_level_up(self):
        """Override to prevent double level-up animations"""
        pass  # Do nothing - the effect is handled by the parent function

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

# Function to load player position preference
def get_player_position():
    from src.utils.settings_manager import get_setting
    return get_setting("gameplay", "player_position", "right")


from src.utils.settings_manager import set_setting

def save_player_position(position):
    """Save player position preference using the unified config system"""
    # Update the unified configuration system
    try:
        import src.ui.shared_globals as globals_module
        
        # Set the position in shared_globals for access at program exit
        globals_module.player_position = position
        
        # Use the settings manager to save directly
        set_setting("gameplay", "player_position", position)
        return True
    except Exception as e:
        print(f"Error saving player position: {e}")
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
    
    # 1) Set up window dimensions that maintain the grid alignment
    game_w = 640  # Keep width the same
    game_h = 640  # Make height a clean multiple of BLOCK_SIZE (20px)
    screen_width = game_w * 2   # 1280px
    screen_height = game_h + 80 # 720px total (640 for game + 80 for header/footer)
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("AI Serpentis - Player vs AI")
    
    # Header is now 60px and footer is 20px (total 80px non-game area)
    header_height = 60
    footer_height = 20
    
    # Create permanent UI elements to avoid flickering
    # Permanent background for the entire screen
    permanent_bg = pygame.Surface((screen_width, screen_height))
    permanent_bg.fill((0, 0, 0))
    
    # Permanent header area for scores
    header_area = pygame.Surface((screen_width, header_height))
    header_area.fill((0, 0, 35))  # Dark blue background
    
    # Create footer area for controls
    footer_area = pygame.Surface((screen_width, footer_height))
    footer_area.fill((0, 0, 35))  # Match header color
    
    # Make divider wider and more visible
    divider_width = 8  # Increased from 4 to 8 for better visibility
    divider_x = screen_width // 2 - divider_width // 2
    divider = pygame.Surface((divider_width, screen_height))
    divider.fill((150, 150, 200))  # Light blue color
    
    # Load player position preference
    player_position = get_player_position()
    
    # 2) Create two sub-surfaces for the games based on player position
    if player_position == "right":
        player_surf = screen.subsurface(pygame.Rect(game_w, header_height, game_w, game_h))
        ai_surf = screen.subsurface(pygame.Rect(0, header_height, game_w, game_h))
    else:
        player_surf = screen.subsurface(pygame.Rect(0, header_height, game_w, game_h))
        ai_surf = screen.subsurface(pygame.Rect(game_w, header_height, game_w, game_h))
    
    # Load fonts with error handling
    try:
        main_font = pygame.font.Font("assets/fonts/game_over.ttf", 64)  # LARGER score font
        small_font = pygame.font.Font("assets/fonts/game_over.ttf", 36)  # Increased from 28 to 36
        labels_font = pygame.font.Font("assets/fonts/game_over.ttf", 42)  # New larger font for YOU/AI labels
    except FileNotFoundError:
        print("Warning: Font file not found. Using system fonts.")
        main_font = pygame.font.SysFont("Arial", 64)  
        small_font = pygame.font.SysFont("Arial", 36)  # Increased from 28 to 36
        labels_font = pygame.font.SysFont("Arial", 42)  # New larger font for YOU/AI labels
    
    # Setup AI agent model
    model = Linear_QNet(11, 256, 3)
    
    # Try multiple model loading paths with better error handling
    try:
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
    class VSPlayerGameNoFlip(VSPlayerGame):
        def _update_ui_simple(self):
            """A minimal UI update that doesn't flip the display"""
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
            # No pygame.display.flip() call here
    
    class VSAIGameNoFlip(VSAIGame):
        def _update_ui(self):
            """Override to provide minimal UI without display flip"""
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
            # No pygame.display.flip() call here
    
        def _show_level_up(self):
            """Override to prevent double level-up animations"""
            pass  # Do nothing - the effect is handled by the parent function
    
    # Create permanent UI elements with more elements pre-rendered
    permanent_bg = pygame.Surface((screen_width, screen_height))
    permanent_bg.fill((0, 0, 0))
    
    # Create a more permanent header with divider included
    header_area = pygame.Surface((screen_width, 60))
    header_area.fill((0, 0, 35))  # Dark blue background
    
    # Draw divider on the permanent background AND header
    divider = pygame.Surface((divider_width, screen_height))
    divider.fill((150, 150, 200))  # Light blue color
    
    # Use the modified game classes
    player_game = VSPlayerGameNoFlip(width=game_w, height=game_h, display_surface=player_surf)
    ai_game = VSAIGameNoFlip(width=game_w, height=game_h, display_surface=ai_surf)
    
    # Get background theme from unified config system
    from src.utils.settings_manager import get_setting
    background_theme = get_setting("appearance", "background_theme", "dark")
    
    # Apply the background theme to both games
    player_game.background_theme = background_theme
    ai_game.background_theme = background_theme
    
    # Apply customization settings to both games
    player_snake_theme = customization.get_current_snake_theme()  # Get theme for player
    ai_snake_theme = customization.get_current_snake_theme()      # Get separate theme for AI
    food_theme = customization.get_current_food_theme()
    
    # If random theme is selected, ensure player and AI have different colors
    if hasattr(player_snake_theme, 'name') and player_snake_theme.name == "Random":
        # For Random theme, we need to ensure they're visually distinct
        # Create copies so we can modify them independently
        player_snake_theme = player_snake_theme.copy()
        ai_snake_theme = ai_snake_theme.copy()
        
        # Force different random colors by regenerating one of them
        ai_snake_theme.new_random_color()
        
        # Make sure they're sufficiently different - regenerate if too similar
        def color_distance(c1, c2):
            return sum((a-b)**2 for a, b in zip(c1, c2))**0.5
        
        # Keep regenerating until themes are visually distinct enough
        while color_distance(player_snake_theme.head_color, ai_snake_theme.head_color) < 100:
            ai_snake_theme.new_random_color()
    
    # Apply the themes to the games
    player_game.snake_theme = player_snake_theme
    player_game.food_theme = food_theme
    
    ai_game.snake_theme = ai_snake_theme
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
    
    # Pre-render label texts to avoid recreating them every frame
    if player_position == "right":
        player_label = labels_font.render("YOU", True, (220, 220, 220))  # Using larger font
        ai_label = labels_font.render("AI", True, (220, 220, 220))  # Using larger font
        player_label_pos = (screen_width - 120, 8)  # Adjusted position for larger font
        ai_label_pos = (120, 8)  # Adjusted position for larger font
        # Position controls text within the footer area
        controls_text = small_font.render("ESC - Menu | P - Pause", True, (200, 200, 200))
        controls_pos = (screen_width - controls_text.get_width() - 10, screen_height - footer_height + 0)
    else:
        player_label = labels_font.render("YOU", True, (220, 220, 220))  # Using larger font
        ai_label = labels_font.render("AI", True, (220, 220, 220))  # Using larger font
        player_label_pos = (120, 8)  # Adjusted position for larger font
        ai_label_pos = (screen_width - 120, 8)  # Adjusted position for larger font
        # Position controls text within the footer area
        controls_text = small_font.render("ESC - Menu | P - Pause", True, (200, 200, 200))
        controls_pos = (10, screen_height - footer_height + 0)
    
    # Pre-render the static UI elements to prevent flickering
    # Add the labels to the header
    header_area.blit(player_label, player_label_pos)
    header_area.blit(ai_label, ai_label_pos)
    
    # Define a function to show level up animation
    def show_level_up(is_player):
        """Show level up animation for either player or AI"""
        # Determine which side to show the effect on
        side = "right" if (is_player and player_position == "right") or \
                        (not is_player and player_position == "left") else "left"
        
        # Get the surface and position based on side
        surface = player_surf if is_player else ai_surf
        overlay_x = game_w if side == "right" else 0
        
        # Create semi-transparent overlay for the specific game area
        overlay = pygame.Surface((game_w, game_h), pygame.SRCALPHA)
        
        # Choose color based on theme
        if background_theme == "dark":
            overlay_color = (255, 255, 0, 80)  # Yellow semi-transparent for dark mode
            text_color = (255, 255, 0)  # Bright yellow for dark mode
        else:
            overlay_color = (0, 100, 0, 80)  # Green semi-transparent for light mode
            text_color = (0, 120, 0)  # Dark green for light mode
            
        overlay.fill(overlay_color)
        
        # Draw overlay directly on the game surface
        surface.blit(overlay, (0, 0))
        
        # Create and position the level up text
        level_text = main_font.render("LEVEL UP!", True, text_color)
        text_rect = level_text.get_rect(center=(game_w//2, game_h//2))
        surface.blit(level_text, text_rect)
        
        # Update display to show the level up effect
        pygame.display.flip()
        
        # Pause briefly to show the effect
        pygame.time.delay(500)
    
    # Add countdown before starting the game
    def show_countdown():
        """Display 5-4-3-2-1 countdown before game starts. Return False if canceled."""
        
        def cleanup_sounds():
            # Stop all currently playing sound effects
            pygame.mixer.stop()  # This stops all playing channels
            
        # Create semi-transparent overlay for the countdown
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark semi-transparent background
        
        # Show "Get Ready" text and play countdown sound immediately
        ready_text = main_font.render("Get Ready!", True, (255, 255, 255))
        screen.blit(overlay, (0, 0))
        screen.blit(ready_text, (screen_width//2 - ready_text.get_width()//2, screen_height//2 - 100))
        
        # Play the countdown tick sound using sound_manager
        play_sound("countdown_tick")
        
        pygame.display.flip()
        
        # Check for escape key press before starting countdown
        pygame.event.clear()  # Clear any pending events
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 500:  # Short delay before starting the count
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cleanup_sounds()  # Stop sounds before quitting
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    cleanup_sounds()  # Stop sounds before returning
                    return False  # Player wants to exit
            pygame.time.delay(50)  # Small delay to prevent CPU hogging
        
        # The countdown audio is approximately 5 seconds
        # We'll sync our visuals to match this timing
        for count in range(5, 0, -1):
            # Draw the number
            count_text = main_font.render(str(count), True, (255, 255, 255))
            count_rect = count_text.get_rect(center=(screen_width//2, screen_height//2))
            
            # Clear the screen and redraw
            screen.blit(overlay, (0, 0))
            screen.blit(ready_text, (screen_width//2 - ready_text.get_width()//2, screen_height//2 - 100))
            screen.blit(count_text, count_rect)
            
            pygame.display.flip()
            
            # Check for escape key press during each number
            start_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start_time < 1100:  # Matches the timing in the audio file
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        cleanup_sounds()  # Stop sounds before quitting
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        cleanup_sounds()  # Stop sounds before returning
                        return False  # Player wants to exit
                pygame.time.delay(50)  # Small delay to prevent CPU hogging
        
        # Show "GO!" text when countdown completes
        go_text = main_font.render("GO!", True, (50, 255, 50))  # Green text
        go_rect = go_text.get_rect(center=(screen_width//2, screen_height//2))
        screen.blit(overlay, (0, 0))
        screen.blit(go_text, go_rect)
        
        # Play begin sound using sound_manager
        play_sound("pvai_begin")
            
        pygame.display.flip()
        
        # Check for escape key press during "GO!"
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 700:  # Brief pause on "GO!"
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cleanup_sounds()  # Stop sounds before quitting
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    cleanup_sounds()  # Stop sounds before returning
                    return False  # Player wants to exit
            pygame.time.delay(50)  # Small delay to prevent CPU hogging
        
        return True  # Countdown completed successfully
    
    # Show countdown before starting the game
    if not show_countdown():
        return
    
    # Game loop
    running = True
    while running:
        # a) Handle shared events and player movement
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                # Handle escape key - now also pauses
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    paused = True
                    
                    # Draw pause overlay
                    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))  # Semi-transparent black
                    screen.blit(overlay, (0, 0))
                    
                    pause_text = main_font.render("PAUSED", True, (255, 255, 255))
                    screen.blit(pause_text, (screen_width//2 - pause_text.get_width()//2, screen_height//2 - 30))
                    
                    # Updated instructions
                    continue_text = small_font.render("Press R to resume, ESC to exit", True, (200, 200, 200))
                    screen.blit(continue_text, (screen_width//2 - continue_text.get_width()//2, screen_height//2 + 30))
                    
                    pygame.display.flip()
                    
                    # Pause loop
                    while paused:
                        for pause_event in pygame.event.get():
                            if pause_event.type == pygame.QUIT:
                                pygame.quit()
                                return
                            
                            if pause_event.type == pygame.KEYDOWN:
                                if pause_event.key == pygame.K_r:  # R to resume
                                    paused = False
                                elif pause_event.key == pygame.K_ESCAPE:  # ESC to exit
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
        
        # Important: Always redraw everything in the correct order to prevent flickering
        # 1. Draw the permanent background 
        screen.blit(permanent_bg, (0, 0))
        
        # 2. Draw the central divider
        screen.blit(divider, (divider_x, 0))
        
        # 3. Draw the header area with pre-rendered labels
        screen.blit(header_area, (0, 0))
        
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
                        # Ignore screenshot keys
                        if is_screenshot_key(wait_event.key):
                            continue
                            
                        # Any other key press returns to menu
                        running = False
                        waiting_for_key = False
                
                pygame.time.delay(100)
            
            continue
        
        # b) Process game steps if not game over
        if not player_game_over:
            # Save previous score to check for level up
            prev_player_score = player_score
            
            # Process player game step with the current player direction
            player_game_over, player_score = player_game.play_step(player_direction)
            
            # Play sounds for player and show level up if needed
            if player_score > prev_player_score:  # Score increased
                play_sound("eat")  # Instead of eat_sound.play()
                if player_score % 10 == 0 and player_score > 0:
                    play_sound("level_up")  # Instead of level_up_sound.play()
                    show_level_up(is_player=True)  # Show level up animation for player
            
            if player_game_over:
                play_sound("game_over")  # Instead of game_over_sound.play()
        
        if not ai_game_over:
            # Save previous score to check for level up
            prev_ai_score = ai_score
            
            # Get AI state and action
            state = agent.get_state(ai_game)
            action = agent.get_action(state)
            
            # Process AI game step
            _, ai_game_over, ai_score = ai_game.play_step(action)
            
            # Play sounds for AI and show level up if needed
            if ai_score > prev_ai_score:  # Score increased
                play_sound("eat")  # Instead of eat_sound.play()
                if ai_score % 10 == 0 and ai_score > 0:
                    play_sound("level_up")  # Instead of level_up_sound.play()
                    show_level_up(is_player=False)  # Show level up animation for AI
        
        # Draw score numbers that change each frame
        player_txt = main_font.render(f"{player_score}", True, (255, 255, 255))
        ai_txt = main_font.render(f"{ai_score}", True, (255, 255, 255))
        
        # Position score displays based on player position
        if player_position == "right":
            screen.blit(player_txt, (screen_width - game_w//2 - player_txt.get_width()//2, 5))  # Player on right
            screen.blit(ai_txt, (game_w//2 - ai_txt.get_width()//2, 5))  # AI on left
        else:
            screen.blit(player_txt, (game_w//2 - player_txt.get_width()//2, 5))  # Player on left
            screen.blit(ai_txt, (screen_width - game_w//2 - ai_txt.get_width()//2, 5))  # AI on right
            
        # 4. IMPORTANT: Draw the divider AFTER the games have updated their surfaces
        # but BEFORE drawing game over text
        screen.blit(divider, (divider_x, 0))
        
        # Draw controls in the footer area
        screen.blit(footer_area, (0, screen_height - footer_height))
        screen.blit(controls_text, controls_pos)  # Only render controls text once, in the footer
        
        # Draw game over text if needed
        if player_game_over:
            game_over_surf = main_font.render("GAME OVER", True, (255, 50, 50))
            player_surf.blit(game_over_surf, (game_w//2 - game_over_surf.get_width()//2, game_h//2))
        
        if ai_game_over:
            game_over_surf = main_font.render("GAME OVER", True, (255, 50, 50))
            ai_surf.blit(game_over_surf, (game_w//2 - game_over_surf.get_width()//2, game_h//2))
        
        # Update display and control frame rate
        pygame.display.flip()
        clock.tick(15)  # Lower frame rate for fair gameplay
    
    # Game is over when we reach this point - save scores
    print(f"Game ended - Player: {player_score}, AI: {ai_score}")
    
    # Save player's final score
    if player_score > 0:  # Only save non-zero scores
        is_player_new_high = save_vs_high_score("player", player_score)
        print(f"Player score {player_score} saved.{' New high score!' if is_player_new_high else ''}")
    
    # Save AI's final score 
    if ai_score > 0:  # Only save non-zero scores
        is_ai_new_high = save_vs_high_score("ai", ai_score)
        print(f"AI score {ai_score} saved.{' New high score!' if is_ai_new_high else ''}")
    
    # Reset display mode for returning to main menu
    pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("AI Serpentis")

if __name__ == "__main__":
    player_vs_ai()