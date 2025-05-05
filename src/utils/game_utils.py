import pygame

def show_pause_screen(screen, fonts, screen_dimensions):
    """
    Display a pause screen and handle pause state inputs.
    
    Args:
        screen: Pygame display surface
        fonts: Dictionary containing 'main' and 'small' font objects
        screen_dimensions: Tuple of (width, height)
        
    Returns:
        str: 'continue' to resume game, 'menu' to return to menu, 'exit' to quit
    """
    screen_width, screen_height = screen_dimensions
    paused = True
    
    # Draw pause overlay
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # Semi-transparent black
    screen.blit(overlay, (0, 0))
    
    # Draw pause text
    pause_text = fonts['main'].render("PAUSED", True, (255, 255, 255))
    screen.blit(pause_text, (screen_width//2 - pause_text.get_width()//2, screen_height//2 - 50))
    
    # Instructions text - clearly indicate ESC returns to menu
    continue_text = fonts['small'].render("Press P to continue, ESC to return to menu", True, (200, 200, 200))
    screen.blit(continue_text, (screen_width//2 - continue_text.get_width()//2, screen_height//2 + 30))
    
    pygame.display.flip()
    
    # Pause event loop
    while paused:
        for pause_event in pygame.event.get():
            if pause_event.type == pygame.QUIT:
                return 'exit'  # Exit the game
            
            if pause_event.type == pygame.KEYDOWN:
                if pause_event.key == pygame.K_p:
                    return 'continue'  # Resume the game
                elif pause_event.key == pygame.K_ESCAPE:
                    return 'menu'  # Return to menu
        
        pygame.time.delay(100)  # Small delay to prevent CPU hogging