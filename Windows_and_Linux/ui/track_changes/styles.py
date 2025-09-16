"""Style management for Track Changes Editor"""

import os
import sys
from ui.UIUtils import colorMode
from .constants import UI_FONT_FAMILY


def get_icon_path(icon_name: str) -> str:
    """Get the appropriate icon path based on theme"""
    suffix = '_dark.png' if colorMode == 'dark' else '_light.png'
    return os.path.join(os.path.dirname(sys.argv[0]), 'icons', f'{icon_name}{suffix}')


class StyleManager:
    """Centralized style management for consistent theming"""
    
    @staticmethod
    def get_button_style() -> str:
        """Get consistent button styling"""
        return f"""
            QPushButton {{
                background-color: {'#444' if colorMode == 'dark' else '#f0f0f0'};
                color: {'#ffffff' if colorMode == 'dark' else '#000000'};
                border: 1px solid {'#666' if colorMode == 'dark' else '#ccc'};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                font-family: {UI_FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {'#555' if colorMode == 'dark' else '#e0e0e0'};
            }}
            QPushButton:pressed {{
                background-color: {'#333' if colorMode == 'dark' else '#d0d0d0'};
            }}
        """

    @staticmethod
    def get_success_button_style() -> str:
        """Get success button styling"""
        return f"""
            QPushButton {{
                background-color: {'#2e7d32' if colorMode == 'dark' else '#4CAF50'};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-family: {UI_FONT_FAMILY};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#1b5e20' if colorMode == 'dark' else '#45a049'};
            }}
            QPushButton:pressed {{
                background-color: {'#0d4f14' if colorMode == 'dark' else '#3d8b40'};
            }}
        """

    @staticmethod
    def get_small_icon_button_style(button_type: str = "success") -> str:
        """Get small icon button styling"""
        colors = {
            "success": {
                "bg": '#2e7d32' if colorMode == 'dark' else '#4CAF50',
                "hover": '#1b5e20' if colorMode == 'dark' else '#45a049'
            },
            "danger": {
                "bg": '#d32f2f' if colorMode == 'dark' else '#f44336',
                "hover": '#b71c1c' if colorMode == 'dark' else '#da190b'
            }
        }
        
        color_set = colors.get(button_type, colors["success"])
        
        return f"""
            QPushButton {{
                background-color: {color_set["bg"]};
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {color_set["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {color_set["hover"]};
            }}
        """

    @staticmethod
    def get_text_edit_style() -> str:
        """Get consistent text edit styling"""
        return f"""
            QTextEdit {{
                background-color: {'#333' if colorMode == 'dark' else 'white'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#e0e0e0'};
                border-radius: 8px;
                padding: 15px;
                font-size: 15px;
                font-family: {UI_FONT_FAMILY};
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border-color: #4CAF50;
                outline: none;
            }}
        """

    @staticmethod
    def get_scroll_area_style() -> str:
        """Get consistent scroll area styling"""
        return f"""
            QScrollArea {{
                background-color: transparent;
                border: 1px solid {'#555' if colorMode == 'dark' else '#e0e0e0'};
                border-radius: 8px;
            }}
            QScrollBar:vertical {{
                background-color: {'#444' if colorMode == 'dark' else '#f0f0f0'};
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {'#666' if colorMode == 'dark' else '#c0c0c0'};
                min-height: 20px;
                border-radius: 5px;
                margin: 1px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {'#777' if colorMode == 'dark' else '#a0a0a0'};
            }}
        """