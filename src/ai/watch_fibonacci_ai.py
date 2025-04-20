import sys
import os
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import torch
import pygame
import time
from src.game.fibonacci_ai import FibonacciGameAI
from src.ai.fibonacci_agent import FibonacciAgent
from src.ai.model import Linear_QNet

def watch_ai():
    # Create a new agent to load the model
    agent = FibonacciAgent()
    
    # Initialize game with 1280x720 resolution for better viewing
    game = FibonacciGameAI(width=1280, height=720)
    game.viewing_mode = True  # Enable viewer mode UI
    
    # Check if trained model exists
    model_dir = "data/models"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    model_files = [f for f in os.listdir(model_dir) if f.startswith('fibonacci_model_') and f.endswith('.pth')]
    
    if not model_files:
        # Try checkpoint models if no final models exist
        model_dir = "data/checkpoints"
        model_files = [f for f in os.listdir(model_dir) if f == "fibonacci_checkpoint_model.pth"]
        
    if not model_files:
        print("No trained model found. Please train the AI first.")
        return
    
    # Get the latest model (with highest game count)
    if "fibonacci_checkpoint_model.pth" in model_files:
        latest_model = "fibonacci_checkpoint_model.pth"
    else:
        latest_model = max(model_files, key=lambda x: int(x.split('_')[2].split('games')[0]))
    
    model_path = os.path.join(model_dir, latest_model)
    print(f"Loading model: {latest_model}")
    
    # Load the model
    agent.model.load_state_dict(torch.load(model_path))
    agent.epsilon = 0  # No exploration, pure exploitation
    
    # Set game to play mode (slower for viewing)
    game.clock = pygame.time.Clock()
    
    # Main game loop
    while True:
        # Get old state
        state_old = agent.get_state(game)
        
        # Get move
        final_move = agent.get_action(state_old)
        
        # Perform move and get new state
        reward, done, score = game.play_step(final_move)
        
        # Handle game over
        if done:
            game.reset()
            time.sleep(1)  # Short pause before restarting
        
        # Control speed for viewing and handle exit
        game.clock.tick(15)  # Adjust speed as needed for viewing (lower = slower)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

if __name__ == '__main__':
    watch_ai()