import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from datetime import timezone, timedelta

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.utils.docsps.creator import NoteCreator
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

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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
    
    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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
        
        # Check asset directory is created in co-located structure
        expected_asset_dir = subdir / "assets" / "iter"
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
        # Test with nested note (co-located structure)
        subdir = self.temp_dir / "dsa" / "anal"
        subdir.mkdir(parents=True, exist_ok=True)
        note_path = subdir / "intro.md"
        note_path.touch()
        
        asset_dir = self.creator._get_asset_directory(note_path)
        
        # Asset directory should be next to the note file
        expected = subdir / "assets" / "intro"
        self.assertEqual(asset_dir, expected)

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
    def test_validate_note_creation_file_exists(self, mock_initializer):
        """Test note creation validation when file exists."""
        note_path = self.temp_dir / "existing-note.md"
        note_path.write_text("# Existing Note")
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertFalse(is_valid)
        self.assertIn("File already exists", error_msg)

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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

    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
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
    
    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
    def test_validate_note_creation_excluded_pattern(self, mock_initializer):
        """Test note creation validation with excluded pattern (index.md)."""
        note_path = self.temp_dir / "index.md"
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertFalse(is_valid)
        self.assertIn("index.md", error_msg)
        self.assertIn("exclude_patterns", error_msg)
    
    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
    def test_validate_note_creation_excluded_readme(self, mock_initializer):
        """Test note creation validation with excluded pattern (README.md)."""
        note_path = self.temp_dir / "README.md"
        
        is_valid, error_msg = self.creator.validate_note_creation(note_path)
        
        self.assertFalse(is_valid)
        self.assertIn("README.md", error_msg)
        self.assertIn("exclude_patterns", error_msg)
    
    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
    def test_create_new_note_excluded_pattern(self, mock_initializer):
        """Test note creation with excluded pattern should fail."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "index.md"
        
        result = self.creator.create_new_note(note_path)
        
        self.assertEqual(result, 1)
        self.assertFalse(note_path.exists())
    
    @patch('mkdocs_note.utils.docsps.creator.NoteInitializer')
    def test_create_new_note_excluded_readme(self, mock_initializer):
        """Test note creation with README.md should fail."""
        # Mock the initializer to return compliant structure
        mock_init = Mock()
        mock_init.validate_asset_tree_compliance.return_value = (True, [])
        self.creator.initializer = mock_init
        
        note_path = self.temp_dir / "README.md"
        
        result = self.creator.create_new_note(note_path)
        
        self.assertEqual(result, 1)
        self.assertFalse(note_path.exists())
    
    def test_parse_timezone_utc(self):
        """Test timezone parsing for UTC+0."""
        result = self.creator._parse_timezone('UTC+0')
        self.assertEqual(result, timezone.utc)
    
    def test_parse_timezone_positive(self):
        """Test timezone parsing for positive offset."""
        result = self.creator._parse_timezone('UTC+8')
        expected = timezone(timedelta(hours=8))
        self.assertEqual(result, expected)
    
    def test_parse_timezone_negative(self):
        """Test timezone parsing for negative offset."""
        result = self.creator._parse_timezone('UTC-5')
        expected = timezone(timedelta(hours=-5))
        self.assertEqual(result, expected)
    
    def test_parse_timezone_invalid_format(self):
        """Test timezone parsing with invalid format."""
        with patch.object(self.logger, 'warning') as mock_warning:
            result = self.creator._parse_timezone('Invalid')
        self.assertEqual(result, timezone.utc)
        mock_warning.assert_called_once()


if __name__ == '__main__':
    unittest.main()
