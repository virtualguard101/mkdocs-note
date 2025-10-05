import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.core.note_creator import NoteCreator
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger


class TestNoteCreator(unittest.TestCase):
    """Test cases for NoteCreator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.creator = NoteCreator(self.config, self.logger)
        
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config.notes_dir = str(self.temp_dir)
        
        # Set assets_dir to be relative to temp_dir
        assets_dir = self.temp_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        self.config.assets_dir = str(assets_dir)
        
        # Create template directory and file for tests
        template_dir = self.temp_dir / "template"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "default.md"
        template_content = "# {{title}}\n\nCreated on {{date}}\n\nNote: {{note_name}}"
        template_file.write_text(template_content)
        self.config.notes_template = str(template_file)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test NoteCreator initialization."""
        self.assertIs(self.creator.config, self.config)
        self.assertIs(self.creator.logger, self.logger)

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_create_new_note_success(self, mock_initializer):
        """Test successful note creation."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "new-note.md"
        
        result = self.creator.create_new_note(note_path)
        
        self.assertEqual(result, 0)
        self.assertTrue(note_path.exists())
        
        # Check asset directory is created (should be at config.assets_dir / "new-note")
        expected_asset_dir = Path(self.config.assets_dir) / "new-note"
        self.assertTrue(expected_asset_dir.exists())
        
        # Check content
        content = note_path.read_text()
        self.assertIn("new-note", content.lower())  # Title should be processed
        self.assertIn("2025", content)  # Date should be included

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_create_new_note_non_compliant_structure(self, mock_initializer):
        """Test note creation with non-compliant structure."""
        # Mock the initializer to return non-compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (False, ["Structure error"])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "new-note.md"
        
        result = self.creator.create_new_note(note_path)
        
        self.assertEqual(result, 1)
        self.assertFalse(note_path.exists())

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_create_new_note_file_exists(self, mock_initializer):
        """Test note creation when file already exists."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "existing-note.md"
        note_path.write_text("# Existing Note")
        
        result = self.creator.create_new_note(note_path)
        
        self.assertEqual(result, 1)

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_create_new_note_with_template(self, mock_initializer):
        """Test note creation with custom template."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        # Create custom template
        template_path = self.temp_dir / "custom-template.md"
        template_content = "# {{title}}\n\nCustom template content for {{note_name}}"
        template_path.write_text(template_content)
        
        note_path = self.temp_dir / "custom-note.md"
        
        result = self.creator.create_new_note(note_path, template_path)
        
        self.assertEqual(result, 0)
        self.assertTrue(note_path.exists())
        
        # Check content uses template
        content = note_path.read_text()
        self.assertIn("# Custom Note", content)
        self.assertIn("Custom template content for custom-note", content)
    
    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_create_new_note_nested(self, mock_initializer):
        """Test note creation in nested subdirectory."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        # Create nested directory
        subdir = self.temp_dir / "dsa" / "anal"
        subdir.mkdir(parents=True, exist_ok=True)
        note_path = subdir / "iter.md"
        
        result = self.creator.create_new_note(note_path)
        
        self.assertEqual(result, 0)
        self.assertTrue(note_path.exists())
        
        # Check asset directory is created with .assets suffix on first level
        expected_asset_dir = Path(self.config.assets_dir) / "dsa.assets" / "anal" / "iter"
        self.assertTrue(expected_asset_dir.exists())
        
        # Check content
        content = note_path.read_text()
        self.assertIn("iter", content.lower())  # Title should be processed

    def test_generate_note_content_default_template_from_config(self):
        """Test note content generation with template from config."""
        # Create a template file in the expected location
        template_path = Path(self.config.notes_template)
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_content = "# {{title}}\n\nConfig template for {{note_name}}"
        template_path.write_text(template_content)
        
        note_path = Path("test-note.md")
        
        content = self.creator._generate_note_content(note_path)
        
        self.assertIn("# Test Note", content)
        self.assertIn("Config template for test-note", content)
        self.assertNotIn("{{note_name}}", content)  # Should be replaced
        self.assertNotIn("{{title}}", content)  # Should be replaced

    def test_generate_note_content_fallback_template(self):
        """Test note content generation with fallback template when config template doesn't exist."""
        # Ensure config template doesn't exist
        template_path = Path(self.config.notes_template)
        if template_path.exists():
            template_path.unlink()
        
        note_path = Path("test-note.md")
        
        content = self.creator._generate_note_content(note_path)
        
        # With empty fallback template, content should be minimal
        self.assertIn("test-note", content.lower())

    def test_generate_note_content_custom_template(self):
        """Test note content generation with custom template."""
        # Create custom template
        template_path = self.temp_dir / "custom-template.md"
        template_content = "# {{title}}\n\nDate: {{date}}\n\nNote: {{note_name}}"
        template_path.write_text(template_content)
        
        note_path = Path("test-note.md")
        
        content = self.creator._generate_note_content(note_path, template_path)
        
        self.assertIn("# Test Note", content)
        self.assertIn("Date:", content)
        self.assertIn("Note: test-note", content)

    def test_get_asset_directory(self):
        """Test asset directory path generation."""
        # Test with root-level note
        note_path = self.temp_dir / "my-note.md"
        note_path.touch()
        
        asset_dir = self.creator._get_asset_directory(note_path)
        
        expected = Path(self.config.assets_dir) / "my-note"
        self.assertEqual(asset_dir, expected)
    
    def test_get_asset_directory_nested(self):
        """Test asset directory path generation for nested notes."""
        # Test with nested note (should have .assets suffix on first level)
        subdir = self.temp_dir / "dsa" / "anal"
        subdir.mkdir(parents=True, exist_ok=True)
        note_path = subdir / "intro.md"
        note_path.touch()
        
        asset_dir = self.creator._get_asset_directory(note_path)
        
        # First level should have .assets suffix
        expected = Path(self.config.assets_dir) / "dsa.assets" / "anal" / "intro"
        self.assertEqual(asset_dir, expected)

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_validate_note_creation_valid(self, mock_initializer):
        """Test note creation validation for valid path."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "valid-note.md"
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_validate_note_creation_file_exists(self, mock_initializer):
        """Test note creation validation when file exists."""
        note_path = self.temp_dir / "existing-note.md"
        note_path.write_text("# Existing Note")
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertFalse(is_valid)
        self.assertIn("File already exists", error_msg)

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_validate_note_creation_non_compliant(self, mock_initializer):
        """Test note creation validation with non-compliant structure."""
        # Mock the initializer to return non-compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (False, ["Structure error"])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "new-note.md"
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertFalse(is_valid)
        self.assertIn("Asset tree structure is not compliant", error_msg)

    @patch('mkdocs_note.core.note_creator.NoteInitializer')
    def test_validate_note_creation_unsupported_extension(self, mock_initializer):
        """Test note creation validation with unsupported extension."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "note.txt"  # .txt is not in supported_extensions
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertFalse(is_valid)
        self.assertIn("Unsupported file extension", error_msg)


if __name__ == '__main__':
    unittest.main()
