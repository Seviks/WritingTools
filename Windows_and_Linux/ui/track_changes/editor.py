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
    BUTTON_ICON_SIZE, LOADING_TIMER_INTERVAL, LOADING_MESSAGE_CYCLE,
    LOADING_MESSAGES, UI_FONT_FAMILY, COLORBLIND_COLORS
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
        self._setup_keyboard_shortcuts()
        self.init_ui()
    
    def _setup_window(self):
        self.setWindowTitle("Writing Tools - Review Changes")
        self.setMinimumSize(500, 200)
        
        icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'icons', 'app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
    
    def _setup_keyboard_shortcuts(self):
        accept_apply_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        accept_apply_shortcut.activated.connect(self.accept_all_and_apply)
    
    def accept_all_and_apply(self):
        self.accept_all_changes()
        self.apply_selected_changes()
    
    def init_ui(self):
        UIUtils.setup_window_and_layout(self)
        
        layout = QVBoxLayout(self.background)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        self.background.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        if self.loading:
            self.changes = []
        
        self._create_editor_ui(layout)
        
        if self.loading:
            self._create_loading_overlay()
    
    def _create_loading_overlay(self):
        self.loading_overlay = QWidget(self.background)
        self.loading_overlay.setStyleSheet(f"""
            QWidget {{
                background-color: {'rgba(42, 42, 42, 0.9)' if colorMode == 'dark' else 'rgba(255, 255, 255, 0.9)'};
                border-radius: 8px;
            }}
        """)
        
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.setContentsMargins(40, 40, 40, 40)
        overlay_layout.setSpacing(15)
        
        self.loading_label = QLabel("Processing with AI")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 18px;
                font-family: {UI_FONT_FAMILY};
                font-weight: 600;
                background-color: transparent;
            }}
        """)
        
        subtitle = QLabel("Analyzing your text and generating improvements...")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {'#aaaaaa' if colorMode == 'dark' else '#666666'};
                font-size: 14px;
                font-family: {UI_FONT_FAMILY};
                background-color: transparent;
            }}
        """)
        
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.loading_label)
        overlay_layout.addWidget(subtitle)
        overlay_layout.addStretch()
        
        self.loading_overlay.setGeometry(self.background.rect())
        self.loading_overlay.show()
        
        self._start_loading_animation()
        
        def update_overlay_position():
            if hasattr(self, 'loading_overlay') and self.loading_overlay:
                self.loading_overlay.setGeometry(self.background.rect())
        
        self.background.resizeEvent = lambda event: (
            QWidget.resizeEvent(self.background, event),
            update_overlay_position()
        )
    
    def _create_editor_ui(self, layout: QVBoxLayout):
        try:
            self.editor = InlineChangeEditor(self.changes, self.original_text, self.differ)
            self.editor.change_accepted.connect(self.on_change_accepted)
            self.editor.change_rejected.connect(self.on_change_rejected)
            layout.addWidget(self.editor)
            
            self.status_bar = ChangeStatusBar(self.changes)
            layout.addWidget(self.status_bar)
            
            controls = self._create_control_buttons()
            layout.addLayout(controls)
            
            QtCore.QTimer.singleShot(100, self._adjust_window_size)
        except Exception as e:
            logging.error(f"Error creating editor UI: {e}")
            self._show_error_message(layout, "Failed to create editor interface")
    
    def _show_error_message(self, layout: QVBoxLayout, message: str):
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
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setStyleSheet(StyleManager.get_scroll_area_style())
        return scroll_area
    
    def _add_shadow_effect(self, widget: QWidget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(0, 0, 0, 30 if colorMode == 'light' else 60))
        widget.setGraphicsEffect(shadow)
    
    def _start_loading_animation(self):
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
        logging.debug("Updating track changes editor with AI suggestion")
        
        try:
            self.suggested_text = suggested_text
            self.loading = False
            
            if hasattr(self, 'loading_timer'):
                self.loading_timer.stop()
            
            if hasattr(self, 'loading_overlay') and self.loading_overlay:
                self.loading_overlay.hide()
                self.loading_overlay.deleteLater()
                self.loading_overlay = None
            
            self.changes = self.differ.get_changes(self.original_text, suggested_text)
            
            if hasattr(self, 'editor'):
                self.editor.changes = self.changes
                self.editor.update_preview_with_inline_changes()
            
            if hasattr(self, 'status_bar'):
                self.status_bar.changes = self.changes
                self.status_bar.update_status()
            
        except Exception as e:
            logging.error(f"Error updating with suggestion: {e}")
            if hasattr(self, 'loading_overlay') and self.loading_overlay:
                self.loading_overlay.hide()
                self.loading_overlay.deleteLater()
                self.loading_overlay = None
    
    def _clear_layout(self, layout: QVBoxLayout):
        for i in reversed(range(layout.count())):
            child = layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
    
    def _create_loading_control_buttons(self) -> QHBoxLayout:
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
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)
        
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(8)
        
        accept_all_btn = QPushButton("Accept All")
        accept_all_icon = get_icon_path('check')
        if os.path.exists(accept_all_icon):
            accept_all_btn.setIcon(QtGui.QIcon(accept_all_icon))
            accept_all_btn.setIconSize(BUTTON_ICON_SIZE)
        accept_all_btn.setStyleSheet(StyleManager.get_button_style())
        accept_all_btn.clicked.connect(self.accept_all_changes)
        self._add_shadow_effect(accept_all_btn)
        
        reject_all_btn = QPushButton("Reject All")
        reject_all_icon = get_icon_path('cross')
        if os.path.exists(reject_all_icon):
            reject_all_btn.setIcon(QtGui.QIcon(reject_all_icon))
            reject_all_btn.setIconSize(BUTTON_ICON_SIZE)
        reject_all_btn.setStyleSheet(StyleManager.get_button_style())
        reject_all_btn.clicked.connect(self.reject_all_changes)
        self._add_shadow_effect(reject_all_btn)
        
        secondary_layout.addWidget(accept_all_btn)
        secondary_layout.addWidget(reject_all_btn)
        
        primary_layout = QHBoxLayout()
        primary_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_icon = get_icon_path('cross')
        if os.path.exists(cancel_icon):
            cancel_btn.setIcon(QtGui.QIcon(cancel_icon))
            cancel_btn.setIconSize(BUTTON_ICON_SIZE)
        cancel_btn.setStyleSheet(StyleManager.get_button_style())
        cancel_btn.clicked.connect(self.close)
        self._add_shadow_effect(cancel_btn)
        
        apply_btn = QPushButton("Apply Changes")
        apply_icon = get_icon_path('check')
        if os.path.exists(apply_icon):
            apply_btn.setIcon(QtGui.QIcon(apply_icon))
            apply_btn.setIconSize(BUTTON_ICON_SIZE)
        primary_bg = COLORBLIND_COLORS['primary_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['primary_light']
        primary_hover = COLORBLIND_COLORS['primary_hover_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['primary_hover_light']
        primary_pressed = COLORBLIND_COLORS['primary_pressed_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['primary_pressed_light']
        
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_bg};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-family: {UI_FONT_FAMILY};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {primary_pressed};
            }}
        """)
        apply_btn.clicked.connect(self.apply_selected_changes)
        self._add_shadow_effect(apply_btn)
        
        primary_layout.addWidget(cancel_btn)
        primary_layout.addWidget(apply_btn)
        
        layout.addLayout(secondary_layout)
        layout.addStretch()
        layout.addLayout(primary_layout)
        
        return layout
    
    def on_change_accepted(self, index: int):
        self.status_bar.update_status()
        logging.debug(f"Change {index} accepted")
    
    def on_change_rejected(self, index: int):
        self.status_bar.update_status()
        logging.debug(f"Change {index} rejected")
    
    def accept_all_changes(self):
        for change in self.changes:
            if change['status'] == 'pending':
                change['status'] = 'accepted'
        
        self.editor.update_all_widgets()
        self.status_bar.update_status()
    
    def reject_all_changes(self):
        for change in self.changes:
            if change['status'] == 'pending':
                change['status'] = 'rejected'
        
        self.editor.update_all_widgets()
        self.status_bar.update_status()
    
    def apply_selected_changes(self):
        final_text = self.editor.build_current_text()
        logging.debug(f"Applying final text: '{final_text[:50]}...'")
        
        self.close()
        QtCore.QTimer.singleShot(100, lambda: self.changes_applied.emit(final_text))
    
    def build_final_text(self) -> str:
        return self.editor.build_current_text()
    
    def _adjust_window_size(self):
        """Dynamic window sizing that fits content based on actual text measurement"""
        try:
            # Get screen dimensions for maximum height calculation
            screen = QtWidgets.QApplication.screenAt(self.pos())
            if not screen:
                screen = QtWidgets.QApplication.primaryScreen()
            screen_height = screen.geometry().height()
            max_screen_height = int(screen_height * 0.8)  # 80% of screen height
            
            # Calculate text box height dynamically based on content
            text_box_height = self._calculate_optimal_text_height(max_screen_height)
            
            # Set the text box height
            if hasattr(self, 'editor') and hasattr(self.editor, 'preview_text_display'):
                self.editor.preview_text_display.setFixedHeight(text_box_height)
            
            # Calculate actual window height needed based on UI elements
            header_height = 35  # Preview header height
            status_bar_height = 35  # Estimated status bar height
            control_buttons_height = 50  # Control buttons area height
            layout_margins = 16  # Top and bottom margins
            layout_spacing = 12  # Spacing gaps
            
            # Calculate total window height needed
            calculated_height = (header_height + text_box_height + status_bar_height +
                               control_buttons_height + layout_margins + layout_spacing)
            
            # Set reasonable bounds
            min_window_height = 240
            window_height = max(min_window_height, min(calculated_height, max_screen_height))
            
            # Set window size with dynamic height (fixed width as requested)
            self.resize(600, window_height)
            
            # Update minimum size to be content-aware
            content_aware_min_height = max(200, calculated_height - 50)  # Allow some manual shrinking
            self.setMinimumSize(500, content_aware_min_height)
            
            # Center on screen
            frame_geometry = self.frameGeometry()
            screen_center = screen.geometry().center()
            frame_geometry.moveCenter(screen_center)
            self.move(frame_geometry.topLeft())
            
        except Exception as e:
            logging.error(f"Error adjusting window size: {e}")
            # Fallback to smaller default size
            self.resize(600, 300)
            self.setMinimumSize(500, 250)
    
    def _calculate_optimal_text_height(self, max_screen_height: int) -> int:
        """Calculate optimal text box height based on actual content, properly accounting for newlines"""
        try:
            # Use a more reliable approach: estimate based on line count and character count
            text_to_measure = self.original_text or ""
            
            # If we have changes, use the HTML content for measurement
            if hasattr(self, 'editor') and self.editor and len(self.changes) > 0:
                # Create temporary widget for accurate measurement
                temp_widget = QTextEdit()
                temp_widget.setFixedWidth(560)
                temp_widget.setHtml(self.editor.build_html_with_changes())
                
                # Force layout update
                temp_widget.document().adjustSize()
                document_height = int(temp_widget.document().size().height())
                temp_widget.deleteLater()
                
                line_height = 22
                suggestion_buffer = 2 * line_height
                optimal_height = document_height + 40 + suggestion_buffer
            else:
                lines = text_to_measure.split('\n')
                line_height = 22
                chars_per_line = 75
                
                total_wrapped_lines = 0
                for line in lines:
                    if len(line.strip()) == 0:
                        total_wrapped_lines += 1
                    else:
                        wrapped_count = max(1, (len(line) + chars_per_line - 1) // chars_per_line)
                        total_wrapped_lines += wrapped_count
                
                paragraph_breaks = text_to_measure.count('\n\n')
                extra_paragraph_space = paragraph_breaks * (line_height * 0.5)
                
                optimal_height = (total_wrapped_lines * line_height) + extra_paragraph_space + 50
            
            suggestion_buffer = 2 * line_height
            optimal_height += suggestion_buffer
            
            min_text_height = 120
            max_text_height = max_screen_height - 150
            
            return max(min_text_height, min(optimal_height, max_text_height))
            
        except Exception as e:
            logging.error(f"Error calculating optimal text height: {e}")
            text_length = len(self.original_text) if self.original_text else 0
            newline_count = self.original_text.count('\n') if self.original_text else 0
            
            base_height = max(120, min(text_length // 3, 300))
            newline_bonus = newline_count * 22
            suggestion_buffer = 2 * 22
            
            return min(base_height + newline_bonus + suggestion_buffer, 500)