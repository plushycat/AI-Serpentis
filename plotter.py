import matplotlib.pyplot as plt
from threading import Thread

def plot(scores, mean_scores):
    def plot_thread():
        plt.clf()
        plt.title('Training')
        plt.xlabel('Number of Games')
        plt.ylabel('Score')
        plt.plot(scores, label='Score')
        plt.plot(mean_scores, label='Mean Score')
        plt.ylim(ymin=0)
        plt.text(len(scores)-1, scores[-1], str(scores[-1]))
        plt.text(len(mean_scores)-1, mean_scores[-1], str(mean_scores[-1]))
        plt.legend()
        plt.show(block=False)  # Non-blocking show
        plt.pause(0.001)  # Pause to allow the UI to update

    Thread(target=plot_thread).start()