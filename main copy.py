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

# Import all functions from the original main.py
# This maintains existing functionality while using the newer file structure
from src.ui.old_main import (
    home_page, 
    play_classic_game,
    play_fibonacci_game,
    watch_ai_play,
    watch_fibonacci_ai_play,
    player_vs_ai,
    settings_page,
    load_high_scores,
    save_high_score
)

if __name__ == "__main__":
    home_page()