import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from mkdocs_note.plugin import MkdocsNotePlugin
from mkdocs_note.config import PluginConfig
from mkdocs_note.core.note_manager import NoteInfo


class TestMkdocsNotePlugin(unittest.TestCase):
    """Test cases for MkdocsNotePlugin class."""

    def setUp(self):
        """Set up test fixtures."""
        self.plugin = MkdocsNotePlugin()
        self.plugin.config = PluginConfig()

    def test_initialization(self):
        """Test plugin initialization."""
        self.assertIsInstance(self.plugin.logger, type(self.plugin.logger))
        self.assertEqual(self.plugin._recent_notes, [])

    def test_plugin_enabled_property(self):
        """Test plugin_enabled property."""
        self.plugin.config.enabled = True
        self.assertTrue(self.plugin.plugin_enabled)
        
        self.plugin.config.enabled = False
        self.assertFalse(self.plugin.plugin_enabled)

    @patch('mkdocs_note.plugin.Logger')
    def test_on_config_disabled(self, mock_logger):
        """Test on_config when plugin is disabled."""
        self.plugin.config.enabled = False
        mock_config = Mock()
        
        with patch.object(self.plugin.logger, 'debug') as mock_debug:
            result = self.plugin.on_config(mock_config)
        
        self.assertEqual(result, mock_config)
        mock_debug.assert_called_once()

    @patch('mkdocs_note.plugin.Logger')
    def test_on_config_enabled(self, mock_logger):
        """Test on_config when plugin is enabled."""
        self.plugin.config.enabled = True
        mock_config = Mock()
        mock_config.mdx_configs = {}
        
        with patch.object(self.plugin.logger, 'info') as mock_info:
            result = self.plugin.on_config(mock_config)
        
        self.assertEqual(result, mock_config)
        self.assertIn('toc', mock_config.mdx_configs)
        self.assertEqual(mock_config.mdx_configs['toc']['separator'], '-')
        mock_info.assert_called_once()

    @patch('mkdocs_note.plugin.Logger')
    def test_on_config_with_existing_toc(self, mock_logger):
        """Test on_config with existing toc configuration."""
        self.plugin.config.enabled = True
        mock_config = Mock()
        mock_config.mdx_configs = {
            'toc': {
                'separator': '|',
                'slugify': lambda x: x
            }
        }
        
        result = self.plugin.on_config(mock_config)
        
        # Should preserve existing configuration
        self.assertEqual(mock_config.mdx_configs['toc']['separator'], '|')
        self.assertIsNotNone(mock_config.mdx_configs['toc']['slugify'])

    @patch('mkdocs_note.plugin.Logger')
    def test_on_config_slugify_pymdownx(self, mock_logger):
        """Test on_config with pymdownx.slugs.slugify."""
        self.plugin.config.enabled = True
        mock_config = Mock()
        mock_config.mdx_configs = {'toc': {}}
        
        with patch('pymdownx.slugs.slugify') as mock_slugify:
            with patch.object(self.plugin.logger, 'debug') as mock_debug:
                result = self.plugin.on_config(mock_config)
        
        self.assertEqual(mock_config.mdx_configs['toc']['slugify'], mock_slugify)
        mock_debug.assert_called()

    @patch('mkdocs_note.plugin.Logger')
    def test_on_config_slugify_fallback(self, mock_logger):
        """Test on_config with fallback slugify."""
        self.plugin.config.enabled = True
        mock_config = Mock()
        mock_config.mdx_configs = {'toc': {}}
        
        with patch('pymdownx.slugs.slugify', side_effect=ImportError):
            with patch('markdown.extensions.toc.slugify') as mock_fallback_slugify:
                with patch.object(self.plugin.logger, 'debug') as mock_debug:
                    result = self.plugin.on_config(mock_config)
        
        # Check that a slugify function was set (not necessarily the exact mock object)
        self.assertIsNotNone(mock_config.mdx_configs['toc']['slugify'])
        self.assertTrue(callable(mock_config.mdx_configs['toc']['slugify']))
        mock_debug.assert_called()

    @patch('mkdocs_note.plugin.Logger')
    def test_on_files_disabled(self, mock_logger):
        """Test on_files when plugin is disabled."""
        self.plugin.config.enabled = False
        mock_files = Mock()
        mock_config = Mock()
        
        result = self.plugin.on_files(mock_files, mock_config)
        
        self.assertEqual(result, mock_files)

    @patch('mkdocs_note.plugin.Logger')
    @patch('mkdocs_note.plugin.FileScanner')
    @patch('mkdocs_note.plugin.NoteProcessor')
    def test_on_files_success(self, mock_processor_class, mock_scanner_class, mock_logger):
        """Test successful on_files processing."""
        self.plugin.config.enabled = True
        self.plugin.config.max_notes = 5
        
        # Mock scanner and processor
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_notes.return_value = [Path('/test/note1.md'), Path('/test/note2.md')]
        
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock note info
        note1 = Mock()
        note1.modified_time = 1705311000.0
        note2 = Mock()
        note2.modified_time = 1705310000.0
        mock_processor.process_note.side_effect = [note1, note2]
        
        mock_files = Mock()
        mock_config = Mock()
        
        with patch.object(self.plugin.logger, 'info') as mock_info:
            result = self.plugin.on_files(mock_files, mock_config)
        
        self.assertEqual(result, mock_files)
        self.assertEqual(len(self.plugin._recent_notes), 2)
        mock_info.assert_called()

    @patch('mkdocs_note.plugin.Logger')
    @patch('mkdocs_note.plugin.FileScanner')
    def test_on_files_no_notes(self, mock_scanner_class, mock_logger):
        """Test on_files when no notes found."""
        self.plugin.config.enabled = True
        
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_notes.return_value = []
        
        mock_files = Mock()
        mock_config = Mock()
        
        with patch.object(self.plugin.logger, 'warning') as mock_warning:
            result = self.plugin.on_files(mock_files, mock_config)
        
        self.assertEqual(result, mock_files)
        mock_warning.assert_called_once()

    @patch('mkdocs_note.plugin.Logger')
    @patch('mkdocs_note.plugin.FileScanner')
    def test_on_files_exception(self, mock_scanner_class, mock_logger):
        """Test on_files with exception."""
        self.plugin.config.enabled = True
        
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_notes.side_effect = Exception("Test error")
        
        mock_files = Mock()
        mock_config = Mock()
        
        with patch.object(self.plugin.logger, 'error') as mock_error:
            result = self.plugin.on_files(mock_files, mock_config)
        
        self.assertEqual(result, mock_files)
        mock_error.assert_called_once()

    @patch('mkdocs_note.plugin.Logger')
    def test_on_page_markdown_disabled(self, mock_logger):
        """Test on_page_markdown when plugin is disabled."""
        self.plugin.config.enabled = False
        markdown = "Test content"
        page = Mock()
        config = Mock()
        files = Mock()
        
        result = self.plugin.on_page_markdown(markdown, page, config, files)
        
        self.assertEqual(result, markdown)

    @patch('mkdocs_note.plugin.Logger')
    def test_on_page_markdown_not_index_page(self, mock_logger):
        """Test on_page_markdown when not index page."""
        self.plugin.config.enabled = True
        markdown = "Test content"
        page = Mock()
        config = Mock()
        files = Mock()
        
        with patch.object(self.plugin, '_is_notes_index_page', return_value=False):
            result = self.plugin.on_page_markdown(markdown, page, config, files)
        
        self.assertEqual(result, markdown)

    @patch('mkdocs_note.plugin.Logger')
    def test_on_page_markdown_index_page(self, mock_logger):
        """Test on_page_markdown when is index page."""
        self.plugin.config.enabled = True
        markdown = "Test content"
        page = Mock()
        config = Mock()
        files = Mock()
        
        # Add some recent notes
        note = Mock()
        note.title = "Test Note"
        note.relative_url = "test/note/"
        note.modified_date = "2024-01-15 10:30:00"
        self.plugin._recent_notes = [note]
        
        with patch.object(self.plugin, '_is_notes_index_page', return_value=True):
            with patch.object(self.plugin, '_insert_recent_notes', return_value="Updated content"):
                result = self.plugin.on_page_markdown(markdown, page, config, files)
        
        self.assertEqual(result, "Updated content")

    def test_is_notes_index_page_success(self):
        """Test _is_notes_index_page when page matches index file."""
        page = Mock()
        page.file = Mock()
        page.file.src_path = "/project/docs/notes/index.md"
        
        self.plugin.config.index_file = Path("/project/docs/notes/index.md")
        
        result = self.plugin._is_notes_index_page(page)
        
        self.assertTrue(result)

    def test_is_notes_index_page_different_path(self):
        """Test _is_notes_index_page when page doesn't match index file."""
        page = Mock()
        page.file = Mock()
        page.file.src_path = "/project/docs/notes/other.md"
        
        self.plugin.config.index_file = Path("/project/docs/notes/index.md")
        
        result = self.plugin._is_notes_index_page(page)
        
        self.assertFalse(result)

    def test_is_notes_index_page_exception(self):
        """Test _is_notes_index_page with exception."""
        page = Mock()
        page.file = Mock()
        page.file.src_path = None  # This will cause an exception
        
        result = self.plugin._is_notes_index_page(page)
        
        self.assertFalse(result)

    def test_insert_recent_notes_no_notes(self):
        """Test _insert_recent_notes with no recent notes."""
        markdown = "Test content"
        self.plugin._recent_notes = []
        
        result = self.plugin._insert_recent_notes(markdown)
        
        self.assertEqual(result, markdown)

    def test_insert_recent_notes_markers_not_found(self):
        """Test _insert_recent_notes when markers not found."""
        markdown = "Test content without markers"
        note = Mock()
        note.title = "Test Note"
        note.relative_url = "test/note/"
        note.modified_date = "2024-01-15 10:30:00"
        self.plugin._recent_notes = [note]
        
        with patch.object(self.plugin.logger, 'warning') as mock_warning:
            result = self.plugin._insert_recent_notes(markdown)
        
        self.assertEqual(result, markdown)
        mock_warning.assert_called_once()

    def test_insert_recent_notes_end_before_start(self):
        """Test _insert_recent_notes when end marker before start marker."""
        markdown = "<!-- recent_notes_end -->\n<!-- recent_notes_start -->"
        note = Mock()
        note.title = "Test Note"
        note.relative_url = "test/note/"
        note.modified_date = "2024-01-15 10:30:00"
        self.plugin._recent_notes = [note]
        
        with patch.object(self.plugin.logger, 'error') as mock_error:
            result = self.plugin._insert_recent_notes(markdown)
        
        self.assertEqual(result, markdown)
        mock_error.assert_called_once()

    def test_insert_recent_notes_success(self):
        """Test successful _insert_recent_notes."""
        markdown = "Content\n<!-- recent_notes_start -->\n<!-- recent_notes_end -->\nMore content"
        note = Mock()
        note.title = "Test Note"
        note.relative_url = "test/note/"
        note.modified_date = "2024-01-15 10:30:00"
        self.plugin._recent_notes = [note]
        
        with patch.object(self.plugin.logger, 'info') as mock_info:
            result = self.plugin._insert_recent_notes(markdown)
        
        self.assertIn("Test Note", result)
        self.assertIn("test/note/", result)
        self.assertIn("2024-01-15 10:30:00", result)
        mock_info.assert_called_once()

    def test_generate_notes_html(self):
        """Test _generate_notes_html."""
        note1 = Mock()
        note1.title = "Note 1"
        note1.relative_url = "note1/"
        note1.modified_date = "2024-01-15 10:30:00"
        
        note2 = Mock()
        note2.title = "Note 2"
        note2.relative_url = "note2/"
        note2.modified_date = "2024-01-14 09:15:00"
        
        self.plugin._recent_notes = [note1, note2]
        
        result = self.plugin._generate_notes_html()
        
        self.assertIn('<ul>', result)
        self.assertIn('</ul>', result)
        self.assertIn('Note 1', result)
        self.assertIn('Note 2', result)
        self.assertIn('note1/', result)
        self.assertIn('note2/', result)
        self.assertIn('2024-01-15 10:30:00', result)
        self.assertIn('2024-01-14 09:15:00', result)


if __name__ == '__main__':
    unittest.main()
