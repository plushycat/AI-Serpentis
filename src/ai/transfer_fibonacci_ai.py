import sys
import os
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import torch
import pygame
import time
import argparse
import random
import numpy as np
from collections import deque
import json

from src.ai.model import Linear_QNet, QTrainer
from src.game.fibonacci_ai import FibonacciGameAI, Point, RIGHT, LEFT, UP, DOWN, BLOCK_SIZE
from src.utils.plotter import plot

# Hyperparameters for fine-tuning
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.0005  # Lower learning rate for fine-tuning
GAMMA = 0.9  # discount rate

# Directories
CHECKPOINT_DIR = "data/checkpoints"
MODEL_DIR = "data/models"
PLOT_DIR = "data/plots"

for directory in [CHECKPOINT_DIR, MODEL_DIR, PLOT_DIR]:
    os.makedirs(directory, exist_ok=True)

def transfer_weights(classic_model_path="data/models/model.pth"):
    """
    Load weights from classic snake model and transfer to expanded Fibonacci model
    """
    # Load classic model (11 inputs, 256 hidden, 3 outputs)
    classic_model = Linear_QNet(11, 256, 3)
    
    try:
        classic_model.load_state_dict(torch.load(classic_model_path))
        print(f"Loaded classic model from {classic_model_path}")
    except:
        print(f"Could not load classic model from {classic_model_path}. Using random weights.")
        return Linear_QNet(13, 256, 3)  # Return a new model with random weights
    
    # Create new Fibonacci model with expanded input size (13 inputs)
    fib_model = Linear_QNet(13, 256, 3)
    
    # Transfer weights for shared parts
    with torch.no_grad():
        # Copy weights for the first 11 inputs (keep the same connections)
        fib_model.linear1.weight[:, :11] = classic_model.linear1.weight
        
        # Initialize the weights for the 2 new inputs with small random values
        # This helps them integrate smoothly with existing weights
        nn_gain = torch.nn.init.calculate_gain('relu')
        std = nn_gain / np.sqrt(13)
        fib_model.linear1.weight[:, 11:].data.normal_(0, std)
        
        # Copy bias terms
        fib_model.linear1.bias = classic_model.linear1.bias
        
        # Copy all weights for the hidden and output layers
        fib_model.linear2.weight = classic_model.linear2.weight
        fib_model.linear2.bias = classic_model.linear2.bias
        
    # Save the transferred model
    torch.save(fib_model.state_dict(), os.path.join(MODEL_DIR, "fibonacci_transferred_model.pth"))
    print(f"Transferred model saved to {os.path.join(MODEL_DIR, 'fibonacci_transferred_model.pth')}")
    
    return fib_model

class TransferredFibonacciAgent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 40  # Start with some randomness even with transferred model
        self.gamma = GAMMA
        self.memory = deque(maxlen=MAX_MEMORY)
        
        # Define state size for Fibonacci game
        self.input_size = 13
        self.hidden_size = 256
        self.output_size = 3  # [straight, right, left]
        
        # Load the transferred model or create a new one
        self.model = transfer_weights()
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        
        # Statistics
        self.total_score = 0
        self.record = 0
        self.fib_record = 0

    def get_state(self, game):
        head = game.snake[0]
        point_l = Point(head.x - BLOCK_SIZE, head.y)
        point_r = Point(head.x + BLOCK_SIZE, head.y)
        point_u = Point(head.x, head.y - BLOCK_SIZE)
        point_d = Point(head.x, head.y + BLOCK_SIZE)
        
        dir_l = game.direction == LEFT
        dir_r = game.direction == RIGHT
        dir_u = game.direction == UP
        dir_d = game.direction == DOWN
        
        # Get current and next Fibonacci values (normalized)
        max_fib = 144.0  # Maximum value in initial sequence
        current_fib = game.get_fibonacci_at_position(max(0, game.fib_index - 1))
        next_fib = game.get_fibonacci_at_position(game.fib_index)
        
        state = [
            # Danger straight
            (dir_r and game.is_collision(point_r)) or
            (dir_l and game.is_collision(point_l)) or
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)),
            
            # Danger right
            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_l and game.is_collision(point_u)) or
            (dir_r and game.is_collision(point_d)),
            
            # Danger left
            (dir_d and game.is_collision(point_r)) or
            (dir_u and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_u)) or
            (dir_l and game.is_collision(point_d)),
            
            # Move direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,
            
            # Food location
            game.food.x < head.x,  # food left
            game.food.x > head.x,  # food right
            game.food.y < head.y,  # food up
            game.food.y > head.y,  # food down
            
            # Fibonacci-specific inputs (normalized)
            current_fib / max_fib,  # Current Fibonacci value
            next_fib / max_fib      # Next growth value
        ]
        
        return np.array(state, dtype=int)
        
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        
    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory
            
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        
    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)
        
    def get_action(self, state):
        # Random moves: tradeoff exploration / exploitation
        self.epsilon = max(0, 40 - self.n_games)  # Decrease epsilon as training progresses
        final_move = [0, 0, 0]
        
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1
            
        return final_move
        
    def save_model(self):
        """Save the model after training"""
        model_filename = f"fibonacci_transferred_model_finetuned_{self.n_games}.pth"
        model_path = os.path.join(MODEL_DIR, model_filename)
        torch.save(self.model.state_dict(), model_path)
        print(f"Model saved to {model_path}")

def finetune():
    """Fine-tune the transferred model for the Fibonacci game"""
    plot_scores = []
    plot_mean_scores = []
    plot_fib_scores = []
    total_score = 0
    record = 0
    fib_record = 0
    
    agent = TransferredFibonacciAgent()
    game = FibonacciGameAI()
    
    print("Starting fine-tuning of transferred model...")
    print("Press CTRL+C to stop training and save the model")
    
    try:
        while True:
            # Get old state
            state_old = agent.get_state(game)
            
            # Get move
            final_move = agent.get_action(state_old)
            
            # Perform move and get new state
            reward, done, score = game.play_step(final_move)
            state_new = agent.get_state(game)
            
            # Train short memory
            agent.train_short_memory(state_old, final_move, reward, state_new, done)
            
            # Remember
            agent.remember(state_old, final_move, reward, state_new, done)
            
            if done:
                # Train long memory (experience replay)
                game.reset()
                agent.n_games += 1
                agent.train_long_memory()
                
                # Update records
                if score > record:
                    record = score
                    agent.save_model()  # Save model when record is broken
                
                if game.fib_score > fib_record:
                    fib_record = game.fib_score
                
                # Track statistics
                print(f"Game: {agent.n_games}, Score: {score}, Fibonacci Score: {game.fib_score}, Record: {record}")
                
                # Update plots
                plot_scores.append(score)
                plot_fib_scores.append(game.fib_score)
                total_score += score
                mean_score = total_score / agent.n_games
                plot_mean_scores.append(mean_score)
                
                # Create plot
                plot(plot_scores, plot_mean_scores)
                
                # Save checkpoint every 25 games
                if agent.n_games % 25 == 0:
                    agent.save_model()
                    
    except KeyboardInterrupt:
        print("Training interrupted. Saving final model...")
        agent.save_model()
        pygame.quit()

def watch():
    """Watch the transferred AI play"""
    # Initialize agent
    agent = TransferredFibonacciAgent()
    
    # Get the path to the transferred model (either original or fine-tuned)
    model_files = [f for f in os.listdir(MODEL_DIR) if f.startswith('fibonacci_transferred_model')]
    
    if not model_files:
        print("No transferred model found. Please run transfer or finetune first.")
        return
    
    # Use fine-tuned model if available, otherwise use base transferred model
    fine_tuned = [f for f in model_files if 'finetuned' in f]
    if fine_tuned:
        # Get the one with the highest game count
        model_file = max(fine_tuned, key=lambda x: int(x.split('_')[-1].split('.')[0]) if x.split('_')[-1].split('.')[0].isdigit() else 0)
    else:
        model_file = "fibonacci_transferred_model.pth"
        
    model_path = os.path.join(MODEL_DIR, model_file)
    print(f"Loading model: {model_file}")
    
    # Load the model
    agent.model.load_state_dict(torch.load(model_path))
    agent.epsilon = 0  # No random moves when watching
    
    # Initialize game with viewer mode
    game = FibonacciGameAI(width=1280, height=720)
    game.viewing_mode = True
    
    print("Watching AI play. Press ESC to exit.")
    
    # Main game loop
    while True:
        # Get current state
        state = agent.get_state(game)
        
        # Get AI move
        final_move = agent.get_action(state)
        
        # Perform move and get new state
        reward, done, score = game.play_step(final_move)
        
        # Reset game if over
        if done:
            game.reset()
            time.sleep(1)
            
        # Handle exit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                    
        # Control game speed for viewing
        game.clock.tick(15)  # Slower for watching (adjust as needed)

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Transfer learning for Fibonacci Snake AI")
    parser.add_argument('--transfer', action='store_true', help='Transfer weights from classic model')
    parser.add_argument('--finetune', action='store_true', help='Fine-tune the transferred model')
    parser.add_argument('--watch', action='store_true', help='Watch the transferred AI play')
    parser.add_argument('--model', type=str, default="data/models/model.pth", help='Path to classic model')
    
    args = parser.parse_args()
    
    if args.transfer:
        transfer_weights(args.model)
    elif args.finetune:
        finetune()
    elif args.watch:
        watch()
    else:
        # Show menu if no arguments provided
        print("Fibonacci AI Transfer Learning")
        print("1. Transfer weights from classic model")
        print("2. Fine-tune transferred model")
        print("3. Watch transferred AI play")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ")
        
        if choice == '1':
            model_path = input("Enter classic model path (or press Enter for default): ")
            if not model_path.strip():
                model_path = "data/models/model.pth"
            transfer_weights(model_path)
        elif choice == '2':
            finetune()
        elif choice == '3':
            watch()
        else:
            print("Exiting...")

if __name__ == "__main__":
    main()