import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
import os
from threading import Thread
import matplotlib
matplotlib.use('Agg')  # Use Agg backend which doesn't require a GUI

# Create a directory for saved plots
PLOTS_DIR = "data/plots"
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)

def plot(scores, mean_scores, fib_scores=None):
    """Plot the training scores and save the plot to disk.
    
    Args:
        scores (list): List of scores from each game
        mean_scores (list): List of mean scores
        fib_scores (list, optional): List of fibonacci scores from each game (not plotted)
    """
    # Start the plotting in a separate thread to avoid blocking the main game
    Thread(target=lambda: plot_thread(scores, mean_scores, fib_scores), daemon=True).start()

def plot_thread(scores, mean_scores, fib_scores=None):
    """Thread function to create and save the plot without using interactive features."""
    try:
        # Create a new figure with specified size
        fig = Figure(figsize=(10, 6), dpi=100)
        
        # Always create a single plot for scores
        ax = fig.add_subplot(111)
        ax.plot(scores, label='Score', color='blue')
        ax.plot(mean_scores, label='Mean Score', color='red')
        ax.set_title('Fibonacci Snake Training Progress')
        ax.set_xlabel('Number of Games')
        ax.set_ylabel('Score')
        ax.set_ylim(bottom=0)
        
        # Add text annotations for the latest scores
        if scores and mean_scores:
            ax.text(len(scores)-1, scores[-1], str(scores[-1]))
            ax.text(len(mean_scores)-1, mean_scores[-1], f"{mean_scores[-1]:.1f}")
        
        # Add legend
        ax.legend(loc='upper left')
        
        # Save the plot to disk
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        
        # Save as the main plot file (overwrite)
        plot_filename = 'fibonacci_plot.png' if fib_scores is not None else 'current_plot.png'
        fig.savefig(os.path.join(PLOTS_DIR, plot_filename))
        
        # Also save a timestamped version periodically (every 10 games)
        if len(scores) % 10 == 0:
            timestamp_filename = f'fibonacci_plot_game_{len(scores)}.png' if fib_scores is not None else f'plot_game_{len(scores)}.png'
            fig.savefig(os.path.join(PLOTS_DIR, timestamp_filename))
        
    except Exception as e:
        print(f"Error in plotting: {e}")