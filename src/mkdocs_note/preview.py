"""Same-site link hover preview: build-time JSON and static asset helpers.

See issue #82. Opt-in via ``preview_config.enabled``; when disabled the plugin
must not register assets, inject scripts, or write ``previews.json``.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urljoin, urlparse

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import Files

from mkdocs_note.utils.links import find_link_targets
from mkdocs_note.utils.meta import parse_frontmatter

logger = get_plugin_logger(__name__)

# Heading line: ATX style # … ######
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
_FENCE_RE = re.compile(r"^```[\w+-]*\s*$")
_CODE_FENCE_BLOCK_RE = re.compile(
	r"```[\w+-]*\n(.*?)```",
	re.DOTALL,
)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_MD_BOLD_RE = re.compile(r"(\*\*|__)(.*?)\1")
_MD_ITALIC_RE = re.compile(r"(\*|_)(.*?)\1")
_MD_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_MD_HTML_TAG_RE = re.compile(r"</?[^>]+>")


def _get_slugify():
	"""Return a pymdownx-compatible slugify callable ``(text, sep) -> id``."""
	try:
		from pymdownx.slugs import slugify as _slugify_factory

		return _slugify_factory()
	except (ImportError, TypeError, AttributeError):  # pragma: no cover - fallback

		def _fallback(text: str, sep: str = "-") -> str:
			slug = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
			slug = re.sub(r"[\s_]+", sep, slug.strip()).strip(sep)
			return slug or "section"

		return _fallback


def slugify_heading(text: str) -> str:
	"""Slugify a heading title to match Material / pymdownx TOC ids."""
	fn = _get_slugify()
	return fn(text, "-")


def strip_markdown_inline(text: str) -> str:
	"""Remove common inline markdown markers for plain-text summaries."""
	text = _MD_IMAGE_RE.sub(r"\1", text)
	text = _MD_LINK_RE.sub(r"\1", text)
	text = _MD_BOLD_RE.sub(r"\2", text)
	text = _MD_ITALIC_RE.sub(r"\2", text)
	text = _MD_INLINE_CODE_RE.sub(r"\1", text)
	text = _MD_HTML_TAG_RE.sub("", text)
	return re.sub(r"\s+", " ", text).strip()


def first_prose_paragraph(body: str, max_chars: int) -> str:
	"""Extract the first non-empty prose paragraph from markdown body."""
	# Drop fenced code blocks so we don't preview code as summary.
	without_code = _CODE_FENCE_BLOCK_RE.sub("", body)
	chunks: list[str] = []
	buf: list[str] = []
	for line in without_code.splitlines():
		stripped = line.strip()
		if not stripped:
			if buf:
				chunks.append(" ".join(buf))
				buf = []
			continue
		if stripped.startswith(("#", ">", "|")):
			if buf:
				chunks.append(" ".join(buf))
				buf = []
			continue
		if stripped.startswith(("- ", "* ")) or re.match(r"^\d+\.\s", stripped):
			if buf:
				chunks.append(" ".join(buf))
				buf = []
			continue
		buf.append(stripped)
	if buf:
		chunks.append(" ".join(buf))

	for chunk in chunks:
		plain = strip_markdown_inline(chunk)
		if plain:
			if len(plain) > max_chars:
				return plain[: max_chars - 1].rstrip() + "…"
			return plain
	return ""


def extract_summary(
	meta: dict[str, Any],
	body: str,
	max_chars: int,
) -> str:
	"""Summary priority: frontmatter description → summary → first paragraph."""
	for key in ("description", "summary"):
		val = meta.get(key)
		if isinstance(val, str) and val.strip():
			text = strip_markdown_inline(val.strip())
			if len(text) > max_chars:
				return text[: max_chars - 1].rstrip() + "…"
			return text
	return first_prose_paragraph(body, max_chars)


def extract_title_from_page(
	meta: dict[str, Any],
	body: str,
	fallback: str,
) -> str:
	"""Resolve a display title from frontmatter, first H1, or fallback."""
	title = meta.get("title")
	if isinstance(title, str) and title.strip():
		return title.strip()
	m = _HEADING_RE.search(body)
	if m and len(m.group(1)) == 1:
		return strip_markdown_inline(m.group(2))
	return fallback


def _split_sections(body: str) -> list[tuple[str, str, str]]:
	"""Split body into ``(heading_id, heading_text, section_md)`` parts.

	Content before the first heading is ``("", "", lead_md)``.
	"""
	matches = list(_HEADING_RE.finditer(body))
	if not matches:
		return [("", "", body)]

	sections: list[tuple[str, str, str]] = []
	lead = body[: matches[0].start()]
	if lead.strip():
		sections.append(("", "", lead))

	for i, match in enumerate(matches):
		heading_text = strip_markdown_inline(match.group(2))
		heading_id = slugify_heading(heading_text)
		start = match.end()
		end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
		sections.append((heading_id, heading_text, body[start:end]))
	return sections


def excerpt_plain(section_md: str, max_chars: int) -> str:
	"""Plain-text excerpt: prose + fenced code as text, truncated."""
	parts: list[str] = []
	in_fence = False
	fence_lines: list[str] = []
	for line in section_md.splitlines():
		if _FENCE_RE.match(line.strip()):
			if in_fence:
				parts.append("\n".join(fence_lines))
				fence_lines = []
				in_fence = False
			else:
				in_fence = True
			continue
		if in_fence:
			fence_lines.append(line)
			continue
		stripped = line.strip()
		if not stripped or stripped.startswith("#"):
			continue
		parts.append(strip_markdown_inline(stripped))
	if fence_lines:
		parts.append("\n".join(fence_lines))
	text = "\n\n".join(p for p in parts if p)
	if len(text) > max_chars:
		return text[: max_chars - 1].rstrip() + "…"
	return text


def _markdown_blocks_to_html(section_md: str, page_url: str, site_base: str) -> str:
	"""Convert a limited subset of markdown to sanitized HTML."""
	blocks: list[str] = []
	lines = section_md.splitlines()
	i = 0
	while i < len(lines):
		line = lines[i]
		stripped = line.strip()
		if not stripped:
			i += 1
			continue
		if _FENCE_RE.match(stripped):
			code_lines: list[str] = []
			i += 1
			while i < len(lines) and not _FENCE_RE.match(lines[i].strip()):
				code_lines.append(lines[i])
				i += 1
			if i < len(lines):
				i += 1  # closing fence
			escaped = html.escape("\n".join(code_lines))
			blocks.append(
				f'<pre class="mkdocs-note-preview__pre"><code class="mkdocs-note-preview__code">'
				f"{escaped}</code></pre>",
			)
			continue
		hm = re.match(r"^(#{1,6})\s+(.+)$", stripped)
		if hm:
			level = len(hm.group(1))
			inner = html.escape(strip_markdown_inline(hm.group(2)))
			blocks.append(
				f'<h{level} class="mkdocs-note-preview__heading">{inner}</h{level}>',
			)
			i += 1
			continue
		# Collect paragraph lines
		para: list[str] = [stripped]
		i += 1
		while i < len(lines):
			nxt = lines[i].strip()
			if not nxt or nxt.startswith("#") or _FENCE_RE.match(nxt):
				break
			para.append(nxt)
			i += 1
		para_html = _inline_md_to_html(" ".join(para), page_url, site_base)
		blocks.append(f'<p class="mkdocs-note-preview__p">{para_html}</p>')
	return "\n".join(blocks)


def _rewrite_url(url: str, page_url: str, site_base: str) -> str:
	"""Rewrite relative asset URLs against the page and site base."""
	if not url or url.startswith(("#", "mailto:", "data:", "javascript:")):
		return url
	parsed = urlparse(url)
	if parsed.scheme or parsed.netloc:
		return url
	# Absolute site path
	if url.startswith("/"):
		return urljoin(site_base, url.lstrip("/"))
	page_dir = page_url if page_url.endswith("/") else page_url.rsplit("/", 1)[0] + "/"
	return urljoin(urljoin(site_base, page_dir), url)


_INLINE_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline_md_to_html(text: str, page_url: str, site_base: str) -> str:
	"""Escape text and convert a few inline constructs; images get rewritten src."""

	def repl_img(m: re.Match[str]) -> str:
		alt = html.escape(m.group(1))
		src = html.escape(_rewrite_url(m.group(2).strip(), page_url, site_base))
		return f'<img class="mkdocs-note-preview__img" alt="{alt}" src="{src}" loading="lazy"/>'

	def repl_link(m: re.Match[str]) -> str:
		label = html.escape(strip_markdown_inline(m.group(1)))
		href = html.escape(_rewrite_url(m.group(2).strip(), page_url, site_base))
		return f'<a class="mkdocs-note-preview__a" href="{href}">{label}</a>'

	# Process images before links
	pieces: list[str] = []
	pos = 0
	for m in _INLINE_IMG_RE.finditer(text):
		pieces.append(html.escape(text[pos : m.start()]))
		pieces.append(repl_img(m))
		pos = m.end()
	rest = text[pos:]
	pos2 = 0
	tmp: list[str] = []
	for m in _INLINE_LINK_RE.finditer(rest):
		tmp.append(html.escape(rest[pos2 : m.start()]))
		tmp.append(repl_link(m))
		pos2 = m.end()
	tmp.append(html.escape(rest[pos2:]))
	pieces.append("".join(tmp))
	out = "".join(pieces)
	# Bold / italic / code on already-escaped text using markers still present
	out = re.sub(
		r"`([^`]+)`",
		r'<code class="mkdocs-note-preview__code">\1</code>',
		out,
	)
	return out


class _PreviewHTMLSanitizer(HTMLParser):
	"""Whitelist sanitizer for preview HTML snippets."""

	ALLOWED: ClassVar[set[str]] = {
		"h1",
		"h2",
		"h3",
		"h4",
		"h5",
		"h6",
		"p",
		"pre",
		"code",
		"a",
		"img",
		"br",
	}
	ALLOWED_ATTRS: ClassVar[dict[str, set[str]]] = {
		"a": {"href", "class"},
		"img": {"src", "alt", "class", "loading"},
		"h1": {"class"},
		"h2": {"class"},
		"h3": {"class"},
		"h4": {"class"},
		"h5": {"class"},
		"h6": {"class"},
		"p": {"class"},
		"pre": {"class"},
		"code": {"class"},
	}

	def __init__(self) -> None:
		super().__init__(convert_charrefs=True)
		self._out: list[str] = []

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		if tag not in self.ALLOWED:
			return
		allowed = self.ALLOWED_ATTRS.get(tag, set())
		parts = [tag]
		for k, v in attrs:
			if k in allowed and v is not None:
				if k in ("href", "src") and v.strip().lower().startswith("javascript:"):
					continue
				parts.append(f'{k}="{html.escape(v, quote=True)}"')
		self._out.append("<" + " ".join(parts) + ">")

	def handle_endtag(self, tag: str) -> None:
		if tag in self.ALLOWED and tag not in ("br", "img"):
			self._out.append(f"</{tag}>")

	def handle_data(self, data: str) -> None:
		self._out.append(html.escape(data))

	def handle_entityref(self, name: str) -> None:
		self._out.append(f"&{name};")

	def handle_charref(self, name: str) -> None:
		self._out.append(f"&#{name};")

	def result(self) -> str:
		return "".join(self._out)


def sanitize_preview_html(raw: str) -> str:
	"""Sanitize HTML to the preview allow-list."""
	parser = _PreviewHTMLSanitizer()
	try:
		parser.feed(raw)
		parser.close()
	except (ValueError, TypeError, AssertionError):
		return html.escape(raw)
	return parser.result()


def excerpt_html(section_md: str, page_url: str, site_base: str) -> str:
	"""Build a sanitized rich HTML excerpt from section markdown."""
	raw = _markdown_blocks_to_html(section_md, page_url, site_base)
	return sanitize_preview_html(raw)


class PreviewBuilder:
	"""Build ``previews.json`` payloads from documentation pages."""

	def __init__(self, preview_config: dict[str, Any], *, site_base: str = "/"):
		self.config = preview_config
		self.site_base = site_base if site_base.endswith("/") else site_base + "/"
		self.mode = preview_config.get("mode", "summary")
		self.max_chars = int(preview_config.get("max_chars", 200))
		self.include_fragments = bool(preview_config.get("include_fragments", True))
		self.scope = preview_config.get("scope", "linked_only")
		self.data: dict[str, dict[str, Any]] = {}

	def _page_key(self, page_url: str, fragment: str = "") -> str:
		url = page_url.lstrip("/")
		if fragment:
			return f"{url}#{fragment}"
		return url

	def __call__(self, files: Files) -> dict[str, dict[str, Any]]:
		"""Scan files and return the preview mapping."""
		logger.info("Building link previews...")
		docs = [f for f in files.documentation_pages() if f.page]
		known = {f.src_path for f in docs}
		src_to_file = {f.src_path: f for f in docs}

		# Collect which pages (and fragments) are linked-to when scoped.
		linked: set[str] = set()
		linked_fragments: set[tuple[str, str]] = set()
		if self.scope == "linked_only":
			for f in docs:
				try:
					text = Path(f.abs_src_path).read_text(encoding="utf-8")
				except OSError:
					continue
				for target_src, frag in find_link_targets(text, f.src_path, known):
					linked.add(target_src)
					if frag:
						linked_fragments.add((target_src, frag))
			targets = [src_to_file[s] for s in linked if s in src_to_file]
		else:
			targets = docs
			linked_fragments = set()
			# Still collect fragments referenced for include_fragments
			if self.include_fragments:
				for f in docs:
					try:
						text = Path(f.abs_src_path).read_text(encoding="utf-8")
					except OSError:
						continue
					for target_src, frag in find_link_targets(text, f.src_path, known):
						if frag:
							linked_fragments.add((target_src, frag))

		for f in targets:
			self._add_page(f, linked_fragments)

		logger.info(f"Created {len(self.data)} preview entries")
		return self.data

	def _add_page(self, f, linked_fragments: set[tuple[str, str]]) -> None:
		try:
			raw = Path(f.abs_src_path).read_text(encoding="utf-8")
		except OSError as e:
			logger.warning(f"Cannot read {f.abs_src_path}: {e}")
			return

		meta, body = parse_frontmatter(raw)
		if meta.get("preview") is False:
			return

		page_url = f.url  # e.g. notes/foo/
		title = extract_title_from_page(
			meta,
			body,
			fallback=f.page.title if f.page and f.page.title else f.name,
		)
		summary = extract_summary(meta, body, self.max_chars)
		preview_image = meta.get("preview_image") or meta.get("image")
		if not isinstance(preview_image, str):
			preview_image = None
		elif preview_image:
			preview_image = _rewrite_url(preview_image, page_url, self.site_base)

		entry: dict[str, Any] = {
			"title": title,
			"summary": summary,
		}
		if preview_image:
			entry["image"] = preview_image

		# Page-level entry (summary mode and excerpt fallback)
		key = self._page_key(page_url)
		page_entry = dict(entry)

		if self.mode == "excerpt":
			sections = _split_sections(body)
			# Lead / whole-page excerpt
			lead_md = next((s[2] for s in sections if not s[0]), body)
			page_entry["excerpt"] = excerpt_plain(lead_md, self.max_chars)
			page_entry["html"] = excerpt_html(lead_md, page_url, self.site_base)

		self.data[key] = page_entry

		if not self.include_fragments or self.mode != "excerpt":
			# Still emit fragment keys with page summary if fragments requested
			# in summary mode for lookup convenience? Issue: fragment-aware only
			# in excerpt mode. Skip unless excerpt.
			return

		sections = {sid: (text, md) for sid, text, md in _split_sections(body) if sid}
		# Emit all sections when scope=all; when linked_only only linked frags
		frag_ids: set[str]
		if self.scope == "linked_only":
			frag_ids = {frag for src, frag in linked_fragments if src == f.src_path}
		else:
			frag_ids = set(sections.keys())

		for frag in frag_ids:
			if frag not in sections:
				continue
			heading_text, section_md = sections[frag]
			frag_entry: dict[str, Any] = {
				"title": f"{title} · {heading_text}",
				"summary": excerpt_plain(section_md, self.max_chars) or summary,
				"excerpt": excerpt_plain(section_md, self.max_chars),
				"html": excerpt_html(section_md, page_url, self.site_base),
			}
			if preview_image:
				frag_entry["image"] = preview_image
			self.data[self._page_key(page_url, frag)] = frag_entry


def _base_path_from_config(config: MkDocsConfig) -> str:
	site_url = config.get("site_url")
	if site_url:
		base_path = urlparse(site_url).path
		if not base_path.endswith("/"):
			base_path += "/"
		return base_path
	return "/"


def add_preview_static_resources(config: MkDocsConfig) -> None:
	"""Register preview JS/CSS on the MkDocs config (call only when enabled)."""
	if "js/preview.js" not in config["extra_javascript"]:
		config["extra_javascript"].append("js/preview.js")
	if "css/preview.css" not in config["extra_css"]:
		config["extra_css"].append("css/preview.css")


def inject_preview_script(
	output: str,
	config: MkDocsConfig,
	preview_config: dict[str, Any],
	*,
	graph_enabled: bool = False,
) -> str:
	"""Inject ``window.preview_options`` before ``</body>``."""
	base_path = _base_path_from_config(config)
	options = {
		"base_path": base_path,
		"mode": preview_config.get("mode", "summary"),
		"delay_ms": int(preview_config.get("delay_ms", 300)),
		"mobile": bool(preview_config.get("mobile", False)),
		"graph_enabled": graph_enabled,
	}
	payload = json.dumps(options)
	options_script = f"<script>window.preview_options = {payload};</script>"
	if "</body>" in output:
		return output.replace("</body>", f"{options_script}</body>")
	return output


def copy_preview_static_assets(static_dir: str, config: MkDocsConfig) -> None:
	"""Copy preview.js / preview.css into the site directory."""
	js_output_dir = os.path.join(config["site_dir"], "js")
	os.makedirs(js_output_dir, exist_ok=True)
	shutil.copy(os.path.join(static_dir, "preview.js"), js_output_dir)

	css_output_dir = os.path.join(config["site_dir"], "css")
	os.makedirs(css_output_dir, exist_ok=True)
	shutil.copy(os.path.join(static_dir, "preview.css"), css_output_dir)


def write_previews_file(
	data: dict[str, dict[str, Any]],
	config: MkDocsConfig,
) -> None:
	"""Write ``site/previews/previews.json``."""
	output_dir = os.path.join(config["site_dir"], "previews")
	os.makedirs(output_dir, exist_ok=True)
	path = os.path.join(output_dir, "previews.json")
	with open(path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False)
	logger.info(f"Wrote previews to {path}")
