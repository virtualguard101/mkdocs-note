import unittest
import sys
import os

# Add src to path to allow imports
sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.config import MkdocsNoteConfig


class TestMkdocsNoteConfig(unittest.TestCase):
	"""Test cases for MkdocsNoteConfig class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.config = MkdocsNoteConfig()

	def test_default_values(self):
		"""Test that default values are set correctly."""
		self.assertTrue(self.config.enabled)
		self.assertEqual(self.config.notes_root, "docs")
		self.assertIsNotNone(self.config.recent_notes_config)
		self.assertFalse(self.config.recent_notes_config["enabled"])
		self.assertEqual(
			self.config.recent_notes_config["insert_marker"], "<!-- recent_notes -->"
		)
		self.assertEqual(self.config.recent_notes_config["insert_num"], 10)

	def test_graph_config_default(self):
		"""Test graph configuration defaults."""
		self.assertIsNotNone(self.config.graph_config)
		self.assertFalse(self.config.graph_config["enabled"])
		self.assertEqual(self.config.graph_config["name"], "title")
		self.assertFalse(self.config.graph_config["debug"])

	def test_config_attributes_exist(self):
		"""Test that all required config attributes exist."""
		required_attrs = [
			"enabled",
			"notes_root",
			"recent_notes_config",
			"graph_config",
		]

		for attr in required_attrs:
			self.assertTrue(
				hasattr(self.config, attr),
				f"Config missing required attribute: {attr}",
			)

	def test_recent_notes_config_structure(self):
		"""Test that recent notes config has all required keys."""
		required_keys = ["enabled", "insert_marker", "insert_num"]
		for key in required_keys:
			self.assertIn(
				key,
				self.config.recent_notes_config,
				f"recent_notes_config missing required key: {key}",
			)

	def test_graph_config_structure(self):
		"""Test that graph config has all required keys."""
		required_keys = ["enabled", "name", "debug"]
		for key in required_keys:
			self.assertIn(
				key,
				self.config.graph_config,
				f"graph_config missing required key: {key}",
			)


if __name__ == "__main__":
	unittest.main()
