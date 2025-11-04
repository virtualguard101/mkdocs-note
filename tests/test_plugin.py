import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src to path to allow imports
sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.plugin import MkdocsNotePlugin
from mkdocs_note.config import MkdocsNoteConfig


class TestMkdocsNotePlugin(unittest.TestCase):
	"""Test cases for MkdocsNotePlugin class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.plugin = MkdocsNotePlugin()
		self.plugin.config = MkdocsNoteConfig()

	def test_initialization(self):
		"""Test plugin initialization."""
		self.assertIsInstance(self.plugin, MkdocsNotePlugin)
		self.assertIsInstance(self.plugin.notes_list, list)
		self.assertEqual(len(self.plugin.notes_list), 0)

	def test_plugin_has_config(self):
		"""Test that plugin has config attribute."""
		self.assertIsNotNone(self.plugin.config)
		self.assertIsInstance(self.plugin.config, MkdocsNoteConfig)

	def test_config_default_values(self):
		"""Test plugin config default values."""
		config = MkdocsNoteConfig()
		self.assertTrue(config.enabled)
		self.assertEqual(config.notes_root, "docs")
		self.assertIsNotNone(config.recent_notes_config)
		self.assertIsNotNone(config.graph_config)

	def test_is_note_index_page(self):
		"""Test is_note_index_page method."""
		# Create a mock file
		mock_file = Mock()
		# src_uri is relative to docs_dir, so 'index.md' not 'docs/index.md'
		mock_file.src_uri = "index.md"

		# Test with default notes_root
		result = self.plugin.is_note_index_page(mock_file)
		self.assertTrue(result)

		# Test with non-index file
		mock_file.src_uri = "some-other-page.md"
		result = self.plugin.is_note_index_page(mock_file)
		self.assertFalse(result)

	def test_on_files(self):
		"""Test on_files event handler."""
		# Create mock objects
		mock_files = Mock()
		mock_files.remove = Mock()
		mock_config = Mock()

		# Mock scanner.scan_notes to return empty lists
		with patch("mkdocs_note.plugin.scanner.scan_notes") as mock_scan:
			mock_scan.return_value = ([], [])

			result = self.plugin.on_files(mock_files, mock_config)

			# Verify scan_notes was called
			mock_scan.assert_called_once_with(mock_files, self.plugin.config)

			# Verify files was returned
			self.assertEqual(result, mock_files)

	def test_on_config(self):
		"""Test on_config event handler."""
		mock_config = Mock()

		# Mock add_static_resouces
		with patch("mkdocs_note.plugin.add_static_resouces") as mock_add:
			result = self.plugin.on_config(mock_config)

			# Verify add_static_resouces was called
			mock_add.assert_called_once_with(mock_config)

			# Verify static_dir was set
			self.assertIsNotNone(self.plugin.static_dir)

			# Verify config was returned
			self.assertEqual(result, mock_config)

	def test_on_pre_build_graph_disabled(self):
		"""Test on_pre_build when graph is disabled."""
		self.plugin.config.graph_config["enabled"] = False
		mock_config = Mock()

		# Should not raise any errors
		self.plugin.on_pre_build(config=mock_config)

	def test_on_pre_build_graph_enabled(self):
		"""Test on_pre_build when graph is enabled."""
		self.plugin.config.graph_config["enabled"] = True
		mock_config = Mock()

		# Mock Graph class
		with patch("mkdocs_note.plugin.Graph") as mock_graph:
			self.plugin.on_pre_build(config=mock_config)

			# Verify Graph was instantiated
			mock_graph.assert_called_once()

	def test_on_nav(self):
		"""Test on_nav event handler."""
		mock_nav = Mock()
		mock_config = Mock()
		mock_files = Mock()

		result = self.plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

		# Verify nav was returned
		self.assertEqual(result, mock_nav)

		# Verify _files was set
		self.assertEqual(self.plugin._files, mock_files)

	def test_on_page_markdown_disabled(self):
		"""Test on_page_markdown when recent notes is disabled."""
		self.plugin.config.recent_notes_config["enabled"] = False

		markdown = "# Test Content"
		mock_page = Mock()
		mock_config = Mock()
		mock_files = Mock()

		result = self.plugin.on_page_markdown(
			markdown, mock_page, mock_config, mock_files
		)

		# Markdown should be unchanged
		self.assertEqual(result, markdown)

	def test_insert_recent_note_links(self):
		"""Test insert_recent_note_links function."""
		from mkdocs_note.plugin import insert_recent_note_links
		from datetime import datetime

		# Create mock files
		mock_file1 = Mock()
		# The function uses f.page.url, not f.page.abs_url
		mock_file1.page.url = "/note1/"
		mock_file1.note_title = "Note 1"
		mock_file1.note_date = datetime.now()

		mock_file2 = Mock()
		mock_file2.page.url = "/note2/"
		mock_file2.note_title = "Note 2"
		mock_file2.note_date = datetime.now()

		notes_list = [mock_file1, mock_file2]
		markdown = "# Index\n<!-- recent_notes -->"

		result = insert_recent_note_links(
			markdown=markdown,
			notes_list=notes_list,
			insert_num=2,
			replace_marker="<!-- recent_notes -->",
		)

		# Verify marker was replaced
		self.assertNotIn("<!-- recent_notes -->", result)

		# Verify links were inserted
		self.assertIn("Note 1", result)
		self.assertIn("Note 2", result)
		self.assertIn("/note1/", result)
		self.assertIn("/note2/", result)

	def test_write_graph_file(self):
		"""Test _write_graph_file method."""
		mock_config = {"site_dir": "/tmp/test_site"}

		# Mock the graph
		mock_graph = Mock()
		mock_graph.to_dict.return_value = {"nodes": [], "edges": []}
		self.plugin._graph = mock_graph

		# Mock os operations
		with (
			patch("mkdocs_note.plugin.os.makedirs") as mock_makedirs,
			patch("mkdocs_note.plugin.open", create=True) as mock_open,
			patch("mkdocs_note.plugin.json.dump") as mock_dump,
		):
			mock_file = MagicMock()
			mock_open.return_value.__enter__.return_value = mock_file

			self.plugin._write_graph_file(mock_config)

			# Verify directory was created
			mock_makedirs.assert_called_once()

			# Verify file was opened
			mock_open.assert_called_once()

			# Verify graph data was written
			mock_dump.assert_called_once()


if __name__ == "__main__":
	unittest.main()
