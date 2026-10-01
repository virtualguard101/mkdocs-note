"""Unit tests for shared link normalization helpers."""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.links import (
	LINK_PATTERN,
	find_link_targets,
	iter_markdown_links,
	normalize_link,
	resolve_target_src,
	split_href,
	unescape_url,
)


class TestUnescapeUrl(unittest.TestCase):
	def test_angle_brackets(self):
		self.assertEqual(unescape_url("<foo%20bar.md>"), "foo bar.md")

	def test_plain(self):
		self.assertEqual(unescape_url("a%2Fb.md"), "a/b.md")


class TestNormalizeLink(unittest.TestCase):
	def _match(self, text: str) -> re.Match[str]:
		m = re.search(LINK_PATTERN, text)
		assert m is not None
		return m

	def test_markdown_link(self):
		self.assertEqual(
			normalize_link(self._match("[x](./other.md)")),
			"./other.md",
		)

	def test_drops_query_and_fragment(self):
		self.assertEqual(
			normalize_link(self._match("[x](./other.md?q=1#sec)")),
			"./other.md",
		)

	def test_wikilink_adds_md(self):
		self.assertEqual(normalize_link(self._match("[[Other]]")), "Other.md")

	def test_wikilink_with_md(self):
		self.assertEqual(normalize_link(self._match("[[Other.md]]")), "Other.md")

	def test_wikilink_with_fragment(self):
		self.assertEqual(
			normalize_link(self._match("[[Other#Heading]]")),
			"Other.md",
		)

	def test_angle_bracket_link(self):
		self.assertEqual(
			normalize_link(self._match("[x](<path/to/file.md>)")),
			"path/to/file.md",
		)


class TestSplitHref(unittest.TestCase):
	def test_with_fragment(self):
		self.assertEqual(split_href("a.md#hello"), ("a.md", "hello"))

	def test_without_fragment(self):
		self.assertEqual(split_href("a.md"), ("a.md", ""))


class TestResolveAndIter(unittest.TestCase):
	def test_resolve_relative(self):
		self.assertEqual(
			resolve_target_src("notes/a.md", "../b.md"),
			"b.md",
		)

	def test_iter_markdown_and_wiki(self):
		md = "See [a](./t.md#frag) and [[Wiki#Sec]]"
		links = list(iter_markdown_links(md))
		self.assertEqual(links[0], ("./t.md", "frag"))
		self.assertEqual(links[1], ("Wiki.md", "Sec"))

	def test_find_link_targets(self):
		known = {"notes/a.md", "notes/b.md"}
		md = "[go](./b.md#x) [miss](./c.md)"
		targets = list(find_link_targets(md, "notes/a.md", known))
		self.assertEqual(targets, [("notes/b.md", "x")])


if __name__ == "__main__":
	unittest.main()
