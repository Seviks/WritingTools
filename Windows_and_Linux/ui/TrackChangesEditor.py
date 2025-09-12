"""
Track Changes Editor - Backward compatibility wrapper

This module provides backward compatibility by importing the main TrackChangesEditor
from the new modular structure.
"""

# Import the main class from the new modular structure
from .track_changes import TrackChangesEditor

# Maintain backward compatibility
__all__ = ['TrackChangesEditor']