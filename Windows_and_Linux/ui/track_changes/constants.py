"""Constants for the Track Changes Editor"""

from PySide6 import QtCore

# Button and icon sizes
BUTTON_ICON_SIZE = QtCore.QSize(16, 16)

# Animation settings
LOADING_TIMER_INTERVAL = 500
LOADING_MESSAGE_CYCLE = 8

# Grouping thresholds
MAX_GAP_SIZE = 8
MERGE_GAP_SIZE = 3

# Colorblind-friendly color scheme
COLORBLIND_COLORS = {
    'accept_dark': '#64b5f6',
    'accept_light': '#1976d2',
    'accept_bg_dark': '#2d3a4a',
    'accept_bg_light': '#e3f2fd',
    'reject_dark': '#ffb74d',
    'reject_light': '#f57c00',
    'reject_bg_dark': '#4a3a2d',
    'reject_bg_light': '#fff3e0',
    'primary_dark': '#1976d2',
    'primary_light': '#2196f3',
    'primary_hover_dark': '#1565c0',
    'primary_hover_light': '#1976d2',
    'primary_pressed_dark': '#0d47a1',
    'primary_pressed_light': '#1565c0',
}

# Font settings
UI_FONT_FAMILY = "'Segoe UI', 'Arial', sans-serif"

# Loading messages
LOADING_MESSAGES = [
    "Processing with AI",
    "Analyzing your text",
    "Generating improvements",
    "Preparing changes"
]