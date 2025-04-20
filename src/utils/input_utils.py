import pygame

def is_screenshot_key(key):
    """
    Determine if a key is used for screenshot functionality and should be ignored in game over screens.
    This allows players to take screenshots of their high scores.
    """
    # Control, Shift, Alt, Windows/Command keys
    if key in (pygame.K_LCTRL, pygame.K_RCTRL, 
                pygame.K_LSHIFT, pygame.K_RSHIFT,
                pygame.K_LALT, pygame.K_RALT,
                pygame.K_LMETA, pygame.K_RMETA):
        return True
    
    # Function keys F1-F15
    if pygame.K_F1 <= key <= pygame.K_F15:
        return True
    
    # Print Screen key
    if key == pygame.K_PRINT or key == pygame.K_SYSREQ:
        return True
        
    return False