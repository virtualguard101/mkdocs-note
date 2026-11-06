"""Tests for the network graph's handling of encrypted notes."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.graph import Graph


class TestGraphEncryptedNotes(unittest.TestCase):
	def test_node_kept_but_out_edges_skipped(self):
		"""The title stays public, so the node stays; its links are secret."""
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			secret = root / "secret.md"
			open_note = root / "open.md"
			secret.write_text(
				"---\n"
				"title: Secret\n"
				"encrypt: true\n"
				"permalink: secret\n"
				"---\n"
				"\n"
				"See [Open](./open.md).\n",
				encoding="utf-8",
			)
			open_note.write_text(
				"---\ntitle: Open\n---\n\nSee [Secret](./secret.md).\n",
				encoding="utf-8",
			)

			graph = Graph({"name": "title"})
			graph.nodes = [
				{
					"id": "secret.md",
					"path": str(secret),
					"name": "Secret",
					"url": "secret/",
				},
				{
					"id": "open.md",
					"path": str(open_note),
					"name": "Open",
					"url": "open/",
				},
			]

			graph._create_edges(MagicMock())

			self.assertEqual(len(graph.nodes), 2)
			self.assertIn({"source": "open.md", "target": "secret.md"}, graph.edges)
			self.assertFalse(any(edge["source"] == "secret.md" for edge in graph.edges))

	def test_unencrypted_edges_are_unchanged(self):
		"""Notes without the flag keep producing outgoing edges."""
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			a = root / "a.md"
			b = root / "b.md"
			a.write_text("---\ntitle: A\n---\n\nSee [B](./b.md).\n", encoding="utf-8")
			b.write_text("---\ntitle: B\n---\n\nBody.\n", encoding="utf-8")

			graph = Graph({"name": "title"})
			graph.nodes = [
				{"id": "a.md", "path": str(a), "name": "A", "url": "a/"},
				{"id": "b.md", "path": str(b), "name": "B", "url": "b/"},
			]
			graph._create_edges(MagicMock())
			self.assertIn({"source": "a.md", "target": "b.md"}, graph.edges)


if __name__ == "__main__":
	unittest.main()
