import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.utils.fileps.handlers import NoteScanner, AssetScanner
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger


class TestNoteScanner(unittest.TestCase):
    """Test cases for NoteScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.file_scanner = NoteScanner(self.config, self.logger)

    def test_initialization(self):
        """Test NoteScanner initialization."""
        self.assertIs(self.file_scanner.config, self.config)
        self.assertIs(self.file_scanner.logger, self.logger)

    @patch('pathlib.Path.exists')
    def test_scan_notes_directory_not_exists(self, mock_exists):
        """Test scan_notes when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = self.file_scanner.scan_notes()
        
        self.assertEqual(result, [])
        mock_exists.assert_called_once()

    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_scan_notes_success(self, mock_exists, mock_rglob):
        """Test successful note scanning."""
        mock_exists.return_value = True
        
        # Create mock file paths with proper mocking
        mock_files = []
        
        # Create mock for note1.md
        mock_file1 = Mock()
        mock_file1.is_file.return_value = True
        mock_file1.name = 'note1.md'
        mock_file1.suffix = '.md'
        mock_file1.parts = ('notes', 'note1.md')
        mock_files.append(mock_file1)
        
        # Create mock for note2.ipynb
        mock_file2 = Mock()
        mock_file2.is_file.return_value = True
        mock_file2.name = 'note2.ipynb'
        mock_file2.suffix = '.ipynb'
        mock_file2.parts = ('notes', 'note2.ipynb')
        mock_files.append(mock_file2)
        
        # Create mock for subdir/note3.md
        mock_file3 = Mock()
        mock_file3.is_file.return_value = True
        mock_file3.name = 'note3.md'
        mock_file3.suffix = '.md'
        mock_file3.parts = ('notes', 'subdir', 'note3.md')
        mock_files.append(mock_file3)
        
        # Create mock for index.md (should be excluded)
        mock_file4 = Mock()
        mock_file4.is_file.return_value = True
        mock_file4.name = 'index.md'
        mock_file4.suffix = '.md'
        mock_file4.parts = ('notes', 'index.md')
        mock_files.append(mock_file4)
        
        # Create mock for README.md (should be excluded)
        mock_file5 = Mock()
        mock_file5.is_file.return_value = True
        mock_file5.name = 'README.md'
        mock_file5.suffix = '.md'
        mock_file5.parts = ('notes', 'README.md')
        mock_files.append(mock_file5)
        
        # Create mock for __pycache__/temp.py (should be excluded)
        mock_file6 = Mock()
        mock_file6.is_file.return_value = True
        mock_file6.name = 'temp.py'
        mock_file6.suffix = '.py'
        mock_file6.parts = ('notes', '__pycache__', 'temp.py')
        mock_files.append(mock_file6)
        
        mock_rglob.return_value = mock_files
        
        result = self.file_scanner.scan_notes()
        
        # Should return valid note files (excluding index.md, README.md, and __pycache__)
        self.assertEqual(len(result), 3)
        # Check that the returned files are the valid ones
        result_names = [f.name for f in result]
        self.assertIn('note1.md', result_names)
        self.assertIn('note2.ipynb', result_names)
        self.assertIn('note3.md', result_names)

    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_scan_notes_permission_error(self, mock_exists, mock_rglob):
        """Test scan_notes with permission error."""
        mock_exists.return_value = True
        mock_rglob.side_effect = PermissionError("Permission denied")
        
        result = self.file_scanner.scan_notes()
        
        self.assertEqual(result, [])

    def test_is_valid_note_file_markdown(self):
        """Test _is_valid_note_file with markdown file."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.md'
        mock_file.name = 'note.md'
        mock_file.parts = ('notes', 'note.md')
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertTrue(result)

    def test_is_valid_note_file_notebook(self):
        """Test _is_valid_note_file with Jupyter notebook."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.ipynb'
        mock_file.name = 'note.ipynb'
        mock_file.parts = ('notes', 'note.ipynb')
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertTrue(result)

    def test_is_valid_note_file_not_file(self):
        """Test _is_valid_note_file with directory."""
        mock_file = Mock()
        mock_file.is_file.return_value = False
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertFalse(result)

    def test_is_valid_note_file_unsupported_extension(self):
        """Test _is_valid_note_file with unsupported extension."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.txt'
        mock_file.name = 'note.txt'
        mock_file.parts = ('notes', 'note.txt')
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertFalse(result)

    def test_is_valid_note_file_excluded_pattern(self):
        """Test _is_valid_note_file with excluded pattern."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.md'
        mock_file.name = 'index.md'  # Should be excluded
        mock_file.parts = ('notes', 'index.md')
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertFalse(result)

    def test_is_valid_note_file_excluded_directory(self):
        """Test _is_valid_note_file in excluded directory."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.md'
        mock_file.name = 'note.md'
        mock_file.parts = ('notes', '__pycache__', 'note.md')  # In excluded directory
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertFalse(result)

    def test_is_valid_note_file_case_insensitive_extension(self):
        """Test _is_valid_note_file with uppercase extension."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.MD'  # Uppercase
        mock_file.name = 'note.MD'
        mock_file.parts = ('notes', 'note.MD')
        
        result = self.file_scanner._is_valid_note_file(mock_file)
        
        self.assertTrue(result)

    def test_config_integration(self):
        """Test that FileScanner uses config values correctly."""
        # Test with custom config
        custom_config = PluginConfig()
        custom_config.supported_extensions = {'.txt', '.py'}
        custom_config.exclude_patterns = {'test.txt'}
        custom_config.exclude_dirs = {'temp'}
        
        custom_scanner = NoteScanner(custom_config, self.logger)
        
        # Test with .txt file (should be valid with custom config)
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.txt'
        mock_file.name = 'note.txt'
        mock_file.parts = ('notes', 'note.txt')
        
        result = custom_scanner._is_valid_note_file(mock_file)
        self.assertTrue(result)
        
        # Test with excluded pattern
        mock_file.name = 'test.txt'
        result = custom_scanner._is_valid_note_file(mock_file)
        self.assertFalse(result)


class TestAssetScanner(unittest.TestCase):
    """Test cases for AssetScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.asset_scanner = AssetScanner(self.config, self.logger)

    def test_initialization(self):
        """Test AssetScanner initialization."""
        self.assertIs(self.asset_scanner.config, self.config)
        self.assertIs(self.asset_scanner.logger, self.logger)

    @patch('pathlib.Path.exists')
    def test_scan_assets_directory_not_exists(self, mock_exists):
        """Test scan_assets when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = self.asset_scanner.scan_assets()
        
        self.assertEqual(result, [])
        mock_exists.assert_called_once()

    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_scan_assets_success(self, mock_exists, mock_rglob):
        """Test successful asset scanning."""
        mock_exists.return_value = True
        
        # Create mock file paths
        mock_files = []
        
        # Create mock for image1.png
        mock_file1 = Mock()
        mock_file1.is_file.return_value = True
        mock_file1.name = 'image1.png'
        mock_files.append(mock_file1)
        
        # Create mock for document.pdf
        mock_file2 = Mock()
        mock_file2.is_file.return_value = True
        mock_file2.name = 'document.pdf'
        mock_files.append(mock_file2)
        
        # Create mock for directory (should be excluded)
        mock_file3 = Mock()
        mock_file3.is_file.return_value = False
        mock_file3.name = 'subdir'
        mock_files.append(mock_file3)
        
        mock_rglob.return_value = mock_files
        
        result = self.asset_scanner.scan_assets()
        
        # Should return only files (excluding directories)
        self.assertEqual(len(result), 2)
        result_names = [f.name for f in result]
        self.assertIn('image1.png', result_names)
        self.assertIn('document.pdf', result_names)

    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_scan_assets_permission_error(self, mock_exists, mock_rglob):
        """Test scan_assets with permission error."""
        mock_exists.return_value = True
        mock_rglob.side_effect = PermissionError("Permission denied")
        
        result = self.asset_scanner.scan_assets()
        
        self.assertEqual(result, [])

    def test_is_valid_asset_file(self):
        """Test _is_valid_asset_file with valid file."""
        mock_file = Mock()
        mock_file.is_file.return_value = True
        
        result = self.asset_scanner._is_valid_asset_file(mock_file)
        
        self.assertTrue(result)

    def test_is_valid_asset_file_not_file(self):
        """Test _is_valid_asset_file with directory."""
        mock_file = Mock()
        mock_file.is_file.return_value = False
        
        result = self.asset_scanner._is_valid_asset_file(mock_file)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()