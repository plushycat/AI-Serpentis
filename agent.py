import torch
import random
import numpy as np
import os
import pygame
import json
import datetime
from collections import deque
from snake_ai import SnakeGameAI, Point, RIGHT, LEFT, UP, DOWN
from model import Linear_QNet, QTrainer
from plotter import plot

# Hyperparameters
MAX_MEMORY = 100_000  # Maximum size of replay memory
BATCH_SIZE = 1000  # Size of mini-batches for training
LR = 0.001  # Learning rate for the Q-learning model

# Checkpoint directory
CHECKPOINT_DIR = "training_checkpoints"
if not os.path.exists(CHECKPOINT_DIR):
    os.makedirs(CHECKPOINT_DIR)

class Agent:
    """
    Represents the reinforcement learning agent using deep Q-learning.
    Manages the state, action selection, memory, and training of the agent.
    """
    def __init__(self):
        self.n_games = 0  # Number of games played
        self.epsilon = 0  # Exploration-exploitation tradeoff parameter
        self.gamma = 0.9  # Discount factor for future rewards
        self.memory = deque(maxlen=MAX_MEMORY)  # Replay memory for experience replay
        self.model = Linear_QNet(11, 256, 3)  # Neural network for Q-value approximation
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)  # Q-learning trainer
        self.total_score = 0  # Track total score for calculating mean
        self.record = 0  # Track record score
        
        # Load previous training data if available
        self._try_load_checkpoint()

    def _try_load_checkpoint(self):
        """Tries to load training state from checkpoint files."""
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "training_state.json")
        model_file = os.path.join(CHECKPOINT_DIR, "checkpoint_model.pth")
        
        if os.path.exists(checkpoint_file) and os.path.exists(model_file):
            try:
                # Load training state
                with open(checkpoint_file, 'r') as f:
                    state = json.load(f)
                self.n_games = state.get('n_games', 0)
                self.total_score = state.get('total_score', 0)
                self.record = state.get('record', 0)
                print(f"Loaded training state: Games={self.n_games}, Record={self.record}")
                
                # Load model
                self.model.load_state_dict(torch.load(model_file))
                print("Loaded model state from checkpoint")
                
                # Load memory if available (optional, may be large)
                memory_file = os.path.join(CHECKPOINT_DIR, "memory.pth")
                if os.path.exists(memory_file):
                    try:
                        loaded_memory = torch.load(memory_file)
                        self.memory = loaded_memory
                        print(f"Loaded replay memory with {len(self.memory)} experiences")
                    except Exception as e:
                        print(f"Error loading memory: {e}")
                
                return True
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
        
        return False

    def save_checkpoint(self):
        """Saves the current training state to checkpoint files."""
        try:
            # Save training stats
            state = {
                'n_games': self.n_games,
                'total_score': self.total_score,
                'record': self.record,
                'timestamp': str(datetime.datetime.now())
            }
            
            with open(os.path.join(CHECKPOINT_DIR, "training_state.json"), 'w') as f:
                json.dump(state, f, indent=2)
            
            # Save model
            torch.save(self.model.state_dict(), os.path.join(CHECKPOINT_DIR, "checkpoint_model.pth"))
            
            # Save a regular snapshot to the model folder too
            self.model.save()
            
            # Optionally save memory (may be large)
            # torch.save(self.memory, os.path.join(CHECKPOINT_DIR, "memory.pth"))
            
            print(f"Checkpoint saved: Games={self.n_games}, Record={self.record}")
            return True
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
            return False

    def get_state(self, game):
        """
        Extracts the current state of the game as an 11-dimensional vector.
        The state includes danger information, movement direction, and food location.
        """
        head = game.snake[0]  # Position of the snake's head

        # Movement directions
        dir_u = game.direction == UP
        dir_r = game.direction == RIGHT
        dir_d = game.direction == DOWN
        dir_l = game.direction == LEFT

        # Points around the head
        point_u = Point(head.x, head.y - 20)
        point_r = Point(head.x + 20, head.y)
        point_d = Point(head.x, head.y + 20)
        point_l = Point(head.x - 20, head.y)

        # State representation: Danger, direction, and food location
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

            # Current movement direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # Food location relative to the head
            game.food.x < game.head.x,  # Food is left
            game.food.x > game.head.x,  # Food is right
            game.food.y < game.head.y,  # Food is up
            game.food.y > game.head.y  # Food is down
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        """
        Stores a state transition in the replay memory.
        """
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        """
        Trains the model using a batch of transitions from the replay memory.
        If memory is smaller than the batch size, trains on the entire memory.
        """
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)  # Random sample
        else:
            mini_sample = self.memory  # Use entire memory if not enough samples

        # Extract components of the transitions
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        """
        Trains the model on a single state transition (short-term memory).
        """
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        """
        Selects an action using an epsilon-greedy strategy.
        - Explores with probability proportional to epsilon.
        - Exploits (chooses the best action) otherwise.
        """
        self.epsilon = 80 - self.n_games  # Decay epsilon as games progress
        final_move = [0, 0, 0]  # Action format: [straight, right, left]

        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)  # Random action
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)  # Predict Q-values for each action
            move = torch.argmax(prediction).item()  # Select action with max Q-value
            final_move[move] = 1

        return final_move

def train():
    """
    Main training loop for the reinforcement learning agent.
    - Trains the agent to play the Snake game.
    - Tracks performance metrics and plots results.
    - Supports saving checkpoints and handling interruptions.
    - Automatically stops after 1000 games.
    """
    # Import pygame for event handling
    import pygame
    import datetime
    
    # Set maximum number of games to train
    MAX_GAMES = 1000
    
    agent = Agent()  # Initialize the agent
    
    # Load previous training data for plotting
    plot_scores = []
    plot_mean_scores = []
    
    # Try to load previous plot data if it exists
    plot_data_file = os.path.join(CHECKPOINT_DIR, "plot_data.json")
    if os.path.exists(plot_data_file):
        try:
            with open(plot_data_file, 'r') as f:
                plot_data = json.load(f)
                plot_scores = plot_data.get('scores', [])
                plot_mean_scores = plot_data.get('mean_scores', [])
                print(f"Loaded plot data for {len(plot_scores)} previous games")
        except Exception as e:
            print(f"Error loading plot data: {e}")
    
    game = SnakeGameAI(record=agent.record)  # Initialize game with loaded record
    game.avg = agent.total_score / max(1, agent.n_games)  # Calculate average
    game.iteration = agent.n_games  # Set current iteration
    
    # Time tracking for auto-save
    last_save_time = datetime.datetime.now()
    save_interval = datetime.timedelta(minutes=10)  # Save every 10 minutes
    
    print(f"Starting training session. Will train until {MAX_GAMES} games or manual interruption.")
    print(f"Current progress: {agent.n_games}/{MAX_GAMES} games completed")
    
    try:
        # Continue training until we reach MAX_GAMES
        while agent.n_games < MAX_GAMES:
            # Get the current state
            state_old = agent.get_state(game)

            # Decide on an action
            final_move = agent.get_action(state_old)

            # Perform the action and observe the next state and reward
            reward, done, score = game.play_step(final_move)
            state_new = agent.get_state(game)

            # Train the agent on the immediate transition
            agent.train_short_memory(state_old, final_move, reward, state_new, done)

            # Store the transition in memory
            agent.remember(state_old, final_move, reward, state_new, done)

            # Check for keyboard input - FIXED: using pygame.event.get() instead of game.event.get()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Save checkpoint before quitting
                    agent.save_checkpoint()
                    
                    # Save plot data
                    with open(plot_data_file, 'w') as f:
                        json.dump({
                            'scores': plot_scores,
                            'mean_scores': plot_mean_scores
                        }, f)
                        
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:  # Press 'S' to save
                        agent.save_checkpoint()
                        # Add visual feedback when save is triggered
                        font = pygame.font.SysFont('arial', 30)
                        save_text = font.render('SAVED! Training progress stored.', True, (255, 255, 0))
                        game.display.blit(save_text, (game.width//2 - save_text.get_width()//2, game.height - 50))
                        pygame.display.update()
                        # Wait briefly so the message is visible
                        pygame.time.wait(1000)
                    elif event.key == pygame.K_p:  # Press 'P' to pause
                        paused = True
                        font = pygame.font.SysFont('arial', 30)
                        pause_text = font.render('PAUSED - Press P to continue', True, (255, 255, 255))
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

            if done:
                # Train on long-term memory
                game.reset()
                agent.n_games += 1
                agent.train_long_memory()

                # Update total score and record
                agent.total_score += score
                if score > agent.record:
                    agent.record = score
                    game.record = agent.record
                    # Save new record immediately
                    agent.model.save()

                # Print progress with games remaining
                print(f'Game {agent.n_games}/{MAX_GAMES} - Score: {score}, Record: {agent.record}')

                # Update plots
                plot_scores.append(score)
                mean_score = round(agent.total_score / agent.n_games, 2)
                game.avg = mean_score
                game.iteration = agent.n_games
                plot_mean_scores.append(mean_score)

                # Plot every 10 iterations or when score is good
                if game.iteration % 10 == 0 or score > 10:
                    plot(plot_scores, plot_mean_scores)
                
                # Auto-save periodically
                now = datetime.datetime.now()
                if now - last_save_time > save_interval:
                    last_save_time = now
                    agent.save_checkpoint()
                    
                    # Save plot data too
                    with open(plot_data_file, 'w') as f:
                        json.dump({
                            'scores': plot_scores,
                            'mean_scores': plot_mean_scores
                        }, f)
                    print("Auto-saved checkpoint and plot data")
                    
                # Check if we've reached MAX_GAMES
                if agent.n_games >= MAX_GAMES:
                    print(f"Training complete! Reached {MAX_GAMES} games.")
                    break
    
    except KeyboardInterrupt:
        print("Training interrupted. Saving checkpoint...")
        agent.save_checkpoint()
        
        # Save plot data
        with open(plot_data_file, 'w') as f:
            json.dump({
                'scores': plot_scores,
                'mean_scores': plot_mean_scores
            }, f)
        print("Checkpoint and plot data saved. You can resume later.")
    
    # Final save when training is complete
    if agent.n_games >= MAX_GAMES:
        print("Training successfully completed. Saving final model...")
        agent.save_checkpoint()
        
        # Save plot data
        with open(plot_data_file, 'w') as f:
            json.dump({
                'scores': plot_scores,
                'mean_scores': plot_mean_scores
            }, f)
        
        # Create a special "completed" model file
        torch.save(agent.model.state_dict(), os.path.join(CHECKPOINT_DIR, "completed_model.pth"))
        print(f"Final model saved after {MAX_GAMES} games of training.")

if __name__ == '__main__':
    train()
