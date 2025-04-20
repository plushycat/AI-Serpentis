import sys
import os
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import torch
import random
import numpy as np
from collections import deque
import json
import datetime
from src.game.fibonacci_ai import FibonacciGameAI, Point, RIGHT, LEFT, UP, DOWN, BLOCK_SIZE
from src.ai.model import Linear_QNet, QTrainer
from src.utils.plotter import plot

# Hyperparameters
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001
GAMMA = 0.9  # discount rate

# Checkpoint directory
CHECKPOINT_DIR = "data/checkpoints"
MODEL_DIR = "data/models"
PLOT_DIR = "data/plots"

for directory in [CHECKPOINT_DIR, MODEL_DIR, PLOT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class FibonacciAgent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = GAMMA  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        
        # Define state size: 
        # 11 states from snake AI + 2 for Fibonacci info (current value and next growth)
        self.input_size = 13
        self.hidden_size = 256  # Increased for more complex patterns
        self.output_size = 3  # [straight, right, left]
        
        self.model = Linear_QNet(self.input_size, self.hidden_size, self.output_size)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        
        # Statistics
        self.total_score = 0
        self.record = 0
        self.fib_record = 0  # Highest fibonacci score
        
        # Try to load checkpoint if exists
        self._try_load_checkpoint()
        
    def _try_load_checkpoint(self):
        """Tries to load training state from checkpoint files."""
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "fibonacci_training_state.json")
        model_file = os.path.join(CHECKPOINT_DIR, "fibonacci_checkpoint_model.pth")
        
        if os.path.exists(checkpoint_file) and os.path.exists(model_file):
            try:
                # Load training state
                with open(checkpoint_file, 'r') as f:
                    state = json.load(f)
                self.n_games = state.get('n_games', 0)
                self.total_score = state.get('total_score', 0)
                self.record = state.get('record', 0)
                self.fib_record = state.get('fib_record', 0)
                print(f"Loaded Fibonacci training state: Games={self.n_games}, Record={self.record}, Fib Record={self.fib_record}")
                
                # Load model
                self.model.load_state_dict(torch.load(model_file))
                print("Loaded Fibonacci model state from checkpoint")
                
                # Load memory if available (optional, may be large)
                memory_file = os.path.join(CHECKPOINT_DIR, "fibonacci_memory.pth")
                if os.path.exists(memory_file):
                    try:
                        loaded_memory = torch.load(memory_file)
                        self.memory = loaded_memory
                        print(f"Loaded Fibonacci replay memory with {len(self.memory)} experiences")
                    except Exception as e:
                        print(f"Error loading memory: {e}")
                
                return True
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
        
        return False
        
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
        self.epsilon = 80 - self.n_games
        final_move = [0, 0, 0]
        
        # More exploration in the beginning
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1
            
        return final_move
        
    def save_checkpoint(self):
        """Save training state to continue later"""
        # Create directories if they don't exist
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        
        # Save training state
        state = {
            'n_games': self.n_games,
            'total_score': self.total_score,
            'record': self.record,
            'fib_record': self.fib_record
        }
        
        with open(os.path.join(CHECKPOINT_DIR, "fibonacci_training_state.json"), 'w') as f:
            json.dump(state, f)
            
        # Save model
        torch.save(self.model.state_dict(), os.path.join(CHECKPOINT_DIR, "fibonacci_checkpoint_model.pth"))
        
        # Optionally save memory (can be large)
        torch.save(self.memory, os.path.join(CHECKPOINT_DIR, "fibonacci_memory.pth"))
        
        print("Checkpoint saved!")
        
    def save_trained_model(self):
        """Save the final trained model"""
        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save(self.model.state_dict(), os.path.join(MODEL_DIR, f"fibonacci_model_{self.n_games}games.pth"))
        print(f"Model saved after {self.n_games} games!")

def train():
    # Setup plotting
    plot_scores = []
    plot_fib_scores = []  # Plot Fibonacci scores separately
    plot_mean_scores = []
    total_score = 0
    record = 0
    fib_record = 0
    
    # Create agent and game
    agent = FibonacciAgent()
    game = FibonacciGameAI()
    
    # Load from previous training if available
    if agent.n_games > 0:
        total_score = agent.total_score
        record = agent.record
        fib_record = agent.fib_record
        
        # Try to load existing plot data
        plot_file = os.path.join(PLOT_DIR, "fibonacci_training_data.json")
        if os.path.exists(plot_file):
            try:
                with open(plot_file, 'r') as f:
                    plot_data = json.load(f)
                    plot_scores = plot_data.get('scores', [])
                    plot_fib_scores = plot_data.get('fib_scores', [])
                    plot_mean_scores = plot_data.get('mean_scores', [])
                    print(f"Loaded plot data with {len(plot_scores)} records")
            except Exception as e:
                print(f"Error loading plot data: {e}")
    
    # Training loop
    while True:
        # Get current state
        state_old = agent.get_state(game)
        
        # Get action
        final_move = agent.get_action(state_old)
        
        # Perform action and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)
        
        # Train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)
        
        # Remember
        agent.remember(state_old, final_move, reward, state_new, done)
        
        if done:
            # Train long memory (replay memory) and reset game
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()
            
            # Track records
            if score > record:
                record = score
                agent.record = record
                agent.save_trained_model()
                
            if game.fib_score > fib_record:
                fib_record = game.fib_score
                agent.fib_record = fib_record
            
            print(f"Game {agent.n_games}, Score {score}, Fib Score: {game.fib_score}, Record: {record}")
            
            # Update plots
            plot_scores.append(score)
            plot_fib_scores.append(game.fib_score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            
            # Save plot data
            os.makedirs(PLOT_DIR, exist_ok=True)
            plot_data = {
                'scores': plot_scores,
                'fib_scores': plot_fib_scores,
                'mean_scores': plot_mean_scores
            }
            with open(os.path.join(PLOT_DIR, "fibonacci_training_data.json"), 'w') as f:
                json.dump(plot_data, f)
            
            # Update plot visualization
            plot(plot_scores, plot_mean_scores)
            
            # Save checkpoint every 10 games
            if agent.n_games % 10 == 0:
                agent.total_score = total_score
                agent.save_checkpoint()

if __name__ == '__main__':
    train()