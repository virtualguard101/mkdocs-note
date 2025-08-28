"""
Managers Package

Contains high-level manager classes for coordinating operations.
"""

from .file_manager import FileManager
from .note_manager import NoteManager

__all__ = ['FileManager', 'NoteManager']