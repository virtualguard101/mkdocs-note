import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.utils.docsps.initializer import NoteInitializer
from mkdocs_note.utils.dataps.meta import AssetTreeInfo
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger


class TestAssetTreeInfo(unittest.TestCase):
    """Test cases for AssetTreeInfo dataclass."""

    def test_asset_tree_info_creation(self):
        """Test AssetTreeInfo creation with all fields."""
        asset_info = AssetTreeInfo(
            note_name="test-note",
            asset_dir=Path("/test/assets/test-note"),
            expected_structure=[Path("/test/assets/test-note")],
            actual_structure=[Path("/test/assets/test-note")],
            is_compliant=True,
            missing_dirs=[],
            extra_dirs=[]
        )
        
        self.assertEqual(asset_info.note_name, "test-note")
        self.assertEqual(asset_info.is_compliant, True)
        self.assertEqual(len(asset_info.missing_dirs), 0)


class TestNoteInitializer(unittest.TestCase):
    """Test cases for NoteInitializer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.initializer = NoteInitializer(self.config, self.logger)
        
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config.notes_dir = str(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test NoteInitializer initialization."""
        self.assertIs(self.initializer.config, self.config)
        self.assertIs(self.initializer.logger, self.logger)

    @patch('mkdocs_note.utils.docsps.initializer.NoteScanner')
    def test_initialize_note_directory_new_directory(self, mock_file_scanner):
        """Test initializing a new directory."""
        mock_scanner = Mock()
        mock_scanner.scan_notes.return_value = []
        mock_file_scanner.return_value = mock_scanner
        
        result = self.initializer.initialize_note_directory(self.temp_dir)
        
        self.assertEqual(result, 0)
        self.assertTrue(self.temp_dir.exists())
        self.assertTrue((self.temp_dir / "assets").exists())
        # Template directory is not created automatically

    @patch('mkdocs_note.utils.docsps.initializer.NoteScanner')
    def test_initialize_note_directory_with_existing_notes(self, mock_file_scanner):
        """Test initializing directory with existing notes."""
        # Create mock note files
        note_file = self.temp_dir / "test-note.md"
        note_file.write_text("# Test Note\n\nContent here.")
        
        mock_scanner = Mock()
        mock_scanner.scan_notes.return_value = [note_file]
        mock_file_scanner.return_value = mock_scanner
        
        result = self.initializer.initialize_note_directory(self.temp_dir)
        
        self.assertEqual(result, 0)
        self.assertTrue((self.temp_dir / "assets" / "test-note").exists())

    def test_analyze_asset_tree(self):
        """Test asset tree analysis."""
        # Create test structure with co-located assets
        note_file = self.temp_dir / "test-note.md"
        note_file.write_text("# Test Note")
        
        # Create compliant asset directory (co-located)
        assets_dir = self.temp_dir / "assets"
        assets_dir.mkdir(parents=True)
        asset_dir = assets_dir / "test-note"
        asset_dir.mkdir()
        
        analysis = self.initializer._analyze_asset_tree(self.temp_dir, [note_file])
        
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0].note_name, "test-note.md")
        self.assertTrue(analysis[0].is_compliant)

    def test_check_compliance_compliant(self):
        """Test compliance check for compliant structure."""
        # Create note file
        note_file = self.temp_dir / "test-note.md"
        note_file.write_text("# Test")
        
        # Create co-located asset directory
        assets_dir = self.temp_dir / "assets"
        assets_dir.mkdir(parents=True)
        asset_dir = assets_dir / "test-note"
        asset_dir.mkdir()
        
        is_compliant = self.initializer._check_compliance(asset_dir, note_file)
        
        self.assertTrue(is_compliant)

    def test_check_compliance_non_compliant(self):
        """Test compliance check for non-compliant structure."""
        # Create note file
        note_file = self.temp_dir / "test-note.md"
        note_file.write_text("# Test")
        
        # Create non-compliant structure (wrong location)
        assets_dir = self.temp_dir / "assets"
        assets_dir.mkdir(parents=True)
        wrong_dir = assets_dir / "wrong-name"  # Wrong name, should be "test-note"
        wrong_dir.mkdir(parents=True)
        
        is_compliant = self.initializer._check_compliance(wrong_dir, note_file)
        
        self.assertFalse(is_compliant)

    def test_ensure_index_file(self):
        """Test index file creation."""
        self.initializer._ensure_index_file(self.temp_dir)
        
        index_file = self.temp_dir / "index.md"
        self.assertTrue(index_file.exists())
        
        content = index_file.read_text()
        self.assertEqual(content, "")

    def test_ensure_template_file_exists(self):
        """Test template file check when template exists."""
        # Use a temporary template path instead of the real one
        temp_template_path = self.temp_dir / "test_template.md"
        temp_template_path.parent.mkdir(parents=True, exist_ok=True)
        temp_template_path.write_text("# Template content")
        
        # Override config to use temp path
        original_template = self.config.notes_template
        self.config.notes_template = str(temp_template_path)
        
        try:
            self.initializer._ensure_template_file(self.temp_dir)
            
            # Template should still exist
            self.assertTrue(temp_template_path.exists())
        finally:
            # Restore original config
            self.config.notes_template = original_template

    def test_ensure_template_file_create_in_notes_dir(self):
        """Test template file creation when template is in notes directory."""
        # Set template path to be in notes directory
        self.config.notes_template = str(self.temp_dir / "templates" / "default.md")
        
        self.initializer._ensure_template_file(self.temp_dir)
        
        template_path = Path(self.config.notes_template)
        self.assertTrue(template_path.exists())
        
        content = template_path.read_text()
        # Template should have frontmatter
        self.assertIn("---", content)
        self.assertIn("{{date}}", content)
        self.assertIn("{{title}}", content)

    def test_ensure_template_file_cannot_create_outside_notes_dir(self):
        """Test template file handling when template is outside notes directory."""
        # Set template path outside notes directory
        self.config.notes_template = "/tmp/external-template.md"
        
        self.initializer._ensure_template_file(self.temp_dir)
        
        # Template should not be created
        template_path = Path(self.config.notes_template)
        self.assertFalse(template_path.exists())

    def test_validate_asset_tree_compliance_compliant(self):
        """Test validation for compliant asset tree."""
        # Create compliant structure
        assets_dir = self.temp_dir / "assets"
        assets_dir.mkdir(parents=True)
        
        note_file = self.temp_dir / "test-note.md"
        note_file.write_text("# Test Note")
        
        asset_dir = assets_dir / "test-note"
        asset_dir.mkdir()
        
        with patch('mkdocs_note.utils.docsps.initializer.NoteScanner') as mock_file_scanner:
            mock_scanner = Mock()
            mock_scanner.scan_notes.return_value = [note_file]
            mock_file_scanner.return_value = mock_scanner
            
            is_compliant, errors = self.initializer.validate_asset_tree_compliance(self.temp_dir)
            
            self.assertTrue(is_compliant)
            self.assertEqual(len(errors), 0)

    def test_validate_asset_tree_compliance_non_compliant(self):
        """Test validation for non-compliant asset tree."""
        # Create non-compliant structure
        assets_dir = self.temp_dir / "assets"
        assets_dir.mkdir(parents=True)
        
        note_file = self.temp_dir / "test-note.md"
        note_file.write_text("# Test Note")
        
        # Create nested structure (non-compliant)
        nested_dir = assets_dir / "old-structure" / "test-note"
        nested_dir.mkdir(parents=True)
        
        with patch('mkdocs_note.utils.docsps.initializer.NoteScanner') as mock_file_scanner:
            mock_scanner = Mock()
            mock_scanner.scan_notes.return_value = [note_file]
            mock_file_scanner.return_value = mock_scanner
            
            is_compliant, errors = self.initializer.validate_asset_tree_compliance(self.temp_dir)
            
            self.assertFalse(is_compliant)
            self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
