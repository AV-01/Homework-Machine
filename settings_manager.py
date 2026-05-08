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
    "LINED_PAPER_MODE": False,
    "F_TRACE": 3000,
    "DRAW_GUIDE_LINES": False,
    "ROTATE_90": False,
    "NOZZLE_TEMP": 200.0,
    "BED_TEMP": 60.0,
    "EXTRUSION_RATIO": 0.033,
    "HOTEND_Z": 0.28,
    "FLOAT_OFFSET": 2.5,
    "LEFT_MARGIN": 5.0,
    "TOOL_MODE": "Pen",
    "CHAOS_SCALE": 0.15,
    "CHAOS_BOUNCE": 1.5,
    "CHAOS_BASE_TILT": 10.0,
    "CHAOS_ROT": 6.0,
    "CHAOS_DRIFT": 0.15,
    "CHAOS_KERNING": 0.6,
    "CHAOS_SPACE": 0.5
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
