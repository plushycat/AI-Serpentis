import sys
import os
import pygame
from src.ai.agent import Agent
from src.ai.model import Linear_QNet
from src.game.snake_game import SnakeGame
from src.game.snake_ai import SnakeGameAI
from src.game.customization import customization

# Import all functions from the original main.py
# This maintains existing functionality while using the new structure
from src.ui.main import (
    home_page, 
    play_classic_game,
    watch_ai_play,
    settings_page,
    load_high_scores,
    save_high_score
)

if __name__ == "__main__":
    home_page()