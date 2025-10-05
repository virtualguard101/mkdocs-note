import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs_note.core.assets_manager import (
    AssetsCatalogTree,
    AssetsManager,
    AssetsProcessor,
    get_note_relative_path,
)
from mkdocs_note.core.data_models import NoteInfo, AssetsInfo
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger


class TestGetNoteRelativePath(unittest.TestCase):
    """Test cases for get_note_relative_path function."""

    def test_root_level_note(self):
        """Test note at root level (no subdirectory)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            note_file = notes_dir / "test.md"
            note_file.touch()
            
            result = get_note_relative_path(note_file, notes_dir)
            self.assertEqual(result, "test")
    
    def test_single_level_note(self):
        """Test note in single-level subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            subdir = notes_dir / "dsa"
            subdir.mkdir()
            note_file = subdir / "intro.md"
            note_file.touch()
            
            result = get_note_relative_path(note_file, notes_dir)
            # First level should have .assets suffix
            self.assertEqual(result, "dsa.assets/intro")
    
    def test_multi_level_note(self):
        """Test note in multi-level subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            subdir = notes_dir / "dsa" / "anal"
            subdir.mkdir(parents=True)
            note_file = subdir / "iter_and_recu.md"
            note_file.touch()
            
            result = get_note_relative_path(note_file, notes_dir)
            # Only first level should have .assets suffix
            self.assertEqual(result, "dsa.assets/anal/iter_and_recu")
    
    def test_deep_nested_note(self):
        """Test note in deeply nested subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            subdir = notes_dir / "language" / "cpp" / "fundamental"
            subdir.mkdir(parents=True)
            note_file = subdir / "11-smart_pointer.md"
            note_file.touch()
            
            result = get_note_relative_path(note_file, notes_dir)
            # Only first level should have .assets suffix
            self.assertEqual(result, "language.assets/cpp/fundamental/11-smart_pointer")
    
    def test_without_assets_suffix(self):
        """Test with use_assets_suffix=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            subdir = notes_dir / "dsa"
            subdir.mkdir()
            note_file = subdir / "intro.md"
            note_file.touch()
            
            result = get_note_relative_path(note_file, notes_dir, use_assets_suffix=False)
            # Should not have .assets suffix
            self.assertEqual(result, "dsa/intro")


class TestAssetsInfo(unittest.TestCase):
    """Test cases for AssetsInfo dataclass."""

    def test_assets_info_creation(self):
        """Test AssetsInfo creation with all fields."""
        file_path = Path('/test/image.png')
        asset_info = AssetsInfo(
            file_path=file_path,
            file_name='image.png',
            relative_path='assets/note1/image.png',
            index_in_list=0,
            exists=True
        )
        
        self.assertEqual(asset_info.file_path, file_path)
        self.assertEqual(asset_info.file_name, 'image.png')
        self.assertEqual(asset_info.relative_path, 'assets/note1/image.png')
        self.assertEqual(asset_info.index_in_list, 0)
        self.assertTrue(asset_info.exists)


class TestAssetsCatalogTree(unittest.TestCase):
    """Test cases for AssetsCatalogTree class."""

    def setUp(self):
        """Set up test fixtures."""
        self.root_path = Path('/test/assets')
        self.notes_dir = Path('/test/notes')
        self.catalog = AssetsCatalogTree(self.root_path, self.notes_dir)

    def test_initialization(self):
        """Test AssetsCatalogTree initialization."""
        self.assertEqual(self.catalog._root, self.root_path)
        self.assertEqual(self.catalog._notes_dir, self.notes_dir)
        self.assertIsInstance(self.catalog._catalog, dict)

    def test_add_node(self):
        """Test adding assets for a note."""
        note_relative_path = "test-note"
        assets_list = [
            AssetsInfo(
                file_path=Path('/test/image1.png'),
                file_name='image1.png',
                relative_path='assets/test-note/image1.png',
                index_in_list=0,
                exists=True
            ),
            AssetsInfo(
                file_path=Path('/test/image2.png'),
                file_name='image2.png',
                relative_path='assets/test-note/image2.png',
                index_in_list=1,
                exists=False
            )
        ]
        
        self.catalog.add_node(note_relative_path, assets_list)
        
        self.assertEqual(len(self.catalog._catalog), 1)
        self.assertIn(note_relative_path, self.catalog._catalog)
        self.assertEqual(self.catalog._catalog[note_relative_path], assets_list)

    def test_add_node_with_subdirectories(self):
        """Test adding assets for notes in subdirectories."""
        # Two notes with same name in different directories (with .assets suffix)
        python_note = "language.assets/python/intro"
        javascript_note = "language.assets/javascript/intro"
        
        python_assets = [Mock()]
        javascript_assets = [Mock()]
        
        self.catalog.add_node(python_note, python_assets)
        self.catalog.add_node(javascript_note, javascript_assets)
        
        # Both should exist without conflict
        self.assertEqual(len(self.catalog._catalog), 2)
        self.assertIn(python_note, self.catalog._catalog)
        self.assertIn(javascript_note, self.catalog._catalog)
        self.assertEqual(self.catalog.get_assets(python_note), python_assets)
        self.assertEqual(self.catalog.get_assets(javascript_note), javascript_assets)

    def test_get_assets(self):
        """Test getting assets for a specific note."""
        note_relative_path = "test-note"
        assets_list = [Mock()]
        
        self.catalog.add_node(note_relative_path, assets_list)
        
        result = self.catalog.get_assets(note_relative_path)
        self.assertEqual(result, assets_list)

    def test_get_assets_nonexistent(self):
        """Test getting assets for non-existent note."""
        result = self.catalog.get_assets("nonexistent-note")
        self.assertEqual(result, [])

    def test_get_all_assets(self):
        """Test getting all assets."""
        assets1 = [Mock()]
        assets2 = [Mock()]
        
        self.catalog.add_node("note1", assets1)
        self.catalog.add_node("note2", assets2)
        
        result = self.catalog.get_all_assets()
        
        self.assertEqual(len(result), 2)
        self.assertIn("note1", result)
        self.assertIn("note2", result)
        self.assertEqual(result["note1"], assets1)
        self.assertEqual(result["note2"], assets2)
    
    def test_get_asset_dir_for_note(self):
        """Test getting asset directory for a note."""
        # Create a real temporary directory for this test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_notes = Path(temp_dir) / "notes"
            temp_assets = Path(temp_dir) / "assets"
            temp_notes.mkdir()
            temp_assets.mkdir()
            
            catalog = AssetsCatalogTree(temp_assets, temp_notes)
            
            # Test with nested note (should have .assets suffix in first level)
            note_file = temp_notes / "dsa" / "anal" / "intro.md"
            note_file.parent.mkdir(parents=True, exist_ok=True)
            note_file.touch()
            
            result = catalog.get_asset_dir_for_note(note_file)
            expected = temp_assets / "dsa.assets" / "anal" / "intro"
            
            self.assertEqual(result, expected)
            
            # Test with root-level note (no .assets suffix)
            root_note = temp_notes / "test.md"
            root_note.touch()
            
            result_root = catalog.get_asset_dir_for_note(root_note)
            expected_root = temp_assets / "test"
            
            self.assertEqual(result_root, expected_root)


class TestAssetsManager(unittest.TestCase):
    """Test cases for AssetsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.manager = AssetsManager(self.config, self.logger)

    def test_initialization(self):
        """Test AssetsManager initialization."""
        self.assertIs(self.manager.config, self.config)
        self.assertIs(self.manager.logger, self.logger)
        self.assertIsInstance(self.manager.catalog_tree, AssetsCatalogTree)

    def test_catalog_generator_empty_list(self):
        """Test catalog generation with empty assets list."""
        note_info = Mock()
        note_info.title = "Test Note"
        note_info.file_path = Path('/test/note.md')
        
        result = self.manager.catalog_generator([], note_info)
        
        self.assertEqual(result, "")

    def test_catalog_generator_with_assets(self):
        """Test catalog generation with assets."""
        note_info = Mock()
        note_info.title = "Test Note"
        note_info.file_path = Path('/test/note.md')
        
        assets_list = [
            AssetsInfo(
                file_path=Path('/test/image1.png'),
                file_name='image1.png',
                relative_path='assets/test-note/image1.png',
                index_in_list=0,
                exists=True
            ),
            AssetsInfo(
                file_path=Path('/test/image2.png'),
                file_name='image2.png',
                relative_path='assets/test-note/image2.png',
                index_in_list=1,
                exists=False
            )
        ]
        
        result = self.manager.catalog_generator(assets_list, note_info)
        
        self.assertIn("## Assets for Test Note", result)
        self.assertIn("✓ `image1.png`", result)
        self.assertIn("✗ `image2.png`", result)

    def test_catalog_updater_success(self):
        """Test successful catalog update."""
        catalog = "Test catalog content"
        
        with patch.object(self.logger, 'debug') as mock_debug:
            result = self.manager.catalog_updater(catalog)
        
        self.assertTrue(result)
        mock_debug.assert_called_once()

    def test_catalog_updater_exception(self):
        """Test catalog update with exception."""
        catalog = "Test catalog content"
        
        with patch.object(self.logger, 'debug', side_effect=Exception("Test error")):
            with patch.object(self.logger, 'error') as mock_error:
                result = self.manager.catalog_updater(catalog)
        
        self.assertFalse(result)
        mock_error.assert_called_once()


class TestAssetsProcessor(unittest.TestCase):
    """Test cases for AssetsProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PluginConfig()
        self.logger = Logger()
        self.processor = AssetsProcessor(self.config, self.logger)
        
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config.assets_dir = str(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test AssetsProcessor initialization."""
        self.assertIs(self.processor.config, self.config)
        self.assertIs(self.processor.logger, self.logger)
        self.assertIsNotNone(self.processor.image_pattern)

    def test_process_assets_no_images(self):
        """Test processing assets with no images."""
        note_info = Mock()
        note_info.file_path = self.temp_dir / "test-note.md"
        
        # Create a note file with no images
        note_info.file_path.write_text("# Test Note\n\nNo images here.")
        
        result = self.processor.process_assets(note_info)
        
        self.assertEqual(len(result), 0)

    def test_process_assets_with_images(self):
        """Test processing assets with images."""
        note_info = Mock()
        note_info.file_path = self.temp_dir / "test-note.md"
        
        # Create a note file with images
        content = "# Test Note\n\n![Image 1](image1.png)\n\n![Image 2](images/image2.jpg)"
        note_info.file_path.write_text(content)
        
        # Create asset directories and files
        (self.temp_dir / "test-note").mkdir(parents=True)
        (self.temp_dir / "test-note" / "image1.png").touch()
        (self.temp_dir / "test-note" / "images").mkdir()
        (self.temp_dir / "test-note" / "images" / "image2.jpg").touch()
        
        result = self.processor.process_assets(note_info)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].file_name, 'image1.png')
        self.assertEqual(result[1].file_name, 'images/image2.jpg')
        self.assertTrue(result[0].exists)
        self.assertTrue(result[1].exists)

    def test_process_assets_external_urls(self):
        """Test processing assets with external URLs."""
        note_info = Mock()
        note_info.file_path = self.temp_dir / "test-note.md"
        
        # Create a note file with external URLs
        content = "# Test Note\n\n![External](https://example.com/image.png)\n\n![Another](//cdn.example.com/image.jpg)"
        note_info.file_path.write_text(content)
        
        result = self.processor.process_assets(note_info)
        
        # External URLs should be skipped
        self.assertEqual(len(result), 0)

    def test_process_image_reference_simple(self):
        """Test processing simple image reference."""
        # Setup: create a note file in the temp directory
        note_file = self.temp_dir / "test-note.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        image_path = "image.png"
        
        result = self.processor._process_image_reference(image_path, note_file, 0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.file_name, 'image.png')
        self.assertEqual(result.relative_path, 'assets/test-note/image.png')
        self.assertFalse(result.exists)  # File doesn't exist

    def test_process_image_reference_with_subdir(self):
        """Test processing image reference with subdirectory."""
        # Setup: create a note file in the temp directory
        note_file = self.temp_dir / "test-note.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        image_path = "images/photo.jpg"
        
        result = self.processor._process_image_reference(image_path, note_file, 0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.file_name, 'images/photo.jpg')
        self.assertEqual(result.relative_path, 'assets/test-note/images/photo.jpg')
    
    def test_process_image_reference_nested_notes(self):
        """Test processing image reference for notes in subdirectories."""
        # Create a note in a subdirectory
        subdir = self.temp_dir / "dsa" / "anal"
        subdir.mkdir(parents=True)
        note_file = subdir / "intro.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        image_path = "diagram.png"
        
        result = self.processor._process_image_reference(image_path, note_file, 0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.file_name, 'diagram.png')
        # Should use dsa.assets/anal/intro as the path with .assets suffix
        self.assertEqual(result.relative_path, 'assets/dsa.assets/anal/intro/diagram.png')

    def test_update_markdown_content_no_images(self):
        """Test updating markdown content with no images."""
        content = "# Test Note\n\nNo images here."
        note_file = self.temp_dir / "test-note.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        result = self.processor.update_markdown_content(content, note_file)
        
        self.assertEqual(result, content)

    def test_update_markdown_content_with_images(self):
        """Test updating markdown content with images."""
        content = "# Test Note\n\n![Image](image.png)\n\n![Subdir Image](images/photo.jpg)"
        note_file = self.temp_dir / "test-note.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        result = self.processor.update_markdown_content(content, note_file)
        
        # Root level notes don't need ../ prefix
        self.assertIn("![Image](assets/test-note/image.png)", result)
        self.assertIn("![Subdir Image](assets/test-note/images/photo.jpg)", result)

    def test_update_markdown_content_external_urls(self):
        """Test updating markdown content with external URLs."""
        content = "# Test Note\n\n![External](https://example.com/image.png)\n\n![Local](local.png)"
        note_file = self.temp_dir / "test-note.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        result = self.processor.update_markdown_content(content, note_file)
        
        # External URL should remain unchanged
        self.assertIn("![External](https://example.com/image.png)", result)
        # Local image should be updated
        self.assertIn("![Local](assets/test-note/local.png)", result)
    
    def test_update_markdown_content_nested_notes(self):
        """Test updating markdown content for notes in subdirectories."""
        # Create a note in a subdirectory
        subdir = self.temp_dir / "language" / "python"
        subdir.mkdir(parents=True)
        note_file = subdir / "intro.md"
        note_file.touch()
        
        # Update config to use temp_dir as notes_dir
        self.config.notes_dir = str(self.temp_dir)
        
        content = "# Python Intro\n\n![Diagram](diagram.png)"
        result = self.processor.update_markdown_content(content, note_file)
        
        # Should use ../../ to go up two levels, then into assets
        self.assertIn("![Diagram](../../assets/language.assets/python/intro/diagram.png)", result)


if __name__ == '__main__':
    unittest.main()
