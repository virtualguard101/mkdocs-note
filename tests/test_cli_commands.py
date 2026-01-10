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
		permalink = "test-permalink"
		command = NewCommand()
		command.execute(permalink, note_path)

		# Check note file was created
		self.assertTrue(note_path.exists())
		self.assertTrue(note_path.is_file())

		# Check asset directory was created using permalink
		asset_dir = common.get_asset_directory_by_permalink(note_path, permalink)
		self.assertTrue(asset_dir.exists())
		self.assertTrue(asset_dir.is_dir())

	def test_create_nested_note(self):
		"""Test creating a note in nested directories."""
		note_path = self.root_dir / "python" / "intro.md"
		permalink = "python-intro"
		command = NewCommand()
		command.execute(permalink, note_path)

		# Check note file was created
		self.assertTrue(note_path.exists())
		# Check asset directory was created using permalink
		asset_dir = common.get_asset_directory_by_permalink(note_path, permalink)
		self.assertTrue(asset_dir.exists())

	def test_note_content_has_frontmatter(self):
		"""Test that created note has proper frontmatter."""
		note_path = self.root_dir / "test-note.md"
		permalink = "test-permalink"
		command = NewCommand()
		command.execute(permalink, note_path)

		content = note_path.read_text(encoding="utf-8")

		# Check for frontmatter markers
		self.assertTrue(content.startswith("---"))
		self.assertIn("date:", content)
		self.assertIn("title:", content)
		self.assertIn(f"permalink: {permalink}", content)
		self.assertIn("publish:", content)

	def test_note_title_generation(self):
		"""Test that note title is generated from filename."""
		note_path = self.root_dir / "my-test-note.md"
		permalink = "my-test-note"
		command = NewCommand()
		command.execute(permalink, note_path)

		content = note_path.read_text(encoding="utf-8")
		# Title should be "My Test Note" (converted from filename)
		self.assertIn("title: My Test Note", content)
		# Permalink should match the provided value
		self.assertIn(f"permalink: {permalink}", content)

	def test_note_date_format(self):
		"""Test that note has proper date format."""
		note_path = self.root_dir / "test.md"
		permalink = "test"
		command = NewCommand()
		command.execute(permalink, note_path)

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
		permalink = "existing"

		command = NewCommand()
		command.execute(permalink, note_path)

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
		# Create a note with permalink and asset directory
		permalink = "test-permalink"
		note_path = self.root_dir / "test.md"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Test Note
permalink: {permalink}
publish: true
---

# Test note
"""
		note_path.write_text(note_content)
		# Asset directory should be based on permalink
		asset_dir = common.get_asset_directory_by_permalink(note_path, permalink)
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
		permalink = "test-keep-assets"
		note_path = self.root_dir / "test.md"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Test Note
permalink: {permalink}
publish: true
---

# Test note
"""
		note_path.write_text(note_content)
		asset_dir = common.get_asset_directory_by_permalink(note_path, permalink)
		asset_dir.mkdir(parents=True)

		command = RemoveCommand()
		command.execute(note_path, remove_assets=False)

		# Note should be removed, assets should remain
		self.assertFalse(note_path.exists())
		self.assertTrue(asset_dir.exists())

	def test_remove_note_without_assets(self):
		"""Test removing a note that has no asset directory."""
		permalink = "test-no-assets"
		note_path = self.root_dir / "test.md"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Test Note
permalink: {permalink}
publish: true
---

# Test note
"""
		note_path.write_text(note_content)

		command = RemoveCommand()
		command.execute(note_path, remove_assets=True)

		# Should not raise exception
		self.assertFalse(note_path.exists())

	def test_remove_note_without_permalink_fallback(self):
		"""Test removing a note without permalink falls back to filename-based asset directory."""
		note_path = self.root_dir / "test.md"
		# Note without permalink (old format)
		note_content = """---
date: 2025-01-15 10:00:00
title: Test Note
publish: true
---

# Test note
"""
		note_path.write_text(note_content)
		# Create asset directory using filename (backwards compatibility)
		asset_dir = common.get_asset_directory(note_path)
		asset_dir.mkdir(parents=True)
		(asset_dir / "image.png").write_text("fake image")

		command = RemoveCommand()
		command.execute(note_path, remove_assets=True)

		# Note should be removed, and asset directory should be removed (based on filename)
		self.assertFalse(note_path.exists())
		self.assertFalse(asset_dir.exists())

	def test_remove_non_existent_note(self):
		"""Test removing a note that doesn't exist."""
		note_path = self.root_dir / "non_existent.md"

		command = RemoveCommand()
		command.execute(note_path, remove_assets=True)

		# Should not raise exception (just log error)
		self.assertFalse(note_path.exists())

	def test_remove_directory_of_notes(self):
		"""Test removing all notes in a directory."""
		# Create multiple notes with permalinks
		notes_dir = self.root_dir / "notes"
		notes_dir.mkdir()

		# Create notes with frontmatter containing permalinks
		(notes_dir / "note1.md").write_text("""---
date: 2025-01-15 10:00:00
title: Note 1
permalink: note1-permalink
publish: true
---

# Note 1
""")
		(notes_dir / "note2.md").write_text("""---
date: 2025-01-15 10:00:00
title: Note 2
permalink: note2-permalink
publish: true
---

# Note 2
""")
		(notes_dir / "note3.ipynb").write_text('{"cells": []}')

		# Create asset directories based on permalinks
		asset_dir1 = notes_dir / "assets" / "note1-permalink"
		asset_dir2 = notes_dir / "assets" / "note2-permalink"
		asset_dir1.mkdir(parents=True)
		asset_dir2.mkdir(parents=True)

		command = RemoveCommand()
		command.execute(notes_dir, remove_assets=True)

		# All notes should be removed
		self.assertFalse((notes_dir / "note1.md").exists())
		self.assertFalse((notes_dir / "note2.md").exists())
		self.assertFalse((notes_dir / "note3.ipynb").exists())
		# Asset directories should be removed
		self.assertFalse(asset_dir1.exists())
		self.assertFalse(asset_dir2.exists())


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
		"""Test moving a simple note file with permalink."""
		permalink = "my-permalink"
		# Create source note with permalink and assets
		source = self.root_dir / "old.md"
		source_content = f"""---
date: 2025-01-15 10:00:00
title: Old Note
permalink: {permalink}
publish: true
---

# Old note
"""
		source.write_text(source_content)
		source_asset = common.get_asset_directory_by_permalink(source, permalink)
		source_asset.mkdir(parents=True)
		(source_asset / "image.png").write_text("image")

		# Move to destination
		dest = self.root_dir / "new.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Check source is gone and destination exists
		self.assertFalse(source.exists())
		self.assertTrue(dest.exists())
		dest_content = dest.read_text()
		self.assertIn("# Old note", dest_content)
		# Permalink should be preserved after move
		self.assertIn(f"permalink: {permalink}", dest_content)

		# Check assets: Since source and dest are in the same directory,
		# assets directory should stay in place (based on permalink, not filename)
		dest_asset = common.get_asset_directory_by_permalink(dest, permalink)
		# Assets directory should still exist at the same location (same parent dir)
		self.assertTrue(dest_asset.exists())
		self.assertTrue((dest_asset / "image.png").exists())
		# Source and dest asset dirs are the same when in same directory
		self.assertEqual(source_asset, dest_asset)

	def test_move_to_different_directory(self):
		"""Test moving a note to a different directory with permalink."""
		permalink = "my-note"
		source = self.root_dir / "source" / "note.md"
		source.parent.mkdir()
		source_content = f"""---
date: 2025-01-15 10:00:00
title: Note
permalink: {permalink}
publish: true
---

# Note
"""
		source.write_text(source_content)
		source_asset = common.get_asset_directory_by_permalink(source, permalink)
		source_asset.mkdir(parents=True)
		(source_asset / "image.png").write_text("image")

		dest = self.root_dir / "destination" / "note.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Check move was successful
		self.assertFalse(source.exists())
		self.assertTrue(dest.exists())
		# Assets should be moved based on permalink to destination directory
		dest_asset = common.get_asset_directory_by_permalink(dest, permalink)
		self.assertTrue(dest_asset.exists())
		self.assertTrue((dest_asset / "image.png").exists())
		# Source asset directory should be gone (moved to dest)
		self.assertFalse(source_asset.exists())

	def test_move_to_existing_directory(self):
		"""Test moving a note to an existing directory (destination is a directory)."""
		permalink = "test-permalink"
		# Create source file with permalink
		source = self.root_dir / "test.md"
		source_content = f"""---
date: 2025-01-15 10:00:00
title: Test
permalink: {permalink}
publish: true
---

# Test
"""
		source.write_text(source_content)
		source_asset = common.get_asset_directory_by_permalink(source, permalink)
		source_asset.mkdir(parents=True)
		(source_asset / "image.png").write_text("test image")

		# Create destination directory (not a file path)
		dest_dir = self.root_dir / "dest_dir"
		dest_dir.mkdir()

		command = MoveCommand()
		command.execute(source, dest_dir)

		# Check file was moved (to dest_dir/test.md)
		final_dest = dest_dir / source.name
		self.assertFalse(source.exists())
		self.assertTrue(final_dest.exists())

		# Check assets were moved based on permalink
		dest_asset = common.get_asset_directory_by_permalink(final_dest, permalink)
		self.assertTrue(
			dest_asset.exists(), f"Asset directory should exist at {dest_asset}"
		)
		self.assertTrue((dest_asset / "image.png").exists())
		# Source asset directory should be gone
		self.assertFalse(
			source_asset.exists(),
			f"Source asset directory should be removed: {source_asset}",
		)

	def test_move_note_without_assets(self):
		"""Test moving a note that has no assets."""
		permalink = "my-note"
		source = self.root_dir / "note.md"
		source_content = f"""---
date: 2025-01-15 10:00:00
title: Note
permalink: {permalink}
publish: true
---

# Note
"""
		source.write_text(source_content)

		dest = self.root_dir / "moved.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Should not raise exception
		self.assertFalse(source.exists())
		self.assertTrue(dest.exists())

	def test_move_note_without_permalink_fallback(self):
		"""Test moving a note without permalink falls back to filename-based asset directory."""
		# Create source note without permalink (old format)
		source = self.root_dir / "old.md"
		source_content = """---
date: 2025-01-15 10:00:00
title: Old Note
publish: true
---

# Old note
"""
		source.write_text(source_content)
		# Create asset directory using filename (backwards compatibility)
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

		# Check assets were moved (based on filename, not permalink)
		self.assertFalse(source_asset.exists())
		dest_asset = common.get_asset_directory(dest)
		self.assertTrue(dest_asset.exists())
		self.assertTrue((dest_asset / "image.png").exists())

	def test_move_non_existent_note(self):
		"""Test moving a note that doesn't exist."""
		source = self.root_dir / "non_existent.md"
		dest = self.root_dir / "dest.md"

		command = MoveCommand()
		command.execute(source, dest)

		# Should not create destination
		self.assertFalse(dest.exists())

	def test_move_directory_of_notes(self):
		"""Test moving a directory containing notes with permalinks."""
		# Create source directory with notes that have permalinks
		source_dir = self.root_dir / "source"
		source_dir.mkdir()
		(source_dir / "note1.md").write_text("""---
date: 2025-01-15 10:00:00
title: Note 1
permalink: note1-permalink
publish: true
---

# Note 1
""")
		(source_dir / "note2.md").write_text("""---
date: 2025-01-15 10:00:00
title: Note 2
permalink: note2-permalink
publish: true
---

# Note 2
""")

		# Create assets based on permalinks
		asset1 = common.get_asset_directory_by_permalink(
			source_dir / "note1.md", "note1-permalink"
		)
		asset2 = common.get_asset_directory_by_permalink(
			source_dir / "note2.md", "note2-permalink"
		)
		asset1.mkdir(parents=True)
		asset2.mkdir(parents=True)

		# Move directory
		dest_dir = self.root_dir / "destination"
		command = MoveCommand()
		command.execute(source_dir, dest_dir)

		# Check files were moved
		self.assertTrue((dest_dir / "note1.md").exists())
		self.assertTrue((dest_dir / "note2.md").exists())
		# Assets should be moved based on permalinks
		dest_asset1 = common.get_asset_directory_by_permalink(
			dest_dir / "note1.md", "note1-permalink"
		)
		dest_asset2 = common.get_asset_directory_by_permalink(
			dest_dir / "note2.md", "note2-permalink"
		)
		self.assertTrue(dest_asset1.exists())
		self.assertTrue(dest_asset2.exists())

	def test_move_cleans_up_empty_directories(self):
		"""Test that moving notes cleans up empty parent directories."""
		permalink = "my-note"
		# Create deeply nested source with permalink
		source = self.root_dir / "level1" / "level2" / "level3" / "note.md"
		source.parent.mkdir(parents=True)
		source_content = f"""---
date: 2025-01-15 10:00:00
title: Note
permalink: {permalink}
publish: true
---

# Note
"""
		source.write_text(source_content)
		source_asset = common.get_asset_directory_by_permalink(source, permalink)
		source_asset.mkdir(parents=True)

		# Move to root
		dest = self.root_dir / "note.md"
		command = MoveCommand()
		command.execute(source, dest)

		# Check empty directories were cleaned up
		self.assertFalse((self.root_dir / "level1" / "level2" / "level3").exists())
		# Assets should be moved based on permalink
		dest_asset = common.get_asset_directory_by_permalink(dest, permalink)
		self.assertTrue(dest_asset.exists())

	def test_rename_permalink(self):
		"""Test renaming permalink value and asset directory."""
		old_permalink = "old-permalink"
		new_permalink = "new-permalink"

		# Create note with old permalink and assets
		note = self.root_dir / "note.md"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Note
permalink: {old_permalink}
publish: true
---

# Note content
"""
		note.write_text(note_content)

		# Create asset directory based on old permalink
		old_asset_dir = common.get_asset_directory_by_permalink(note, old_permalink)
		old_asset_dir.mkdir(parents=True)
		(old_asset_dir / "image.png").write_text("image data")

		# Rename permalink
		command = MoveCommand()
		command.execute(note, destination=None, permalink=new_permalink)

		# Check permalink was updated in file
		self.assertTrue(note.exists())  # File should not move
		updated_content = note.read_text()
		self.assertIn(f"permalink: {new_permalink}", updated_content)
		self.assertNotIn(f"permalink: {old_permalink}", updated_content)

		# Check asset directory was renamed
		new_asset_dir = common.get_asset_directory_by_permalink(note, new_permalink)
		self.assertTrue(new_asset_dir.exists())
		self.assertTrue((new_asset_dir / "image.png").exists())
		# Old asset directory should be gone
		self.assertFalse(old_asset_dir.exists())

	def test_rename_permalink_without_existing(self):
		"""Test adding permalink to a note without existing permalink."""
		new_permalink = "new-permalink"

		# Create note without permalink
		note = self.root_dir / "note.md"
		note_content = """---
date: 2025-01-15 10:00:00
title: Note
publish: true
---

# Note content
"""
		note.write_text(note_content)

		# Create asset directory based on filename (fallback)
		old_asset_dir = common.get_asset_directory(note)
		old_asset_dir.mkdir(parents=True)
		(old_asset_dir / "image.png").write_text("image data")

		# Rename permalink (adding new permalink)
		command = MoveCommand()
		command.execute(note, destination=None, permalink=new_permalink)

		# Check permalink was added to file
		updated_content = note.read_text()
		self.assertIn(f"permalink: {new_permalink}", updated_content)

		# Check new asset directory was created
		new_asset_dir = common.get_asset_directory_by_permalink(note, new_permalink)
		self.assertTrue(new_asset_dir.exists())
		# Assets should be moved from filename-based to permalink-based
		self.assertTrue((new_asset_dir / "image.png").exists())
		# Old asset directory should be gone
		self.assertFalse(old_asset_dir.exists())

	def test_rename_permalink_same_name_no_move(self):
		"""Test that renaming permalink to the same name doesn't cause issues."""
		permalink = "my-permalink"

		# Create note with permalink
		note = self.root_dir / "note.md"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Note
permalink: {permalink}
publish: true
---

# Note content
"""
		note.write_text(note_content)

		# Create asset directory
		asset_dir = common.get_asset_directory_by_permalink(note, permalink)
		asset_dir.mkdir(parents=True)
		(asset_dir / "image.png").write_text("image data")

		# Rename permalink to the same value
		command = MoveCommand()
		command.execute(note, destination=None, permalink=permalink)

		# Check file still exists and permalink is still there
		self.assertTrue(note.exists())
		content = note.read_text()
		self.assertIn(f"permalink: {permalink}", content)

		# Check asset directory still exists
		self.assertTrue(asset_dir.exists())
		self.assertTrue((asset_dir / "image.png").exists())

	def test_rename_permalink_file_stays_in_place(self):
		"""Test that renaming permalink doesn't move the file, only updates permalink and assets."""
		old_permalink = "old"
		new_permalink = "new"

		# Create note in a specific location
		note = self.root_dir / "subdir" / "note.md"
		note.parent.mkdir(parents=True)
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Note
permalink: {old_permalink}
publish: true
---

# Note content
"""
		note.write_text(note_content)

		original_path = note.resolve()

		# Rename permalink
		command = MoveCommand()
		command.execute(note, destination=None, permalink=new_permalink)

		# File should stay in the same location
		self.assertEqual(note.resolve(), original_path)
		self.assertTrue(note.exists())

		# Permalink should be updated
		content = note.read_text()
		self.assertIn(f"permalink: {new_permalink}", content)

		# Asset directory should be renamed in the same location
		new_asset_dir = common.get_asset_directory_by_permalink(note, new_permalink)
		self.assertEqual(new_asset_dir.parent, note.parent / "assets")


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
