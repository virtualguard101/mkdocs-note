"""
Integration tests for mkdocs-note CLI.

This module tests the complete CLI workflow including command parsing
and execution through the Click interface.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from mkdocs_note.cli import cli


class TestCLIIntegration(unittest.TestCase):
	"""Integration tests for the complete CLI workflow."""

	def setUp(self):
		"""Set up test fixtures."""
		self.runner = CliRunner()
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_cli_help(self):
		"""Test that CLI help command works."""
		result = self.runner.invoke(cli, ["--help"])
		self.assertEqual(result.exit_code, 0)
		self.assertIn("MkDocs Note CLI", result.output)
		self.assertIn("Commands:", result.output)

	def test_cli_version(self):
		"""Test that CLI version command works."""
		result = self.runner.invoke(cli, ["--version"])
		self.assertEqual(result.exit_code, 0)
		# Version output format is "cli, version X.Y.Z"
		self.assertIn("version", result.output.lower())

	def test_new_command_help(self):
		"""Test new command help."""
		result = self.runner.invoke(cli, ["new", "--help"])
		self.assertEqual(result.exit_code, 0)
		self.assertIn("Create a new note file", result.output)

	def test_remove_command_help(self):
		"""Test remove command help."""
		result = self.runner.invoke(cli, ["remove", "--help"])
		self.assertEqual(result.exit_code, 0)
		self.assertIn("Remove a note file", result.output)

	def test_move_command_help(self):
		"""Test move command help."""
		result = self.runner.invoke(cli, ["move", "--help"])
		self.assertEqual(result.exit_code, 0)
		self.assertIn("Move or rename a note", result.output)

	def test_clean_command_help(self):
		"""Test clean command help."""
		result = self.runner.invoke(cli, ["clean", "--help"])
		self.assertEqual(result.exit_code, 0)
		self.assertIn("Clean up orphaned asset", result.output)


class TestNewCommandIntegration(unittest.TestCase):
	"""Integration tests for 'new' command."""

	def setUp(self):
		"""Set up test fixtures."""
		self.runner = CliRunner()
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_new_creates_note_and_assets(self):
		"""Test that 'new' command creates note and asset directory."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			# Create mkdocs.yml to define root
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()

			result = self.runner.invoke(cli, ["new", "docs/test.md"])

			# Command should succeed
			self.assertEqual(result.exit_code, 0, f"Output: {result.output}")
			self.assertIn("Successfully created note", result.output)

			# Check files were created
			self.assertTrue(Path("docs/test.md").exists())
			self.assertTrue(Path("docs/assets/test").exists())

	def test_new_with_nested_path(self):
		"""Test creating a note in nested directories."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()

			result = self.runner.invoke(cli, ["new", "docs/python/intro.md"])

			self.assertEqual(result.exit_code, 0)
			self.assertTrue(Path("docs/python/intro.md").exists())
			self.assertTrue(Path("docs/python/assets/intro").exists())

	def test_new_existing_file_fails(self):
		"""Test that creating an existing note fails gracefully."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/existing.md").write_text("# Existing")

			result = self.runner.invoke(cli, ["new", "docs/existing.md"])

			# Should fail with error message
			self.assertNotEqual(result.exit_code, 0)
			self.assertIn("already exists", result.output)


class TestRemoveCommandIntegration(unittest.TestCase):
	"""Integration tests for 'remove' command."""

	def setUp(self):
		"""Set up test fixtures."""
		self.runner = CliRunner()
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_remove_with_confirmation(self):
		"""Test removing a note with user confirmation."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/test.md").write_text("# Test")
			Path("docs/assets/test").mkdir(parents=True)

			# Confirm removal
			result = self.runner.invoke(cli, ["remove", "docs/test.md"], input="y\n")

			self.assertEqual(result.exit_code, 0)
			self.assertIn("Successfully removed", result.output)
			self.assertFalse(Path("docs/test.md").exists())
			self.assertFalse(Path("docs/assets/test").exists())

	def test_remove_with_yes_flag(self):
		"""Test removing a note with --yes flag."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/test.md").write_text("# Test")
			Path("docs/assets/test").mkdir(parents=True)

			result = self.runner.invoke(cli, ["remove", "docs/test.md", "--yes"])

			self.assertEqual(result.exit_code, 0)
			self.assertFalse(Path("docs/test.md").exists())

	def test_remove_cancelled(self):
		"""Test that cancelling remove keeps the file."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/test.md").write_text("# Test")

			# Cancel removal
			result = self.runner.invoke(cli, ["remove", "docs/test.md"], input="n\n")

			self.assertEqual(result.exit_code, 0)
			self.assertIn("Cancelled", result.output)
			self.assertTrue(Path("docs/test.md").exists())

	def test_remove_keep_assets(self):
		"""Test removing note while keeping assets."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/test.md").write_text("# Test")
			Path("docs/assets/test").mkdir(parents=True)

			result = self.runner.invoke(
				cli, ["remove", "docs/test.md", "--keep-assets", "--yes"]
			)

			self.assertEqual(result.exit_code, 0)
			self.assertFalse(Path("docs/test.md").exists())
			self.assertTrue(Path("docs/assets/test").exists())

	def test_rm_alias(self):
		"""Test that 'rm' alias works."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/test.md").write_text("# Test")

			result = self.runner.invoke(cli, ["rm", "docs/test.md", "--yes"])

			self.assertEqual(result.exit_code, 0)
			self.assertFalse(Path("docs/test.md").exists())


class TestMoveCommandIntegration(unittest.TestCase):
	"""Integration tests for 'move' command."""

	def setUp(self):
		"""Set up test fixtures."""
		self.runner = CliRunner()
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_move_with_confirmation(self):
		"""Test moving a note with user confirmation."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/old.md").write_text("# Old")
			Path("docs/assets/old").mkdir(parents=True)

			result = self.runner.invoke(
				cli, ["move", "docs/old.md", "docs/new.md"], input="y\n"
			)

			self.assertEqual(result.exit_code, 0)
			self.assertIn("Successfully moved", result.output)
			self.assertFalse(Path("docs/old.md").exists())
			self.assertTrue(Path("docs/new.md").exists())
			self.assertTrue(Path("docs/assets/new").exists())

	def test_move_with_yes_flag(self):
		"""Test moving with --yes flag."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/old.md").write_text("# Old")

			result = self.runner.invoke(
				cli, ["move", "docs/old.md", "docs/new.md", "--yes"]
			)

			self.assertEqual(result.exit_code, 0)
			self.assertTrue(Path("docs/new.md").exists())

	def test_move_to_different_directory(self):
		"""Test moving note to different directory."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/note.md").write_text("# Note")
			Path("docs/assets/note").mkdir(parents=True)

			result = self.runner.invoke(
				cli, ["move", "docs/note.md", "docs/archive/note.md", "--yes"]
			)

			self.assertEqual(result.exit_code, 0)
			self.assertTrue(Path("docs/archive/note.md").exists())
			self.assertTrue(Path("docs/archive/assets/note").exists())

	def test_mv_alias(self):
		"""Test that 'mv' alias works."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/old.md").write_text("# Old")

			result = self.runner.invoke(
				cli, ["mv", "docs/old.md", "docs/new.md", "--yes"]
			)

			self.assertEqual(result.exit_code, 0)
			self.assertTrue(Path("docs/new.md").exists())


class TestCleanCommandIntegration(unittest.TestCase):
	"""Integration tests for 'clean' command."""

	def setUp(self):
		"""Set up test fixtures."""
		self.runner = CliRunner()
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_clean_with_orphaned_assets(self):
		"""Test cleaning up orphaned asset directories."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			# Create orphaned asset
			Path("docs/assets/orphaned").mkdir(parents=True)

			result = self.runner.invoke(cli, ["clean"], input="y\n")

			self.assertEqual(result.exit_code, 0)
			self.assertIn("Successfully removed", result.output)
			self.assertFalse(Path("docs/assets/orphaned").exists())

	def test_clean_with_yes_flag(self):
		"""Test clean with --yes flag."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/assets/orphaned").mkdir(parents=True)

			result = self.runner.invoke(cli, ["clean", "--yes"])

			self.assertEqual(result.exit_code, 0)
			self.assertFalse(Path("docs/assets/orphaned").exists())

	def test_clean_dry_run(self):
		"""Test clean with --dry-run flag."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			Path("docs/assets/orphaned").mkdir(parents=True)

			result = self.runner.invoke(cli, ["clean", "--dry-run"])

			self.assertEqual(result.exit_code, 0)
			self.assertIn("dry run", result.output.lower())
			# Directory should still exist
			self.assertTrue(Path("docs/assets/orphaned").exists())

	def test_clean_no_orphaned_assets(self):
		"""Test clean when there are no orphaned assets."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()
			# Create valid note with assets
			Path("docs/note.md").write_text("# Note")
			Path("docs/assets/note").mkdir(parents=True)

			result = self.runner.invoke(cli, ["clean", "--yes"])

			self.assertEqual(result.exit_code, 0)
			self.assertIn("No orphaned", result.output)


class TestCLIWorkflow(unittest.TestCase):
	"""Test complete CLI workflow scenarios."""

	def setUp(self):
		"""Set up test fixtures."""
		self.runner = CliRunner()
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up."""
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_create_move_remove_workflow(self):
		"""Test a complete workflow: create -> move -> remove."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()

			# 1. Create a note
			result = self.runner.invoke(cli, ["new", "docs/draft.md"])
			self.assertEqual(result.exit_code, 0)
			self.assertTrue(Path("docs/draft.md").exists())

			# 2. Move it
			result = self.runner.invoke(
				cli, ["move", "docs/draft.md", "docs/published.md", "--yes"]
			)
			self.assertEqual(result.exit_code, 0)
			self.assertTrue(Path("docs/published.md").exists())
			self.assertFalse(Path("docs/draft.md").exists())

			# 3. Remove it
			result = self.runner.invoke(cli, ["remove", "docs/published.md", "--yes"])
			self.assertEqual(result.exit_code, 0)
			self.assertFalse(Path("docs/published.md").exists())

	def test_create_and_clean_orphaned_workflow(self):
		"""Test creating a note, manually removing it, then cleaning orphans."""
		with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
			Path("mkdocs.yml").write_text("site_name: Test\n")
			Path("docs").mkdir()

			# Create a note
			result = self.runner.invoke(cli, ["new", "docs/test.md"])
			self.assertEqual(result.exit_code, 0)

			# Manually remove just the note file (not through CLI)
			Path("docs/test.md").unlink()

			# Clean orphaned assets
			result = self.runner.invoke(cli, ["clean", "--yes"])
			self.assertEqual(result.exit_code, 0)
			self.assertFalse(Path("docs/assets/test").exists())


if __name__ == "__main__":
	unittest.main()
