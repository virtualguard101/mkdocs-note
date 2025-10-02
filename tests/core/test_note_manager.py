import unittest
import sys
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from datetime import datetime

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.core.note_manager import (
    NoteInfo,
    NoteProcessor,
    CacheManager,
    IndexUpdater,
    RecentNotesUpdater,
)
from mkdocs_note.core.file_manager import FileScanner
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger

class TestNoteInfo(unittest.TestCase):
    """Test cases for NoteInfo dataclass."""

    def test_note_info_creation(self):
        """Test NoteInfo creation with all fields."""
        file_path = Path('/test/note.md')
        note_info = NoteInfo(
            file_path=file_path,
            title='Test Note',
            relative_url='test/note/',
            modified_date='2024-01-15 10:30:00',
            file_size=1024,
            modified_time=1705311000.0
        )
        
        self.assertEqual(note_info.file_path, file_path)
        self.assertEqual(note_info.title, 'Test Note')
        self.assertEqual(note_info.relative_url, 'test/note/')
        self.assertEqual(note_info.modified_date, '2024-01-15 10:30:00')
        self.assertEqual(note_info.file_size, 1024)
        self.assertEqual(note_info.modified_time, 1705311000.0)


class TestNoteProcessor(unittest.TestCase):
    """Test cases for NoteProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.processor = NoteProcessor(self.config, self.logger)

    def test_initialization(self):
        """Test NoteProcessor initialization."""
        self.assertIs(self.processor.config, self.config)
        self.assertIs(self.processor.logger, self.logger)

    @patch('pathlib.Path.stat')
    def test_process_note_success(self, mock_stat):
        """Test successful note processing."""
        # Mock file stat
        mock_stat_result = Mock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1705311000.0
        mock_stat.return_value = mock_stat_result
        
        # Mock file path
        file_path = Path('/test/note.md')
        
        # Mock title extraction
        with patch.object(self.processor, '_extract_title', return_value='Test Note'):
            with patch.object(self.processor, '_generate_relative_url', return_value='test/note/'):
                result = self.processor.process_note(file_path)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, NoteInfo)
        self.assertEqual(result.title, 'Test Note')
        self.assertEqual(result.relative_url, 'test/note/')
        self.assertEqual(result.file_size, 1024)
        self.assertEqual(result.modified_time, 1705311000.0)

    @patch('pathlib.Path.stat')
    def test_process_note_no_title(self, mock_stat):
        """Test note processing when no title is found."""
        mock_stat_result = Mock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1705311000.0
        mock_stat.return_value = mock_stat_result
        
        file_path = Path('/test/note.md')
        
        with patch.object(self.processor, '_extract_title', return_value=None):
            result = self.processor.process_note(file_path)
        
        self.assertIsNone(result)

    @patch('pathlib.Path.stat')
    def test_process_note_notebook_title(self, mock_stat):
        """Test note processing when title is 'Notebook'."""
        mock_stat_result = Mock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1705311000.0
        mock_stat.return_value = mock_stat_result
        
        file_path = Path('/test/note.md')
        
        with patch.object(self.processor, '_extract_title', return_value='Notebook'):
            result = self.processor.process_note(file_path)
        
        self.assertIsNone(result)

    @patch('pathlib.Path.stat')
    def test_process_note_exception(self, mock_stat):
        """Test note processing with exception."""
        mock_stat.side_effect = OSError("File not found")
        
        file_path = Path('/test/note.md')
        
        with patch.object(self.processor.logger, 'error') as mock_error:
            result = self.processor.process_note(file_path)
        
        self.assertIsNone(result)
        mock_error.assert_called_once()

    def test_extract_title_markdown(self):
        """Test title extraction from markdown file."""
        file_path = Path('/test/note.md')
        
        # Mock the Path.open method to avoid actual file operations
        with patch.object(Path, 'open', mock_open(read_data='# My Test Note\n\nContent here')):
            result = self.processor._extract_title_from_markdown(file_path)
        
        self.assertEqual(result, 'My Test Note')

    def test_extract_title_markdown_no_title(self):
        """Test title extraction from markdown file with no title."""
        file_path = Path('/test/note.md')
        
        with patch.object(Path, 'open', mock_open(read_data='No title here\n\nContent here')):
            result = self.processor._extract_title_from_markdown(file_path)
        
        self.assertEqual(result, 'note')  # Should return file stem

    def test_extract_title_notebook(self):
        """Test title extraction from Jupyter notebook."""
        file_path = Path('/test/note.ipynb')
        
        notebook_data = {
            'cells': [
                {
                    'cell_type': 'markdown',
                    'source': ['# My Notebook Title\n', 'Content here']
                }
            ]
        }
        
        with patch.object(Path, 'open', mock_open(read_data=json.dumps(notebook_data))):
            result = self.processor._extract_title_from_notebook(file_path)
        
        self.assertEqual(result, 'My Notebook Title')

    def test_extract_title_notebook_no_title(self):
        """Test title extraction from Jupyter notebook with no title."""
        file_path = Path('/test/note.ipynb')
        
        notebook_data = {
            'cells': [
                {
                    'cell_type': 'markdown',
                    'source': ['No title here\n', 'Content here']
                }
            ]
        }
        
        with patch.object(Path, 'open', mock_open(read_data=json.dumps(notebook_data))):
            result = self.processor._extract_title_from_notebook(file_path)
        
        self.assertEqual(result, 'note')  # Should return file stem

    def test_generate_relative_url(self):
        """Test relative URL generation."""
        file_path = Path('/project/docs/notes/subdir/note.md')
        
        # Create a new processor with mocked config
        mock_config = Mock()
        mock_config.index_file = Path('/project/docs/notes/index.md')
        processor = NoteProcessor(mock_config, self.logger)
        
        result = processor._generate_relative_url(file_path)
        
        self.assertEqual(result, 'subdir/note/')

    def test_generate_relative_url_index_file(self):
        """Test relative URL generation for index file."""
        file_path = Path('/project/docs/notes/index.md')
        
        # Create a new processor with mocked config
        mock_config = Mock()
        mock_config.index_file = Path('/project/docs/notes/index.md')
        processor = NoteProcessor(mock_config, self.logger)
        
        result = processor._generate_relative_url(file_path)
        
        self.assertEqual(result, '')


class TestCacheManager(unittest.TestCase):
    """Test cases for CacheManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Logger()
        self.cache_manager = CacheManager(self.logger)

    def test_initialization(self):
        """Test CacheManager initialization."""
        self.assertIs(self.cache_manager.logger, self.logger)
        self.assertIsNone(self.cache_manager._last_notes_hash)
        self.assertIsNone(self.cache_manager._last_content_hash)

    def test_should_update_notes_first_time(self):
        """Test should_update_notes on first call."""
        notes = [Mock()]
        notes[0].file_path = Path('/test/note.md')
        notes[0].modified_time = 1705311000.0
        notes[0].file_size = 1024
        
        result = self.cache_manager.should_update_notes(notes)
        
        self.assertTrue(result)
        self.assertIsNotNone(self.cache_manager._last_notes_hash)

    def test_should_update_notes_no_change(self):
        """Test should_update_notes when no change."""
        notes = [Mock()]
        notes[0].file_path = Path('/test/note.md')
        notes[0].modified_time = 1705311000.0
        notes[0].file_size = 1024
        
        # First call
        self.cache_manager.should_update_notes(notes)
        
        # Second call with same notes
        result = self.cache_manager.should_update_notes(notes)
        
        self.assertFalse(result)

    def test_should_update_content_first_time(self):
        """Test should_update_content on first call."""
        content = "Test content"
        
        result = self.cache_manager.should_update_content(content)
        
        self.assertTrue(result)
        self.assertIsNotNone(self.cache_manager._last_content_hash)

    def test_should_update_content_no_change(self):
        """Test should_update_content when no change."""
        content = "Test content"
        
        # First call
        self.cache_manager.should_update_content(content)
        
        # Second call with same content
        result = self.cache_manager.should_update_content(content)
        
        self.assertFalse(result)


class TestIndexUpdater(unittest.TestCase):
    """Test cases for IndexUpdater class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.updater = IndexUpdater(self.config, self.logger)

    def test_initialization(self):
        """Test IndexUpdater initialization."""
        self.assertIs(self.updater.config, self.config)
        self.assertIs(self.updater.logger, self.logger)

    @patch('pathlib.Path.exists')
    def test_update_index_file_not_exists(self, mock_exists):
        """Test update_index when file doesn't exist."""
        mock_exists.return_value = False
        
        notes = []
        
        with patch.object(self.logger, 'error') as mock_error:
            result = self.updater.update_index(notes)
        
        self.assertFalse(result)
        mock_error.assert_called_once()

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_update_index_success(self, mock_exists, mock_write, mock_read):
        """Test successful index update."""
        mock_exists.return_value = True
        mock_read.return_value = 'Content\n<!-- recent_notes_start -->\n<!-- recent_notes_end -->\nMore content'
        
        notes = [Mock()]
        notes[0].title = 'Test Note'
        notes[0].relative_url = 'test/note/'
        notes[0].modified_date = '2024-01-15 10:30:00'
        
        result = self.updater.update_index(notes)
        
        self.assertTrue(result)
        mock_read.assert_called_once_with(encoding='utf-8')
        mock_write.assert_called_once()

    def test_generate_html_list(self):
        """Test HTML list generation."""
        notes = [Mock(), Mock()]
        notes[0].title = 'Note 1'
        notes[0].relative_url = 'note1/'
        notes[0].modified_date = '2024-01-15 10:30:00'
        notes[1].title = 'Note 2'
        notes[1].relative_url = 'note2/'
        notes[1].modified_date = '2024-01-14 09:15:00'
        
        result = self.updater._generate_html_list(notes)
        
        self.assertIn('<ul>', result)
        self.assertIn('</ul>', result)
        self.assertIn('Note 1', result)
        self.assertIn('Note 2', result)
        self.assertIn('note1/', result)
        self.assertIn('note2/', result)

    def test_replace_section_markers_not_found(self):
        """Test replace_section when markers not found."""
        content = 'No markers here'
        
        with patch.object(self.logger, 'error') as mock_error:
            result = self.updater._replace_section(content, 'new content')
        
        self.assertIsNone(result)
        mock_error.assert_called_once()

    def test_replace_section_end_before_start(self):
        """Test replace_section when end marker before start marker."""
        content = '<!-- recent_notes_end -->\n<!-- recent_notes_start -->'
        
        with patch.object(self.logger, 'error') as mock_error:
            result = self.updater._replace_section(content, 'new content')
        
        self.assertIsNone(result)
        mock_error.assert_called_once()


class TestRecentNotesUpdater(unittest.TestCase):
    """Test cases for RecentNotesUpdater class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.updater = RecentNotesUpdater(self.config)

    def test_initialization(self):
        """Test RecentNotesUpdater initialization."""
        self.assertIs(self.updater.config, self.config)
        self.assertIsInstance(self.updater.logger, Logger)
        self.assertIsInstance(self.updater.file_scanner, FileScanner)
        self.assertIsInstance(self.updater.note_processor, NoteProcessor)
        self.assertIsInstance(self.updater.cache_manager, CacheManager)
        self.assertIsInstance(self.updater.index_updater, IndexUpdater)

    def test_initialization_default_config(self):
        """Test RecentNotesUpdater initialization with default config."""
        updater = RecentNotesUpdater()
        self.assertIsInstance(updater.config, PluginConfig)

    @patch('mkdocs_note.core.note_manager.FileScanner.scan_notes')
    def test_update_no_files(self, mock_scan):
        """Test update when no files found."""
        mock_scan.return_value = []
        
        with patch.object(self.updater.logger, 'warning') as mock_warning:
            result = self.updater.update()
        
        self.assertFalse(result)
        mock_warning.assert_called_once()

    @patch('mkdocs_note.core.note_manager.IndexUpdater.update_index')
    @patch('mkdocs_note.core.note_manager.CacheManager.should_update_notes')
    @patch('mkdocs_note.core.note_manager.NoteProcessor.process_note')
    @patch('mkdocs_note.core.note_manager.FileScanner.scan_notes')
    def test_update_success(self, mock_scan, mock_process, mock_cache, mock_update):
        """Test successful update."""
        # Mock file paths
        mock_files = [Path('/test/note1.md'), Path('/test/note2.md')]
        mock_scan.return_value = mock_files
        
        # Mock processed notes
        note1 = Mock()
        note1.modified_time = 1705311000.0
        note2 = Mock()
        note2.modified_time = 1705310000.0
        
        mock_process.side_effect = [note1, note2]
        mock_cache.return_value = True
        mock_update.return_value = True
        
        result = self.updater.update()
        
        self.assertTrue(result)
        mock_scan.assert_called_once()
        self.assertEqual(mock_process.call_count, 2)
        mock_cache.assert_called_once()
        mock_update.assert_called_once()

    @patch('mkdocs_note.core.note_manager.CacheManager.should_update_notes')
    @patch('mkdocs_note.core.note_manager.NoteProcessor.process_note')
    @patch('mkdocs_note.core.note_manager.FileScanner.scan_notes')
    def test_update_no_changes(self, mock_scan, mock_process, mock_cache):
        """Test update when no changes detected."""
        mock_files = [Path('/test/note1.md')]
        mock_scan.return_value = mock_files
        
        note1 = Mock()
        note1.modified_time = 1705311000.0
        mock_process.return_value = note1
        mock_cache.return_value = False  # No changes
        
        with patch.object(self.updater.logger, 'info') as mock_info:
            result = self.updater.update()
        
        self.assertTrue(result)
        # Check that the specific "Notes unchanged" message was called
        mock_info.assert_any_call('Notes unchanged, skipping update')


if __name__ == '__main__':
    unittest.main()