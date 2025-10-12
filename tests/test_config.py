import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from mkdocs_note.config import PluginConfig, load_config_from_mkdocs_yml, _find_mkdocs_yml, _extract_plugin_config


class TestPluginConfig(unittest.TestCase):
    """Test cases for PluginConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()

    def test_default_values(self):
        """Test that default values are set correctly."""
        self.assertTrue(self.config.enabled)
        self.assertIsInstance(self.config.project_root, Path)
        self.assertIsInstance(self.config.notes_dir, (Path, str))
        self.assertIsInstance(self.config.index_file, (Path, str))
        self.assertEqual(self.config.start_marker, '<!-- recent_notes_start -->')
        self.assertEqual(self.config.end_marker, '<!-- recent_notes_end -->')
        self.assertEqual(self.config.max_notes, 11)
        self.assertEqual(self.config.git_date_format, '%a %b %d %H:%M:%S %Y %z')
        self.assertEqual(self.config.output_date_format, '%Y-%m-%d %H:%M:%S')
        self.assertEqual(self.config.supported_extensions, {'.md', '.ipynb'})
        self.assertEqual(self.config.exclude_patterns, {'index.md', 'README.md'})
        self.assertEqual(self.config.exclude_dirs, {'__pycache__', '.git', 'node_modules'})
        self.assertEqual(self.config.cache_size, 256)
        self.assertTrue(self.config.use_git_timestamps)
        self.assertEqual(self.config.assets_dir, 'docs/notes/assets')
        self.assertEqual(self.config.notes_template, 'docs/templates/default.md')

    def test_config_validation(self):
        """Test configuration validation."""
        # Test enabled field
        self.assertIsInstance(self.config.enabled, bool)
        
        # Test path fields
        self.assertIsInstance(self.config.project_root, Path)
        self.assertIsInstance(self.config.notes_dir, (Path, str))
        self.assertIsInstance(self.config.index_file, (Path, str))
        
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
        
        # Test new fields
        self.assertIsInstance(self.config.use_git_timestamps, bool)
        self.assertIsInstance(self.config.assets_dir, (Path, str))
        self.assertIsInstance(self.config.notes_template, str)

    def test_path_relationships(self):
        """Test that path relationships are logical."""
        # notes_dir should be under project_root
        notes_dir_path = Path(self.config.notes_dir)
        # Convert to absolute paths for comparison
        notes_abs = (self.config.project_root / notes_dir_path).resolve()
        project_abs = self.config.project_root.resolve()
        self.assertTrue(notes_abs.is_relative_to(project_abs))
        
        # index_file should be under notes_dir
        index_file_path = Path(self.config.index_file)
        index_abs = (self.config.project_root / index_file_path).resolve()
        self.assertTrue(index_abs.is_relative_to(notes_abs))
        
        # assets_dir should be under notes_dir
        assets_dir_path = Path(self.config.assets_dir)
        assets_abs = (self.config.project_root / assets_dir_path).resolve()
        self.assertTrue(assets_abs.is_relative_to(notes_abs))

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


class TestConfigLoading(unittest.TestCase):
    """Test cases for configuration loading from mkdocs.yml."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mkdocs_yml(self, config_content: str, filename: str = 'mkdocs.yml'):
        """Helper to create a test mkdocs.yml file."""
        config_path = Path(self.test_dir) / filename
        config_path.write_text(config_content, encoding='utf-8')
        return config_path

    def test_load_config_with_custom_notes_dir(self):
        """Test loading config with custom notes_dir."""
        config_content = """
site_name: Test Site
plugins:
  - mkdocs-note:
      notes_dir: "docs/usage"
      max_notes: 20
"""
        config_path = self._create_mkdocs_yml(config_content)
        
        config = load_config_from_mkdocs_yml(config_path)
        
        self.assertEqual(config.notes_dir, 'docs/usage')
        self.assertEqual(config.max_notes, 20)

    def test_load_config_with_all_options(self):
        """Test loading config with multiple custom options."""
        config_content = """
site_name: Test Site
plugins:
  - mkdocs-note:
      notes_dir: "docs/my-notes"
      max_notes: 15
      start_marker: "<!-- start -->"
      end_marker: "<!-- end -->"
      timestamp_zone: "UTC+8"
      use_git_timestamps: false
"""
        config_path = self._create_mkdocs_yml(config_content)
        
        config = load_config_from_mkdocs_yml(config_path)
        
        self.assertEqual(config.notes_dir, 'docs/my-notes')
        self.assertEqual(config.max_notes, 15)
        self.assertEqual(config.start_marker, '<!-- start -->')
        self.assertEqual(config.end_marker, '<!-- end -->')
        self.assertEqual(config.timestamp_zone, 'UTC+8')
        self.assertFalse(config.use_git_timestamps)

    def test_load_config_without_plugin(self):
        """Test loading config when mkdocs-note plugin is not configured."""
        config_content = """
site_name: Test Site
plugins:
  - search
"""
        config_path = self._create_mkdocs_yml(config_content)
        
        config = load_config_from_mkdocs_yml(config_path)
        
        # Should return default config
        self.assertEqual(config.notes_dir, 'docs/notes')
        self.assertEqual(config.max_notes, 11)

    def test_load_config_with_plugin_no_options(self):
        """Test loading config when plugin is enabled with no custom options."""
        config_content = """
site_name: Test Site
plugins:
  - mkdocs-note
"""
        config_path = self._create_mkdocs_yml(config_content)
        
        config = load_config_from_mkdocs_yml(config_path)
        
        # Should return default config
        self.assertEqual(config.notes_dir, 'docs/notes')
        self.assertEqual(config.max_notes, 11)

    def test_load_config_invalid_file(self):
        """Test loading config from non-existent file."""
        non_existent_path = Path(self.test_dir) / 'non_existent.yml'
        
        with self.assertRaises(FileNotFoundError):
            load_config_from_mkdocs_yml(non_existent_path)

    def test_load_config_invalid_yaml(self):
        """Test loading config from invalid YAML file."""
        config_content = """
site_name: Test Site
plugins:
  - mkdocs-note:
      notes_dir: "docs/usage"
    invalid_indentation
"""
        config_path = self._create_mkdocs_yml(config_content)
        
        with self.assertRaises(ValueError):
            load_config_from_mkdocs_yml(config_path)

    def test_find_mkdocs_yml_in_current_dir(self):
        """Test finding mkdocs.yml in current directory."""
        self._create_mkdocs_yml("site_name: Test")
        os.chdir(self.test_dir)
        
        found_path = _find_mkdocs_yml()
        
        self.assertIsNotNone(found_path)
        self.assertEqual(found_path.name, 'mkdocs.yml')

    def test_find_mkdocs_yaml_variant(self):
        """Test finding mkdocs.yaml (alternate extension)."""
        self._create_mkdocs_yml("site_name: Test", filename='mkdocs.yaml')
        os.chdir(self.test_dir)
        
        found_path = _find_mkdocs_yml()
        
        self.assertIsNotNone(found_path)
        self.assertEqual(found_path.name, 'mkdocs.yaml')

    def test_find_mkdocs_yml_in_parent_dir(self):
        """Test finding mkdocs.yml in parent directory."""
        self._create_mkdocs_yml("site_name: Test")
        
        # Create a subdirectory and change to it
        subdir = Path(self.test_dir) / 'subdir'
        subdir.mkdir()
        os.chdir(subdir)
        
        found_path = _find_mkdocs_yml()
        
        self.assertIsNotNone(found_path)
        self.assertEqual(found_path.name, 'mkdocs.yml')

    def test_find_mkdocs_yml_not_found(self):
        """Test when mkdocs.yml is not found."""
        os.chdir(self.test_dir)
        
        found_path = _find_mkdocs_yml()
        
        self.assertIsNone(found_path)

    def test_extract_plugin_config_list_format(self):
        """Test extracting plugin config from list format."""
        mkdocs_config = {
            'plugins': [
                'search',
                {
                    'mkdocs-note': {
                        'notes_dir': 'docs/my-notes',
                        'max_notes': 20
                    }
                }
            ]
        }
        
        plugin_config = _extract_plugin_config(mkdocs_config)
        
        self.assertEqual(plugin_config['notes_dir'], 'docs/my-notes')
        self.assertEqual(plugin_config['max_notes'], 20)

    def test_extract_plugin_config_dict_format(self):
        """Test extracting plugin config from dict format."""
        mkdocs_config = {
            'plugins': {
                'search': {},
                'mkdocs-note': {
                    'notes_dir': 'docs/usage',
                    'max_notes': 15
                }
            }
        }
        
        plugin_config = _extract_plugin_config(mkdocs_config)
        
        self.assertEqual(plugin_config['notes_dir'], 'docs/usage')
        self.assertEqual(plugin_config['max_notes'], 15)

    def test_extract_plugin_config_string_format(self):
        """Test extracting plugin config when plugin is string (no options)."""
        mkdocs_config = {
            'plugins': [
                'search',
                'mkdocs-note'
            ]
        }
        
        plugin_config = _extract_plugin_config(mkdocs_config)
        
        # Should return empty dict (use defaults)
        self.assertEqual(plugin_config, {})

    def test_extract_plugin_config_no_plugins(self):
        """Test extracting plugin config when no plugins section."""
        mkdocs_config = {
            'site_name': 'Test Site'
        }
        
        plugin_config = _extract_plugin_config(mkdocs_config)
        
        self.assertEqual(plugin_config, {})

    def test_extract_plugin_config_plugin_not_found(self):
        """Test extracting plugin config when mkdocs-note is not in plugins."""
        mkdocs_config = {
            'plugins': [
                'search',
                'minify'
            ]
        }
        
        plugin_config = _extract_plugin_config(mkdocs_config)
        
        self.assertEqual(plugin_config, {})

    def test_load_config_preserves_defaults(self):
        """Test that loading config preserves default values for unspecified options."""
        config_content = """
site_name: Test Site
plugins:
  - mkdocs-note:
      notes_dir: "docs/custom"
"""
        config_path = self._create_mkdocs_yml(config_content)
        
        config = load_config_from_mkdocs_yml(config_path)
        
        # Custom value should be applied
        self.assertEqual(config.notes_dir, 'docs/custom')
        
        # Default values should be preserved
        self.assertEqual(config.max_notes, 11)
        self.assertEqual(config.start_marker, '<!-- recent_notes_start -->')
        self.assertEqual(config.end_marker, '<!-- recent_notes_end -->')
        self.assertTrue(config.use_git_timestamps)


if __name__ == '__main__':
    unittest.main()
