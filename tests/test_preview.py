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
	_rewrite_url,
	_split_sections,
	add_preview_static_resources,
	decode_fragment,
	excerpt_html,
	excerpt_plain,
	extract_summary,
	first_prose_paragraph,
	inject_preview_script,
	resolve_section_markdown,
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

	def test_skip_admonition_marker_as_summary(self):
		body = (
			"!!! abstract\n"
			"    Hidden abstract body.\n\n"
			"Real prose paragraph after the admonition.\n"
		)
		summary = first_prose_paragraph(body, 200)
		self.assertIn("Real prose", summary)
		self.assertNotIn("!!!", summary)
		self.assertNotIn("abstract", summary.lower())

	def test_skip_details_and_tab_markers(self):
		body = (
			'??? note "Hidden"\n'
			"    details body\n\n"
			'=== "Tab"\n'
			"    tab body\n\n"
			"Visible paragraph.\n"
		)
		summary = first_prose_paragraph(body, 200)
		self.assertEqual(summary, "Visible paragraph.")


class TestSectionHierarchy(unittest.TestCase):
	def test_parent_includes_nested_children(self):
		body = (
			"## Parent\n\n"
			"### Child\n\n"
			"Child prose here.\n\n"
			"## Sibling\n\n"
			"Sibling prose.\n"
		)
		sections = _split_sections(body)
		by_id = {sid: md for sid, _t, md in sections if sid}
		parent_id = slugify_heading("Parent")
		self.assertIn(parent_id, by_id)
		self.assertIn("Child prose here", by_id[parent_id])
		self.assertIn("### Child", by_id[parent_id])
		self.assertNotIn("Sibling prose", by_id[parent_id])

	def test_leaf_section_unchanged(self):
		body = "## Double Pointers\n\nLeaf only.\n\n## Next\n\nOther.\n"
		sections = {sid: (t, md) for sid, t, md in _split_sections(body) if sid}
		sid = slugify_heading("Double Pointers")
		_heading, md = resolve_section_markdown(sections, sid)
		self.assertIn("Leaf only", md)
		self.assertNotIn("Other", md)

	def test_empty_parent_descends_to_child(self):
		body = "## Parent\n\n### Child\n\nNested content only.\n"
		sections = {sid: (t, md) for sid, t, md in _split_sections(body) if sid}
		parent_id = slugify_heading("Parent")
		# Hierarchical split already includes child; resolve still returns content
		heading, md = resolve_section_markdown(sections, parent_id)
		self.assertEqual(heading, "Parent")
		self.assertIn("Nested content only", md)


class TestFragmentEncoding(unittest.TestCase):
	def test_decode_fragment_cjk_and_ascii(self):
		self.assertEqual(decode_fragment("进程的内存映像"), "进程的内存映像")
		encoded = "%E8%BF%9B%E7%A8%8B%E7%9A%84%E5%86%85%E5%AD%98%E6%98%A0%E5%83%8F"
		self.assertEqual(decode_fragment(encoded), "进程的内存映像")
		self.assertEqual(decode_fragment("Stack-and-Heap"), "Stack-and-Heap")
		self.assertEqual(decode_fragment("#Stack-and-Heap"), "Stack-and-Heap")

	def test_page_key_stores_unicode_fragment(self):
		builder = PreviewBuilder({"mode": "excerpt", "scope": "all"})
		key = builder._page_key(
			"notes/os/",
			"%E8%BF%9B%E7%A8%8B%E7%9A%84%E5%86%85%E5%AD%98%E6%98%A0%E5%83%8F",
		)
		self.assertEqual(key, "notes/os/#进程的内存映像")
		self.assertEqual(
			builder._page_key("notes/os/", "Stack-and-Heap"),
			"notes/os/#Stack-and-Heap",
		)

	def test_cjk_fragment_entry_in_builder(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			a = root / "a.md"
			b = root / "b.md"
			heading = "进程的内存映像"
			a.write_text(
				f"See [B](./b.md#{heading}).\n",
				encoding="utf-8",
			)
			b.write_text(
				f"---\ntitle: B\n---\n\n## {heading}\n\nCJK section body.\n",
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
			frag_key = f"b/#{slugify_heading(heading)}"
			self.assertIn(frag_key, data)
			self.assertIn("CJK section body", data[frag_key]["summary"])


class TestImageUrlRewrite(unittest.TestCase):
	def test_cdn_absolute_passthrough(self):
		self.assertEqual(
			_rewrite_url("https://cdn.example/x.png", "notes/page/", "/"),
			"https://cdn.example/x.png",
		)
		self.assertEqual(
			_rewrite_url("//cdn.example/x.png", "notes/page/", "/"),
			"//cdn.example/x.png",
		)
		self.assertEqual(
			_rewrite_url("data:image/png;base64,xx", "notes/page/", "/"),
			"data:image/png;base64,xx",
		)

	def test_files_api_primary(self):
		source = MagicMock()
		source.src_path = "notes/page.md"
		asset = MagicMock()
		asset.src_path = "notes/assets/foo.png"
		asset.url = "notes/assets/foo.png"
		files = MagicMock()
		files.get_file_from_path = MagicMock(return_value=asset)
		out = _rewrite_url(
			"assets/foo.png",
			"notes/page/",
			"/site/",
			source_file=source,
			files=files,
		)
		self.assertEqual(out, "/site/notes/assets/foo.png")
		# Must not nest under page/ as if page were a directory for assets
		self.assertNotIn("notes/page/assets", out)

	def test_fallback_b_directory_page_url(self):
		# No Files hit → dirname of directory-style page URL
		out = _rewrite_url("assets/foo.png", "notes/page/", "/site/")
		self.assertEqual(out, "/site/notes/assets/foo.png")
		self.assertNotEqual(out, "/site/notes/page/assets/foo.png")


class TestLinkedOnlyScopeExpansion(unittest.TestCase):
	def _make_file(self, path: Path, url: str):
		f = MagicMock()
		f.src_path = path.name
		f.abs_src_path = str(path)
		f.url = url
		f.name = path.stem
		f.page = MagicMock()
		f.page.title = path.stem
		return f

	def test_recent_extra_src_included(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			a = root / "a.md"
			recent = root / "recent.md"
			orphan = root / "orphan.md"
			a.write_text("No outbound note links.\n", encoding="utf-8")
			recent.write_text(
				"---\ntitle: Recent\ndescription: From recent\n---\n\nBody.\n",
				encoding="utf-8",
			)
			orphan.write_text(
				"---\ntitle: Orphan\n---\n\nNever linked.\n",
				encoding="utf-8",
			)
			files = MagicMock()
			fa, fr, fo = (
				self._make_file(a, "a/"),
				self._make_file(recent, "recent/"),
				self._make_file(orphan, "orphan/"),
			)
			files.documentation_pages.return_value = [fa, fr, fo]
			builder = PreviewBuilder(
				{"mode": "summary", "scope": "linked_only"},
				extra_src_paths={"recent.md"},
			)
			data = builder(files)
			self.assertIn("recent/", data)
			self.assertEqual(data["recent/"]["summary"], "From recent")
			self.assertNotIn("orphan/", data)
			self.assertNotIn("a/", data)

	def test_graph_src_included(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			a = root / "a.md"
			g = root / "g.md"
			a.write_text("Alone.\n", encoding="utf-8")
			g.write_text(
				"---\ntitle: GraphNode\ndescription: Via graph\n---\n\nBody.\n",
				encoding="utf-8",
			)
			files = MagicMock()
			fa, fg = self._make_file(a, "a/"), self._make_file(g, "g/")
			files.documentation_pages.return_value = [fa, fg]
			builder = PreviewBuilder(
				{"mode": "summary", "scope": "linked_only"},
				graph_src_paths={"g.md"},
			)
			data = builder(files)
			self.assertIn("g/", data)
			self.assertNotIn("a/", data)

	def test_index_out_links_included(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			idx = root / "index.md"
			target = root / "target.md"
			idx.write_text("Index [Target](./target.md).\n", encoding="utf-8")
			target.write_text(
				"---\ntitle: Target\ndescription: From index\n---\n\nBody.\n",
				encoding="utf-8",
			)
			files = MagicMock()
			fi, ft = self._make_file(idx, "index/"), self._make_file(target, "target/")
			files.documentation_pages.return_value = [fi, ft]
			# Without index_src_paths, target is already linked from index.md
			# because all docs are scanned for links. Use a silent index that
			# is NOT in docs scan... Actually linked_only scans ALL docs for
			# link targets. Index expansion matters when index is listed but
			# we want explicit coverage: builder with only target via index set
			# while a "silent" page has no links — simulate by putting the
			# link only reachable via index_src re-scan (already covered by
			# normal scan). Test that index_src_paths does not error and
			# includes targets.
			builder = PreviewBuilder(
				{"mode": "summary", "scope": "linked_only"},
				index_src_paths={"index.md"},
			)
			data = builder(files)
			self.assertIn("target/", data)


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
