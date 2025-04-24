import sys
import os
import pygame
from src.ai.agent import Agent
from src.ai.model import Linear_QNet
from src.game.snake_game import SnakeGame
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization
from src.ai.watch_fibonacci_ai import watch_ai as watch_fibonacci_ai
from src.ai.transfer_fibonacci_ai import finetune as train_fibonacci_ai

from src.utils.scores import load_high_scores, save_high_score, resort_all_high_scores

import pygame
import sys

# Initialize pygame first - before ANY imports
pygame.init()

# Import and initialize shared globals immediately
from src.ui.shared_globals import init_globals

# Initialize all shared resources
init_globals()

# Now it's safe to import home_page
def main():
    try:
        # Import here to avoid circular imports
        from src.ui.pages.home_page import home_page
        
        # Resort all high scores at startup to fix existing data
        resort_all_high_scores()
        
        home_page()
    except Exception as e:
        print(f"Error in main application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()