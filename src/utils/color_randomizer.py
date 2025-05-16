import random

def is_valid_hex(hex_str):
    """Validate if a string is a valid hex color code."""
    if not hex_str:
        return False
    try:
        int(hex_str, 16)
        return len(hex_str) in [3, 6]  # Valid hex can be 3 or 6 chars
    except ValueError:
        return False

def hex_to_rgb(hex_str):
    """Convert hex color string to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        return tuple(int(c + c, 16) for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def generate_random_hex(is_top=True, complement_hex=None):
    """Generate a random hex color suitable for gradients.
    
    Args:
        is_top: Whether this is for top gradient (True) or bottom (False)
        complement_hex: Optional hex string to complement (for bottom gradient)
    """
    # Create more visually appealing colors
    if is_top:
        # For top gradient, use more saturated, vibrant colors
        r = random.randint(20, 100)
        g = random.randint(20, 100)
        b = random.randint(50, 150)
    else:
        # For bottom gradient, use darker colors that complement the top
        # If we have a top input already, relate to it
        if complement_hex and is_valid_hex(complement_hex):
            try:
                top_rgb = hex_to_rgb(complement_hex)
                # Create a darker variant of the top color
                r = max(0, top_rgb[0] - random.randint(10, 30))
                g = max(0, top_rgb[1] - random.randint(10, 30))
                b = max(0, top_rgb[2] - random.randint(10, 30))
            except:
                r = random.randint(10, 40)
                g = random.randint(10, 40)
                b = random.randint(30, 80)
        else:
            # Default darker colors
            r = random.randint(10, 40)
            g = random.randint(10, 40) 
            b = random.randint(30, 80)
    
    return f"{r:02x}{g:02x}{b:02x}"

def generate_random_gradient_color(is_top=True):
    """Generate a random hex color suitable for gradients with better diversity."""
    if is_top:
        # For top gradient, use more vibrant colors with higher saturation
        # Use HSL-like approach for better control over color properties
        h = random.randint(0, 360)  # Full hue range
        s = random.randint(60, 90)  # Higher saturation (60-90%)
        l = random.randint(30, 60)  # Medium lightness for vibrant colors
        
        # Convert HSL-like values to RGB (simplified conversion)
        h_i = h / 60
        c = (1 - abs(2 * l/100 - 1)) * s/100
        x = c * (1 - abs(h_i % 2 - 1))
        m = l/100 - c/2
        
        if 0 <= h_i < 1:
            r, g, b = c, x, 0
        elif 1 <= h_i < 2:
            r, g, b = x, c, 0
        elif 2 <= h_i < 3:
            r, g, b = 0, c, x
        elif 3 <= h_i < 4:
            r, g, b = 0, x, c
        elif 4 <= h_i < 5:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    else:
        # For bottom gradient, create a darker complementary color
        # Start with a dark base and add some color
        r = random.randint(5, 35)
        g = random.randint(5, 35)
        b = random.randint(15, 45)  # Slightly more blue for better depth
        
        # Occasionally make it more interesting with a color accent
        if random.random() < 0.3:  # 30% chance
            accent = random.choice(['r', 'g', 'b'])
            if accent == 'r':
                r = random.randint(30, 60)
            elif accent == 'g':
                g = random.randint(30, 60)
            else:
                b = random.randint(40, 70)
    
    # Convert to hex
    return f"#{r:02x}{g:02x}{b:02x}"

def draw_gradient_preview(surface, top_color_hex, bottom_color_hex, rect):
    """Draw a gradient preview with the given colors on the surface."""
    import pygame
    import math
    
    # Convert hex to RGB
    try:
        top_rgb = hex_to_rgb(top_color_hex)
        bottom_rgb = hex_to_rgb(bottom_color_hex)
    except:
        # Fallback for invalid hex
        top_rgb = (25, 25, 45)
        bottom_rgb = (10, 10, 35)
    
    # Draw gradient
    height = rect.height
    for i in range(height):
        # Calculate color for this line
        ratio = i / height
        r = int(top_rgb[0] * (1 - ratio) + bottom_rgb[0] * ratio)
        g = int(top_rgb[1] * (1 - ratio) + bottom_rgb[1] * ratio)
        b = int(top_rgb[2] * (1 - ratio) + bottom_rgb[2] * ratio)
        
        # Draw a line of the gradient
        pygame.draw.line(surface, (r, g, b), (rect.left, rect.top + i),(rect.right, rect.top + i))
    
    # Add decorative elements for better visualization
    # Draw a "snake" silhouette on the gradient
    snake_color = (255, 255, 255, 180)  # Semi-transparent white
    snake_height = rect.height // 2
    snake_wave = math.sin(pygame.time.get_ticks() * 0.002) * 5  # Subtle animation
    
    # Simple snake representation
    snake_points = []
    for x in range(rect.left + 5, rect.right - 5, 10):
        y_offset = snake_wave * math.sin((x - rect.left) * 0.05)
        snake_points.append((x, rect.top + snake_height + y_offset))
    
    if len(snake_points) > 1:
        # Draw with anti-aliasing if available
        try:
            pygame.draw.aalines(surface, snake_color, False, snake_points, 2)
        except:
            pygame.draw.lines(surface, snake_color, False, snake_points, 2)