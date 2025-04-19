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
    """Save high score for vs mode using the unified system"""
    try:
        # Import the unified save function
        from src.ui.main import save_high_score
        # Call it with the proper formatted mode
        return save_high_score(f"vs.{player_type}", score)
    except ImportError:
        # Fallback to old method if import fails
        highscore_file = "data/stats/highscores.json"
        try:
            if os.path.exists(highscore_file):
                with open(highscore_file, 'r') as f:
                    high_scores = json.load(f)
            else:
                high_scores = {"classic": 0, "ai": 0, "vs": {"player": 0, "ai": 0}}
                os.makedirs(os.path.dirname(highscore_file), exist_ok=True)
                
            # Update if it's a new high score
            if score > high_scores.get("vs", {}).get(player_type, 0):
                if "vs" not in high_scores:
                    high_scores["vs"] = {}
                high_scores["vs"][player_type] = score
                
                # Save updated high scores
                with open(highscore_file, 'w') as f:
                    json.dump(high_scores, f, indent=2)
                return True  # Indicates this is a new high score
            return False
        except Exception as e:
            print(f"Error saving high score: {e}")
            return False

# Function to load player position preference
def get_player_position():
    """Get player position preference (left or right) from the unified config system"""
    # Use the unified configuration system
    try:
        from src.ui.main import load_config
        config = load_config()
        return config.get("gameplay", {}).get("player_position", "left")
    except (ImportError, Exception) as e:
        print(f"Error loading player position from unified config: {e}")
        
        # Legacy fallback in case the unified system fails
        try:
            config_file = "statics/game_settings.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return data.get("gameplay", {}).get("player_position", "left")
        except Exception as e:
            print(f"Error in fallback position loading: {e}")
        
        # Default to left if all else fails
        return "left"

# Function to save player position preference
def save_player_position(position):
    """Save player position preference using the unified config system"""
    # Update the unified configuration system
    try:
        from src.ui.main import load_config, save_config
        config = load_config()
        config["gameplay"]["player_position"] = position
        save_config(config)
        return True
    except (ImportError, Exception) as e:
        print(f"Error saving player position to unified config: {e}")
        
        # Legacy fallback in case the unified system fails
        try:
            config_file = "statics/game_settings.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                if "gameplay" not in data:
                    data["gameplay"] = {}
                data["gameplay"]["player_position"] = position
                
                with open(config_file, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
        except Exception as e:
            print(f"Error in fallback position saving: {e}")
        
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
    
    # Get background theme - handle the missing method error first
    try:
        # Try to access the background theme from the UI module
        from src.ui.main import background_theme as ui_background_theme
        background_theme = ui_background_theme
    except ImportError:
        # If we can't import it, try to load it from customization.json
        try:
            with open("statics/customization.json", "r") as f:
                config = json.load(f)
                background_theme = config.get("background_theme", "dark")
        except:
            # Default to dark theme if all else fails
            background_theme = "dark"
    
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
    player_game.background_theme = background_theme  # Now background_theme is defined
    
    ai_game.snake_theme = ai_snake_theme
    ai_game.food_theme = food_theme
    ai_game.background_theme = background_theme
    
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
        # Try to load countdown sounds ONCE outside the loop
        try:
            tick_sound = pygame.mixer.Sound("assets/sounds/countdown.mp3")
            begin_sound = pygame.mixer.Sound("assets/sounds/pvai_begin.mp3")
            # Set volume to avoid being too loud
            tick_sound.set_volume(0.7)
            begin_sound.set_volume(0.8)
        except Exception as e:
            print(f"Warning: Could not load countdown sounds: {e}")
            tick_sound = None
            begin_sound = None
        
        # Helper function to stop sounds when exiting
        def cleanup_sounds():
            if tick_sound:
                tick_sound.stop()
            if begin_sound:
                begin_sound.stop()
            
        # Create semi-transparent overlay for the countdown
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark semi-transparent background
        
        # Show "Get Ready" text and play countdown sound immediately
        ready_text = main_font.render("Get Ready!", True, (255, 255, 255))
        screen.blit(overlay, (0, 0))
        screen.blit(ready_text, (screen_width//2 - ready_text.get_width()//2, screen_height//2 - 100))
        
        # Play the countdown tick sound IMMEDIATELY
        if tick_sound:
            tick_sound.play()
        
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
        
        # Play begin sound ONCE when the countdown finishes
        if begin_sound:
            begin_sound.play()
            
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
                        # Any key press returns to menu (previously only ESC did this)
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
                if eat_sound:
                    eat_sound.play()
                if player_score % 10 == 0 and player_score > 0:
                    if level_up_sound:
                        level_up_sound.play()
                    show_level_up(is_player=True)  # Show level up animation for player
            
            if player_game_over and game_over_sound:
                game_over_sound.play()
        
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
                if eat_sound:
                    eat_sound.play()
                if ai_score % 10 == 0 and ai_score > 0:
                    if level_up_sound:
                        level_up_sound.play()
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