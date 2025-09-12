"""Main Track Changes Editor"""

import logging
import os
import sys
from typing import List, Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QWidget, QSizePolicy, QGraphicsDropShadowEffect

from ui.UIUtils import UIUtils, colorMode
from .constants import (
    BUTTON_ICON_SIZE, PREVIEW_MIN_HEIGHT, PREVIEW_MAX_HEIGHT,
    CHANGES_MIN_HEIGHT, CHANGES_MAX_HEIGHT, LOADING_TIMER_INTERVAL,
    LOADING_MESSAGE_CYCLE, LOADING_MESSAGES, UI_FONT_FAMILY
)
from .styles import get_icon_path, StyleManager
from .differ import TextDiffer
from .inline_editor import InlineChangeEditor
from .widgets import ChangeStatusBar


class TrackChangesEditor(QWidget):
    """Main editor widget with inline change tracking"""
    
    changes_applied = Signal(str)
    
    def __init__(self, original_text: str, suggested_text: str, option_used: str, loading: bool = False):
        super().__init__()
        self.original_text = original_text or ""
        self.suggested_text = suggested_text or ""
        self.option_used = option_used
        self.loading = loading
        
        # Initialize differ and changes
        self.differ = TextDiffer()
        self.changes = []
        
        if not loading and suggested_text:
            try:
                self.changes = self.differ.get_changes(original_text, suggested_text)
            except Exception as e:
                logging.error(f"Error generating changes: {e}")
                self.changes = []
        
        self._setup_window()
        self.init_ui()
    
    def _setup_window(self):
        """Configure window properties"""
        self.setWindowTitle("Writing Tools - Review Changes")
        self.setMinimumSize(700, 550)
        self.resize(750, 600)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'icons', 'app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
    
    def init_ui(self):
        UIUtils.setup_window_and_layout(self)
        
        layout = QVBoxLayout(self.background)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        self.background.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Title removed to save space
        
        if self.loading:
            self._create_loading_ui(layout)
        else:
            self._create_editor_ui(layout)
    
    def _create_loading_ui(self, layout: QVBoxLayout):
        """Create loading UI with consistent design"""
        # Original text section
        preview_header = self._create_section_header('pencil', 'Original Text')
        layout.addWidget(preview_header)
        
        self.original_text_display = QTextEdit()
        self.original_text_display.setPlainText(self.original_text)
        self.original_text_display.setReadOnly(True)
        self.original_text_display.setMinimumHeight(PREVIEW_MIN_HEIGHT)
        self.original_text_display.setMaximumHeight(PREVIEW_MAX_HEIGHT)
        self.original_text_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.original_text_display.setStyleSheet(StyleManager.get_text_edit_style())
        
        self._add_shadow_effect(self.original_text_display)
        layout.addWidget(self.original_text_display, 0)
        
        # Processing section
        processing_header = self._create_section_header('smiley-face', 'Processing Changes')
        layout.addWidget(processing_header)
        
        # Loading label
        self.loading_label = QLabel("Processing with AI...")
        self.loading_label.setStyleSheet(f"""
            QLabel {{
                color: {'#aaaaaa' if colorMode == 'dark' else '#666666'};
                font-size: 12px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                background-color: {'#444' if colorMode == 'dark' else '#f0f0f0'};
                border-radius: 10px;
                padding: 4px 8px;
            }}
        """)
        
        # Processing area
        scroll_area = self._create_scroll_area()
        processing_widget = QWidget()
        processing_layout = QVBoxLayout(processing_widget)
        processing_layout.setContentsMargins(20, 15, 20, 15)
        processing_layout.setSpacing(10)
        
        progress_desc = QLabel("Analyzing your text and generating improvements...")
        progress_desc.setStyleSheet(f"""
            QLabel {{
                color: {'#aaaaaa' if colorMode == 'dark' else '#666666'};
                font-size: 13px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
        """)
        
        processing_layout.addWidget(progress_desc)
        processing_layout.addStretch()
        scroll_area.setWidget(processing_widget)
        layout.addWidget(scroll_area, 1)
        
        self._start_loading_animation()
        
        # Control buttons
        controls = self._create_loading_control_buttons()
        layout.addLayout(controls)
    
    def _create_editor_ui(self, layout: QVBoxLayout):
        """Create the main editor UI with changes"""
        try:
            self.editor = InlineChangeEditor(self.changes, self.original_text, self.differ)
            self.editor.change_accepted.connect(self.on_change_accepted)
            self.editor.change_rejected.connect(self.on_change_rejected)
            layout.addWidget(self.editor)
            
            # Status bar
            self.status_bar = ChangeStatusBar(self.changes)
            layout.addWidget(self.status_bar)
            
            # Control buttons
            controls = self._create_control_buttons()
            layout.addLayout(controls)
        except Exception as e:
            logging.error(f"Error creating editor UI: {e}")
            self._show_error_message(layout, "Failed to create editor interface")
    
    def _show_error_message(self, layout: QVBoxLayout, message: str):
        """Show error message in the UI"""
        error_label = QLabel(f"Error: {message}")
        error_label.setStyleSheet(f"""
            QLabel {{
                color: #ff4444;
                font-size: 14px;
                font-family: {UI_FONT_FAMILY};
                padding: 20px;
                text-align: center;
            }}
        """)
        layout.addWidget(error_label)
    
    def _create_section_header(self, icon_name: str, title: str) -> QWidget:
        """Create a consistent section header"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        icon = QLabel()
        icon_path = get_icon_path(icon_name)
        if os.path.exists(icon_path):
            icon.setPixmap(QtGui.QPixmap(icon_path).scaled(
                18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-weight: 600;
                font-size: 16px;
                font-family: {UI_FONT_FAMILY};
            }}
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        return header
    
    def _create_scroll_area(self) -> QtWidgets.QScrollArea:
        """Create a standardized scroll area"""
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(CHANGES_MIN_HEIGHT)
        scroll_area.setMaximumHeight(CHANGES_MAX_HEIGHT)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setStyleSheet(StyleManager.get_scroll_area_style())
        return scroll_area
    
    def _add_shadow_effect(self, widget: QWidget):
        """Add consistent shadow effect to widgets"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(0, 0, 0, 30 if colorMode == 'light' else 60))
        widget.setGraphicsEffect(shadow)
    
    def _start_loading_animation(self):
        """Start loading animation with rotating messages"""
        self.loading_timer = QTimer()
        self.loading_dots = 0
        self.current_message_index = 0
        
        def update_loading():
            dots = "." * (self.loading_dots % 4)
            message = LOADING_MESSAGES[self.current_message_index]
            self.loading_label.setText(f"{message}{dots}")
            self.loading_dots += 1
            
            if self.loading_dots % LOADING_MESSAGE_CYCLE == 0:
                self.current_message_index = (self.current_message_index + 1) % len(LOADING_MESSAGES)
        
        self.loading_timer.timeout.connect(update_loading)
        self.loading_timer.start(LOADING_TIMER_INTERVAL)
    
    def update_with_suggestion(self, suggested_text: str):
        """Update the editor with the AI suggestion"""
        logging.debug("Updating track changes editor with AI suggestion")
        
        try:
            self.suggested_text = suggested_text
            self.loading = False
            
            if hasattr(self, 'loading_timer'):
                self.loading_timer.stop()
            
            self.changes = self.differ.get_changes(self.original_text, suggested_text)
            
            # Clear current layout but preserve background
            layout = self.background.layout()
            self._clear_layout(layout)
            
            # Title removed to save space
            
            self._create_editor_ui(layout)
            
        except Exception as e:
            logging.error(f"Error updating with suggestion: {e}")
            self._show_error_message(self.background.layout(), "Failed to update with AI suggestion")
    
    def _clear_layout(self, layout: QVBoxLayout):
        """Safely clear layout widgets"""
        for i in reversed(range(layout.count())):
            child = layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
    
    def _create_loading_control_buttons(self) -> QHBoxLayout:
        """Create control buttons for loading state"""
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 8, 15, 12)
        layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_icon_path = get_icon_path('cross')
        if os.path.exists(cancel_icon_path):
            cancel_btn.setIcon(QtGui.QIcon(cancel_icon_path))
            cancel_btn.setIconSize(BUTTON_ICON_SIZE)
        cancel_btn.setStyleSheet(StyleManager.get_button_style())
        
        self._add_shadow_effect(cancel_btn)
        cancel_btn.clicked.connect(self.close)
        
        layout.addStretch()
        layout.addWidget(cancel_btn)
        
        return layout
    
    def _create_control_buttons(self) -> QHBoxLayout:
        """Create main control buttons"""
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 8, 15, 12)
        layout.setSpacing(12)
        
        # Button configurations
        buttons_config = [
            ("Accept All", "check", StyleManager.get_button_style(), self.accept_all_changes),
            ("Reject All", "cross", StyleManager.get_button_style(), self.reject_all_changes),
            ("Cancel", "cross", StyleManager.get_button_style(), self.close),
            ("Apply Changes", "send", StyleManager.get_success_button_style(), self.apply_selected_changes)
        ]
        
        buttons = []
        for text, icon_name, style, action in buttons_config:
            btn = QPushButton(text)
            icon_path = get_icon_path(icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QtGui.QIcon(icon_path))
                btn.setIconSize(BUTTON_ICON_SIZE)
            btn.setStyleSheet(style)
            btn.clicked.connect(action)
            self._add_shadow_effect(btn)
            buttons.append(btn)
        
        layout.addWidget(buttons[0])  # Accept All
        layout.addWidget(buttons[1])  # Reject All
        layout.addStretch()
        layout.addWidget(buttons[2])  # Cancel
        layout.addWidget(buttons[3])  # Apply Changes
        
        return layout
    
    def on_change_accepted(self, index: int):
        """Handle individual change acceptance"""
        self.status_bar.update_status()
        logging.debug(f"Change {index} accepted")
    
    def on_change_rejected(self, index: int):
        """Handle individual change rejection"""
        self.status_bar.update_status()
        logging.debug(f"Change {index} rejected")
    
    def accept_all_changes(self):
        """Accept all pending changes"""
        for change in self.changes:
            if change['status'] == 'pending':
                change['status'] = 'accepted'
        
        self.editor.update_all_widgets()
        self.status_bar.update_status()
    
    def reject_all_changes(self):
        """Reject all pending changes"""
        for change in self.changes:
            if change['status'] == 'pending':
                change['status'] = 'rejected'
        
        self.editor.update_all_widgets()
        self.status_bar.update_status()
    
    def apply_selected_changes(self):
        """Apply the selected changes and return final text"""
        final_text = self.editor.build_current_text()
        logging.debug(f"Applying final text: '{final_text[:50]}...'")
        
        self.close()
        QtCore.QTimer.singleShot(100, lambda: self.changes_applied.emit(final_text))
    
    def build_final_text(self) -> str:
        """Build the final text based on accepted/rejected changes"""
        return self.editor.build_current_text()