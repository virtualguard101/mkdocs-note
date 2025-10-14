"""
Tests for the note manager module.
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

from mkdocs_note.utils.notes.note_manager import (
    NoteProcessor,
)
from mkdocs_note.utils.data_models import NoteInfo
from mkdocs_note.utils.file_manager import NoteScanner
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger


class TestNoteProcessor(unittest.TestCase):
    """Test cases for NoteProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.processor = NoteProcessor(self.config, self.logger)
        
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test NoteProcessor initialization."""
        self.assertIs(self.processor.config, self.config)
        self.assertIs(self.processor.logger, self.logger)
        self.assertIsNotNone(self.processor.assets_processor)
        self.assertIsNotNone(self.processor.frontmatter_manager)
    
    def test_parse_timezone_valid(self):
        """Test timezone parsing with valid formats."""
        # Test UTC+8
        tz = self.processor._parse_timezone('UTC+8')
        self.assertEqual(tz.utcoffset(None).total_seconds(), 8 * 3600)
        
        # Test UTC-5
        tz = self.processor._parse_timezone('UTC-5')
        self.assertEqual(tz.utcoffset(None).total_seconds(), -5 * 3600)
        
        # Test UTC+0
        tz = self.processor._parse_timezone('UTC+0')
        self.assertEqual(tz.utcoffset(None).total_seconds(), 0)
    
    def test_parse_timezone_invalid(self):
        """Test timezone parsing with invalid formats."""
        # Test invalid format
        tz = self.processor._parse_timezone('invalid')
        self.assertEqual(tz, self.processor._timezone)  # Should fallback to default
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp = 1704067200.0  # 2024-01-01 00:00:00 UTC
        formatted = self.processor._format_timestamp(timestamp)
        
        # Should be formatted according to config
        self.assertIsInstance(formatted, str)
        self.assertGreater(len(formatted), 0)
    
    def test_extract_title_from_markdown(self):
        """Test title extraction from markdown file."""
        # Create test markdown file
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Test Title\n\nSome content here.')
        
        title = self.processor._extract_title_from_markdown(test_file)
        
        self.assertEqual(title, 'Test Title')
    
    def test_extract_title_from_markdown_no_title(self):
        """Test title extraction from markdown file without title."""
        # Create test markdown file without title
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('No title here.\n\nSome content.')
        
        title = self.processor._extract_title_from_markdown(test_file)
        
        self.assertEqual(title, 'test')  # Should fallback to filename
    
    def test_extract_title_from_notebook(self):
        """Test title extraction from Jupyter notebook."""
        # Create test notebook file
        test_file = self.temp_dir / 'test.ipynb'
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Notebook Title\n", "Some content"]
                }
            ]
        }
        
        import json
        test_file.write_text(json.dumps(notebook_content))
        
        title = self.processor._extract_title_from_notebook(test_file)
        
        self.assertEqual(title, 'Notebook Title')
    
    def test_extract_title_from_notebook_no_title(self):
        """Test title extraction from Jupyter notebook without title."""
        # Create test notebook file without title
        test_file = self.temp_dir / 'test.ipynb'
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["No title here\n", "Some content"]
                }
            ]
        }
        
        import json
        test_file.write_text(json.dumps(notebook_content))
        
        title = self.processor._extract_title_from_notebook(test_file)
        
        self.assertEqual(title, 'test')  # Should fallback to filename
    
    def test_extract_title_unsupported_extension(self):
        """Test title extraction from unsupported file extension."""
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('Some content')
        
        title = self.processor._extract_title(test_file)
        
        # Note: _extract_title returns filename stem for unsupported extensions
        self.assertEqual(title, 'test')
    
    @patch('mkdocs_note.utils.notes.note_manager.subprocess.run')
    def test_get_git_commit_time_success(self, mock_run):
        """Test successful Git commit time retrieval."""
        # Mock successful git command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '1704067200'
        mock_run.return_value = mock_result
        
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Test')
        
        git_time = self.processor._get_git_commit_time(test_file)
        
        self.assertEqual(git_time, 1704067200.0)
        mock_run.assert_called_once()
    
    @patch('mkdocs_note.utils.notes.note_manager.subprocess.run')
    def test_get_git_commit_time_failure(self, mock_run):
        """Test Git commit time retrieval failure."""
        # Mock failed git command
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = 'Not a git repository'
        mock_run.return_value = mock_result
        
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Test')
        
        git_time = self.processor._get_git_commit_time(test_file)
        
        self.assertIsNone(git_time)
    
    def test_generate_relative_url(self):
        """Test relative URL generation."""
        # Create test file
        test_file = self.temp_dir / 'subdir' / 'test.md'
        test_file.parent.mkdir()
        test_file.write_text('# Test')
        
        # Mock config to have recent_notes_index_file
        self.config.recent_notes_index_file = str(self.temp_dir / 'index.md')
        
        url = self.processor._generate_relative_url(test_file)
        
        self.assertIsInstance(url, str)
        self.assertTrue(url.endswith('/'))
    
    def test_process_note_success(self):
        """Test successful note processing."""
        # Create test markdown file
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Test Note\n\nSome content here.')
        
        # Mock config
        self.config.recent_notes_index_file = str(self.temp_dir / 'index.md')
        
        note_info = self.processor.process_note(test_file)
        
        self.assertIsNotNone(note_info)
        self.assertIsInstance(note_info, NoteInfo)
        self.assertEqual(note_info.title, 'Test Note')
        self.assertEqual(note_info.file_path, test_file)
    
    def test_process_note_no_title(self):
        """Test note processing with no title."""
        # Create test markdown file without title
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('No title here.\n\nSome content.')
        
        note_info = self.processor.process_note(test_file)
        
        # Note: process_note returns NoteInfo with filename as title when no title found
        self.assertIsNotNone(note_info)
        self.assertEqual(note_info.title, 'test')
    
    def test_process_note_notebook_title(self):
        """Test note processing with 'Notebook' title."""
        # Create test markdown file with 'Notebook' title
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Notebook\n\nSome content.')
        
        note_info = self.processor.process_note(test_file)
        
        self.assertIsNone(note_info)  # Should return None for 'Notebook' title
    
    def test_extract_frontmatter_markdown(self):
        """Test frontmatter extraction from markdown file."""
        # Create test markdown file with frontmatter
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('''---
title: Test Note
date: 2024-01-01
---

# Test Note

Some content.''')
        
        frontmatter = self.processor._extract_frontmatter(test_file)
        
        self.assertIsNotNone(frontmatter)
        # Note: date is parsed as datetime.date object, not string
        from datetime import date
        self.assertEqual(frontmatter.date, date(2024, 1, 1))
    
    def test_extract_frontmatter_no_frontmatter(self):
        """Test frontmatter extraction from file without frontmatter."""
        # Create test markdown file without frontmatter
        test_file = self.temp_dir / 'test.md'
        test_file.write_text('# Test Note\n\nSome content.')
        
        frontmatter = self.processor._extract_frontmatter(test_file)
        
        self.assertIsNone(frontmatter)
    
    def test_extract_frontmatter_not_markdown(self):
        """Test frontmatter extraction from non-markdown file."""
        # Create test text file
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('Some content.')
        
        frontmatter = self.processor._extract_frontmatter(test_file)
        
        self.assertIsNone(frontmatter)


if __name__ == '__main__':
    unittest.main()