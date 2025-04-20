import sys
import os
import pygame
from src.ai.agent import Agent
from src.ai.model import Linear_QNet
from src.game.snake_game import SnakeGame
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization
from src.ai.watch_fibonacci_ai import watch_ai as watch_fibonacci_ai
from src.ai.fibonacci_agent import train as train_fibonacci_ai

# Import all functions from the original main.py
# This maintains existing functionality while using the newer file structure
from src.ui.main import (
    home_page, 
    play_classic_game,
    watch_ai_play,
    settings_page,
    load_high_scores,
    save_high_score
)

# Add a button for Fibonacci AI mode
fibonacci_button = Button(
    screen, 
    "Fibonacci AI", 
    lambda: watch_fibonacci_ai()
)

# Add a button for training the Fibonacci AI
train_fibonacci_button = Button(
    screen, 
    "Train Fibonacci AI", 
    lambda: train_fibonacci_ai()
)

if __name__ == "__main__":
    home_page()