"""
font_data.py - Hershey Simplex Font Data and Layout Engine
Embedded subset of Hershey Simplex for an MVP pen plotter.
"""

import os
import json
import random
import math

# Character data format: [left_boundary, right_boundary, stroke1, stroke2, ...]

# Each stroke is a list of (x, y) points. Coordinates are relative to character center.
# Y increases UP in Hershey data, so we'll flip it for our screen (Y increases DOWN).
# Scaling: Hershey Simplex is roughly 21 units tall (-9 to 12).

HERSHEY_SIMPLEX = {
    ' ': [-10, 10],
    '!': [-5, 5, [(0, 10), (0, 0)], [(0, -5), (0, -7)]],
    '#': [-10, 10, [(-5, 5), (5, 5)], [(-5, -5), (5, -5)], [(-2, 8), (-2, -8)], [(2, 8), (2, -8)]],
    '$': [-10, 10, [(0, 10), (0, -10)], [(-5, 5), (5, 5), (5, 0), (-5, 0), (-5, -5), (5, -5)]],
    '(': [-5, 5, [(2, 10), (-2, 5), (-2, -5), (2, -10)]],
    ')': [-5, 5, [(-2, 10), (2, 5), (2, -5), (-2, -10)]],
    '*': [-7, 7, [(0, 5), (0, -5)], [(-4, 3), (4, -3)], [(4, 3), (-4, -3)]],
    '+': [-10, 10, [(0, 5), (0, -5)], [(-5, 0), (5, 0)]],
    ',': [-5, 5, [(0, -5), (0, -7), (-1, -8)]],
    '-': [-10, 10, [(-5, 0), (5, 0)]],
    '.': [-5, 5, [(0, -5), (0, -7)]],
    '/': [-10, 10, [(-5, -10), (5, 10)]],
    '0': [-10, 10, [(-5, 10), (5, 10), (5, -10), (-5, -10), (-5, 10)]],
    '1': [-10, 10, [(-2, 5), (0, 10), (0, -10)], [(-5, -10), (5, -10)]],
    '2': [-10, 10, [(-5, 5), (-5, 10), (5, 10), (5, 0), (-5, -10), (5, -10)]],
    '3': [-10, 10, [(-5, 10), (5, 10), (0, 0), (5, -10), (-5, -10)]],
    '4': [-10, 10, [(0, -10), (0, 10), (-5, 0), (5, 0)]],
    '5': [-10, 10, [(5, 10), (-5, 10), (-5, 0), (5, 0), (5, -10), (-5, -10)]],
    '6': [-10, 10, [(5, 10), (-5, 10), (-5, -10), (5, -10), (5, 0), (-5, 0)]],
    '7': [-10, 10, [(-5, 10), (5, 10), (-5, -10)]],
    '8': [-10, 10, [(-5, 10), (5, 10), (5, -10), (-5, -10), (-5, 10)], [(-5, 0), (5, 0)]],
    '9': [-10, 10, [(-5, -10), (5, -10), (5, 10), (-5, 10), (-5, 0), (5, 0)]],
    ':': [-5, 5, [(0, 5), (0, 3)], [(0, -3), (0, -5)]],
    ';': [-5, 5, [(0, 5), (0, 3)], [(0, -3), (0, -5), (-1, -6)]],
    '=': [-10, 10, [(-5, 3), (5, 3)], [(-5, -3), (5, -3)]],
    '?': [-10, 10, [(-5, 5), (-5, 10), (5, 10), (5, 5), (0, 0), (0, -5)], [(0, -9), (0, -10)]],
    'A': [-10, 10, [(0, 10), (-8, -10)], [(0, 10), (8, -10)], [(-4, 0), (4, 0)]],
    'B': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (2, 10), (6, 6), (2, 0), (6, -6), (2, -10), (-8, -10)], [(-8, 0), (2, 0)]],
    'C': [-10, 10, [(8, 6), (6, 10), (-2, 10), (-8, 4), (-8, -4), (-2, -10), (6, -10), (8, -6)]],
    'D': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (2, 10), (8, 4), (8, -4), (2, -10), (-8, -10)]],
    'E': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (8, 10)], [(-8, 0), (2, 0)], [(-8, -10), (8, -10)]],
    'F': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (8, 10)], [(-8, 0), (2, 0)]],
    'G': [-10, 10, [(8, 6), (6, 10), (-2, 10), (-8, 4), (-8, -4), (-2, -10), (6, -10), (8, -6), (8, 0), (2, 0)]],
    'H': [-10, 10, [(-8, 10), (-8, -10)], [(8, 10), (8, -10)], [(-8, 0), (8, 0)]],
    'I': [-5, 5, [(0, 10), (0, -10)], [(-5, 10), (5, 10)], [(-5, -10), (5, -10)]],
    'J': [-10, 10, [(5, 10), (5, -4), (0, -10), (-5, -10), (-8, -7)]],
    'K': [-10, 10, [(-8, 10), (-8, -10)], [(8, 10), (-8, 0)], [(0, 0), (8, -10)]],
    'L': [-10, 10, [(-8, 10), (-8, -10)], [(-8, -10), (8, -10)]],
    'M': [-12, 12, [(-10, 10), (-10, -10)], [(-10, 10), (0, 0)], [(0, 0), (10, 10)], [(10, 10), (10, -10)]],
    'N': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (8, -10)], [(8, 10), (8, -10)]],
    'O': [-10, 10, [(-8, 4), (-2, 10), (2, 10), (8, 4), (8, -4), (2, -10), (-2, -10), (-8, -4), (-8, 4)]],
    'P': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (2, 10), (8, 6), (8, 4), (2, 0), (-8, 0)]],
    'Q': [-10, 10, [(-8, 4), (-2, 10), (2, 10), (8, 4), (8, -4), (2, -10), (-2, -10), (-8, -4), (-8, 4)], [(2, -4), (8, -10)]],
    'R': [-10, 10, [(-8, 10), (-8, -10)], [(-8, 10), (2, 10), (8, 6), (8, 4), (2, 0), (-8, 0)], [(2, 0), (8, -10)]],
    'S': [-10, 10, [(8, 6), (4, 10), (-4, 10), (-8, 6), (-8, 2), (8, -2), (8, -6), (4, -10), (-4, -10), (-8, -6)]],
    'T': [-10, 10, [(0, 10), (0, -10)], [(-8, 10), (8, 10)]],
    'U': [-10, 10, [(-8, 10), (-8, -6), (-4, -10), (4, -10), (8, -6), (8, 10)]],
    'V': [-10, 10, [(-8, 10), (0, -10)], [(0, -10), (8, 10)]],
    'W': [-12, 12, [(-10, 10), (-5, -10)], [(-5, -10), (0, 0)], [(0, 0), (5, -10)], [(5, -10), (10, 10)]],
    'X': [-10, 10, [(-8, 10), (8, -10)], [(8, 10), (-8, -10)]],
    'Y': [-10, 10, [(-8, 10), (0, 0)], [(8, 10), (0, 0)], [(0, 0), (0, -10)]],
    'Z': [-10, 10, [(-8, 10), (8, 10)], [(8, 10), (-8, -10)], [(-8, -10), (8, -10)]],
    'a': [-8, 8, [(6, -10), (6, -2), (2, 2), (-2, 2), (-6, -2), (-6, -6), (-2, -10), (6, -10)], [(-6, -2), (2, -2)]],
    'b': [-8, 8, [(-6, 10), (-6, -10)], [(-6, -2), (-2, 2), (2, 2), (6, -2), (6, -6), (2, -10), (-6, -10)]],
    'c': [-8, 8, [(6, -2), (2, 2), (-2, 2), (-6, -2), (-6, -6), (-2, -10), (6, -10)]],
    'd': [-8, 8, [(6, 10), (6, -10)], [(6, -2), (2, 2), (-2, 2), (-6, -2), (-6, -6), (-2, -10), (6, -10)]],
    'e': [-8, 8, [(-6, -6), (6, -6), (6, -2), (2, 2), (-2, 2), (-6, -2), (-6, -10), (6, -10)]],
    'f': [-6, 6, [(4, 10), (0, 10), (0, -10)], [(-4, 2), (4, 2)]],
    'g': [-8, 8, [(6, 2), (6, -14), (2, -18), (-6, -18)], [(6, 2), (2, 6), (-2, 6), (-6, 2), (-6, -2), (-2, -6), (6, -6)]],
    'h': [-8, 8, [(-6, 10), (-6, -10)], [(-6, -2), (-2, 2), (2, 2), (6, -2), (6, -10)]],
    'i': [-2, 2, [(0, 0), (0, -10)], [(0, 4), (0, 6)]],
    'j': [-4, 4, [(2, 0), (2, -14), (0, -18), (-4, -18)], [(2, 4), (2, 6)]],
    'k': [-8, 8, [(-6, 10), (-6, -10)], [(6, 2), (-6, -4)], [(0, -2), (6, -10)]],
    'l': [-2, 2, [(0, 10), (0, -10)]],
    'm': [-12, 12, [(-10, 2), (-10, -10)], [(-10, -2), (-6, 2), (-2, 2), (-2, -10)], [(-2, -2), (2, 2), (6, 2), (10, -10)]],
    'n': [-8, 8, [(-6, 2), (-6, -10)], [(-6, -2), (-2, 2), (2, 2), (6, -2), (6, -10)]],
    'o': [-8, 8, [(-6, -2), (-2, 2), (2, 2), (6, -2), (6, -6), (2, -10), (-2, -10), (-6, -6), (-6, -2)]],
    'p': [-8, 8, [(-6, 2), (-6, -18)], [(-6, -2), (-2, 2), (2, 2), (6, -2), (6, -6), (2, -10), (-6, -10)]],
    'q': [-8, 8, [(6, 2), (6, -18)], [(6, -2), (2, 2), (-2, 2), (-6, -2), (-6, -6), (-2, -10), (6, -10)]],
    'r': [-6, 6, [(-4, 2), (-4, -10)], [(-4, -2), (0, 2), (4, 2)]],
    's': [-7, 7, [(4, 2), (0, 6), (-4, 2), (-4, 0), (4, -4), (4, -6), (0, -10), (-4, -6)]],
    't': [-4, 4, [(0, 10), (0, -6), (2, -10), (4, -10)], [(-4, 2), (4, 2)]],
    'u': [-8, 8, [(-6, 2), (-6, -6), (-2, -10), (2, -10), (6, -6), (6, 2)], [(6, -2), (6, -10)]],
    'v': [-8, 8, [(-6, 2), (0, -10), (6, 2)]],
    'w': [-12, 12, [(-10, 2), (-6, -10), (-2, 2), (2, -10), (10, 2)]],
    'x': [-8, 8, [(-6, 2), (6, -10)], [(6, 2), (-6, -10)]],
    'y': [-8, 8, [(-6, 2), (0, -10), (6, 2)], [(0, -10), (-4, -18)]],
    'z': [-8, 8, [(-6, 2), (6, 2), (-6, -10), (6, -10)], [(-2, -4), (2, -4)]],
}

def get_fonts_dir():
    return os.path.join(os.path.dirname(__file__), "fonts")

def list_available_fonts():
    """Returns list of all available fonts including custom JSON ones."""
    fonts = ["Hershey Simplex"]
    fonts_dir = get_fonts_dir()
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.endswith(".json"):
                fonts.append(f[:-5])
    return fonts

def load_font(font_name):
    """Returns a font dictionary, defaulting to Hershey Simplex."""
    if font_name == "Hershey Simplex" or not font_name:
        return HERSHEY_SIMPLEX
        
    path = os.path.join(get_fonts_dir(), f"{font_name}.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data
        except:
            pass
    return HERSHEY_SIMPLEX

def rotate_point(x, y, cx, cy, angle_deg):
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    nx = cos_a * (x - cx) - sin_a * (y - cy) + cx
    ny = sin_a * (x - cx) + cos_a * (y - cy) + cy
    return nx, ny

def get_text_strokes(text, font_dicts=None, font_size=10.0, start_x=80.0, start_y=220.0, max_width=150.0, line_height=None, humanize=0.0, chaos_settings=None):
    """
    Converts a string of text into a list of strokes (list of points).
    Handles line wrapping and basic vertical layout.
    
    font_dicts: List of dictionaries of character data. If None, uses [HERSHEY_SIMPLEX].
    font_size: Height of character in mm (Hershey Simplex height is approx 21 units).
    start_x, start_y: Initial machine coordinates for top-left.
    max_width: Maximum width in mm before wrapping.
    line_height: Explicit line spacing in mm. If None, defaults to 1.5 * font_size.
    humanize: Value from 0.0 to 1.0 to add random variation to strokes.
    chaos_settings: Dictionary of configuration values for humanize chaos.
    """
    if font_dicts is None:
        font_dicts = [HERSHEY_SIMPLEX]
    elif isinstance(font_dicts, dict):
        font_dicts = [font_dicts]
        
    scale = font_size / 21.0
    if line_height is None:
        line_height = font_size * 1.5
    
    strokes = []
    # Pin baseline (py = -10) to start_y
    # my = cursor_y + (py * scale) -> start_y = cursor_y + (-10 * scale)
    cursor_y_initial = start_y
    cursor_x = start_x
    cursor_y = cursor_y_initial
    
    # Simple word wrapping by splitting on space
    lines = text.split('\n')
    
    for line in lines:
        line_drift = 0.0 # Accumulates vertically across the line
        words = line.split(' ')
        for word in words:
            # Calculate approx word width for wrapping
            word_width = 0
            for char in word:
                valid_for_width = [f for f in font_dicts if char in f]
                if valid_for_width:
                    data = valid_for_width[0][char]
                elif char in HERSHEY_SIMPLEX:
                    data = HERSHEY_SIMPLEX[char]
                else:
                    data = [-10, 10]
                word_width += (data[1] - data[0]) * scale
            
            # Wrap if necessary
            if cursor_x + word_width > start_x + max_width and cursor_x > start_x:
                cursor_x = start_x
                cursor_y -= line_height
            
            # Draw word
            for char in word:
                valid_fonts = [f for f in font_dicts if char in f]
                if valid_fonts:
                    active_font = random.choice(valid_fonts)
                    data = active_font[char]
                elif char in HERSHEY_SIMPLEX:
                    data = HERSHEY_SIMPLEX[char]
                else:
                    data = [-10, 10]
                    
                char_left = data[0]
                char_right = data[1]
                
                # Humanization Base Metrics
                char_scale = 1.0
                char_bounce = 0.0
                char_rot = 0.0
                kerning = 0.0
                
                if humanize > 0:
                    c_scale = chaos_settings.get("CHAOS_SCALE", 0.15) if chaos_settings else 0.15
                    c_bounce = chaos_settings.get("CHAOS_BOUNCE", 1.5) if chaos_settings else 1.5
                    c_base_tilt = chaos_settings.get("CHAOS_BASE_TILT", 10.0) if chaos_settings else 10.0
                    c_rot = chaos_settings.get("CHAOS_ROT", 6.0) if chaos_settings else 6.0
                    c_drift = chaos_settings.get("CHAOS_DRIFT", 0.15) if chaos_settings else 0.15
                    c_kerning = chaos_settings.get("CHAOS_KERNING", 0.6) if chaos_settings else 0.6
                    
                    char_scale = random.uniform(1.0 - (c_scale * humanize), 1.0 + (c_scale * humanize))
                    char_bounce = random.uniform(-c_bounce * humanize, c_bounce * humanize)
                    # Add a consistent rightward tilt (forward slant) plus some randomness
                    char_rot = (c_base_tilt * humanize) + random.uniform(-c_rot * humanize, c_rot * humanize)
                    line_drift += random.uniform(-c_drift * humanize, c_drift * humanize)
                    kerning = random.uniform(-c_kerning * humanize, c_kerning * humanize)

                char_width = (char_right - char_left) * scale * char_scale
                char_offset_x = cursor_x - (char_left * scale * char_scale) + kerning
                
                cx_center = char_offset_x + ((char_right + char_left)/2.0 * scale * char_scale)
                cy_center = cursor_y + char_bounce + line_drift
                
                # Add strokes for character
                for path in data[2:]:
                    stroke = []
                    for px, py in path:
                        mx = char_offset_x + (px * scale * char_scale)
                        my = cy_center + (py * scale * char_scale)
                        
                        if char_rot != 0:
                            mx, my = rotate_point(mx, my, cx_center, cy_center, char_rot)
                            
                        if humanize > 0:
                            mx += random.uniform(-0.1 * humanize, 0.1 * humanize)
                            my += random.uniform(-0.1 * humanize, 0.1 * humanize)
                            
                        stroke.append((mx, my))
                    strokes.append(stroke)
                
                cursor_x += char_width + kerning
            
            # Add space after word
            space_data = font_dicts[0].get(' ', [-10, 10])
            space_width = (space_data[1] - space_data[0]) * scale
            if humanize > 0:
                 c_space = chaos_settings.get("CHAOS_SPACE", 0.5) if chaos_settings else 0.5
                 # In handwriting space widths vary aggressively
                 space_width *= random.uniform(1.0 - (c_space * humanize), 1.0 + (c_space * humanize))
            cursor_x += space_width
            
        # New line after each block in lines
        cursor_x = start_x
        cursor_y -= line_height
        
    return strokes
