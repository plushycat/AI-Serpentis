# AI Serpentis

This project implements a modern Snake Game featuring manual play, AI-controlled play with Deep Q-Learning, Player vs AI split-screen mode, and Fibonacci Snake Mode—all wrapped in a sleek, customizable Pygame GUI.

> Forked from [armin2080/Snake-Game-AI](https://github.com/armin2080/Snake-Game-AI) with significant enhancements.

---

# Demo Video

[https://github.com/user-attachments/assets/1b68bf50-60f1-4c06-9df4-b9c3b067056d](https://github.com/user-attachments/assets/1b68bf50-60f1-4c06-9df4-b9c3b067056d)



---

## ✨ Features

### Game Features

- Classic Mode: Play manually with Arrow Keys/WASD.
- AI Mode: Watch a trained neural network play autonomously.
- (NEW) Player vs AI Split-Screen Mode: Real-time head-to-head competition.
- (NEW) Fibonacci Snake Mode: Each food increases length by the next Fibonacci number.
- Unified Scoreboard: View and compare scores across all game modes.

### UI & Customization

- Dynamic Gradient Backgrounds: Pastel palettes with subtle animations.
- Centered Titles & Consistent Buttons: Uniform styling throughout.
- Particle Effects & Transitions: Smooth visual flourishes on game events.
- Theme Customization: Swap snake, food, and background themes on the fly.

### AI Implementation

- Deep Q-Learning: Feedforward network (`11 → 256 → 3`) with ReLU activations.
- State Representation: 11-dimensional vector (danger sensors, movement direction, food position).
- Reward Scheme: `+10` for eating food, `-10` for collisions, incremental reward for moving toward food.
- Training Pipeline: Checkpoint save/load, real-time plotting of scores and loss.

---

## 📁 Project Structure

```
AI-Serpentis/
├── assets/                  # Game assets (fonts, sounds, images)
├── data/
│   ├── checkpoints/         # Saved AI model weights
│   ├── plots/               # Training progress graphs
│   └── stats/               # Gameplay statistics
├── src/
│   ├── ai/
│   │   ├── agent.py         # Training agent & inference loop
│   │   ├── model.py         # Neural network definition
│   │   └── watch_ai.py      # AI-play visualization
│   ├── game/
│   │   ├── snake_game.py    # Manual play environment
│   │   ├── snake_ai.py      # AI-compatible game environment
│   │   └── fibonacci_snake.py # Fibonacci Mode logic
│   ├── ui/
│   │   └── main.py          # Menu and UI flow
│   └── utils/
│       └── plotter.py       # Training and stats plotting utilities
├── main.py                  # Entry point for game
├── requirements.txt         # Dependencies
└── training_plot.png        # Sample training curve
```

---

## 🛠️ Prerequisites

Ensure you have:

- Python 3.10+
- Pygame
- PyTorch
- Matplotlib

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🕹️ Game Logic

### Classic Mode

- Control the snake to eat food and grow.
- Avoid collisions with walls and self.
- Score increases as you eat more food.

### AI Mode

- State Representation: 11-dimensional vector
  - Danger detection (front, left, right)
  - Current movement direction
  - Food location relative to snake head
- Action Selection: `[Straight, Right Turn, Left Turn]`
- Reward System:
  - `+10` for eating food
  - `-10` for collisions
  - Small positive reward for moving toward food
- Neural Network: `11 → 256 → 3` feedforward with ReLU.

### Fibonacci Mode

- Each food consumed increases snake length by the next Fibonacci number of segments.
- Adds strategic depth—plan your path to avoid early collisions.

---

## 🎨 Customization Options

- Snake Themes: Classic Green, Cool Blue, Fire, Royal Purple, Sky Blue, Random
- Food Themes: Red Apple, Blueberry, Rainbow, Golden
- Background Themes: Light, Dark
- Debug Mode: Toggle real-time AI debug overlay

---

## 🚀 Running the Project

### Main Game

```bash
python main.py
```

Use the menu to choose Classic, AI, Player vs AI, or Fibonacci Mode and adjust themes.

### Training the AI

```bash
python src/ai/agent.py
```

- Checkpoints → `data/checkpoints/`
- Plots → `data/plots/`
- Exit training gracefully with `Esc`

Adjust hyperparameters in `src/ai/agent.py`: `MAX_MEMORY`, `BATCH_SIZE`, `LR`, `GAMMA`, etc.

---

## 📈 Results

After \~200 training cycles, the AI learns efficient food-collection and collision-avoidance strategies.

![training_plot](https://github.com/user-attachments/assets/9e84c918-af51-4c8c-bb0f-03a84039a927)

---

## 📜 Credits

- **BGM**: Music by Nicholas Panek — Pixabay
- **Level Up Sound**: Magic Game Key Picked Up — Epic Stock Media
- **UI Click Sound**: Arcade Game Bling — Epic Stock Media
- **Icons**: Freepik
- **Countdown & Start Sounds**: freesound\_community — Pixabay

---

## About

With a self-learning AI at the core and a polished GUI, **AI Serpentis** offers both classic and cutting-edge Snake gameplay. Enjoy the blend of nostalgia and innovation!

