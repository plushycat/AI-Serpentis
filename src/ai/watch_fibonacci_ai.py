import sys
import os
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import torch
import pygame
import time
from src.game.fibonacci_ai import FibonacciGameAI
# Change this import to use transfer_fibonacci_ai instead
from src.ai.transfer_fibonacci_ai import TransferredFibonacciAgent, watch
from src.ai.model import Linear_QNet

def watch_ai():
    """Wrapper function for the existing watch function"""
    watch()  # Simply call the existing watch function

if __name__ == '__main__':
    watch_ai()