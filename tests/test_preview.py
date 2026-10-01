"""Tests for link hover preview build helpers."""

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

from mkdocs_note.preview import (
	PreviewBuilder,
	add_preview_static_resources,
	excerpt_html,
	excerpt_plain,
	extract_summary,
	first_prose_paragraph,
	inject_preview_script,
	sanitize_preview_html,
	slugify_heading,
	strip_markdown_inline,
)


class TestSummaryExtraction(unittest.TestCase):
	def test_frontmatter_description(self):
		meta = {"description": "A short desc"}
		self.assertEqual(
			extract_summary(meta, "Body paragraph here.", 200), "A short desc"
		)

	def test_frontmatter_summary(self):
		meta = {"summary": "From summary"}
		self.assertEqual(extract_summary(meta, "Body.", 200), "From summary")

	def test_first_paragraph(self):
		body = "# Title\n\nFirst paragraph with **bold**.\n\nSecond."
		self.assertIn("First paragraph", first_prose_paragraph(body, 200))
		self.assertNotIn("**", first_prose_paragraph(body, 200))

	def test_truncate(self):
		text = first_prose_paragraph("x" * 500, 50)
		self.assertTrue(len(text) <= 50)
		self.assertTrue(text.endswith("…"))

	def test_strip_inline(self):
		self.assertEqual(strip_markdown_inline("a [b](url) `c`"), "a b c")


class TestSlugifyAndExcerpt(unittest.TestCase):
	def test_slugify_ascii(self):
		self.assertEqual(slugify_heading("Hello World"), "Hello-World")

	def test_excerpt_plain_includes_code(self):
		md = "Intro line.\n\n```\ncode_here\n```\n"
		ex = excerpt_plain(md, 200)
		self.assertIn("Intro line", ex)
		self.assertIn("code_here", ex)

	def test_excerpt_html_sanitized(self):
		md = (
			"Hello **bold**\n\n"
			"| Option | Default |\n"
			"|--------|---------|\n"
			"| a | b |\n\n"
			"```\nalert(1)\n```\n"
		)
		out = excerpt_html(md, "p/", "/")
		self.assertIn("<strong>", out)
		self.assertIn("<table>", out)
		self.assertIn("<th>", out)
		self.assertIn("<td>", out)
		self.assertIn("<pre>", out)
		self.assertNotIn("<script", out.lower())
		self.assertNotIn("| Option |", out)

	def test_excerpt_html_material_extensions(self):
		exts = [
			"tables",
			"admonition",
			"pymdownx.details",
			"pymdownx.keys",
			"pymdownx.mark",
			"pymdownx.tilde",
			"pymdownx.caret",
			"pymdownx.superfences",
			"pymdownx.tabbed",
		]
		mdx = {"pymdownx.tabbed": {"alternate_style": True}}
		md = (
			'!!! note "Title"\n'
			"    Body **here**.\n\n"
			"Press ++ctrl+c++ and ==mark==.\n\n"
			'=== "A"\n'
			"    aaa\n\n"
			'=== "B"\n'
			"    bbb\n"
		)
		out = excerpt_html(
			md,
			"p/",
			"/",
			markdown_extensions=exts,
			mdx_configs=mdx,
		)
		self.assertIn('class="admonition note"', out)
		self.assertIn("admonition-title", out)
		self.assertIn("<kbd", out)
		self.assertIn("<mark>", out)
		self.assertIn("tabbed-set", out)
		self.assertNotIn("!!! note", out)

	def test_sanitize_strips_scripts(self):
		raw = "<p>ok</p><script>bad()</script>"
		out = sanitize_preview_html(raw)
		self.assertIn("ok", out)
		self.assertNotIn("script", out.lower())
		self.assertNotIn("bad()", out)


class TestPreviewBuilder(unittest.TestCase):
	def test_root_page_key_normalized(self):
		builder = PreviewBuilder({"mode": "summary", "scope": "all"})
		self.assertEqual(builder._page_key(""), "")
		self.assertEqual(builder._page_key("./"), "")
		self.assertEqual(builder._page_key("."), "")
		self.assertEqual(builder._page_key("usage/config/"), "usage/config/")

	def test_linked_only_and_preview_false(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			a = root / "a.md"
			b = root / "b.md"
			c = root / "c.md"
			a.write_text(
				"---\ntitle: A\ndescription: Desc A\n---\n\nSee [B](./b.md) and [C](./c.md).\n",
				encoding="utf-8",
			)
			b.write_text(
				"---\ntitle: B\npreview: false\n---\n\nHidden body.\n",
				encoding="utf-8",
			)
			c.write_text(
				"---\ntitle: C\nsummary: Sum C\n---\n\n## Section One\n\nDetails.\n",
				encoding="utf-8",
			)

			def make_file(path: Path, url: str):
				f = MagicMock()
				f.src_path = path.name
				f.abs_src_path = str(path)
				f.url = url
				f.name = path.stem
				f.page = MagicMock()
				f.page.title = path.stem
				return f

			files = MagicMock()
			fa, fb, fc = (
				make_file(a, "a/"),
				make_file(b, "b/"),
				make_file(c, "c/"),
			)
			files.documentation_pages.return_value = [fa, fb, fc]

			builder = PreviewBuilder(
				{
					"mode": "summary",
					"max_chars": 200,
					"include_fragments": True,
					"scope": "linked_only",
				},
			)
			data = builder(files)
			# b is linked but preview:false → skipped; c included
			self.assertNotIn("b/", data)
			self.assertIn("c/", data)
			self.assertEqual(data["c/"]["summary"], "Sum C")
			# a is not a link target → excluded under linked_only
			self.assertNotIn("a/", data)

	def test_excerpt_fragments(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			a = root / "a.md"
			b = root / "b.md"
			a.write_text("See [B](./b.md#Section-One).\n", encoding="utf-8")
			b.write_text(
				"---\ntitle: B\n---\n\nLead para.\n\n## Section One\n\nFragment body here.\n",
				encoding="utf-8",
			)

			def make_file(path: Path, url: str):
				f = MagicMock()
				f.src_path = path.name
				f.abs_src_path = str(path)
				f.url = url
				f.name = path.stem
				f.page = MagicMock()
				f.page.title = path.stem
				return f

			files = MagicMock()
			files.documentation_pages.return_value = [
				make_file(a, "a/"),
				make_file(b, "b/"),
			]
			builder = PreviewBuilder(
				{
					"mode": "excerpt",
					"max_chars": 200,
					"include_fragments": True,
					"scope": "linked_only",
				},
			)
			data = builder(files)
			self.assertIn("b/", data)
			self.assertIn("html", data["b/"])
			frag_key = "b/#Section-One"
			self.assertIn(frag_key, data)
			self.assertIn("Fragment body", data[frag_key]["summary"])


class TestPreviewAssetsGating(unittest.TestCase):
	def test_inject_options(self):
		html = "<html><body>x</body></html>"
		config = {"site_url": "https://example.com/docs/"}
		out = inject_preview_script(
			html,
			config,  # type: ignore[arg-type]
			{"mode": "summary", "delay_ms": 250, "mobile": False},
			graph_enabled=True,
		)
		self.assertIn("window.preview_options", out)
		self.assertIn('"delay_ms": 250', out)
		self.assertIn('"graph_enabled": true', out)

	def test_add_static_resources(self):
		config = {"extra_javascript": [], "extra_css": []}
		add_preview_static_resources(config)  # type: ignore[arg-type]
		self.assertIn("js/preview.js", config["extra_javascript"])
		self.assertIn("css/preview.css", config["extra_css"])


if __name__ == "__main__":
	unittest.main()
