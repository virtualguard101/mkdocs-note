"""Tests for page-tree helpers (nav.yml + directory scan)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.tree import (
	build_directory_tree,
	build_nav_tree,
	build_page_tree,
	index_tree,
	is_index_doc,
)


class TestNavTree(unittest.TestCase):
	def test_build_nav_tree(self):
		nodes = [
			"index.md",
			{"Getting Started": "getting-started.md"},
			{"Guide": [{"Install": "usage/install.md"}]},
		]
		tree = build_nav_tree(nodes)
		index = index_tree(tree)
		self.assertIn("getting-started.md", index)
		self.assertEqual(index["getting-started.md"].title, "Getting Started")
		self.assertIn("Guide", index)
		self.assertIsNone(index["Guide"].file_rel)
		self.assertIn("usage/install.md", index)
		self.assertEqual(index["usage/install.md"].parent_key, "Guide")

	def test_is_index_doc(self):
		self.assertTrue(is_index_doc("usage/index.md"))
		self.assertFalse(is_index_doc("usage/cli.md"))


class TestDirectoryTree(unittest.TestCase):
	def test_preserves_hierarchy(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			(root / "a.md").write_text("# A\n", encoding="utf-8")
			(root / "sub").mkdir()
			(root / "sub" / "b.md").write_text("# B\n", encoding="utf-8")
			(root / "sub" / "index.md").write_text("# Idx\n", encoding="utf-8")
			(root / "assets").mkdir()
			(root / "assets" / "x.png").write_text("x", encoding="utf-8")

			tree = build_directory_tree(root)
			index = index_tree(tree)
			self.assertIn("a.md", index)
			self.assertIn("sub", index)
			self.assertIn("sub/b.md", index)
			self.assertNotIn("sub/index.md", index)
			self.assertEqual(index["sub/b.md"].parent_key, "sub")

	def test_build_page_tree_fallback(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			(root / "note.md").write_text("# N\n", encoding="utf-8")
			tree, source = build_page_tree(
				nav_file=root / "missing.nav.yml",
				notes_root=root,
				docs_dir=root,
			)
			self.assertEqual(source, "directory")
			self.assertTrue(any(n.file_rel == "note.md" for n in tree))


if __name__ == "__main__":
	unittest.main()
