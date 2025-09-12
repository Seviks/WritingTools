"""Inline change editor for Track Changes"""

import logging
import os
from typing import List, Dict

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy, QGraphicsDropShadowEffect

from ui.UIUtils import colorMode
from .constants import (
    PREVIEW_MIN_HEIGHT, PREVIEW_MAX_HEIGHT, CHANGES_MIN_HEIGHT, CHANGES_MAX_HEIGHT,
    HTML_CHANGE_STYLES, MONOSPACE_FONT_FAMILY, UI_FONT_FAMILY
)
from .styles import get_icon_path, StyleManager
from .widgets import ClickableTextEdit, ChangeItemWidget
from .differ import TextDiffer


class InlineChangeEditor(QWidget):
    """Widget that displays changes inline with visual indicators"""
    
    change_accepted = Signal(int)
    change_rejected = Signal(int)
    
    def __init__(self, changes: List[Dict], original_text: str, differ: TextDiffer):
        super().__init__()
        self.changes = changes
        self.original_text = original_text
        self.differ = differ
        self.change_widgets = []
        self.init_ui()
    
    def _create_header_section(self, icon_name: str, title: str, subtitle: str = "") -> QWidget:
        """Create a consistent header section"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon
        icon = QLabel()
        icon_path = get_icon_path(icon_name)
        if os.path.exists(icon_path):
            icon.setPixmap(QtGui.QPixmap(icon_path).scaled(
                18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-weight: 600;
                font-size: 16px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Subtitle if provided
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: {'#aaaaaa' if colorMode == 'dark' else '#666666'};
                    font-size: 12px;
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                }}
            """)
            header_layout.addWidget(subtitle_label)
        
        return header
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Live preview section
        preview_header = self._create_header_section(
            'pencil', 'Live Preview', 'Click highlighted text to accept/reject changes'
        )
        layout.addWidget(preview_header)
        
        # Preview text display
        self.preview_text_display = ClickableTextEdit()
        self.preview_text_display.setReadOnly(True)
        self.preview_text_display.setMinimumHeight(PREVIEW_MIN_HEIGHT)
        self.preview_text_display.setMaximumHeight(PREVIEW_MAX_HEIGHT)
        self.preview_text_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.preview_text_display.setStyleSheet(StyleManager.get_text_edit_style())
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(0, 0, 0, 30 if colorMode == 'light' else 60))
        self.preview_text_display.setGraphicsEffect(shadow)
        
        self.preview_text_display.setAcceptRichText(True)
        self.preview_text_display.change_accepted.connect(self.accept_change)
        self.preview_text_display.change_rejected.connect(self.reject_change)
        self.update_preview_with_inline_changes()
        layout.addWidget(self.preview_text_display, 0)
        
        # Changes section
        changes_header = self._create_header_section(
            'list', 'Individual Changes', f'{len(self.changes)} changes'
        )
        layout.addWidget(changes_header)
        
        # Scroll area for changes
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(CHANGES_MIN_HEIGHT)
        scroll_area.setMaximumHeight(CHANGES_MAX_HEIGHT)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setStyleSheet(StyleManager.get_scroll_area_style())
        
        changes_widget = QWidget()
        changes_layout = QVBoxLayout(changes_widget)
        changes_layout.setContentsMargins(4, 4, 4, 4)
        changes_layout.setSpacing(1)
        
        # Add change widgets
        for i, change in enumerate(self.changes):
            change_widget = ChangeItemWidget(change, i)
            change_widget.change_accepted.connect(self.on_change_accepted)
            change_widget.change_rejected.connect(self.on_change_rejected)
            self.change_widgets.append(change_widget)
            changes_layout.addWidget(change_widget)
        
        changes_layout.addStretch()
        scroll_area.setWidget(changes_widget)
        layout.addWidget(scroll_area, 1)
        
        self.setLayout(layout)
    
    def on_change_accepted(self, index: int):
        """Handle change acceptance"""
        self.update_preview_text()
        if index < len(self.change_widgets):
            self.change_widgets[index].hide()
        self.change_accepted.emit(index)
    
    def on_change_rejected(self, index: int):
        """Handle change rejection"""
        self.update_preview_text()
        if index < len(self.change_widgets):
            self.change_widgets[index].hide()
        self.change_rejected.emit(index)
    
    def update_all_widgets(self):
        """Update all change widgets"""
        for widget in self.change_widgets:
            widget.update_ui()
        self.update_preview_text()
    
    def update_preview_text(self):
        """Update the preview text display based on current change states"""
        self.update_preview_with_inline_changes()
    
    def update_preview_with_inline_changes(self):
        """Update the preview to show inline changes with visual indicators"""
        html_content = self.build_html_with_changes()
        self.preview_text_display.setHtml(html_content)
    
    def accept_change(self, change_index: int):
        """Accept a specific change"""
        if 0 <= change_index < len(self.changes):
            self.changes[change_index]['status'] = 'accepted'
            self.update_preview_with_inline_changes()
            if change_index < len(self.change_widgets):
                self.change_widgets[change_index].hide()
            self.change_accepted.emit(change_index)
    
    def reject_change(self, change_index: int):
        """Reject a specific change"""
        if 0 <= change_index < len(self.changes):
            self.changes[change_index]['status'] = 'rejected'
            self.update_preview_with_inline_changes()
            if change_index < len(self.change_widgets):
                self.change_widgets[change_index].hide()
            self.change_rejected.emit(change_index)
    
    def build_html_with_changes(self) -> str:
        """Build HTML content showing changes inline with data attributes for click detection"""
        original_tokens = self.differ.tokenize(self.original_text)
        html_parts = []
        current_pos = 0
        
        sorted_changes = sorted(enumerate(self.changes), key=lambda x: x[1]['position'][0])
        
        for change_index, change in sorted_changes:
            start_pos, end_pos = change['position']
            
            # Add unchanged text before this change
            if current_pos < start_pos:
                unchanged_text = ''.join(original_tokens[current_pos:start_pos])
                html_parts.append(self._escape_html(unchanged_text))
            
            # Add the change with visual indicators
            status = change['status']
            if status == 'accepted':
                self._add_accepted_change_html(html_parts, change)
            elif status == 'rejected':
                html_parts.append(self._escape_html(change['original']))
            else:
                self._add_pending_change_html(html_parts, change, change_index)
            
            current_pos = end_pos
        
        # Add remaining unchanged text
        if current_pos < len(original_tokens):
            remaining_text = ''.join(original_tokens[current_pos:])
            html_parts.append(self._escape_html(remaining_text))
        
        return self._wrap_html_content(html_parts)
    
    def _add_accepted_change_html(self, html_parts: List[str], change: Dict):
        """Add HTML for accepted changes"""
        if change['type'] == 'replace':
            html_parts.append(self._escape_html(change['suggested'], preserve_inline_newlines=True))
        elif change['type'] == 'insert':
            html_parts.append(self._escape_html(change['suggested'], preserve_inline_newlines=True))
        # For delete, don't add anything (text is deleted)
    
    def _add_pending_change_html(self, html_parts: List[str], change: Dict, change_index: int):
        """Add HTML for pending changes with click handlers"""
        change_type = change['type']
        
        if change_type == 'replace':
            change_text = f'<span style="{HTML_CHANGE_STYLES["replace"]}" title="Click struck-through text to reject, bold text to accept">'
            # Original text (clickable to reject) - preserve inline newlines
            change_text += f'<a href="change:{change_index}:reject" style="text-decoration: line-through; color: inherit; cursor: pointer;">{self._escape_html(change["original"], preserve_inline_newlines=True)}</a>'
            # Suggested text (clickable to accept) - preserve inline newlines
            change_text += f'<a href="change:{change_index}:accept" style="font-weight: bold; color: #007bff; text-decoration: none; cursor: pointer;">{self._escape_html(change["suggested"], preserve_inline_newlines=True)}</a>'
            change_text += '</span>'
            html_parts.append(change_text)
        elif change_type == 'insert':
            change_text = f'<a href="change:{change_index}:accept" style="{HTML_CHANGE_STYLES["insert"]}" title="Click to accept insertion">{self._escape_html(change["suggested"], preserve_inline_newlines=True)}</a>'
            html_parts.append(change_text)
        elif change_type == 'delete':
            change_text = f'<a href="change:{change_index}:accept" style="{HTML_CHANGE_STYLES["delete"]}" title="Click to accept deletion">{self._escape_html(change["original"], preserve_inline_newlines=True)}</a>'
            html_parts.append(change_text)
    
    def _escape_html(self, text: str, preserve_inline_newlines: bool = False) -> str:
        """Escape HTML special characters and handle newlines appropriately"""
        escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        # Convert newlines to <br> for regular text, but preserve them inline for changes
        if preserve_inline_newlines:
            return escaped  # Keep newlines as-is for inline changes
        else:
            return escaped.replace('\n', '<br>')  # Convert to <br> for regular text
    
    def _wrap_html_content(self, html_parts: List[str]) -> str:
        """Wrap HTML parts in complete HTML structure"""
        return f"""<html><head><style>body{{font-family:{UI_FONT_FAMILY};font-size:15px;line-height:1.2;margin:0;padding:0;color:{'#ffffff' if colorMode == 'dark' else '#333333'};}}a{{color:inherit;}}a:hover{{opacity:0.8;}}</style></head><body>{''.join(html_parts)}</body></html>"""
    
    def build_current_text(self) -> str:
        """Build the current text state based on accepted/rejected changes"""
        try:
            original_tokens = self.differ.tokenize(self.original_text)
            result_tokens = original_tokens.copy()
            
            # Apply accepted changes in reverse order to maintain positions
            accepted_changes = [c for c in self.changes if c['status'] == 'accepted']
            accepted_changes.sort(key=lambda x: x['position'][0], reverse=True)
            
            for change in accepted_changes:
                start_pos, end_pos = change['position']
                
                # Validate positions
                if start_pos < 0 or end_pos > len(result_tokens):
                    logging.warning(f"Invalid change position: {start_pos}-{end_pos}")
                    continue
                
                if change['type'] == 'replace':
                    new_tokens = self.differ.tokenize(change['suggested'])
                    result_tokens[start_pos:end_pos] = new_tokens
                elif change['type'] == 'insert':
                    new_tokens = self.differ.tokenize(change['suggested'])
                    result_tokens[start_pos:start_pos] = new_tokens
                elif change['type'] == 'delete':
                    del result_tokens[start_pos:end_pos]
            
            return ''.join(result_tokens)
            
        except Exception as e:
            logging.error(f"Error building current text: {e}")
            return self.original_text  # Fallback to original text