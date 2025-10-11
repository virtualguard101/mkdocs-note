"""
Tests for note remover functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.note_remover import NoteRemover


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
def remover(config, logger):
    """Create test remover."""
    return NoteRemover(config, logger)


def test_remove_note_with_assets(temp_workspace, config, remover):
    """Test removing a note file with its asset directory."""
    # Create test structure
    notes_dir = temp_workspace / "notes"
    notes_dir.mkdir(parents=True)
    
    note_file = notes_dir / "test.md"
    note_file.write_text("# Test Note")
    
    asset_dir = temp_workspace / "notes" / "assets" / "test"
    asset_dir.mkdir(parents=True)
    (asset_dir / "image.png").write_text("fake image")
    
    # Remove note with assets
    result = remover.remove_note(note_file, remove_assets=True)
    
    assert result == 0
    assert not note_file.exists()
    assert not asset_dir.exists()


def test_remove_note_keep_assets(temp_workspace, config, remover):
    """Test removing a note file while keeping its asset directory."""
    # Create test structure
    notes_dir = temp_workspace / "notes"
    notes_dir.mkdir(parents=True)
    
    note_file = notes_dir / "test.md"
    note_file.write_text("# Test Note")
    
    asset_dir = temp_workspace / "notes" / "assets" / "test"
    asset_dir.mkdir(parents=True)
    (asset_dir / "image.png").write_text("fake image")
    
    # Remove note without removing assets
    result = remover.remove_note(note_file, remove_assets=False)
    
    assert result == 0
    assert not note_file.exists()
    assert asset_dir.exists()
    assert (asset_dir / "image.png").exists()


def test_remove_note_nonexistent(temp_workspace, config, remover):
    """Test removing a nonexistent note file."""
    note_file = temp_workspace / "notes" / "nonexistent.md"
    
    result = remover.remove_note(note_file, remove_assets=True)
    
    assert result == 1


def test_remove_note_nested_structure(temp_workspace, config, remover):
    """Test removing a note in a nested directory structure."""
    # Create nested structure
    notes_dir = temp_workspace / "notes"
    nested_dir = notes_dir / "category" / "subcategory"
    nested_dir.mkdir(parents=True)
    
    note_file = nested_dir / "test.md"
    note_file.write_text("# Test Note")
    
    # Create corresponding nested asset structure
    asset_dir = temp_workspace / "notes" / "assets" / "category.assets" / "subcategory" / "test"
    asset_dir.mkdir(parents=True)
    (asset_dir / "image.png").write_text("fake image")
    
    # Remove note with assets
    result = remover.remove_note(note_file, remove_assets=True)
    
    assert result == 0
    assert not note_file.exists()
    assert not asset_dir.exists()


def test_remove_multiple_notes(temp_workspace, config, remover):
    """Test removing multiple note files."""
    # Create test structure
    notes_dir = temp_workspace / "notes"
    notes_dir.mkdir(parents=True)
    
    note_files = []
    for i in range(3):
        note_file = notes_dir / f"test{i}.md"
        note_file.write_text(f"# Test Note {i}")
        note_files.append(note_file)
    
    # Remove multiple notes
    success, failed = remover.remove_multiple_notes(note_files, remove_assets=False)
    
    assert success == 3
    assert failed == 0
    for note_file in note_files:
        assert not note_file.exists()


def test_cleanup_empty_parent_dirs(temp_workspace, config, remover):
    """Test cleanup of empty parent directories."""
    # Create nested empty directory structure
    assets_dir = temp_workspace / "notes" / "assets"
    nested_dir = assets_dir / "level1" / "level2" / "level3"
    nested_dir.mkdir(parents=True)
    
    # Cleanup from level3
    remover._cleanup_empty_parent_dirs(nested_dir)
    
    # All empty directories should be removed up to assets_dir
    assert assets_dir.exists()
    assert not (assets_dir / "level1").exists()

