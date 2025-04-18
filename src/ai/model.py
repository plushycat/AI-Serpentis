import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

# Define the Linear_QNet class for the neural network
class Linear_QNet(nn.Module):
    """
    A simple feedforward neural network with one hidden layer.
    Used to approximate the Q-value function for the reinforcement learning agent.
    """
    def __init__(self, input_size, hidden_size, output_size):
        """
        Initialize the network layers.

        Args:
        - input_size (int): Number of input features.
        - hidden_size (int): Number of neurons in the hidden layer.
        - output_size (int): Number of output actions.
        """
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)  # Input to hidden layer
        self.linear2 = nn.Linear(hidden_size, output_size)  # Hidden to output layer

    def forward(self, x):
        """
        Perform a forward pass through the network.

        Args:
        - x (torch.Tensor): Input tensor.

        Returns:
        - torch.Tensor: Output tensor (predicted Q-values for each action).
        """
        x = F.relu(self.linear1(x))  # Apply ReLU activation on the hidden layer
        x = self.linear2(x)  # Compute the output
        return x

    def save(self, file_name='model.pth'):
        """
        Save the model's state dictionary to a file.

        Args:
        - file_name (str): Name of the file where the model will be saved.
        """
        model_folder_path = './data/models'  # Directory to save the model
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)  # Create the directory if it doesn't exist

        file_name = os.path.join(model_folder_path, file_name)  # Full path to save the file
        torch.save(self.state_dict(), file_name)  # Save the state dictionary


# Define the QTrainer class for training the neural network
class QTrainer:
    """
    Trainer class for the Q-learning model.
    Handles the optimization and loss computation during training.
    """
    def __init__(self, model, lr, gamma):
        """
        Initialize the trainer.

        Args:
        - model (nn.Module): The Q-learning model to train.
        - lr (float): Learning rate for the optimizer.
        - gamma (float): Discount factor for future rewards.
        """
        self.lr = lr
        self.gamma = gamma
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)  # Adam optimizer
        self.criterion = nn.MSELoss()  # Mean Squared Error loss function

    def train_step(self, state, action, reward, next_state, done):
        """
        Perform a single training step.

        Args:
        - state (array-like): Current state.
        - action (array-like): Action taken.
        - reward (array-like): Reward received.
        - next_state (array-like): Next state.
        - done (array-like): Whether the episode is done.
        """
        # Convert inputs to tensors
        state = torch.tensor(state, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)

        # Ensure batch dimensions for single data points
        if len(state.shape) == 1:
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done, )

        # Predicted Q-values for the current state
        pred = self.model(state)

        # Clone the predictions to compute the target values
        target = pred.clone()
        for idx in range(len(done)):
            Q_new = reward[idx]  # Initialize Q_new with the immediate reward
            if not done[idx]:
                # Add the discounted maximum Q-value of the next state
                Q_new = reward[idx] + self.gamma * torch.max(self.model(next_state[idx]))

            # Update the target for the action taken
            target[idx][torch.argmax(action[idx]).item()] = Q_new

        # Perform backpropagation
        self.optimizer.zero_grad()  # Clear gradients
        loss = self.criterion(target, pred)  # Compute the loss
        loss.backward()  # Backpropagate the loss
        self.optimizer.step()  # Update the model parameters
