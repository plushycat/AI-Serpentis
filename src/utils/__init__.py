import pygame

def draw_gradient(display, color1, color2, width, height):
    """
    Draws a vertical gradient on the display.

    Args:
    display: Pygame display object.
    color1: Starting color of the gradient (RGB tuple).
    color2: Ending color of the gradient (RGB tuple).
    width: Width of the gradient area.
    height: Height of the gradient area.
    """
    for i in range(height):
        r = color1[0] + (color2[0] - color1[0]) * i // height
        g = color1[1] + (color2[1] - color1[1]) * i // height
        b = color1[2] + (color2[2] - color1[2]) * i // height
        pygame.draw.line(display, (r, g, b), (0, i), (width, i))