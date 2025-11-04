"""
Test suite for mkdocs_note.utils.cli.commands module.

This module tests all CLI command classes: NewCommand, RemoveCommand,
MoveCommand, and CleanCommand.
"""

import unittest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from mkdocs_note.utils.cli.commands import (
	NewCommand,
	RemoveCommand,
	MoveCommand,
	CleanCommand,
)
from mkdocs_note.utils.cli import common


class TestNewCommand(unittest.TestCase):
	"""Test cases for NewCommand class."""

	def setUp(self):
		"""Set up test fixtures - create a temporary directory."""
		self.temp_dir = tempfile.mkdtemp()
		self.root_dir = Path(self.temp_dir) / "docs"
		self.root_dir.mkdir()

		# Mock the get_plugin_config to return our test directory
		common.get_plugin_config = lambda: {"notes_root": str(self.root_dir)}

	def tearDown(self):
		"""Clean up - remove temporary directory."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_create_simple_note(self):
		"""Test creating a simple note file."""
		note_path = self.root_dir / "test.md"
		command = NewCommand()
		command.execute(note_path)

		# Check note file was created
		self.assertTrue(note_path.exists())
		self.assertTrue(note_path.is_file())

		# Check asset directory was created
		asset_dir = common.get_asset_directory(note_path)
		self.assertTrue(asset_dir.exists())
		self.assertTrue(asset_dir.is_dir())

	def test_create_nested_note(self):
		"""Test creating a note in nested directories."""
		note_path = self.root_dir / "python" / "intro.md"
		command = NewCommand()
		command.execute(note_path)

		# Check note file was created
		self.assertTrue(note_path.exists())
		# Check asset directory was created
		asset_dir = common.get_asset_directory(note_path)
		self.assertTrue(asset_dir.exists())

	def test_note_content_has_frontmatter(self):
		"""Test that created note has proper frontmatter."""
		note_path = self.root_dir / "test-note.md"
		command = NewCommand()
		command.execute(note_path)

		content = note_path.read_text(encoding="utf-8")

		# Check for frontmatter markers
		self.assertTrue(content.startswith("---"))
		self.assertIn("date:", content)
		self.assertIn("title:", content)
		self.assertIn("permalink:", content)
		self.assertIn("publish:", content)

	def test_note_title_generation(self):
		"""Test that note title is generated from filename."""
		note_path = self.root_dir / "my-test-note.md"
		command = NewCommand()
		command.execute(note_path)

		content = note_path.read_text(encoding="utf-8")
		# Title should be "My Test Note" (converted from filename)
		self.assertIn("title: My Test Note", content)

	def test_note_date_format(self):
		"""Test that note has proper date format."""
		note_path = self.root_dir / "test.md"
		command = NewCommand()
		command.execute(note_path)

		content = note_path.read_text(encoding="utf-8")

		# Extract date line
		for line in content.split("\n"):
			if line.startswith("date:"):
				date_str = line.split("date:", 1)[1].strip()
				# Verify date can be parsed
				try:
					datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
					parsed = True
				except ValueError:
					parsed = False
				self.assertTrue(parsed, f"Date format invalid: {date_str}")
				break

	def test_create_note_existing_file(self):
		"""Test that creating an existing note doesn't overwrite."""
		note_path = self.root_dir / "existing.md"
		note_path.write_text("# Existing content")

		command = NewCommand()
		command.execute(note_path)

		# Original content should remain
		content = note_path.read_text()
		self.assertEqual(content, "# Existing content")


class TestRemoveCommand(unittest.TestCase):
	"""Test cases for RemoveCommand class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.temp_dir = tempfile.mkdtemp()
		self.root_dir = Path(self.temp_dir) / "docs"
		self.root_dir.mkdir()

		# Mock the get_plugin_config
		common.get_plugin_config = lambda: {"notes_root": str(self.root_dir)}

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_remove_single_note(self):
		"""Test removing a single note file."""
		# Create a note with asset directory
		note_path = self.root_dir / "test.md"
		note_path.write_text("# Test note")
		asset_dir = common.get_asset_directory(note_path)
		asset_dir.mkdir(parents=True)
		(asset_dir / "image.png").write_text("fake image")

		# Remove the note
		command = RemoveCommand()
		command.execute(note_path, remove_assets=True)

		# Check note and assets are removed
		self.assertFalse(note_path.exists())
		self.assertFalse(asset_dir.exists())

	def test_remove_note_keep_assets(self):
		"""Test removing a note but keeping its assets."""
		note_path = self.root_dir / "test.md"
		note_path.write_text("# Test note")
		asset_dir = common.get_asset_directory(note_path)
		asset_dir.mkdir(parents=True)

		command = RemoveCommand()
		command.execute(note_path, remove_assets=False)

		# Note should be removed, assets should remain
		self.assertFalse(note_path.exists())
		self.assertTrue(asset_dir.exists())

	def test_remove_note_without_assets(self):
		"""Test removing a note that has no asset directory."""
		note_path = self.root_dir / "test.md"
		note_path.write_text("# Test note")

		command = RemoveCommand()
		command.execute(note_path, remove_assets=True)

		# Should not raise exception
		self.assertFalse(note_path.exists())

	def test_remove_non_existent_note(self):
		"""Test removing a note that doesn't exist."""
		note_path = self.root_dir / "non_existent.md"

		command = RemoveCommand()
		command.execute(note_path, remove_assets=True)

		# Should not raise exception (just log error)
		self.assertFalse(note_path.exists())

	def test_remove_directory_of_notes(self):
		"""Test removing all notes in a directory."""
		# Create multiple notes
		notes_dir = self.root_dir / "notes"
		notes_dir.mkdir()
		(notes_dir / "note1.md").write_text("# Note 1")
		(notes_dir / "note2.md").write_text("# Note 2")
		(notes_dir / "note3.ipynb").write_text('{"cells": []}')

		# Create asset directories
		for note in ["note1", "note2", "note3"]:
			asset_dir = notes_dir / "assets" / note
			asset_dir.mkdir(parents=True)

		command = RemoveCommand()
		command.execute(notes_dir, remove_assets=True)

		# All notes should be removed
		self.assertFalse((notes_dir / "note1.md").exists())
		self.assertFalse((notes_dir / "note2.md").exists())
		self.assertFalse((notes_dir / "note3.ipynb").exists())


class TestMoveCommand(unittest.TestCase):
	"""Test cases for MoveCommand class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.temp_dir = tempfile.mkdtemp()
		self.root_dir = Path(self.temp_dir) / "docs"
		self.root_dir.mkdir()

		# Mock the get_plugin_config
		common.get_plugin_config = lambda: {"notes_root": str(self.root_dir)}

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_move_simple_note(self):
		"""Test moving a simple note file."""
		# Create source note with assets
		source = self.root_dir / "old.md"
		source.write_text("# Old note")
		source_asset = common.get_asset_directory(source)
		source_asset.mkdir(parents=True)
		(source_asset / "image.png").write_text("image")

		# Move to destination
		dest = self.root_dir / "new.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Check source is gone and destination exists
		self.assertFalse(source.exists())
		self.assertTrue(dest.exists())
		self.assertEqual(dest.read_text(), "# Old note")

		# Check assets were moved
		self.assertFalse(source_asset.exists())
		dest_asset = common.get_asset_directory(dest)
		self.assertTrue(dest_asset.exists())
		self.assertTrue((dest_asset / "image.png").exists())

	def test_move_to_different_directory(self):
		"""Test moving a note to a different directory."""
		source = self.root_dir / "source" / "note.md"
		source.parent.mkdir()
		source.write_text("# Note")
		source_asset = common.get_asset_directory(source)
		source_asset.mkdir(parents=True)

		dest = self.root_dir / "destination" / "note.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Check move was successful
		self.assertFalse(source.exists())
		self.assertTrue(dest.exists())
		self.assertTrue(common.get_asset_directory(dest).exists())

	def test_move_note_without_assets(self):
		"""Test moving a note that has no assets."""
		source = self.root_dir / "note.md"
		source.write_text("# Note")

		dest = self.root_dir / "moved.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Should not raise exception
		self.assertFalse(source.exists())
		self.assertTrue(dest.exists())

	def test_move_non_existent_note(self):
		"""Test moving a note that doesn't exist."""
		source = self.root_dir / "non_existent.md"
		dest = self.root_dir / "dest.md"

		command = MoveCommand()
		command.execute(source, dest)

		# Should not create destination
		self.assertFalse(dest.exists())

	def test_move_directory_of_notes(self):
		"""Test moving a directory containing notes."""
		# Create source directory with notes
		source_dir = self.root_dir / "source"
		source_dir.mkdir()
		(source_dir / "note1.md").write_text("# Note 1")
		(source_dir / "note2.md").write_text("# Note 2")

		# Create assets
		asset1 = common.get_asset_directory(source_dir / "note1.md")
		asset2 = common.get_asset_directory(source_dir / "note2.md")
		asset1.mkdir(parents=True)
		asset2.mkdir(parents=True)

		# Move directory
		dest_dir = self.root_dir / "destination"
		command = MoveCommand()
		command.execute(source_dir, dest_dir)

		# Check files were moved
		self.assertTrue((dest_dir / "note1.md").exists())
		self.assertTrue((dest_dir / "note2.md").exists())
		self.assertTrue(common.get_asset_directory(dest_dir / "note1.md").exists())
		self.assertTrue(common.get_asset_directory(dest_dir / "note2.md").exists())

	def test_move_cleans_up_empty_directories(self):
		"""Test that moving notes cleans up empty parent directories."""
		# Create deeply nested source
		source = self.root_dir / "level1" / "level2" / "level3" / "note.md"
		source.parent.mkdir(parents=True)
		source.write_text("# Note")
		source_asset = common.get_asset_directory(source)
		source_asset.mkdir(parents=True)

		# Move to root
		dest = self.root_dir / "note.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Check empty directories were cleaned up
		self.assertFalse((self.root_dir / "level1" / "level2" / "level3").exists())


class TestCleanCommand(unittest.TestCase):
	"""Test cases for CleanCommand class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.temp_dir = tempfile.mkdtemp()
		self.root_dir = Path(self.temp_dir) / "docs"
		self.root_dir.mkdir()

		# Mock the get_plugin_config
		common.get_plugin_config = lambda: {"notes_root": str(self.root_dir)}

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_find_orphaned_assets(self):
		"""Test finding orphaned asset directories."""
		# Create a note with assets
		note = self.root_dir / "note.md"
		note.write_text("# Note")
		valid_asset = common.get_asset_directory(note)
		valid_asset.mkdir(parents=True)

		# Create orphaned asset directory
		orphaned = self.root_dir / "assets" / "orphaned"
		orphaned.mkdir(parents=True)

		# Scan for orphaned assets
		command = CleanCommand()
		note_files = command._scan_note_files(self.root_dir)
		orphaned_dirs = command._find_orphaned_assets(note_files)

		# Should find the orphaned directory but not the valid one
		self.assertEqual(len(orphaned_dirs), 1)
		self.assertIn(orphaned, orphaned_dirs)

	def test_clean_orphaned_assets(self):
		"""Test cleaning up orphaned asset directories."""
		# Create orphaned asset
		orphaned = self.root_dir / "assets" / "orphaned"
		orphaned.mkdir(parents=True)
		(orphaned / "file.txt").write_text("orphaned file")

		command = CleanCommand()
		command.execute(dry_run=False)

		# Orphaned directory should be removed
		self.assertFalse(orphaned.exists())

	def test_clean_dry_run(self):
		"""Test dry run mode doesn't actually remove directories."""
		orphaned = self.root_dir / "assets" / "orphaned"
		orphaned.mkdir(parents=True)

		command = CleanCommand()
		command.execute(dry_run=True)

		# Directory should still exist
		self.assertTrue(orphaned.exists())

	def test_no_orphaned_assets(self):
		"""Test when there are no orphaned assets."""
		# Create a valid note with assets
		note = self.root_dir / "note.md"
		note.write_text("# Note")
		asset = common.get_asset_directory(note)
		asset.mkdir(parents=True)

		command = CleanCommand()
		note_files = command._scan_note_files(self.root_dir)
		orphaned_dirs = command._find_orphaned_assets(note_files)

		# Should find no orphaned directories
		self.assertEqual(len(orphaned_dirs), 0)

	def test_scan_note_files(self):
		"""Test scanning for note files."""
		# Create various note files
		(self.root_dir / "note1.md").write_text("# Note 1")
		(self.root_dir / "note2.md").write_text("# Note 2")
		(self.root_dir / "notebook.ipynb").write_text('{"cells": []}')
		(self.root_dir / "readme.txt").write_text("Not a note")

		command = CleanCommand()
		note_files = command._scan_note_files(self.root_dir)

		# Should find only .md and .ipynb files
		self.assertEqual(len(note_files), 3)
		self.assertIn(self.root_dir / "note1.md", note_files)
		self.assertIn(self.root_dir / "note2.md", note_files)
		self.assertIn(self.root_dir / "notebook.ipynb", note_files)

	def test_clean_multiple_orphaned_assets(self):
		"""Test cleaning multiple orphaned asset directories."""
		# Create multiple orphaned assets
		orphaned1 = self.root_dir / "assets" / "orphaned1"
		orphaned2 = self.root_dir / "assets" / "orphaned2"
		orphaned3 = self.root_dir / "subdir" / "assets" / "orphaned3"

		for orphaned in [orphaned1, orphaned2, orphaned3]:
			orphaned.mkdir(parents=True)

		command = CleanCommand()
		note_files = command._scan_note_files(self.root_dir)
		orphaned_dirs = command._find_orphaned_assets(note_files)

		# Should find all orphaned directories
		self.assertEqual(len(orphaned_dirs), 3)


if __name__ == "__main__":
	unittest.main()
