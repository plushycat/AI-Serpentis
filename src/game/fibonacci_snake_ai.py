class FibonacciSnakeGameAI(SnakeGameAI):
    def __init__(self, width=640, height=480, record=0, avg=0, iteration=0, display_surface=None):
        # Call parent constructor
        super().__init__(width, height, record, avg, iteration, display_surface)
        
        # No need to override the theme as it's already loaded in the parent class
        
        # ...rest of initialization...
    
    def _update_ui(self):
        # Use the correct background color based on theme (override parent method)
        if self.background_theme == "light":
            self.display.fill((240, 240, 245))  # Light background
        else:
            self.display.fill((20, 20, 30))  # Dark background (default)
        
        # ...rest of UI update code...