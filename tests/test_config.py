import unittest
import sys
import os
from pathlib import Path

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from mkdocs_note.config import PluginConfig


class TestPluginConfig(unittest.TestCase):
    """Test cases for PluginConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()

    def test_default_values(self):
        """Test that default values are set correctly."""
        self.assertTrue(self.config.enabled)
        self.assertIsInstance(self.config.project_root, Path)
        self.assertIsInstance(self.config.notes_dir, Path)
        self.assertIsInstance(self.config.index_file, Path)
        self.assertEqual(self.config.start_marker, '<!-- recent_notes_start -->')
        self.assertEqual(self.config.end_marker, '<!-- recent_notes_end -->')
        self.assertEqual(self.config.max_notes, 11)
        self.assertEqual(self.config.git_date_format, '%a %b %d %H:%M:%S %Y %z')
        self.assertEqual(self.config.output_date_format, '%Y-%m-%d %H:%M:%S')
        self.assertEqual(self.config.supported_extensions, {'.md', '.ipynb'})
        self.assertEqual(self.config.exclude_patterns, {'index.md', 'README.md'})
        self.assertEqual(self.config.exclude_dirs, {'__pycache__', '.git', 'node_modules'})
        self.assertEqual(self.config.cache_size, 256)

    def test_config_validation(self):
        """Test configuration validation."""
        # Test enabled field
        self.assertIsInstance(self.config.enabled, bool)
        
        # Test path fields
        self.assertIsInstance(self.config.project_root, Path)
        self.assertIsInstance(self.config.notes_dir, Path)
        self.assertIsInstance(self.config.index_file, Path)
        
        # Test string fields
        self.assertIsInstance(self.config.start_marker, str)
        self.assertIsInstance(self.config.end_marker, str)
        self.assertIsInstance(self.config.git_date_format, str)
        self.assertIsInstance(self.config.output_date_format, str)
        
        # Test numeric fields
        self.assertIsInstance(self.config.max_notes, int)
        self.assertIsInstance(self.config.cache_size, int)
        
        # Test set fields
        self.assertIsInstance(self.config.supported_extensions, set)
        self.assertIsInstance(self.config.exclude_patterns, set)
        self.assertIsInstance(self.config.exclude_dirs, set)

    def test_path_relationships(self):
        """Test that path relationships are logical."""
        # notes_dir should be under project_root
        self.assertTrue(self.config.notes_dir.is_relative_to(self.config.project_root))
        
        # index_file should be under notes_dir
        self.assertTrue(self.config.index_file.is_relative_to(self.config.notes_dir))

    def test_marker_consistency(self):
        """Test that markers are properly formatted."""
        self.assertTrue(self.config.start_marker.startswith('<!--'))
        self.assertTrue(self.config.start_marker.endswith('-->'))
        self.assertTrue(self.config.end_marker.startswith('<!--'))
        self.assertTrue(self.config.end_marker.endswith('-->'))
        
        # Markers should be different
        self.assertNotEqual(self.config.start_marker, self.config.end_marker)

    def test_supported_extensions(self):
        """Test supported file extensions."""
        # Should include common note formats
        self.assertIn('.md', self.config.supported_extensions)
        self.assertIn('.ipynb', self.config.supported_extensions)
        
        # Should not include binary or non-note formats
        self.assertNotIn('.pdf', self.config.supported_extensions)
        self.assertNotIn('.docx', self.config.supported_extensions)
        self.assertNotIn('.txt', self.config.supported_extensions)

    def test_exclude_patterns(self):
        """Test exclude patterns."""
        # Should exclude common non-note files
        self.assertIn('index.md', self.config.exclude_patterns)
        self.assertIn('README.md', self.config.exclude_patterns)
        
        # Should not exclude regular note files
        self.assertNotIn('note.md', self.config.exclude_patterns)
        self.assertNotIn('my-notes.md', self.config.exclude_patterns)

    def test_exclude_dirs(self):
        """Test exclude directories."""
        # Should exclude common system/temp directories
        self.assertIn('__pycache__', self.config.exclude_dirs)
        self.assertIn('.git', self.config.exclude_dirs)
        self.assertIn('node_modules', self.config.exclude_dirs)
        
        # Should not exclude regular content directories
        self.assertNotIn('notes', self.config.exclude_dirs)
        self.assertNotIn('docs', self.config.exclude_dirs)


if __name__ == '__main__':
    unittest.main()
