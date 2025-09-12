"""Constants for the Track Changes Editor"""

from PySide6 import QtCore

# Button and icon sizes
BUTTON_ICON_SIZE = QtCore.QSize(16, 16)
SMALL_ICON_SIZE = QtCore.QSize(14, 14)
CHANGE_BUTTON_SIZE = (32, 32)
CONTROL_BUTTON_SIZE = (28, 28)

# UI Dimensions - Font-size aware calculations
PREVIEW_MIN_HEIGHT = 200  
PREVIEW_MAX_HEIGHT = 390  
CHANGES_MIN_HEIGHT = 100  
CHANGES_MAX_HEIGHT = 180  

# Animation settings
LOADING_TIMER_INTERVAL = 500
LOADING_MESSAGE_CYCLE = 8

# Grouping thresholds
MAX_GAP_SIZE = 8
MERGE_GAP_SIZE = 3

# HTML styling constants for change visualization
HTML_CHANGE_STYLES = {
    'replace': "background-color: #fff3cd; color: #856404; border: 1px dashed #ffc107; padding: 1px;",
    'insert': "background-color: #d1ecf1; color: #0c5460; border: 1px dashed #17a2b8; padding: 1px; font-weight: bold; text-decoration: none; cursor: pointer;",
    'delete': "background-color: #f8d7da; color: #721c24; border: 1px dashed #dc3545; padding: 1px; text-decoration: line-through; cursor: pointer;"
}

# Font settings
MONOSPACE_FONT_FAMILY = "'Consolas', 'Monaco', monospace"
UI_FONT_FAMILY = "'Segoe UI', 'Arial', sans-serif"

# Loading messages
LOADING_MESSAGES = [
    "Processing with AI",
    "Analyzing your text",
    "Generating improvements",
    "Preparing changes"
]