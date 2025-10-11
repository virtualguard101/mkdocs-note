"""
Tests for note cleaner and mover functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.note_cleaner import NoteCleaner
from mkdocs_note.core.notes_mover import NoteMover


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config(temp_workspace):
    """Create test configuration."""
    config = PluginConfig()
    config.notes_dir = str(temp_workspace / "notes")
    config.assets_dir = str(temp_workspace / "notes" / "assets")
    return config


@pytest.fixture
def logger():
    """Create test logger."""
    return Logger()


@pytest.fixture
def cleaner(config, logger):
    """Create test cleaner."""
    return NoteCleaner(config, logger)


@pytest.fixture
def mover(config, logger):
    """Create test mover."""
    return NoteMover(config, logger)


class TestNoteCleaner:
    """Tests for NoteCleaner."""
    
    def test_find_orphaned_assets_empty(self, temp_workspace, config, cleaner):
        """Test finding orphaned assets when there are none."""
        # Create notes directory
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        # Create assets directory but no assets
        assets_dir = temp_workspace / "notes" / "assets"
        assets_dir.mkdir(parents=True)
        
        orphaned = cleaner.find_orphaned_assets()
        
        assert len(orphaned) == 0
    
    def test_find_orphaned_assets_with_orphans(self, temp_workspace, config, cleaner):
        """Test finding orphaned assets when they exist."""
        # Create notes directory
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        # Create a note with corresponding assets
        note_file = notes_dir / "test.md"
        note_file.write_text("# Test Note")
        
        asset_dir = temp_workspace / "notes" / "assets" / "test"
        asset_dir.mkdir(parents=True)
        
        # Create an orphaned asset directory
        orphaned_asset_dir = temp_workspace / "notes" / "assets" / "orphaned"
        orphaned_asset_dir.mkdir(parents=True)
        
        orphaned = cleaner.find_orphaned_assets()
        
        assert len(orphaned) == 1
        assert orphaned_asset_dir in orphaned
    
    def test_clean_orphaned_assets_dry_run(self, temp_workspace, config, cleaner):
        """Test cleaning orphaned assets in dry-run mode."""
        # Create notes directory
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        # Create an orphaned asset directory
        orphaned_asset_dir = temp_workspace / "notes" / "assets" / "orphaned"
        orphaned_asset_dir.mkdir(parents=True)
        
        count, removed = cleaner.clean_orphaned_assets(dry_run=True)
        
        assert count == 1
        assert len(removed) == 1
        # Asset directory should still exist in dry-run mode
        assert orphaned_asset_dir.exists()
    
    def test_clean_orphaned_assets(self, temp_workspace, config, cleaner):
        """Test cleaning orphaned assets."""
        # Create notes directory
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        # Create an orphaned asset directory
        orphaned_asset_dir = temp_workspace / "notes" / "assets" / "orphaned"
        orphaned_asset_dir.mkdir(parents=True)
        (orphaned_asset_dir / "file.txt").write_text("test")
        
        count, removed = cleaner.clean_orphaned_assets(dry_run=False)
        
        assert count == 1
        assert len(removed) == 1
        # Asset directory should be removed
        assert not orphaned_asset_dir.exists()
    
    def test_find_orphaned_with_nested_structure(self, temp_workspace, config, cleaner):
        """Test finding orphaned assets in nested structure."""
        # Create notes directory with nested structure
        notes_dir = temp_workspace / "notes"
        category_dir = notes_dir / "category"
        category_dir.mkdir(parents=True)
        
        # Create a note in category
        note_file = category_dir / "test.md"
        note_file.write_text("# Test Note")
        
        # Create corresponding asset
        asset_dir = temp_workspace / "notes" / "assets" / "category.assets" / "test"
        asset_dir.mkdir(parents=True)
        
        # Create an orphaned asset in the same category
        orphaned_dir = temp_workspace / "notes" / "assets" / "category.assets" / "orphaned"
        orphaned_dir.mkdir(parents=True)
        
        orphaned = cleaner.find_orphaned_assets()
        
        assert len(orphaned) == 1
        assert orphaned_dir in orphaned


class TestNoteMover:
    """Tests for NoteMover."""
    
    def test_move_note_with_assets(self, temp_workspace, config, mover):
        """Test moving a note file with its asset directory."""
        # Create test structure
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        source_file = notes_dir / "source.md"
        source_file.write_text("# Source Note")
        
        source_asset_dir = temp_workspace / "notes" / "assets" / "source"
        source_asset_dir.mkdir(parents=True)
        (source_asset_dir / "image.png").write_text("fake image")
        
        dest_file = notes_dir / "destination.md"
        
        # Move note with assets
        result = mover.move_note(source_file, dest_file, move_assets=True)
        
        assert result == 0
        assert not source_file.exists()
        assert dest_file.exists()
        assert not source_asset_dir.exists()
        
        dest_asset_dir = temp_workspace / "notes" / "assets" / "destination"
        assert dest_asset_dir.exists()
        assert (dest_asset_dir / "image.png").exists()
    
    def test_move_note_keep_assets(self, temp_workspace, config, mover):
        """Test moving a note file while keeping its asset directory."""
        # Create test structure
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        source_file = notes_dir / "source.md"
        source_file.write_text("# Source Note")
        
        source_asset_dir = temp_workspace / "notes" / "assets" / "source"
        source_asset_dir.mkdir(parents=True)
        
        dest_file = notes_dir / "destination.md"
        
        # Move note without moving assets
        result = mover.move_note(source_file, dest_file, move_assets=False)
        
        assert result == 0
        assert not source_file.exists()
        assert dest_file.exists()
        assert source_asset_dir.exists()
    
    def test_move_note_to_subdirectory(self, temp_workspace, config, mover):
        """Test moving a note to a subdirectory."""
        # Create test structure
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        source_file = notes_dir / "source.md"
        source_file.write_text("# Source Note")
        
        source_asset_dir = temp_workspace / "notes" / "assets" / "source"
        source_asset_dir.mkdir(parents=True)
        
        # Create destination subdirectory
        dest_dir = notes_dir / "category"
        dest_dir.mkdir(parents=True)
        dest_file = dest_dir / "destination.md"
        
        # Move note with assets
        result = mover.move_note(source_file, dest_file, move_assets=True)
        
        assert result == 0
        assert not source_file.exists()
        assert dest_file.exists()
        assert not source_asset_dir.exists()
        
        dest_asset_dir = temp_workspace / "notes" / "assets" / "category.assets" / "destination"
        assert dest_asset_dir.exists()
    
    def test_move_note_nonexistent_source(self, temp_workspace, config, mover):
        """Test moving a nonexistent note file."""
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        source_file = notes_dir / "nonexistent.md"
        dest_file = notes_dir / "destination.md"
        
        result = mover.move_note(source_file, dest_file, move_assets=True)
        
        assert result == 1
    
    def test_move_note_existing_destination(self, temp_workspace, config, mover):
        """Test moving to an existing destination."""
        # Create test structure
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        source_file = notes_dir / "source.md"
        source_file.write_text("# Source Note")
        
        dest_file = notes_dir / "destination.md"
        dest_file.write_text("# Existing Destination")
        
        result = mover.move_note(source_file, dest_file, move_assets=True)
        
        assert result == 1
        assert source_file.exists()
        assert dest_file.exists()
    
    def test_rename_note(self, temp_workspace, config, mover):
        """Test renaming a note (move within same directory)."""
        # Create test structure
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        source_file = notes_dir / "old_name.md"
        source_file.write_text("# Old Name")
        
        source_asset_dir = temp_workspace / "notes" / "assets" / "old_name"
        source_asset_dir.mkdir(parents=True)
        (source_asset_dir / "image.png").write_text("fake image")
        
        dest_file = notes_dir / "new_name.md"
        
        # Rename note with assets
        result = mover.move_note(source_file, dest_file, move_assets=True)
        
        assert result == 0
        assert not source_file.exists()
        assert dest_file.exists()
        assert not source_asset_dir.exists()
        
        dest_asset_dir = temp_workspace / "notes" / "assets" / "new_name"
        assert dest_asset_dir.exists()
        assert (dest_asset_dir / "image.png").exists()
    
    def test_move_directory_with_notes(self, temp_workspace, config, mover):
        """Test moving a directory with multiple notes."""
        # Create test structure
        notes_dir = temp_workspace / "notes"
        source_dir = notes_dir / "old_category"
        source_dir.mkdir(parents=True)
        
        # Create multiple notes
        note1 = source_dir / "note1.md"
        note1.write_text("# Note 1")
        note2 = source_dir / "note2.md"
        note2.write_text("# Note 2")
        
        # Create assets for notes
        assets_dir = temp_workspace / "notes" / "assets"
        asset1_dir = assets_dir / "old_category.assets" / "note1"
        asset1_dir.mkdir(parents=True)
        (asset1_dir / "image1.png").write_text("image1")
        
        asset2_dir = assets_dir / "old_category.assets" / "note2"
        asset2_dir.mkdir(parents=True)
        (asset2_dir / "image2.png").write_text("image2")
        
        # Move directory
        dest_dir = notes_dir / "new_category"
        result = mover.move_note_or_directory(source_dir, dest_dir, move_assets=True)
        
        assert result == 0
        assert not source_dir.exists()
        assert dest_dir.exists()
        assert (dest_dir / "note1.md").exists()
        assert (dest_dir / "note2.md").exists()
        
        # Check assets moved
        new_asset1_dir = assets_dir / "new_category.assets" / "note1"
        new_asset2_dir = assets_dir / "new_category.assets" / "note2"
        assert new_asset1_dir.exists()
        assert new_asset2_dir.exists()
        assert (new_asset1_dir / "image1.png").exists()
        assert (new_asset2_dir / "image2.png").exists()
        
        # Check old assets removed
        assert not (assets_dir / "old_category.assets").exists()
    
    def test_move_directory_with_nested_notes(self, temp_workspace, config, mover):
        """Test moving a directory with nested subdirectories and notes."""
        # Create nested structure
        notes_dir = temp_workspace / "notes"
        source_dir = notes_dir / "source"
        subdir = source_dir / "subdir"
        subdir.mkdir(parents=True)
        
        # Create notes at different levels
        note1 = source_dir / "note1.md"
        note1.write_text("# Note 1")
        note2 = subdir / "note2.md"
        note2.write_text("# Note 2")
        
        # Create assets
        assets_dir = temp_workspace / "notes" / "assets"
        asset1_dir = assets_dir / "source.assets" / "note1"
        asset1_dir.mkdir(parents=True)
        (asset1_dir / "image1.png").write_text("image1")
        
        asset2_dir = assets_dir / "source.assets" / "subdir" / "note2"
        asset2_dir.mkdir(parents=True)
        (asset2_dir / "image2.png").write_text("image2")
        
        # Move directory
        dest_dir = notes_dir / "destination"
        result = mover.move_directory(source_dir, dest_dir, move_assets=True)
        
        assert result == 0
        assert dest_dir.exists()
        assert (dest_dir / "note1.md").exists()
        assert (dest_dir / "subdir" / "note2.md").exists()
        
        # Check assets moved with correct structure
        new_asset1_dir = assets_dir / "destination.assets" / "note1"
        new_asset2_dir = assets_dir / "destination.assets" / "subdir" / "note2"
        assert new_asset1_dir.exists()
        assert new_asset2_dir.exists()
        assert (new_asset1_dir / "image1.png").exists()
        assert (new_asset2_dir / "image2.png").exists()
    
    def test_move_empty_directory(self, temp_workspace, config, mover):
        """Test moving an empty directory."""
        # Create empty directory
        notes_dir = temp_workspace / "notes"
        source_dir = notes_dir / "empty"
        source_dir.mkdir(parents=True)
        
        dest_dir = notes_dir / "new_empty"
        
        # Move empty directory
        result = mover.move_directory(source_dir, dest_dir, move_assets=True)
        
        # Should succeed but with no notes
        assert result == 0
        assert dest_dir.exists()
    
    def test_move_into_existing_directory(self, temp_workspace, config, mover):
        """Test moving a directory into an existing destination directory (shell mv behavior)."""
        # Create source directory with notes
        notes_dir = temp_workspace / "notes"
        source_dir = notes_dir / "source"
        source_dir.mkdir(parents=True)
        
        note = source_dir / "test.md"
        note.write_text("# Test")
        
        # Create assets
        assets_dir = temp_workspace / "notes" / "assets"
        asset_dir = assets_dir / "source.assets" / "test"
        asset_dir.mkdir(parents=True)
        (asset_dir / "image.png").write_text("image")
        
        # Create existing destination directory
        dest_parent = notes_dir / "destination"
        dest_parent.mkdir(parents=True)
        
        # Move into existing directory
        result = mover.move_note_or_directory(source_dir, dest_parent, move_assets=True)
        
        assert result == 0
        # Should be moved to destination/source
        assert (dest_parent / "source" / "test.md").exists()
        assert not source_dir.exists()
        
        # Check assets moved correctly
        new_asset_dir = assets_dir / "destination.assets" / "source" / "test"
        assert new_asset_dir.exists()
        assert (new_asset_dir / "image.png").exists()
    
    def test_move_note_into_existing_directory(self, temp_workspace, config, mover):
        """Test moving a single note into an existing directory."""
        # Create source note
        notes_dir = temp_workspace / "notes"
        notes_dir.mkdir(parents=True)
        
        note = notes_dir / "test.md"
        note.write_text("# Test")
        
        # Create assets
        assets_dir = temp_workspace / "notes" / "assets"
        asset_dir = assets_dir / "test"
        asset_dir.mkdir(parents=True)
        (asset_dir / "image.png").write_text("image")
        
        # Create existing destination directory
        dest_dir = notes_dir / "archive"
        dest_dir.mkdir(parents=True)
        
        # Move note into existing directory
        result = mover.move_note_or_directory(note, dest_dir, move_assets=True)
        
        assert result == 0
        # Should be moved to archive/test.md
        assert (dest_dir / "test.md").exists()
        assert not note.exists()
        
        # Check assets moved correctly
        new_asset_dir = assets_dir / "archive.assets" / "test"
        assert new_asset_dir.exists()
        assert (new_asset_dir / "image.png").exists()

