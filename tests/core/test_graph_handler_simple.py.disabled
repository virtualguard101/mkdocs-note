#!/usr/bin/env python3
"""
Simplified unit tests for GraphHandler class.
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path to allow imports
sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from mkdocs_note.utils.graphps.handlers import GraphHandler
from mkdocs_note.config import PluginConfig


class TestGraphHandlerSimple(unittest.TestCase):
	"""Simplified test cases for GraphHandler class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.config = PluginConfig()
		self.config.enable_network_graph = True
		self.config.debug = False
		self.handler = GraphHandler(self.config)

		# Create temporary directory for tests
		self.temp_dir = Path(tempfile.mkdtemp())

	def tearDown(self):
		"""Clean up test fixtures."""
		if hasattr(self, "temp_dir") and self.temp_dir.exists():
			shutil.rmtree(self.temp_dir)

	def test_initialization(self):
		"""Test GraphHandler initialization."""
		self.assertIsNotNone(self.handler._graph)
		self.assertEqual(self.handler.config, self.config)

	def test_add_static_resources_basic(self):
		"""Test add_static_resources method basic functionality."""
		# Create a proper mock that supports both attribute and dictionary access
		extra_javascript = []
		extra_css = []

		mock_config = MagicMock()
		mock_config.extra_javascript = extra_javascript
		mock_config.extra_css = extra_css
		mock_config.__getitem__ = lambda self, key: {
			"extra_javascript": extra_javascript,
			"extra_css": extra_css,
		}[key]

		# Test that the method can be called without crashing
		# The actual path resolution will use fallback due to importlib issues in test environment
		self.handler.add_static_resources(mock_config)

		# Check that static_dir is set (should be set to fallback path)
		self.assertIsNotNone(self.handler.static_dir)

		# Check that resources are added to config
		self.assertIn("https://d3js.org/d3.v7.min.js", extra_javascript)
		self.assertIn("js/graph.js", extra_javascript)
		self.assertIn("css/graph.css", extra_css)

	def test_inject_graph_options_basic(self):
		"""Test inject_graph_options method."""
		mock_config = Mock()
		mock_config.get.return_value = False
		mock_config.site_url = ""

		script = self.handler.inject_graph_options(mock_config)

		self.assertIn("<script>", script)
		self.assertIn("window.graph_options", script)
		self.assertIn("debug: false", script)
		self.assertIn("base_path: '/'", script)

	def test_inject_graph_options_with_site_url(self):
		"""Test inject_graph_options with site_url."""
		mock_config = Mock()
		mock_config.get.side_effect = lambda key, default=None: {
			"debug": True,
			"site_url": "https://example.com/docs/",
		}.get(key, default)
		mock_config.site_url = "https://example.com/docs/"

		script = self.handler.inject_graph_options(mock_config)

		self.assertIn("debug: true", script)
		self.assertIn("base_path: '/docs/'", script)

	def test_write_graph_file_basic(self):
		"""Test _write_graph_file method."""
		# Use the class-level temp directory instead of creating a new one
		mock_config = Mock()
		mock_config.site_dir = str(self.temp_dir)

		# Mock the graph data
		self.handler._graph = Mock()
		self.handler._graph.to_dict.return_value = {"nodes": [], "edges": []}

		# Mock the config to support dictionary access
		mock_config.__getitem__ = lambda self, key: getattr(self, key)

		self.handler._write_graph_file(mock_config)

		# Check that graph file was created
		graph_file = self.temp_dir / "graph" / "graph.json"
		self.assertTrue(graph_file.exists())

		# Check file content
		with open(graph_file, "r") as f:
			content = f.read()
			self.assertIn('"nodes"', content)
			self.assertIn('"edges"', content)

	def test_copy_static_assets_basic(self):
		"""Test copy_static_assets method."""
		# Use the class-level temp directory instead of creating a new one
		mock_config = Mock()
		mock_config.site_dir = str(self.temp_dir)
		# Mock the config to support dictionary access
		mock_config.__getitem__ = lambda self, key: getattr(self, key)

		# Mock static_dir to point to existing files
		mock_static_dir = Mock()
		mock_static_dir.__truediv__ = Mock(return_value=Path("/mock/graph.js"))
		self.handler.static_dir = mock_static_dir

		# Mock the files to exist
		with patch("pathlib.Path.exists", return_value=True):
			with patch("mkdocs_note.utils.graphps.handlers.shutil.copy") as mock_copy:
				with patch("pathlib.Path.mkdir") as mock_mkdir:
					self.handler.copy_static_assets(mock_config)

		# Check that directories were created
		self.assertEqual(mock_mkdir.call_count, 2)

		# Check that files were copied
		self.assertEqual(mock_copy.call_count, 2)

	def test_build_graph(self):
		"""Test build_graph method."""
		mock_files = Mock()
		mock_graph = Mock()
		self.handler._graph = mock_graph

		result = self.handler.build_graph(mock_files)

		# The graph should be called with files
		mock_graph.assert_called_once_with(mock_files)
		self.assertEqual(result, mock_graph.return_value)


if __name__ == "__main__":
	unittest.main()
