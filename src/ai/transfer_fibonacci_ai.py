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
import datetime

from src.ai.model import Linear_QNet, QTrainer
from src.game.fibonacci_ai import FibonacciGameAI, Point, RIGHT, LEFT, UP, DOWN, BLOCK_SIZE
from src.utils.fibonacci_plotter import plot  # Use the Fibonacci-specific plotter

# Hyperparameters for fine-tuning
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.0005  # Lower learning rate for fine-tuning
GAMMA = 0.9  # discount rate
MAX_GAMES = 1000  # Maximum games to train

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
    except Exception as e:
        print(f"Could not load classic model from {classic_model_path}: {e}")
        print("Using random weights instead.")
        return Linear_QNet(13, 256, 3)  # Return a new model with random weights
    
    # Create new Fibonacci model with expanded input size (13 inputs)
    fib_model = Linear_QNet(13, 256, 3)
    
    # Transfer weights for shared parts
    with torch.no_grad():
        # Copy weights for the first 11 inputs (keep the same connections)
        fib_model.linear1.weight[:, :11] = classic_model.linear1.weight
        
        # Initialize the weights for the 2 new inputs with small random values
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
        self.epsilon = 60  # Starting randomness
        self.gamma = GAMMA
        self.memory = deque(maxlen=MAX_MEMORY)
        
        # Define state size for Fibonacci game
        self.input_size = 13
        self.hidden_size = 256
        self.output_size = 3  # [straight, right, left]
        
        # Statistics
        self.total_score = 0
        self.record = 0
        self.fib_record = 0
        
        # Create model
        self.model = Linear_QNet(self.input_size, self.hidden_size, self.output_size)
        
        # Try to load checkpoint first
        if not self._try_load_checkpoint():
            # If no checkpoint, load or create the transferred model
            self.model = transfer_weights()
            
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        
    def _try_load_checkpoint(self):
        """Tries to load training state from checkpoint files."""
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "fibonacci_transferred_training_state.json")
        model_file = os.path.join(CHECKPOINT_DIR, "fibonacci_transferred_checkpoint_model.pth")
        
        if os.path.exists(checkpoint_file) and os.path.exists(model_file):
            try:
                # Load training state
                with open(checkpoint_file, 'r') as f:
                    state = json.load(f)
                self.n_games = state.get('n_games', 0)
                self.total_score = state.get('total_score', 0)
                self.record = state.get('record', 0)
                self.fib_record = state.get('fib_record', 0)
                print(f"Loaded Transferred Fibonacci training state: Games={self.n_games}, Record={self.record}, Fib Record={self.fib_record}")
                
                # Load model
                try:
                    self.model.load_state_dict(torch.load(model_file))
                    print("Loaded transferred Fibonacci model state from checkpoint")
                    return True
                except Exception as e:
                    print(f"Error loading model weights: {e}")
                    print("Attempting architecture compatibility fix...")
                    
                    # If we have a model with different input size, try to adapt
                    try:
                        # Load model dictionary
                        state_dict = torch.load(model_file)
                        input_layer_shape = state_dict['linear1.weight'].shape
                        
                        if input_layer_shape[1] != self.input_size:
                            print(f"Model has different input size: {input_layer_shape[1]} vs expected {self.input_size}")
                            print("Creating a new model with the correct architecture")
                            return False
                        else:
                            # Other error, but size matches
                            print("Unknown error loading model, using fresh model")
                            return False
                    except:
                        print("Could not examine model structure, using fresh model")
                        return False
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
                return False
        
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
        
        # Normalize Fibonacci values
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
        # Original epsilon-greedy strategy that worked well
        self.epsilon = max(0, 60 - self.n_games)  # Linear decay, ending at 60 games
        final_move = [0, 0, 0]
        
        if random.randint(0, 200) < self.epsilon:
            # Exploration: choose random action
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            # Exploitation: choose action from model
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
            'fib_record': self.fib_record,
            'timestamp': str(datetime.datetime.now())
        }
        
        with open(os.path.join(CHECKPOINT_DIR, "fibonacci_transferred_training_state.json"), 'w') as f:
            json.dump(state, f, indent=2)
            
        # Save model
        torch.save(self.model.state_dict(), os.path.join(CHECKPOINT_DIR, "fibonacci_transferred_checkpoint_model.pth"))
        
        print(f"Checkpoint saved! Games={self.n_games}, Record={self.record}, Fib Record={self.fib_record}")
        
    def save_trained_model(self):
        """Save the final trained model"""
        os.makedirs(MODEL_DIR, exist_ok=True)
        model_filename = f"fibonacci_transferred_model_finetuned_{self.n_games}_games.pth"
        model_path = os.path.join(MODEL_DIR, model_filename)
        torch.save(self.model.state_dict(), model_path)
        print(f"Model saved to {model_path}")

def finetune():
    """Fine-tune the transferred model for the Fibonacci game"""
    # Set up pygame for event handling
    pygame.init()
    
    # Setup plotting
    plot_scores = []
    plot_mean_scores = []
    plot_fib_scores = []
    total_score = 0
    record = 0
    fib_record = 0
    
    agent = TransferredFibonacciAgent()
    game = FibonacciGameAI()
    
    # Verify Fibonacci sequence
    print(f"Fibonacci sequence: {game.fibonacci_sequence[:10]}")
    
    # Load from previous training if available
    if agent.n_games > 0:
        total_score = agent.total_score
        record = agent.record
        fib_record = agent.fib_record
        
        # Pass the records to the game instance
        game.record = record
        game.iteration = agent.n_games
        game.avg = total_score / max(1, agent.n_games)
        
        # Try to load existing plot data
        plot_file = os.path.join(PLOT_DIR, "fibonacci_transferred_training_data.json")
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
    
    # Auto-save every 20 minutes
    last_save_time = datetime.datetime.now()
    save_interval = datetime.timedelta(minutes=20)
    
    # Auto-save at milestones
    last_milestone = agent.n_games // 50 * 50
    
    print("Starting fine-tuning of transferred model...")
    print(f"Controls: S - Save, P - Pause, ESC - Save and Exit")
    print(f"Current progress: {agent.n_games}/{MAX_GAMES} games completed")
    
    try:
        # Continue until we reach MAX_GAMES
        while agent.n_games < MAX_GAMES:
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
            
            # Check for keyboard events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Save checkpoint before quitting
                    agent.save_checkpoint()
                    pygame.quit()
                    return
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:  # Press 'S' to save
                        agent.save_checkpoint()
                        # Add visual feedback
                        save_text = pygame.font.SysFont('arial', 24).render('SAVED!', True, (255, 255, 0))
                        game.display.blit(save_text, (game.width//2 - save_text.get_width()//2, game.height - 50))
                        pygame.display.update()
                        pygame.time.wait(500)
                        
                    elif event.key == pygame.K_p:  # Press 'P' to pause
                        paused = True
                        
                        # Create overlay for pause screen
                        overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 120))
                        game.display.blit(overlay, (0, 0))
                        
                        pause_text = pygame.font.SysFont('arial', 36).render('PAUSED - Press P to continue', True, (255, 255, 255))
                        game.display.blit(pause_text, (game.width//2 - pause_text.get_width()//2, game.height//2))
                        pygame.display.update()
                        
                        while paused:
                            for pause_event in pygame.event.get():
                                if pause_event.type == pygame.KEYDOWN and pause_event.key == pygame.K_p:
                                    paused = False
                                elif pause_event.type == pygame.QUIT:
                                    agent.save_checkpoint()
                                    pygame.quit()
                                    return
                            pygame.time.wait(100)
                            
                    elif event.key == pygame.K_ESCAPE:  # ESC to save and exit
                        print("Saving and exiting...")
                        agent.save_checkpoint()
                        pygame.quit()
                        return
            
            if done:
                # Train long memory (experience replay)
                game.reset()
                agent.n_games += 1
                agent.train_long_memory()
                
                # Update records
                if score > record:
                    record = score
                    agent.record = record
                    game.record = record  # Update game's record too
                    agent.save_trained_model()
                    print(f"New record! Score: {record}")
                
                if game.fib_score > fib_record:
                    fib_record = game.fib_score
                    agent.fib_record = fib_record
                    print(f"New Fibonacci record! Score: {fib_record}")
                
                # Update game stats for UI
                game.iteration = agent.n_games
                
                # Update total score
                total_score += score
                agent.total_score = total_score
                
                # Track statistics
                mean_score = total_score / agent.n_games
                game.avg = mean_score  # Update game's average for UI
                print(f"Game {agent.n_games}/{MAX_GAMES}, Score: {score}, Fibonacci Sum: {game.fib_score}, Record: {record}")
                
                # Update plots
                plot_scores.append(score)
                plot_fib_scores.append(game.fib_score)
                plot_mean_scores.append(mean_score)
                
                # Create plot
                try:
                    plot(plot_scores, plot_mean_scores, plot_fib_scores)
                except Exception as e:
                    print(f"Error creating plot: {e}")
                
                # Save plot data
                with open(os.path.join(PLOT_DIR, "fibonacci_transferred_training_data.json"), 'w') as f:
                    json.dump({
                        'scores': plot_scores,
                        'fib_scores': plot_fib_scores,
                        'mean_scores': plot_mean_scores
                    }, f)
                
                # Auto-save based on time
                now = datetime.datetime.now()
                if now - last_save_time > save_interval:
                    last_save_time = now
                    agent.save_checkpoint()
                    print(f"Auto-saved checkpoint")
                
                # Auto-save based on milestone (every 50 games)
                current_milestone = agent.n_games // 50 * 50
                if current_milestone > last_milestone:
                    agent.save_checkpoint()
                    print(f"Milestone reached: {current_milestone} games completed")
                    last_milestone = current_milestone
                
                # Check if we've finished training
                if agent.n_games >= MAX_GAMES:
                    print(f"Training complete! Reached {MAX_GAMES} games.")
                    # Final save
                    agent.save_checkpoint()
                    agent.save_trained_model()
                    break
                
    except KeyboardInterrupt:
        print("Training interrupted. Saving checkpoint...")
        agent.save_checkpoint()
        
        # Save plot data
        with open(os.path.join(PLOT_DIR, "fibonacci_transferred_training_data.json"), 'w') as f:
            json.dump({
                'scores': plot_scores,
                'fib_scores': plot_fib_scores,
                'mean_scores': plot_mean_scores
            }, f)
        
        print("Checkpoint and plot data saved. You can resume later.")
        
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        try:
            agent.save_checkpoint()
            print("Emergency checkpoint saved.")
        except:
            print("Could not save emergency checkpoint.")

def watch():
    """Watch the transferred AI play"""
    # Initialize agent
    agent = TransferredFibonacciAgent()
    
    # Initialize game with 1280x720 resolution for better viewing
    game = FibonacciGameAI(width=1280, height=720)
    game.viewing_mode = True  # Enable viewer mode UI
    
    # First check for fine-tuned models
    model_path = ""
    
    try:
        model_files = [f for f in os.listdir(MODEL_DIR) if f.startswith('fibonacci_transferred_model_finetuned_')]
        
        if model_files:
            # Get the one with the highest game count
            try:
                model_file = max(model_files, key=lambda x: int(x.split('_')[-2]))
                model_path = os.path.join(MODEL_DIR, model_file)
            except:
                # If parsing fails, just take the first one
                model_path = os.path.join(MODEL_DIR, model_files[0])
        else:
            # Check for base transferred model
            base_model = os.path.join(MODEL_DIR, "fibonacci_transferred_model.pth")
            if os.path.exists(base_model):
                model_path = base_model
            else:
                # Check for checkpoint model as last resort
                checkpoint_model = os.path.join(CHECKPOINT_DIR, "fibonacci_transferred_checkpoint_model.pth")
                if os.path.exists(checkpoint_model):
                    model_path = checkpoint_model
    except Exception as e:
        print(f"Error finding model files: {e}")
    
    if not model_path or not os.path.exists(model_path):
        print("No trained model found. Please run transfer or finetune first.")
        return
        
    print(f"Loading model: {os.path.basename(model_path)}")
    
    # Load the model
    try:
        agent.model.load_state_dict(torch.load(model_path))
        agent.epsilon = 0  # No random moves when watching
        
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
                print(f"Game over! Score: {score}, Fibonacci Sum: {game.fib_score}")
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
    except Exception as e:
        print(f"Error in watch mode: {e}")
        pygame.quit()

def main():
    """Main entry point with argument parsing"""
    global MAX_GAMES  # Make sure to declare as global
    
    parser = argparse.ArgumentParser(description="Transfer learning for Fibonacci Snake AI")
    parser.add_argument('--transfer', action='store_true', help='Transfer weights from classic model')
    parser.add_argument('--finetune', action='store_true', help='Fine-tune the transferred model')
    parser.add_argument('--watch', action='store_true', help='Watch the transferred AI play')
    parser.add_argument('--model', type=str, default="data/models/model.pth", help='Path to classic model')
    parser.add_argument('--games', type=int, default=MAX_GAMES, help='Number of games to train')
    
    args = parser.parse_args()
    
    # Update MAX_GAMES if specified
    if args.games != MAX_GAMES:
        MAX_GAMES = args.games
        print(f"Will train for {MAX_GAMES} games")
    
    if args.transfer:
        transfer_weights(args.model)
    elif args.finetune:
        finetune()
    elif args.watch:
        watch()
    else:
        # Show menu if no arguments provided
        print("\nFibonacci AI Transfer Learning")
        print("============================\n")
        print("1. Transfer weights from classic model")
        print("2. Fine-tune transferred model")
        print("3. Watch transferred AI play")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ")
        if choice == '1':
            model_path = input("Enter path to classic model (default: data/models/model.pth): ")
            if not model_path:
                model_path = "data/models/model.pth"
            transfer_weights(model_path)
        elif choice == '2':
            games = input("Number of games to train (default: 1000): ")
            try:
                MAX_GAMES = int(games) if games else MAX_GAMES
            except:
                pass
            finetune()
        elif choice == '3':
            watch()
        else:
            print("Exiting...")

if __name__ == "__main__":
    main()