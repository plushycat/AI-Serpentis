import torch
import pygame
from snake_ai import SnakeGameAI
from model import Linear_QNet
from agent import Agent

def watch_ai_play():
    """Launches the AI-controlled Snake game using the pre-trained model."""
    # Load the trained model
    model = Linear_QNet(11, 256, 3)
    try:
        model.load_state_dict(torch.load("model/model.pth"))
        model.eval()
    except FileNotFoundError:
        print("Error: Pre-trained model file not found. Using a fresh model.")
        # Continue with untrained model

    # Initialize the AI game with 1280x720 resolution
    game = SnakeGameAI(width=1280, height=720)  # Set the resolution explicitly
    agent = Agent()
    agent.model = model  # Use the loaded model
    agent.epsilon = 0  # Disable exploration for display (always exploit)

    # Loop until game over
    while True:
        # Get the current state of the game
        state_old = agent.get_state(game)

        # Use the model to decide the next move
        final_move = agent.get_action(state_old)

        # Perform the action and observe the result
        reward, done, score = game.play_step(final_move)

        # If the game is over, print the score and exit the loop
        if done:
            print(f"AI Game Over! Score: {score}")
            break
    
    # Ensure the display is still available for the main menu
    pygame.display.set_mode((1280, 720))