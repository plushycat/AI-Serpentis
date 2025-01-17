# Snake Game AI

This project implements a **Snake Game** where an AI learns to play the game using **Deep Q-Learning**. The AI trains over multiple iterations, improving its performance and strategy. The game is implemented in Python using **Pygame** for the visuals and **PyTorch** for the AI model.



https://github.com/user-attachments/assets/7dbb0ab6-90ae-4156-be62-b0765bf2e839









---

## Features
- **AI-Powered Gameplay**: The AI uses reinforcement learning to master the Snake Game.
- **Gradient-based Visuals**: The game board features modern gradient effects.
- **Live Metrics Display**: Real-time display of score, record, average score, and iteration count during training.
- **Pause/Resume Feature**: Pause the game anytime with the `P` key.
- **Customizable Settings**: Easily modify game speed, block size, and learning parameters.
- **AI Performance Visualization**: A dynamic plot displays the AI's learning progress over time.

---

## Prerequisites
Before running the code, ensure you have the following installed:
- Python 3.8+
- Pygame
- PyTorch
- Matplotlib

You can install the required dependencies using:
```bash
pip install -r requirements.txt
```
---

## Game Logic
The game features a classic Snake environment:
- The snake collects food to grow and score points.
- The snake wraps around the screen edges.
- The game ends if the snake collides with itself.

## AI Logic
The AI is trained using Deep Q-Learning, which involves:
- **State Representation**: The AI observes the environment (snake's position, direction, and food location).
- **Action Selection**: The AI chooses actions using an epsilon-greedy policy.
- **Reward System**: Positive rewards for eating food, negative rewards for collisions.
- **Neural Network**: A feedforward network predicts Q-values for actions, guiding the AI's decisions.

---

## Results
- After sufficient training, the AI learns to consistently achieve high scores.
- The training process is visualized with a real-time plot showing score progression.

![plot](https://github.com/user-attachments/assets/e120a1f6-720a-44e0-b2a1-d8703b9a443a)
