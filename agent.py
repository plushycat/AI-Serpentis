import torch
import random
import numpy as np
from collections import deque
from snake_ai import SnakeGameAI, Point, RIGHT, LEFT, UP, DOWN
from model import Linear_QNet, QTrainer
from plotter import plot

# Hyperparameters
MAX_MEMORY = 100_000  # Maximum size of replay memory
BATCH_SIZE = 1000  # Size of mini-batches for training
LR = 0.001  # Learning rate for the Q-learning model

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
    """
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()  # Initialize the agent
    game = SnakeGameAI()  # Initialize the game

    while True:
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

        if done:
            # Train on long-term memory
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            # Update and save the record score
            if score > record:
                record = score
                game.record = record
                agent.model.save()

            # Print progress
            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            # Plot scores
            plot_scores.append(score)
            total_score += score
            mean_score = round(total_score / agent.n_games, 2)
            game.avg = mean_score
            game.iteration = agent.n_games
            plot_mean_scores.append(mean_score)

            # Plot after 200 iterations
            if game.iteration == 200:
                plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()
