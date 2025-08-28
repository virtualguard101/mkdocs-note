"""
Base Parser

Abstract base class for all parsers in the system.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseParser(ABC):
    """
    Abstract base class for all parsers.
    
    Provides common functionality and defines the interface for parsing operations.
    """

    def __init__(self):
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> Any:
        """
        Parse the given file and return extracted information.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Parsed information (type depends on specific parser)
        """
        pass

    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        return file_path.exists() and file_path.is_file()

    def _read_file_safely(self, file_path: Path, encoding: str = 'utf-8') -> str:
        """
        Safely read a file with error handling.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding to use
            
        Returns:
            File content as string, empty string if error occurs
        """
        try:
            return file_path.read_text(encoding=encoding)
        except (PermissionError, UnicodeDecodeError, OSError) as e:
            print(f"Error reading file {file_path}: {e}")
            return ""