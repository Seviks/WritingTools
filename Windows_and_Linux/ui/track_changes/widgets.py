"""UI widgets for Track Changes Editor"""

import logging
import os
from typing import Dict, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QWidget

from ui.UIUtils import colorMode
from .constants import SMALL_ICON_SIZE, CHANGE_BUTTON_SIZE, CONTROL_BUTTON_SIZE, UI_FONT_FAMILY
from .styles import get_icon_path, StyleManager


class IconButtonHelper:
    """Helper class for creating consistent icon buttons"""
    
    @staticmethod
    def create_icon_button(icon_name: str, size: Tuple[int, int], style_type: str = "success", 
                          tooltip: str = "", fallback_text: str = "") -> QPushButton:
        """Create a standardized icon button"""
        button = QPushButton()
        icon_path = get_icon_path(icon_name)
        
        if os.path.exists(icon_path):
            button.setIcon(QtGui.QIcon(icon_path))
            button.setIconSize(SMALL_ICON_SIZE)
        elif fallback_text:
            button.setText(fallback_text)
        
        button.setFixedSize(*size)
        button.setStyleSheet(StyleManager.get_small_icon_button_style(style_type))
        
        if tooltip:
            button.setToolTip(tooltip)
        
        return button


class ChangeControlWidget(QtWidgets.QWidget):
    """Professional widget with accept/reject buttons using proper icons"""
    
    accepted = Signal(int)
    rejected = Signal(int)
    
    def __init__(self, change: Dict, index: int):
        super().__init__()
        self.change = change
        self.index = index
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        
        # Accept button
        accept_btn = IconButtonHelper.create_icon_button(
            'check', CONTROL_BUTTON_SIZE, "success", "Accept this change", "✓"
        )
        accept_btn.clicked.connect(lambda: self.accepted.emit(self.index))
        
        # Reject button
        reject_btn = IconButtonHelper.create_icon_button(
            'cross', CONTROL_BUTTON_SIZE, "danger", "Reject this change", "✗"
        )
        reject_btn.clicked.connect(lambda: self.rejected.emit(self.index))
        
        layout.addWidget(accept_btn)
        layout.addWidget(reject_btn)
        self.setLayout(layout)


class ChangeItemWidget(QWidget):
    """Professional widget representing a single change with modern styling"""
    
    change_accepted = Signal(int)
    change_rejected = Signal(int)
    
    def __init__(self, change: Dict, index: int):
        super().__init__()
        self.change = change
        self.index = index
        self.init_ui()
    
    def _get_change_display_text(self) -> str:
        """Generate display text based on change type"""
        try:
            change_type = self.change['type']
            
            if change_type == 'replace':
                original_clean = ' '.join(self.change['original'].split())
                suggested_clean = ' '.join(self.change['suggested'].split())
                return f"{original_clean} → {suggested_clean}"
            elif change_type == 'insert':
                suggested_clean = ' '.join(self.change['suggested'].split())
                return f"Add: {suggested_clean}"
            elif change_type == 'delete':
                original_clean = ' '.join(self.change['original'].split())
                return f"Remove: {original_clean}"
            
            return ""
        except Exception as e:
            logging.error(f"Error generating change display text: {e}")
            return "Change"
    
    def _create_status_display(self) -> QWidget:
        """Create status indicator with icons"""
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        
        status_icon = QLabel()
        status_label = QLabel()
        
        status = self.change['status']
        if status == 'accepted':
            icon_path = get_icon_path('check')
            if os.path.exists(icon_path):
                status_icon.setPixmap(QtGui.QPixmap(icon_path).scaled(
                    14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            status_label.setText("Accepted")
            status_label.setStyleSheet("color: #4CAF50; font-weight: 600; font-size: 12px;")
        elif status == 'rejected':
            icon_path = get_icon_path('cross')
            if os.path.exists(icon_path):
                status_icon.setPixmap(QtGui.QPixmap(icon_path).scaled(
                    14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            status_label.setText("Rejected")
            status_label.setStyleSheet("color: #f44336; font-weight: 600; font-size: 12px;")
        else:
            status_label.setText("Pending")
            status_label.setStyleSheet(f"color: {'#cccccc' if colorMode == 'dark' else '#666666'}; font-size: 12px;")
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_label)
        return status_container
    
    def init_ui(self):
        self.setStyleSheet(f"""
            ChangeItemWidget {{
                background-color: {'#333' if colorMode == 'dark' else 'white'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#e0e0e0'};
                border-radius: 8px;
                margin: 2px;
            }}
            ChangeItemWidget:hover {{
                background-color: {'#3a3a3a' if colorMode == 'dark' else '#f8f8f8'};
                border-color: {'#666' if colorMode == 'dark' else '#d0d0d0'};
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Change type icon
        type_icon = QLabel()
        icon_map = {'replace': 'pencil', 'insert': 'plus', 'delete': 'minus'}
        icon_path = get_icon_path(icon_map.get(self.change['type'], 'pencil'))
        
        if os.path.exists(icon_path):
            type_icon.setPixmap(QtGui.QPixmap(icon_path).scaled(
                16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        layout.addWidget(type_icon)
        
        # Change text display
        text = self._get_change_display_text()
        change_label = QLabel(text)
        change_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 13px;
                font-family: {UI_FONT_FAMILY};
                padding: 4px 8px;
                background-color: {'#444' if colorMode == 'dark' else '#f5f5f5'};
                border-radius: 4px;
                border: 1px solid {'#555' if colorMode == 'dark' else '#e0e0e0'};
            }}
        """)
        change_label.setWordWrap(True)
        layout.addWidget(change_label, 1)
        
        # Status indicator
        layout.addWidget(self._create_status_display())
        
        # Accept/Reject buttons (only show if pending)
        if self.change['status'] == 'pending':
            accept_btn = IconButtonHelper.create_icon_button(
                'check', CHANGE_BUTTON_SIZE, "success", "Accept this change", "✓"
            )
            reject_btn = IconButtonHelper.create_icon_button(
                'cross', CHANGE_BUTTON_SIZE, "danger", "Reject this change", "✗"
            )
            
            accept_btn.clicked.connect(self.accept_change)
            reject_btn.clicked.connect(self.reject_change)
            
            layout.addWidget(accept_btn)
            layout.addWidget(reject_btn)
        
        self.setLayout(layout)
    
    def accept_change(self):
        """Accept this change"""
        self.change['status'] = 'accepted'
        self.change_accepted.emit(self.index)
        self.update_ui()
    
    def reject_change(self):
        """Reject this change"""
        self.change['status'] = 'rejected'
        self.change_rejected.emit(self.index)
        self.update_ui()
    
    def update_ui(self):
        """Update UI after status change"""
        layout = self.layout()
        for i in reversed(range(layout.count())):
            child = layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
        self.init_ui()


class ClickableTextEdit(QTextEdit):
    """Custom QTextEdit that can handle clicks on HTML elements using data attributes"""
    
    change_accepted = Signal(int)
    change_rejected = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on change links"""
        if event.button() == Qt.MouseButton.LeftButton:
            anchor = self.anchorAt(event.pos())
            if anchor and anchor.startswith('change:'):
                try:
                    parts = anchor.split(':')
                    if len(parts) >= 3:
                        change_index = int(parts[1])
                        action = parts[2]
                        
                        if action == 'accept':
                            self.change_accepted.emit(change_index)
                        elif action == 'reject':
                            self.change_rejected.emit(change_index)
                        return
                except (ValueError, IndexError) as e:
                    logging.error(f"Error parsing change anchor: {e}")
        
        super().mousePressEvent(event)


class ChangeStatusBar(QWidget):
    """Modern status bar showing change statistics with icons"""
    
    def __init__(self, changes):
        super().__init__()
        self.changes = changes
        self.init_ui()
        self.update_status()
    
    def init_ui(self):
        self.setStyleSheet(f"""
            ChangeStatusBar {{
                background-color: {'#333' if colorMode == 'dark' else '#f8f8f8'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#e0e0e0'};
                border-radius: 6px;
                margin: 5px 0px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(15)
        
        # Status icon
        status_icon = QLabel()
        status_icon_path = get_icon_path('list')
        if os.path.exists(status_icon_path):
            status_icon.setPixmap(QtGui.QPixmap(status_icon_path).scaled(
                16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        layout.addWidget(status_icon)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 13px;
                font-family: {UI_FONT_FAMILY};
                font-weight: 500;
            }}
        """)
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.setLayout(layout)
    
    def update_status(self):
        """Update status display with modern formatting"""
        total = len(self.changes)
        accepted = len([c for c in self.changes if c['status'] == 'accepted'])
        rejected = len([c for c in self.changes if c['status'] == 'rejected'])
        pending = total - accepted - rejected
        
        status_parts = []
        status_parts.append(f"<span style='color: {'#aaaaaa' if colorMode == 'dark' else '#666666'};'>{total} total</span>")
        
        if accepted > 0:
            status_parts.append(f"<span style='color: #4CAF50; font-weight: 600;'>{accepted} accepted</span>")
        
        if rejected > 0:
            status_parts.append(f"<span style='color: #f44336; font-weight: 600;'>{rejected} rejected</span>")
        
        if pending > 0:
            status_parts.append(f"<span style='color: {'#cccccc' if colorMode == 'dark' else '#666666'};'>{pending} pending</span>")
        
        self.status_label.setText(" • ".join(status_parts))