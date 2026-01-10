"""
Test suite for mkdocs_note.utils.cli.common module.

This module tests the common utility functions used by CLI commands.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from mkdocs_note.utils.cli.common import (
	get_asset_directory,
	get_asset_directory_by_permalink,
	get_permalink_from_file,
	is_excluded_name,
	ensure_parent_directory,
	cleanup_empty_directories,
)


class TestGetAssetDirectory(unittest.TestCase):
	"""Test cases for get_asset_directory function."""

	def test_simple_note_path(self):
		"""Test asset directory for a simple note path."""
		note_path = Path("docs/notes/test.md")
		asset_dir = get_asset_directory(note_path)
		self.assertEqual(asset_dir, Path("docs/notes/assets/test"))

	def test_nested_note_path(self):
		"""Test asset directory for a nested note path."""
		note_path = Path("docs/notes/python/intro.md")
		asset_dir = get_asset_directory(note_path)
		self.assertEqual(asset_dir, Path("docs/notes/python/assets/intro"))

	def test_root_note_path(self):
		"""Test asset directory for a note in root."""
		note_path = Path("notes.md")
		asset_dir = get_asset_directory(note_path)
		self.assertEqual(asset_dir, Path("assets/notes"))

	def test_note_with_special_chars(self):
		"""Test asset directory for note with special characters."""
		note_path = Path("docs/my-note_2024.md")
		asset_dir = get_asset_directory(note_path)
		self.assertEqual(asset_dir, Path("docs/assets/my-note_2024"))

	def test_jupyter_notebook(self):
		"""Test asset directory for Jupyter notebook."""
		note_path = Path("docs/analysis/results.ipynb")
		asset_dir = get_asset_directory(note_path)
		self.assertEqual(asset_dir, Path("docs/analysis/assets/results"))


class TestGetAssetDirectoryByPermalink(unittest.TestCase):
	"""Test cases for get_asset_directory_by_permalink function."""

	def test_simple_note_with_permalink(self):
		"""Test asset directory for a simple note with permalink."""
		note_path = Path("docs/notes/test.md")
		permalink = "my-permalink"
		asset_dir = get_asset_directory_by_permalink(note_path, permalink)
		self.assertEqual(asset_dir, Path("docs/notes/assets/my-permalink"))

	def test_nested_note_with_permalink(self):
		"""Test asset directory for a nested note with permalink."""
		note_path = Path("docs/notes/python/intro.md")
		permalink = "python-intro"
		asset_dir = get_asset_directory_by_permalink(note_path, permalink)
		self.assertEqual(asset_dir, Path("docs/notes/python/assets/python-intro"))

	def test_permalink_with_special_chars(self):
		"""Test asset directory with permalink containing special characters."""
		note_path = Path("docs/notes/my-note.md")
		permalink = "my-note-2024"
		asset_dir = get_asset_directory_by_permalink(note_path, permalink)
		self.assertEqual(asset_dir, Path("docs/notes/assets/my-note-2024"))


class TestGetPermalinkFromFile(unittest.TestCase):
	"""Test cases for get_permalink_from_file function."""

	def setUp(self):
		"""Set up test fixtures - create a temporary directory."""
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up - remove temporary directory."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_extract_permalink_from_file(self):
		"""Test extracting permalink from a note file."""
		note_path = Path(self.temp_dir) / "test.md"
		permalink = "my-permalink"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Test Note
permalink: {permalink}
publish: true
---

# Test note content
"""
		note_path.write_text(note_content, encoding="utf-8")

		result = get_permalink_from_file(note_path)
		self.assertEqual(result, permalink)

	def test_extract_permalink_with_whitespace(self):
		"""Test extracting permalink with surrounding whitespace."""
		note_path = Path(self.temp_dir) / "test.md"
		permalink = "my-permalink"
		note_content = f"""---
date: 2025-01-15 10:00:00
title: Test Note
permalink:   {permalink}   
publish: true
---

# Test note content
"""
		note_path.write_text(note_content, encoding="utf-8")

		result = get_permalink_from_file(note_path)
		self.assertEqual(result, permalink)

	def test_no_permalink_in_file(self):
		"""Test when permalink is not present in frontmatter."""
		note_path = Path(self.temp_dir) / "test.md"
		note_content = """---
date: 2025-01-15 10:00:00
title: Test Note
publish: true
---

# Test note content
"""
		note_path.write_text(note_content, encoding="utf-8")

		result = get_permalink_from_file(note_path)
		self.assertIsNone(result)

	def test_empty_permalink_in_file(self):
		"""Test when permalink is empty in frontmatter."""
		note_path = Path(self.temp_dir) / "test.md"
		note_content = """---
date: 2025-01-15 10:00:00
title: Test Note
permalink: 
publish: true
---

# Test note content
"""
		note_path.write_text(note_content, encoding="utf-8")

		result = get_permalink_from_file(note_path)
		self.assertIsNone(result)

	def test_non_existent_file(self):
		"""Test with non-existent file."""
		note_path = Path(self.temp_dir) / "non_existent.md"

		result = get_permalink_from_file(note_path)
		self.assertIsNone(result)

	def test_invalid_frontmatter(self):
		"""Test with file that has invalid frontmatter."""
		note_path = Path(self.temp_dir) / "test.md"
		note_content = "# Just markdown, no frontmatter"
		note_path.write_text(note_content, encoding="utf-8")

		result = get_permalink_from_file(note_path)
		self.assertIsNone(result)


class TestIsExcludedName(unittest.TestCase):
	"""Test cases for is_excluded_name function."""

	def test_excluded_index(self):
		"""Test that index.md is excluded."""
		exclude_patterns = ["index.md", "README.md"]
		self.assertTrue(is_excluded_name("index.md", exclude_patterns))

	def test_excluded_readme(self):
		"""Test that README.md is excluded."""
		exclude_patterns = ["index.md", "README.md"]
		self.assertTrue(is_excluded_name("README.md", exclude_patterns))

	def test_not_excluded(self):
		"""Test that regular note is not excluded."""
		exclude_patterns = ["index.md", "README.md"]
		self.assertFalse(is_excluded_name("test.md", exclude_patterns))

	def test_empty_exclude_list(self):
		"""Test with empty exclude list."""
		exclude_patterns = []
		self.assertFalse(is_excluded_name("index.md", exclude_patterns))

	def test_case_sensitive(self):
		"""Test that exclusion is case-sensitive."""
		exclude_patterns = ["index.md"]
		self.assertFalse(is_excluded_name("INDEX.md", exclude_patterns))


class TestEnsureParentDirectory(unittest.TestCase):
	"""Test cases for ensure_parent_directory function."""

	def setUp(self):
		"""Set up test fixtures - create a temporary directory."""
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up - remove temporary directory."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_create_single_level_directory(self):
		"""Test creating a single level parent directory."""
		test_file = Path(self.temp_dir) / "test" / "file.md"
		ensure_parent_directory(test_file)
		self.assertTrue(test_file.parent.exists())
		self.assertTrue(test_file.parent.is_dir())

	def test_create_nested_directories(self):
		"""Test creating nested parent directories."""
		test_file = Path(self.temp_dir) / "level1" / "level2" / "level3" / "file.md"
		ensure_parent_directory(test_file)
		self.assertTrue(test_file.parent.exists())
		self.assertTrue(test_file.parent.is_dir())

	def test_existing_directory(self):
		"""Test that existing directories are not affected."""
		existing_dir = Path(self.temp_dir) / "existing"
		existing_dir.mkdir()
		test_file = existing_dir / "file.md"

		# Should not raise exception
		ensure_parent_directory(test_file)
		self.assertTrue(test_file.parent.exists())


class TestCleanupEmptyDirectories(unittest.TestCase):
	"""Test cases for cleanup_empty_directories function."""

	def setUp(self):
		"""Set up test fixtures - create a temporary directory structure."""
		self.temp_dir = tempfile.mkdtemp()
		self.root_dir = Path(self.temp_dir) / "docs"
		self.root_dir.mkdir()

	def tearDown(self):
		"""Clean up - remove temporary directory."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_cleanup_single_empty_directory(self):
		"""Test cleaning up a single empty directory."""
		empty_dir = self.root_dir / "empty"
		empty_dir.mkdir()

		cleanup_empty_directories(empty_dir, self.root_dir)
		self.assertFalse(empty_dir.exists())

	def test_cleanup_nested_empty_directories(self):
		"""Test cleaning up nested empty directories."""
		nested_dir = self.root_dir / "level1" / "level2" / "level3"
		nested_dir.mkdir(parents=True)

		cleanup_empty_directories(nested_dir, self.root_dir)

		# All empty directories should be removed
		self.assertFalse(nested_dir.exists())
		self.assertFalse((self.root_dir / "level1" / "level2").exists())
		self.assertFalse((self.root_dir / "level1").exists())
		# Root should still exist
		self.assertTrue(self.root_dir.exists())

	def test_cleanup_stops_at_non_empty_directory(self):
		"""Test that cleanup stops when encountering non-empty directory."""
		level1 = self.root_dir / "level1"
		level2 = level1 / "level2"
		level3 = level2 / "level3"
		level3.mkdir(parents=True)

		# Create a file in level1
		(level1 / "file.txt").write_text("content")

		cleanup_empty_directories(level3, self.root_dir)

		# level3 and level2 should be removed
		self.assertFalse(level3.exists())
		self.assertFalse(level2.exists())
		# level1 should still exist (has file)
		self.assertTrue(level1.exists())
		self.assertTrue((level1 / "file.txt").exists())

	def test_cleanup_stops_at_root(self):
		"""Test that cleanup never removes the root directory."""
		empty_dir = self.root_dir / "empty"
		empty_dir.mkdir()

		cleanup_empty_directories(empty_dir, self.root_dir)

		# Empty dir should be removed, but root should remain
		self.assertFalse(empty_dir.exists())
		self.assertTrue(self.root_dir.exists())

	def test_cleanup_with_non_existent_directory(self):
		"""Test cleanup with a directory that doesn't exist."""
		non_existent = self.root_dir / "non_existent"

		# Should not raise exception
		cleanup_empty_directories(non_existent, self.root_dir)

	def test_cleanup_outside_root(self):
		"""Test that cleanup doesn't affect directories outside root."""
		outside_dir = Path(self.temp_dir) / "outside"
		outside_dir.mkdir()

		# Should not remove directory outside root
		cleanup_empty_directories(outside_dir, self.root_dir)
		self.assertTrue(outside_dir.exists())


if __name__ == "__main__":
	unittest.main()
