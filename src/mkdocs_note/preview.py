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


def _rewrite_url(url: str, page_url: str, site_base: str) -> str:
	"""Rewrite relative asset URLs against the page and site base."""
	if not url or url.startswith(("#", "mailto:", "data:", "javascript:")):
		return url
	parsed = urlparse(url)
	if parsed.scheme or parsed.netloc:
		return url
	if url.startswith("/"):
		return urljoin(site_base, url.lstrip("/"))
	page_dir = page_url if page_url.endswith("/") else page_url.rsplit("/", 1)[0] + "/"
	return urljoin(urljoin(site_base, page_dir), url)


def _rewrite_html_urls(raw_html: str, page_url: str, site_base: str) -> str:
	"""Rewrite relative ``href`` / ``src`` values in an HTML fragment."""

	def repl(match: re.Match[str]) -> str:
		attr = match.group("attr")
		quote = match.group("quote")
		url = match.group("url")
		return (
			f"{attr}={quote}"
			f"{html.escape(_rewrite_url(url, page_url, site_base), quote=True)}"
			f"{quote}"
		)

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
	raw = _rewrite_html_urls(raw, page_url, site_base)
	return sanitize_preview_html(raw)


class PreviewBuilder:
	"""Build ``previews.json`` payloads from documentation pages."""

	def __init__(
		self,
		preview_config: dict[str, Any],
		*,
		site_base: str = "/",
		markdown_extensions: Any = None,
		mdx_configs: dict[str, Any] | None = None,
	):
		self.config = preview_config
		self.site_base = site_base if site_base.endswith("/") else site_base + "/"
		self.mode = preview_config.get("mode", "summary")
		self.max_chars = int(preview_config.get("max_chars", 200))
		self.include_fragments = bool(preview_config.get("include_fragments", True))
		self.scope = preview_config.get("scope", "linked_only")
		self.data: dict[str, dict[str, Any]] = {}
		self._md = create_preview_markdown(markdown_extensions, mdx_configs)

	def _normalize_page_url(self, page_url: str) -> str:
		"""Canonicalize MkDocs ``file.url`` for JSON keys.

		The site homepage is often ``""``, ``"."``, or ``"./`` — normalize to
		empty string so runtime lookups for ``/`` / site root resolve.
		"""
		url = (page_url or "").strip().lstrip("/")
		if url in {"", ".", "./"}:
			return ""
		if not url.endswith("/") and "." not in url.rsplit("/", 1)[-1]:
			url += "/"
		return url

	def _page_key(self, page_url: str, fragment: str = "") -> str:
		url = self._normalize_page_url(page_url)
		if fragment:
			return f"{url}#{fragment}" if url else f"#{fragment}"
		return url

	def _html(self, section_md: str, page_url: str) -> str:
		return excerpt_html(
			section_md,
			page_url,
			self.site_base,
			md=self._md,
		)

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
			page_entry["html"] = self._html(lead_md, page_url)

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
				"html": self._html(section_md, page_url),
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
