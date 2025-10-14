"""
Tests for the recent notes manager module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path to allow imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.utils.notes.recent_notes_manager import (
    RecentNotesScanner, 
    RecentNotesUpdater, 
    RecentNotesManager
)
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.data_models import NoteInfo


class TestRecentNotesScanner(unittest.TestCase):
    """Test cases for RecentNotesScanner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.scanner = RecentNotesScanner(self.config, self.logger)
        
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config.recent_notes_scan_field = str(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test RecentNotesScanner initialization."""
        self.assertIs(self.scanner.config, self.config)
        self.assertIs(self.scanner.logger, self.logger)
    
    def test_is_directory_scan(self):
        """Test directory scan detection."""
        self.assertTrue(self.scanner._is_directory_scan('docs/notes'))
        self.assertTrue(self.scanner._is_directory_scan('docs/blog'))
        self.assertFalse(self.scanner._is_directory_scan('docs/**/*.md'))
        self.assertFalse(self.scanner._is_directory_scan('metadata.publish=true'))
    
    def test_is_pattern_scan(self):
        """Test pattern scan detection."""
        self.assertTrue(self.scanner._is_pattern_scan('docs/**/*.md'))
        self.assertTrue(self.scanner._is_pattern_scan('docs/blog/**/*.md'))
        self.assertFalse(self.scanner._is_pattern_scan('docs/notes'))
        self.assertFalse(self.scanner._is_pattern_scan('metadata.publish=true'))
    
    def test_is_metadata_scan(self):
        """Test metadata scan detection."""
        self.assertTrue(self.scanner._is_metadata_scan('metadata.publish=true'))
        self.assertTrue(self.scanner._is_metadata_scan('metadata.category=tech'))
        self.assertFalse(self.scanner._is_metadata_scan('docs/notes'))
        self.assertFalse(self.scanner._is_metadata_scan('docs/**/*.md'))
    
    def test_scan_directory_success(self):
        """Test successful directory scanning."""
        # Create test files
        (self.temp_dir / 'note1.md').write_text('# Note 1')
        (self.temp_dir / 'note2.md').write_text('# Note 2')
        (self.temp_dir / 'subdir').mkdir()
        (self.temp_dir / 'subdir' / 'note3.md').write_text('# Note 3')
        (self.temp_dir / 'not_note.txt').write_text('Not a note')
        
        result = self.scanner._scan_directory(self.temp_dir)
        
        self.assertEqual(len(result), 3)
        self.assertTrue(any('note1.md' in str(p) for p in result))
        self.assertTrue(any('note2.md' in str(p) for p in result))
        self.assertTrue(any('note3.md' in str(p) for p in result))
    
    def test_scan_directory_nonexistent(self):
        """Test scanning non-existent directory."""
        nonexistent_dir = self.temp_dir / 'nonexistent'
        result = self.scanner._scan_directory(nonexistent_dir)
        self.assertEqual(len(result), 0)
    
    def test_scan_directory_exclude_patterns(self):
        """Test directory scanning with exclude patterns."""
        # Create files including excluded ones
        (self.temp_dir / 'note1.md').write_text('# Note 1')
        (self.temp_dir / 'index.md').write_text('# Index')  # Should be excluded
        (self.temp_dir / 'README.md').write_text('# README')  # Should be excluded
        
        result = self.scanner._scan_directory(self.temp_dir)
        
        self.assertEqual(len(result), 1)
        self.assertTrue(any('note1.md' in str(p) for p in result))
    
    def test_scan_pattern_success(self):
        """Test successful pattern scanning."""
        # Create actual files for testing
        (self.temp_dir / 'note1.md').write_text('# Note 1')
        (self.temp_dir / 'note2.md').write_text('# Note 2')
        
        # Test pattern scanning with actual files
        result = self.scanner._scan_pattern('**/*.md')
        
        # Should find the files we created
        self.assertGreaterEqual(len(result), 2)
    
    @patch('mkdocs_note.utils.notes.recent_notes_manager.FrontmatterManager')
    def test_matches_metadata_criteria(self, mock_fm_manager):
        """Test metadata criteria matching."""
        # Mock frontmatter manager
        mock_fm = Mock()
        mock_fm.parse_file.return_value = ({'publish': True}, '')
        mock_fm_manager.return_value = mock_fm
        
        scanner = RecentNotesScanner(self.config, self.logger)
        scanner.frontmatter_manager = mock_fm
        
        mock_file = Mock()
        result = scanner._matches_metadata_criteria(mock_file, 'publish', 'true')
        
        self.assertTrue(result)
    
    def test_is_valid_note_file(self):
        """Test note file validation."""
        # Create actual file for testing
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Test')
        
        # Valid markdown file
        self.assertTrue(self.scanner._is_valid_note_file(test_file))
        
        # Invalid extension
        txt_file = self.temp_dir / 'test.txt'
        txt_file.write_text('content')
        self.assertFalse(self.scanner._is_valid_note_file(txt_file))
        
        # Excluded pattern
        index_file = self.temp_dir / 'index.md'
        index_file.write_text('# Index')
        self.assertFalse(self.scanner._is_valid_note_file(index_file))
    
    def test_scan_recent_notes_default_behavior(self):
        """Test default scanning behavior."""
        # Create test files
        (self.temp_dir / 'note1.md').write_text('# Note 1')
        (self.temp_dir / 'note2.md').write_text('# Note 2')
        
        result = self.scanner.scan_recent_notes()
        
        self.assertEqual(len(result), 2)


class TestRecentNotesUpdater(unittest.TestCase):
    """Test cases for RecentNotesUpdater class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.updater = RecentNotesUpdater(self.config, self.logger)
    
    def test_initialization(self):
        """Test RecentNotesUpdater initialization."""
        self.assertIs(self.updater.config, self.config)
        self.assertIs(self.updater.logger, self.logger)
    
    def test_update_index_content_success(self):
        """Test successful index content update."""
        content = """# Index
        
<!-- recent_notes_start -->
<!-- recent_notes_end -->

## Other Content"""
        
        notes = [
            NoteInfo(
                file_path=Path('note1.md'),
                title='Note 1',
                relative_url='note1/',
                modified_date='2024-01-01',
                file_size=100,
                modified_time=1704067200,
                assets_list=[]
            )
        ]
        
        result = self.updater.update_index_content(content, notes)
        
        self.assertIn('Recent Notes', result)
        self.assertIn('Note 1', result)
        self.assertIn('note1/', result)
    
    def test_update_index_content_no_markers(self):
        """Test index content update with missing markers."""
        content = "# Index\n\nNo markers here"
        notes = []
        
        result = self.updater.update_index_content(content, notes)
        
        # Should return original content unchanged
        self.assertEqual(result, content)
    
    def test_generate_notes_section_empty(self):
        """Test generating notes section with empty notes list."""
        result = self.updater._generate_notes_section([])
        
        self.assertIn('No recent notes found', result)
    
    def test_generate_notes_section_with_notes(self):
        """Test generating notes section with notes."""
        notes = [
            NoteInfo(
                file_path=Path('note1.md'),
                title='Note 1',
                relative_url='note1/',
                modified_date='2024-01-01',
                file_size=100,
                modified_time=1704067200,
                assets_list=[]
            ),
            NoteInfo(
                file_path=Path('index.md'),
                title='Index',
                relative_url='index/',
                modified_date='2024-01-01',
                file_size=100,
                modified_time=1704067200,
                assets_list=[]
            )
        ]
        
        result = self.updater._generate_notes_section(notes)
        
        self.assertIn('Recent Notes', result)
        self.assertIn('Note 1', result)
        self.assertNotIn('Index', result)  # Index page should be excluded


class TestRecentNotesManager(unittest.TestCase):
    """Test cases for RecentNotesManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.manager = RecentNotesManager(self.config, self.logger)
        
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config.recent_notes_scan_field = str(self.temp_dir)
        self.config.recent_notes_index_file = str(self.temp_dir / 'index.md')
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test RecentNotesManager initialization."""
        self.assertIs(self.manager.config, self.config)
        self.assertIs(self.manager.logger, self.logger)
        self.assertIsNotNone(self.manager.scanner)
        self.assertIsNotNone(self.manager.updater)
        self.assertIsNone(self.manager.note_processor)
    
    @patch('mkdocs_note.utils.notes.note_manager.NoteProcessor')
    def test_get_recent_notes_success(self, mock_processor_class):
        """Test successful recent notes retrieval."""
        # Mock NoteProcessor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Create test files
        note_file = self.temp_dir / 'note1.md'
        note_file.write_text('# Note 1')
        
        # Mock note processing
        mock_note_info = NoteInfo(
            file_path=note_file,
            title='Note 1',
            relative_url='note1/',
            modified_date='2024-01-01',
            file_size=100,
            modified_time=1704067200,
            assets_list=[]
        )
        mock_processor.process_note.return_value = mock_note_info
        
        result = self.manager.get_recent_notes()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, 'Note 1')
    
    def test_get_recent_notes_no_files(self):
        """Test recent notes retrieval with no files."""
        result = self.manager.get_recent_notes()
        
        self.assertEqual(len(result), 0)
    
    def test_update_index_file_success(self):
        """Test successful index file update."""
        # Create index file
        index_file = self.temp_dir / 'index.md'
        index_content = """# Index
        
<!-- recent_notes_start -->
<!-- recent_notes_end -->

## Other Content"""
        index_file.write_text(index_content)
        
        notes = [
            NoteInfo(
                file_path=Path('note1.md'),
                title='Note 1',
                relative_url='note1/',
                modified_date='2024-01-01',
                file_size=100,
                modified_time=1704067200,
                assets_list=[]
            )
        ]
        
        result = self.manager.update_index_file(notes)
        
        self.assertTrue(result)
        
        # Check if file was updated
        updated_content = index_file.read_text()
        self.assertIn('Recent Notes', updated_content)
        self.assertIn('Note 1', updated_content)
    
    def test_update_index_file_nonexistent(self):
        """Test index file update with non-existent file."""
        notes = []
        
        result = self.manager.update_index_file(notes)
        
        self.assertFalse(result)
    
    @patch('mkdocs_note.utils.notes.note_manager.NoteProcessor')
    def test_process_recent_notes_success(self, mock_processor_class):
        """Test complete recent notes processing pipeline."""
        # Mock NoteProcessor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Create test files
        note_file = self.temp_dir / 'note1.md'
        note_file.write_text('# Note 1')
        
        index_file = self.temp_dir / 'index.md'
        index_content = """# Index
        
<!-- recent_notes_start -->
<!-- recent_notes_end -->

## Other Content"""
        index_file.write_text(index_content)
        
        # Mock note processing
        mock_note_info = NoteInfo(
            file_path=note_file,
            title='Note 1',
            relative_url='note1/',
            modified_date='2024-01-01',
            file_size=100,
            modified_time=1704067200,
            assets_list=[]
        )
        mock_processor.process_note.return_value = mock_note_info
        
        result = self.manager.process_recent_notes()
        
        self.assertTrue(result)
        
        # Check if index file was updated
        updated_content = index_file.read_text()
        self.assertIn('Recent Notes', updated_content)
    
    def test_process_recent_notes_no_files(self):
        """Test recent notes processing with no files."""
        # Create index file
        index_file = self.temp_dir / 'index.md'
        index_content = """# Index
        
<!-- recent_notes_start -->
<!-- recent_notes_end -->

## Other Content"""
        index_file.write_text(index_content)
        
        result = self.manager.process_recent_notes()
        
        self.assertTrue(result)  # Should succeed even with no notes


if __name__ == '__main__':
    unittest.main()
