"""Main Track Changes Editor"""

import logging
import os
import sys
from typing import List, Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QWidget, QSizePolicy, QGraphicsDropShadowEffect

from ui.UIUtils import UIUtils, colorMode
from .constants import BUTTON_ICON_SIZE, UI_FONT_FAMILY, COLORBLIND_COLORS
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
        self._setup_resize_handler()
    
    def _setup_window(self):
        self.setWindowTitle("Writing Tools - Review Changes")
        self.setMinimumSize(500, 200)
        
        icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'icons', 'app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
    
    def _setup_keyboard_shortcuts(self):
        accept_apply_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        accept_apply_shortcut.activated.connect(self.accept_all_and_apply)
        
        escape_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.close)
    
    def accept_all_and_apply(self):
        self.accept_all_changes()
        self.apply_selected_changes()
    
    def init_ui(self):
        UIUtils.setup_window_and_layout(self)
        
        self.main_layout = QVBoxLayout(self.background)
        self.main_layout.setContentsMargins(8, 6, 8, 6)
        self.main_layout.setSpacing(4)
        
        self.background.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self._create_full_ui()
        
        if self.loading:
            self.changes = []
            self._show_loading_in_content_area()
        else:
            self._show_editor_content()
    
    def _create_full_ui(self):
        """Create the complete UI structure"""
        self.preview_header = self._create_live_preview_header()
        self.main_layout.addWidget(self.preview_header)
        
        self.content_area = QWidget()
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        self.main_layout.addWidget(self.content_area)
        
        self.status_bar = ChangeStatusBar([])
        self.status_bar.setFixedHeight(40)
        self.status_bar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.main_layout.addWidget(self.status_bar)
        
        controls = self._create_control_buttons()
        controls_widget = QtWidgets.QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setFixedHeight(50)
        self.main_layout.addWidget(controls_widget)
    
    def _create_live_preview_header(self) -> QWidget:
        """Create the Live Preview header"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(2, 2, 2, 4)
        header.setMaximumHeight(25)
        
        icon = QLabel()
        icon_path = get_icon_path('pencil')
        if os.path.exists(icon_path):
            icon.setPixmap(QtGui.QPixmap(icon_path).scaled(
                18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        title_label = QLabel('Review Changes')
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-weight: 600;
                font-size: 16px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
        """)
        
        subtitle_label = QLabel('Click on highlighted changes to accept or reject them')
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {'#aaaaaa' if colorMode == 'dark' else '#666666'};
                font-size: 12px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(subtitle_label)
        
        header.setFixedHeight(35)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        return header
    
    def _show_loading_in_content_area(self):
        """Show thinking animation in the content area"""
        self._clear_content_area()
        
        self.loading_container = QWidget()
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        
        self.loading_label = QLabel("Thinking")
        self.loading_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 18px;
                font-family: {UI_FONT_FAMILY};
                padding: 20px;
            }}
        """)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        loading_inner_container = QWidget()
        loading_inner_container.setFixedWidth(180)
        loading_inner_layout = QHBoxLayout(loading_inner_container)
        loading_inner_layout.setContentsMargins(0, 0, 0, 0)
        loading_inner_layout.addWidget(self.loading_label)
        
        loading_layout.addStretch()
        loading_layout.addWidget(loading_inner_container)
        loading_layout.addStretch()
        
        self.content_layout.addWidget(self.loading_container)
        
        self._start_thinking_animation()
        QtCore.QTimer.singleShot(100, self._adjust_window_size_for_loading)
    
    def _show_editor_content(self):
        """Show the actual editor content in the content area"""
        self._clear_content_area()
        
        try:
            self.editor = InlineChangeEditor(self.changes, self.original_text, self.differ)
            self.editor.change_accepted.connect(self.on_change_accepted)
            self.editor.change_rejected.connect(self.on_change_rejected)
            self.content_layout.addWidget(self.editor)
            
            self.status_bar.changes = self.changes
            self.status_bar.update_status()
            
        except Exception as e:
            logging.error(f"Error creating editor UI: {e}")
            self._show_error_message("Failed to create editor interface")
    
    def _clear_content_area(self):
        """Clear all widgets from the content area"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _show_error_message(self, message: str):
        self._clear_content_area()
        
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
        self.content_layout.addWidget(error_label)
    
    def _add_shadow_effect(self, widget: QWidget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(0, 0, 0, 30 if colorMode == 'light' else 60))
        widget.setGraphicsEffect(shadow)
    
    def _start_thinking_animation(self):
        """Start the thinking animation"""
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self._update_thinking_dots)
        self.thinking_dots_state = 0
        self.thinking_dots = ["", ".", "..", "..."]
        self.thinking_timer.setInterval(300)
        
        self.thinking_dots_state = 0
        self.loading_label.setText("Thinking")
        self.thinking_timer.start()
    
    def _update_thinking_dots(self):
        """Update the thinking animation dots"""
        self.thinking_dots_state = (self.thinking_dots_state + 1) % len(self.thinking_dots)
        dots = self.thinking_dots[self.thinking_dots_state]
        self.loading_label.setText(f"Thinking{dots}")
    
    def _stop_thinking_animation(self):
        """Stop the thinking animation"""
        if hasattr(self, 'thinking_timer'):
            self.thinking_timer.stop()
        if hasattr(self, 'loading_container'):
            self.loading_container.hide()
    
    def update_with_suggestion(self, suggested_text: str):
        logging.debug("Updating track changes editor with AI suggestion")
        
        try:
            self.suggested_text = suggested_text
            self.loading = False
            
            self._stop_thinking_animation()
            self.changes = self.differ.get_changes(self.original_text, suggested_text)
            self._show_editor_content()
            
        except Exception as e:
            logging.error(f"Error updating with suggestion: {e}")
            self._stop_thinking_animation()
            self._show_error_message(f"Error processing suggestion: {e}")
    
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
    
    def on_change_rejected(self, index: int):
        self.status_bar.update_status()
    
    def accept_all_changes(self):
        self._update_all_changes('accepted')
    
    def reject_all_changes(self):
        self._update_all_changes('rejected')
    
    def _update_all_changes(self, status: str):
        for change in self.changes:
            if change['status'] == 'pending':
                change['status'] = status
        self.editor.update_all_widgets()
        self.status_bar.update_status()
    
    def apply_selected_changes(self):
        final_text = self.editor.build_current_text()
        self.close()
        QtCore.QTimer.singleShot(100, lambda: self.changes_applied.emit(final_text))
    
    def _adjust_window_size(self):
        """Dynamic window sizing that fits content"""
        try:
            screen = QtWidgets.QApplication.screenAt(self.pos()) or QtWidgets.QApplication.primaryScreen()
            max_screen_height = int(screen.geometry().height() * 0.8)
            text_box_height = self._calculate_optimal_text_height(max_screen_height)
            
            if hasattr(self, 'editor') and hasattr(self.editor, 'preview_text_display'):
                self.editor.preview_text_display.setMinimumHeight(min(text_box_height, 120))
                self.editor.preview_text_display.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            
            calculated_height = 35 + text_box_height + 40 + 50 + 16 + 12  # header + text + status + controls + margins + spacing
            window_height = max(240, min(calculated_height, max_screen_height))
            
            self.resize(600, window_height)
            self.setMinimumSize(500, max(200, calculated_height - 50))
            
            # Center window
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(screen.geometry().center())
            self.move(frame_geometry.topLeft())
            
        except Exception as e:
            logging.error(f"Error adjusting window size: {e}")
            self.resize(600, 300)
            self.setMinimumSize(500, 250)
    
    def _calculate_optimal_text_height(self, max_screen_height: int) -> int:
        """Calculate optimal text box height based on content"""
        try:
            text_to_measure = self.original_text or ""
            
            if hasattr(self, 'editor') and self.editor and len(self.changes) > 0:
                temp_widget = QTextEdit()
                temp_widget.setFixedWidth(560)
                temp_widget.setHtml(self.editor.build_html_with_changes())
                
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
    
    def _adjust_window_size_for_loading(self):
        """Set window size for loading state"""
        try:
            self._adjust_window_size()
        except Exception:
            self.resize(600, 400)
    
    def _setup_resize_handler(self):
        """Set up resize event handler"""
        self.original_resize_event = self.resizeEvent
        self.resizeEvent = self._handle_resize_event
    
    def _handle_resize_event(self, event):
        """Handle window resize events"""
        if self.original_resize_event:
            self.original_resize_event(event)
        
        if hasattr(self, 'editor') and hasattr(self.editor, 'preview_text_display') and not self.loading:
            self._adjust_text_box_for_window_size()
    
    def _adjust_text_box_for_window_size(self):
        """Adjust text box size based on current window size"""
        try:
            fixed_height = 35 + 40 + 50 + 16 + 12  # header + status + controls + margins + spacing
            available_height = self.height() - fixed_height
            min_text_height = 120
            max_text_height = max(min_text_height, available_height - 20)
            
            self.editor.preview_text_display.setMinimumHeight(min_text_height)
            self.editor.preview_text_display.setMaximumHeight(max_text_height)
            
        except Exception as e:
            logging.error(f"Error adjusting text box for window size: {e}")