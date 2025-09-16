"""Inline change editor for Track Changes"""

import logging
import os
from typing import List, Dict

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy, QGraphicsDropShadowEffect

from ui.UIUtils import colorMode
from .constants import (
    UI_FONT_FAMILY, COLORBLIND_COLORS
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
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(2, 2, 2, 4)
        header.setMaximumHeight(25)
        
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
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
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
        layout.setContentsMargins(0, 4, 0, 0)  # Add top margin for header spacing
        layout.setSpacing(3)  # Increased spacing for better visual balance
        
        # Live preview section
        preview_header = self._create_header_section(
            'pencil', 'Live Preview', 'Click on highlighted changes to accept or reject them'
        )
        # Ensure header has fixed height to prevent resizing
        preview_header.setFixedHeight(35)
        preview_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(preview_header)
        
        # Preview text display - height will be dynamically adjusted by main editor
        self.preview_text_display = ClickableTextEdit()
        self.preview_text_display.setReadOnly(True)
        # Set size policy to allow both horizontal and vertical expansion for resizing
        self.preview_text_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_text_display.setStyleSheet(StyleManager.get_text_edit_style())
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(0, 0, 0, 30 if colorMode == 'light' else 60))
        self.preview_text_display.setGraphicsEffect(shadow)
        
        self.preview_text_display.setAcceptRichText(True)
        self.preview_text_display.change_accepted.connect(self.accept_change)
        self.preview_text_display.change_rejected.connect(self.reject_change)
        self.update_preview_with_inline_changes()
        layout.addWidget(self.preview_text_display, 1)
        
        self.setLayout(layout)
    
    def _adjust_preview_height(self):
        """Height adjustment is now handled by the main editor - this method is kept for compatibility"""
        pass
    
    def on_change_accepted(self, index: int):
        """Handle change acceptance"""
        self.update_preview_text()
        self.change_accepted.emit(index)
    
    def on_change_rejected(self, index: int):
        """Handle change rejection"""
        self.update_preview_text()
        self.change_rejected.emit(index)
    
    def update_all_widgets(self):
        """Update preview text"""
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
        """Add HTML for pending changes with colorblind-friendly styling and click handlers"""
        change_type = change['type']
        
        if change_type == 'replace':
            change_text = f'<span style="background-color: {"#4a3c2a" if colorMode == "dark" else "#fff3cd"}; padding: 2px 4px; border-radius: 3px; margin: 0 1px;" title="Replacement: Click old text to reject, new text to accept">'
            # Original text (clickable to reject) with strikethrough - using orange for removal
            reject_color = COLORBLIND_COLORS['reject_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['reject_light']
            change_text += f'<a href="change:{change_index}:reject" style="text-decoration: line-through; color: {reject_color}; cursor: pointer; text-decoration-thickness: 2px;">{self._escape_html(change["original"], preserve_inline_newlines=True)}</a>'
            change_text += ' → '
            # Suggested text (clickable to accept) with emphasis - using blue for addition
            accept_color = COLORBLIND_COLORS['accept_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['accept_light']
            change_text += f'<a href="change:{change_index}:accept" style="font-weight: bold; color: {accept_color}; text-decoration: none; cursor: pointer;">{self._escape_html(change["suggested"], preserve_inline_newlines=True)}</a>'
            change_text += '</span>'
            html_parts.append(change_text)
        elif change_type == 'insert':
            # Blue background for insertions (colorblind-friendly)
            accept_bg = COLORBLIND_COLORS['accept_bg_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['accept_bg_light']
            accept_color = COLORBLIND_COLORS['accept_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['accept_light']
            change_text = f'<a href="change:{change_index}:accept" style="background-color: {accept_bg}; color: {accept_color}; padding: 2px 4px; border-radius: 3px; font-weight: bold; text-decoration: none; cursor: pointer; border: 1px dashed {accept_color};" title="Click to accept this addition">{self._escape_html(change["suggested"], preserve_inline_newlines=True)}</a>'
            html_parts.append(change_text)
        elif change_type == 'delete':
            # Orange background for deletions (colorblind-friendly)
            reject_bg = COLORBLIND_COLORS['reject_bg_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['reject_bg_light']
            reject_color = COLORBLIND_COLORS['reject_dark'] if colorMode == 'dark' else COLORBLIND_COLORS['reject_light']
            change_text = f'<a href="change:{change_index}:accept" style="background-color: {reject_bg}; color: {reject_color}; padding: 2px 4px; border-radius: 3px; text-decoration: line-through; cursor: pointer; border: 1px dashed {reject_color}; text-decoration-thickness: 2px;" title="Click to accept this deletion">{self._escape_html(change["original"], preserve_inline_newlines=True)}</a>'
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