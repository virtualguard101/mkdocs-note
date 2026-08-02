"""Tests for shared frontmatter helpers."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.meta import (
	extract_tags,
	parse_frontmatter,
	parse_frontmatter_file,
)


class TestParseFrontmatter(unittest.TestCase):
	def test_no_frontmatter(self):
		meta, body = parse_frontmatter("# Hello\n\nworld")
		self.assertEqual(meta, {})
		self.assertIn("Hello", body)

	def test_with_frontmatter(self):
		text = "---\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Body\n"
		meta, body = parse_frontmatter(text)
		self.assertEqual(meta.get("title"), "Test")
		self.assertEqual(meta.get("tags"), ["a", "b"])
		self.assertTrue(body.lstrip().startswith("# Body"))

	def test_parse_frontmatter_file(self):
		with tempfile.TemporaryDirectory() as tmp:
			path = Path(tmp) / "note.md"
			path.write_text("---\ntitle: X\n---\n\ncontent\n", encoding="utf-8")
			meta, body = parse_frontmatter_file(path)
			self.assertEqual(meta["title"], "X")
			self.assertIn("content", body)


class TestExtractTags(unittest.TestCase):
	def test_list(self):
		self.assertEqual(extract_tags({"tags": ["a", "b"]}), ["a", "b"])

	def test_string(self):
		self.assertEqual(extract_tags({"tags": "a, b"}), ["a", "b"])

	def test_tag_alias(self):
		self.assertEqual(extract_tags({"tag": "solo"}), ["solo"])

	def test_empty(self):
		self.assertEqual(extract_tags({}), [])


if __name__ == "__main__":
	unittest.main()
