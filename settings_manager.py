import json
import os

DEFAULT_SETTINGS = {
    "X_MIN": 80.0,
    "X_MAX": 230.0,
    "Y_MIN": 40.0,
    "Y_MAX": 220.0,
    "Z_SAFE": 10.0,
    "Z_DRAW": 1.52,
    "F_TRAVEL": 3000,
    "F_DRAW": 2000,
    "F_Z": 1000,
    "FLIP_X": False,
    "FLIP_Y": False,
    "LINE_SPACING": 7.1, # College ruled standard
    "TOP_MARGIN": 10.0,
    "LINE_RATIO": 0.75,
    "LINED_PAPER_MODE": False
}

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Merge with defaults in case new keys were added
                return {**DEFAULT_SETTINGS, **settings}
        except:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
