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
        fib_scores (list, optional): List of fibonacci scores from each game
    """
    # Start the plotting in a separate thread to avoid blocking the main game
    Thread(target=lambda: plot_thread(scores, mean_scores, fib_scores), daemon=True).start()

def plot_thread(scores, mean_scores, fib_scores=None):
    """Thread function to create and save the plot without using interactive features."""
    try:
        # Create a new figure with specified size
        fig = Figure(figsize=(10, 6), dpi=100)
        
        # If we have fibonacci scores, create two subplots
        if fib_scores:
            # Regular game scores subplot
            ax1 = fig.add_subplot(211)  # 2 rows, 1 column, first plot
            ax1.plot(scores, label='Food Score', color='blue')
            ax1.plot(mean_scores, label='Mean Score', color='red')
            ax1.set_title('Food Collection Progress')
            ax1.set_ylabel('Food Score')
            ax1.set_ylim(bottom=0)
            
            # Add text annotations for the latest scores
            if scores and mean_scores:
                ax1.text(len(scores)-1, scores[-1], str(scores[-1]))
                ax1.text(len(mean_scores)-1, mean_scores[-1], f"{mean_scores[-1]:.1f}")
            
            # Add legend
            ax1.legend(loc='upper left')
            
            # Fibonacci scores subplot
            ax2 = fig.add_subplot(212)  # 2 rows, 1 column, second plot
            ax2.plot(fib_scores, label='Fibonacci Sum', color='green')
            ax2.set_title('Fibonacci Growth Progress')
            ax2.set_xlabel('Number of Games')
            ax2.set_ylabel('Fibonacci Sum')
            ax2.set_ylim(bottom=0)
            
            # Add text annotations for the latest fibonacci scores
            if fib_scores:
                ax2.text(len(fib_scores)-1, fib_scores[-1], str(fib_scores[-1]))
            
            # Add legend
            ax2.legend(loc='upper left')
            
            # Adjust layout to prevent overlap
            fig.tight_layout(pad=3.0)
            
        else:
            # Standard single plot for regular scores
            ax = fig.add_subplot(111)
            ax.plot(scores, label='Score')
            ax.plot(mean_scores, label='Mean Score')
            ax.set_title('Training Progress')
            ax.set_xlabel('Number of Games')
            ax.set_ylabel('Score')
            ax.set_ylim(bottom=0)
            
            # Add text annotations for the latest scores
            if scores and mean_scores:
                ax.text(len(scores)-1, scores[-1], str(scores[-1]))
                ax.text(len(mean_scores)-1, mean_scores[-1], str(mean_scores[-1]))
            
            # Add legend
            ax.legend(loc='upper left')
        
        # Save the plot to disk
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        
        # Save as the main plot file (overwrite)
        plot_filename = 'fibonacci_plot.png' if fib_scores else 'current_plot.png'
        fig.savefig(os.path.join(PLOTS_DIR, plot_filename))
        
        # Also save a timestamped version periodically (every 10 games)
        if len(scores) % 10 == 0:
            timestamp_filename = f'fibonacci_plot_game_{len(scores)}.png' if fib_scores else f'plot_game_{len(scores)}.png'
            fig.savefig(os.path.join(PLOTS_DIR, timestamp_filename))
        
    except Exception as e:
        print(f"Error in plotting: {e}")