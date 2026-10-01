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
from urllib.parse import unquote, urljoin, urlparse

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
	"""Extract the first non-empty prose paragraph from markdown body.

	Skips ATX headings, blockquotes, tables, lists, and Material admonition /
	details / tab markers (``!!!``, ``???``, ``===``) plus their indented bodies.
	"""
	# Drop fenced code blocks so we don't preview code as summary.
	without_code = _CODE_FENCE_BLOCK_RE.sub("", body)
	chunks: list[str] = []
	buf: list[str] = []
	skip_indented_block = False
	for line in without_code.splitlines():
		stripped = line.strip()
		if not stripped:
			if buf:
				chunks.append(" ".join(buf))
				buf = []
			skip_indented_block = False
			continue
		# Admonition / details / tab openers and indented continuation lines.
		if stripped.startswith(("!!!", "???", "===")):
			if buf:
				chunks.append(" ".join(buf))
				buf = []
			skip_indented_block = True
			continue
		if skip_indented_block and line.startswith(("    ", "\t")):
			continue
		skip_indented_block = False
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
		if plain and not plain.startswith(("!!!", "???", "===")):
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

	A section runs until the next heading of the **same or higher** level so
	parent headings include nested subsection markdown.
	"""
	matches = list(_HEADING_RE.finditer(body))
	if not matches:
		return [("", "", body)]

	sections: list[tuple[str, str, str]] = []
	lead = body[: matches[0].start()]
	if lead.strip():
		sections.append(("", "", lead))

	for i, match in enumerate(matches):
		level = len(match.group(1))
		heading_text = strip_markdown_inline(match.group(2))
		heading_id = slugify_heading(heading_text)
		start = match.end()
		end = len(body)
		for j in range(i + 1, len(matches)):
			if len(matches[j].group(1)) <= level:
				end = matches[j].start()
				break
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


def _section_has_prose(section_md: str) -> bool:
	"""Return True if section markdown has extractable prose (not only headings)."""
	return bool(excerpt_plain(section_md, 10_000).strip())


def resolve_section_markdown(
	sections: dict[str, tuple[str, str]],
	frag: str,
) -> tuple[str, str]:
	"""Return ``(heading_text, section_md)`` for a fragment.

	If the section has no extractable prose, descend into the first nested
	child with content; otherwise return the hierarchical section body (which
	already includes nested headings when split with same-or-higher rules).
	"""
	if frag not in sections:
		return "", ""
	heading_text, section_md = sections[frag]
	if _section_has_prose(section_md):
		return heading_text, section_md
	nested = _split_sections(section_md)
	for sid, _child_text, child_md in nested:
		if not sid:
			continue
		if _section_has_prose(child_md):
			return heading_text, child_md
	# Keep hierarchical body even if prose extractor is empty (e.g. only code).
	return heading_text, section_md


def _rewrite_url(
	url: str,
	page_url: str,
	site_base: str,
	*,
	source_file: Any | None = None,
	files: Any | None = None,
) -> str:
	"""Rewrite relative asset URLs for preview HTML.

	Resolution order:
	1. Absolute / scheme / data / mailto — unchanged (CDN-friendly).
	2. MkDocs ``Files`` lookup from the source markdown directory (primary).
	3. Directory-URL parent of ``page_url`` (fallback B).
	4. Source-parent path mapped under ``site_base`` (fallback A).
	"""
	if not url or url.startswith(("#", "mailto:", "data:", "javascript:")):
		return url
	parsed = urlparse(url)
	if parsed.scheme or parsed.netloc:
		return url
	if url.startswith("//"):
		return url
	if url.startswith("/"):
		return urljoin(site_base, url.lstrip("/"))

	# C: Files API from source file directory
	resolved = _resolve_url_via_files(url, source_file, files)
	if resolved is not None:
		return urljoin(site_base, resolved.lstrip("/"))

	# B: dirname of directory-style page URL
	page = (page_url or "").strip()
	if page.endswith("/"):
		parent = page.rstrip("/")
		parent_dir = parent.rsplit("/", 1)[0] + "/" if "/" in parent else ""
		return urljoin(urljoin(site_base, parent_dir), url)

	# A / default: source parent dir → site_base, else classic page_dir join
	if source_file is not None:
		src = getattr(source_file, "src_path", None) or getattr(
			source_file, "src_uri", ""
		)
		src = str(src).replace("\\", "/")
		parent_src = src.rsplit("/", 1)[0] if "/" in src else ""
		# Drop .md stem folder assumption: assets live beside the .md file
		candidate = os.path.normpath(os.path.join(parent_src, url)).replace("\\", "/")
		# Map docs-relative path to URL-ish path (strip .md files only)
		if not candidate.endswith(".md"):
			return urljoin(site_base, candidate.lstrip("/"))

	page_dir = ""
	if page:
		page_dir = page if page.endswith("/") else page.rsplit("/", 1)[0] + "/"
	return urljoin(urljoin(site_base, page_dir), url)


def _resolve_url_via_files(
	rel_url: str,
	source_file: Any | None,
	files: Any | None,
) -> str | None:
	"""Return MkDocs file.url for a relative asset, or None if not found."""
	if source_file is None or files is None:
		return None
	src = getattr(source_file, "src_path", None) or getattr(
		source_file, "src_uri", None
	)
	if not src:
		return None
	src = str(src).replace("\\", "/")
	base = src.rsplit("/", 1)[0] if "/" in src else ""
	target = os.path.normpath(os.path.join(base, rel_url)).replace("\\", "/")
	# Try Files.get_file_from_path when available
	getter = getattr(files, "get_file_from_path", None)
	if callable(getter):
		found = getter(target)
		if found is not None and getattr(found, "url", None):
			return str(found.url)
	# Fallback: linear scan
	try:
		iterable = list(files)
	except TypeError:
		iterable = []
		doc_pages = getattr(files, "documentation_pages", None)
		if callable(doc_pages):
			iterable = list(doc_pages())
	for f in iterable:
		fpath = getattr(f, "src_path", None) or getattr(f, "src_uri", "")
		if str(fpath).replace("\\", "/") == target and getattr(f, "url", None):
			return str(f.url)
	return None


def _rewrite_html_urls(
	raw_html: str,
	page_url: str,
	site_base: str,
	*,
	source_file: Any | None = None,
	files: Any | None = None,
) -> str:
	"""Rewrite relative ``href`` / ``src`` values in an HTML fragment."""

	def repl(match: re.Match[str]) -> str:
		attr = match.group("attr")
		quote = match.group("quote")
		url = match.group("url")
		rewritten = _rewrite_url(
			url,
			page_url,
			site_base,
			source_file=source_file,
			files=files,
		)
		return f"{attr}={quote}{html.escape(rewritten, quote=True)}{quote}"

	return re.sub(
		r'(?P<attr>href|src)=(?P<quote>["\'])(?P<url>.*?)(?P=quote)',
		repl,
		raw_html,
		flags=re.IGNORECASE,
	)


# Extensions that are noisy or unsafe inside a hover card payload.
_PREVIEW_SKIP_EXTENSIONS: frozenset[str] = frozenset(
	{
		"toc",
		"pymdownx.snippets",
	},
)

# Plugin-owned markdown extensions that cannot be reconstructed outside MkDocs page render.
_PREVIEW_SKIP_PREFIXES: tuple[str, ...] = (
	"mkdocstrings",
	"Mkdocstrings",
)

_FALLBACK_EXTENSIONS: tuple[str, ...] = ("tables", "fenced_code", "sane_lists")


def _normalize_extension_name(ext: Any) -> str | None:
	"""Return a stable extension name string, or ``None`` if unknown."""
	if isinstance(ext, str):
		return ext
	# Some loaders pass extension instances.
	name = getattr(ext, "__name__", None) or getattr(type(ext), "__name__", None)
	module = getattr(ext, "__module__", None) or getattr(type(ext), "__module__", None)
	if module and name:
		return f"{module}.{name}" if "." not in name else name
	return str(name) if name else None


def _is_preview_safe_extension(name: str) -> bool:
	"""Return whether an extension name is safe to load for previews."""
	if name in _PREVIEW_SKIP_EXTENSIONS:
		return False
	lower = name.lower()
	return not any(
		lower.startswith(p.lower()) or p.lower() in lower
		for p in _PREVIEW_SKIP_PREFIXES
	)


def prepare_preview_markdown_config(
	markdown_extensions: Any = None,
	mdx_configs: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
	"""Filter site markdown extensions for hover-preview rendering.

	Reuses the MkDocs/Material extension stack where practical, but drops
	``toc`` (permalink clutter), ``pymdownx.snippets`` (arbitrary includes),
	and plugin-only extensions such as mkdocstrings.
	"""
	raw_exts: list[Any] = list(markdown_extensions or [])
	configs = dict(mdx_configs or {})
	kept: list[str] = []
	kept_names: set[str] = set()
	for ext in raw_exts:
		name = _normalize_extension_name(ext)
		if name is None or not _is_preview_safe_extension(name):
			if name:
				configs.pop(name, None)
			continue
		kept.append(name)
		kept_names.add(name)

	if not kept:
		kept = list(_FALLBACK_EXTENSIONS)
		kept_names = set(kept)
	else:
		has_superfences = "pymdownx.superfences" in kept_names
		for required in _FALLBACK_EXTENSIONS:
			if required in kept_names:
				continue
			if required == "fenced_code" and has_superfences:
				continue
			kept.append(required)
			kept_names.add(required)

	configs = {k: v for k, v in configs.items() if k in kept_names}
	return kept, configs


def create_preview_markdown(
	markdown_extensions: Any = None,
	mdx_configs: dict[str, Any] | None = None,
):
	"""Create a Python-Markdown instance aligned with the site config.

	Loads extensions incrementally so one broken/plugin-only extension cannot
	force a full fallback to the basic set.
	"""
	import markdown

	exts, configs = prepare_preview_markdown_config(markdown_extensions, mdx_configs)
	working: list[str] = list(_FALLBACK_EXTENSIONS)
	md = markdown.Markdown(extensions=working)

	for ext in exts:
		if ext in working:
			continue
		trial = [*working, ext]
		trial_configs = {k: configs[k] for k in trial if k in configs}
		try:
			md = markdown.Markdown(extensions=trial, extension_configs=trial_configs)
		except (
			ImportError,
			ValueError,
			TypeError,
			AttributeError,
			KeyError,
			OSError,
		) as exc:
			logger.debug("Skipping markdown extension %s for preview: %s", ext, exc)
			continue
		working = trial

	if working != list(_FALLBACK_EXTENSIONS):
		logger.info(
			"Preview markdown extensions: %s",
			", ".join(working),
		)
	return md


class _PreviewHTMLSanitizer(HTMLParser):
	"""Whitelist sanitizer for preview HTML snippets (Material-friendly)."""

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
		"hr",
		"ul",
		"ol",
		"li",
		"strong",
		"em",
		"b",
		"i",
		"blockquote",
		"table",
		"thead",
		"tbody",
		"tr",
		"th",
		"td",
		"div",
		"span",
		"details",
		"summary",
		"kbd",
		"mark",
		"ins",
		"del",
		"sub",
		"sup",
		"abbr",
		"input",
		"label",
	}
	# Attributes allowed on any permitted tag (Material relies heavily on class).
	_GLOBAL_ATTRS: ClassVar[set[str]] = {"class", "id", "title"}
	ALLOWED_ATTRS: ClassVar[dict[str, set[str]]] = {
		"a": {"href", "rel", "target"},
		"img": {"src", "alt", "loading", "width", "height"},
		"th": {"align", "colspan", "rowspan"},
		"td": {"align", "colspan", "rowspan"},
		"input": {"type", "name", "checked"},
		"label": {"for"},
		"div": {"data-tabs"},
		"abbr": {},
		"details": {"open"},
	}
	_SKIP_CONTENT: ClassVar[set[str]] = {"script", "style", "iframe", "object", "embed"}
	_VOID: ClassVar[set[str]] = {"br", "img", "hr", "input"}

	def __init__(self) -> None:
		super().__init__(convert_charrefs=True)
		self._out: list[str] = []
		self._skip_depth = 0

	def _allowed_attrs_for(self, tag: str) -> set[str]:
		return self._GLOBAL_ATTRS | self.ALLOWED_ATTRS.get(tag, set())

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		if tag in self._SKIP_CONTENT:
			self._skip_depth += 1
			return
		if self._skip_depth or tag not in self.ALLOWED:
			return
		# Only radio inputs (Material tabbed sets); drop other input types.
		if tag == "input":
			attr_map = {k: v for k, v in attrs}
			if attr_map.get("type", "").lower() not in {"radio", "checkbox"}:
				return
		allowed = self._allowed_attrs_for(tag)
		parts = [tag]
		for k, v in attrs:
			if k.startswith("data-") and k in allowed:
				pass
			elif k not in allowed:
				# Allow data-* on tab containers only when listed; skip others.
				continue
			if (
				k in ("href", "src")
				and v is not None
				and v.strip()
				.lower()
				.startswith(
					"javascript:",
				)
			):
				continue
			if v is None:
				parts.append(k)
			else:
				parts.append(f'{k}="{html.escape(v, quote=True)}"')
		self._out.append("<" + " ".join(parts) + ">")

	def handle_endtag(self, tag: str) -> None:
		if tag in self._SKIP_CONTENT and self._skip_depth:
			self._skip_depth -= 1
			return
		if self._skip_depth:
			return
		if tag in self.ALLOWED and tag not in self._VOID:
			self._out.append(f"</{tag}>")

	def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		self.handle_starttag(tag, attrs)

	def handle_data(self, data: str) -> None:
		if self._skip_depth:
			return
		self._out.append(html.escape(data))

	def handle_entityref(self, name: str) -> None:
		if self._skip_depth:
			return
		self._out.append(f"&{name};")

	def handle_charref(self, name: str) -> None:
		if self._skip_depth:
			return
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


def excerpt_html(
	section_md: str,
	page_url: str,
	site_base: str,
	*,
	md: Any | None = None,
	markdown_extensions: Any = None,
	mdx_configs: dict[str, Any] | None = None,
	source_file: Any | None = None,
	files: Any | None = None,
) -> str:
	"""Build a sanitized rich HTML excerpt from section markdown.

	When ``md`` or site extension config is provided, rendering follows the
	MkDocs/Material markdown stack (minus unsafe/noisy extensions).
	"""
	converter = md
	if converter is None:
		converter = create_preview_markdown(markdown_extensions, mdx_configs)
	else:
		converter.reset()
	raw = converter.convert(section_md)
	raw = _rewrite_html_urls(
		raw,
		page_url,
		site_base,
		source_file=source_file,
		files=files,
	)
	return sanitize_preview_html(raw)


def decode_fragment(fragment: str) -> str:
	"""Normalize a URL fragment to decoded Unicode (no leading ``#``)."""
	frag = (fragment or "").lstrip("#")
	if not frag:
		return ""
	try:
		return unquote(frag)
	except (ValueError, TypeError):
		return frag


class PreviewBuilder:
	"""Build ``previews.json`` payloads from documentation pages."""

	def __init__(
		self,
		preview_config: dict[str, Any],
		*,
		site_base: str = "/",
		markdown_extensions: Any = None,
		mdx_configs: dict[str, Any] | None = None,
		extra_src_paths: set[str] | None = None,
		index_src_paths: set[str] | None = None,
		graph_src_paths: set[str] | None = None,
	):
		self.config = preview_config
		self.site_base = site_base if site_base.endswith("/") else site_base + "/"
		self.mode = preview_config.get("mode", "summary")
		self.max_chars = int(preview_config.get("max_chars", 200))
		self.include_fragments = bool(preview_config.get("include_fragments", True))
		self.scope = preview_config.get("scope", "linked_only")
		self.data: dict[str, dict[str, Any]] = {}
		self._md = create_preview_markdown(markdown_extensions, mdx_configs)
		self.extra_src_paths = set(extra_src_paths or ())
		self.index_src_paths = set(index_src_paths or ())
		self.graph_src_paths = set(graph_src_paths or ())
		self._files: Files | None = None

	def _normalize_page_url(self, page_url: str) -> str:
		"""Canonicalize MkDocs ``file.url`` for JSON keys.

		Percent-decodes path segments so keys match runtime decoded lookups
		(CJK directories etc.). Homepage ``""`` / ``.`` / ``./`` → empty string.
		"""
		url = (page_url or "").strip().lstrip("/")
		try:
			url = unquote(url)
		except (ValueError, TypeError):
			pass
		if url in {"", ".", "./"}:
			return ""
		if not url.endswith("/") and "." not in url.rsplit("/", 1)[-1]:
			url += "/"
		return url

	def _page_key(self, page_url: str, fragment: str = "") -> str:
		url = self._normalize_page_url(page_url)
		frag = decode_fragment(fragment)
		if frag:
			return f"{url}#{frag}" if url else f"#{frag}"
		return url

	def _html(self, section_md: str, page_url: str, source_file: Any = None) -> str:
		return excerpt_html(
			section_md,
			page_url,
			self.site_base,
			md=self._md,
			source_file=source_file,
			files=self._files,
		)

	def __call__(self, files: Files) -> dict[str, dict[str, Any]]:
		"""Scan files and return the preview mapping."""
		logger.info("Building link previews...")
		self._files = files
		docs = [f for f in files.documentation_pages() if f.page]
		known = {f.src_path for f in docs}
		src_to_file = {f.src_path: f for f in docs}

		linked: set[str] = set()
		linked_fragments: set[tuple[str, str]] = set()

		def _collect_from_file(f) -> None:
			try:
				text = Path(f.abs_src_path).read_text(encoding="utf-8")
			except OSError:
				return
			for target_src, frag in find_link_targets(text, f.src_path, known):
				linked.add(target_src)
				decoded = decode_fragment(frag)
				if decoded:
					linked_fragments.add((target_src, decoded))

		if self.scope == "linked_only":
			for f in docs:
				_collect_from_file(f)
			# Expand: recent notes, notes-index out-links, soft graph nodes
			linked |= {p for p in self.extra_src_paths if p in known}
			for idx_src in self.index_src_paths:
				idx_file = src_to_file.get(idx_src)
				if idx_file is not None:
					_collect_from_file(idx_file)
			linked |= {p for p in self.graph_src_paths if p in known}
			targets = [src_to_file[s] for s in linked if s in src_to_file]
		else:
			targets = docs
			if self.include_fragments:
				for f in docs:
					_collect_from_file(f)

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
			preview_image = _rewrite_url(
				preview_image,
				page_url,
				self.site_base,
				source_file=f,
				files=self._files,
			)

		entry: dict[str, Any] = {
			"title": title,
			"summary": summary,
		}
		if preview_image:
			entry["image"] = preview_image

		key = self._page_key(page_url)
		page_entry = dict(entry)

		if self.mode == "excerpt":
			sections_list = _split_sections(body)
			lead_md = next((s[2] for s in sections_list if not s[0]), body)
			page_entry["excerpt"] = excerpt_plain(lead_md, self.max_chars)
			page_entry["html"] = self._html(lead_md, page_url, source_file=f)

		self.data[key] = page_entry

		if not self.include_fragments or self.mode != "excerpt":
			return

		sections = {sid: (text, md) for sid, text, md in _split_sections(body) if sid}
		if self.scope == "linked_only":
			frag_ids = {
				decode_fragment(frag)
				for src, frag in linked_fragments
				if src == f.src_path
			}
		else:
			frag_ids = set(sections.keys())

		for frag in frag_ids:
			if not frag or frag not in sections:
				continue
			heading_text, section_md = resolve_section_markdown(sections, frag)
			plain = excerpt_plain(section_md, self.max_chars)
			html_body = self._html(section_md, page_url, source_file=f)
			frag_entry: dict[str, Any] = {
				"title": f"{title} · {heading_text}",
				"summary": plain or summary,
				"excerpt": plain,
				"html": html_body,
			}
			# Avoid misleading page summary when excerpt/html are empty
			if not plain and not (html_body or "").strip():
				frag_entry["summary"] = ""
				frag_entry["excerpt"] = ""
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
