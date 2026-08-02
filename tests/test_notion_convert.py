"""Tests for Notion markdown conversion."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.notion.convert import (
	convert_admonitions_and_tabs,
	convert_inline_math,
	convert_markdown_file,
	is_gfm_table_separator_row,
	strip_gfm_table_separators,
)


class TestAdmonitions(unittest.TestCase):
	def test_note_callout(self):
		src = '!!! note "Title"\n    body line\n'
		out = convert_admonitions_and_tabs(src)
		self.assertIn("<callout", out)
		self.assertIn("Title", out)
		self.assertIn("body line", out)

	def test_collapse_details(self):
		src = "??? tip\n    hidden\n"
		out = convert_admonitions_and_tabs(src)
		self.assertIn("<details>", out)
		self.assertIn("hidden", out)

	def test_tabs_to_heading(self):
		src = '=== "Tab A"\n    content\n'
		out = convert_admonitions_and_tabs(src)
		self.assertIn("### Tab A", out)
		self.assertIn("content", out)


class TestMathAndTables(unittest.TestCase):
	def test_inline_math(self):
		out = convert_inline_math("value $x+1$ here")
		self.assertIn("$`x+1`$", out)

	def test_table_separator(self):
		self.assertTrue(is_gfm_table_separator_row("| --- | :---: |"))
		text = "| a | b |\n| --- | --- |\n| 1 | 2 |\n"
		stripped = strip_gfm_table_separators(text)
		self.assertNotIn("---", stripped)
		self.assertIn("| 1 | 2 |", stripped)


class TestConvertFile(unittest.TestCase):
	def test_markdown_file(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			path = root / "note.md"
			path.write_text(
				"---\ntitle: Hello\ntags: [t1]\n---\n\n# Hello\n\n!!! note\n    hi\n",
				encoding="utf-8",
			)
			title, body, meta = convert_markdown_file(
				path, site_url="https://example.com", page_map={}, docs_root=root
			)
			self.assertEqual(title, "Hello")
			self.assertIn("<callout", body)
			self.assertNotIn("# Hello", body.split("\n")[0] if body else "")
			self.assertEqual(meta.get("tags"), ["t1"])


if __name__ == "__main__":
	unittest.main()
