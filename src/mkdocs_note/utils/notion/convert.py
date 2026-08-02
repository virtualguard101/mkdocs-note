"""Markdown / notebook → Notion Enhanced Markdown conversion.

Pure conversion helpers with no network I/O. Callers pass ``docs_root`` for
path resolution instead of relying on a global docs directory.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import quote

from mkdocs_note.utils.meta import extract_tags, parse_frontmatter
from mkdocs_note.utils.tree import docs_rel, title_from_path

# Re-export for callers that previously imported extract_tags from convert.
__all__ = [
	"ADMONITION_STYLES",
	"ASSET_SUFFIXES",
	"CONTENT_TYPES",
	"convert_markdown_file",
	"extract_tags",
	"md_references_asset",
	"page_has_local_images",
]

ADMONITION_STYLES: dict[str, tuple[str, str]] = {
	"note": ("blue_bg", "✒️️"),
	"abstract": ("gray_bg", "📋"),
	"info": ("blue_bg", "ℹ️"),
	"tip": ("yellow_bg", "💡"),
	"success": ("green_bg", "✅"),
	"question": ("purple_bg", "❓"),
	"warning": ("orange_bg", "⚠️"),
	"failure": ("red_bg", "❌"),
	"danger": ("red_bg", "⛔"),
	"bug": ("red_bg", "🐛"),
	"example": ("gray_bg", "🧪"),
	"quote": ("gray_bg", "💬"),
	"important": ("orange_bg", "⚠️"),
	"review": ("green_bg", "🔍"),
}

CONTENT_TYPES = {
	".jpg": "image/jpeg",
	".jpeg": "image/jpeg",
	".png": "image/png",
	".gif": "image/gif",
	".webp": "image/webp",
	".awebp": "image/webp",
	".svg": "image/svg+xml",
	".bmp": "image/bmp",
	".tif": "image/tiff",
	".tiff": "image/tiff",
}

ASSET_SUFFIXES = set(CONTENT_TYPES) | {".pdf", ".mp4", ".webm", ".svg"}


def strip_duplicate_h1(title: str, body: str) -> str:
	"""Remove a leading H1 that duplicates the page title."""
	lines = body.splitlines()
	if not lines:
		return body
	first = lines[0].strip()
	if first.startswith("# "):
		h1 = first[2:].strip()
		if h1 == title or h1 in title or title in h1:
			return "\n".join(lines[1:]).lstrip("\n")
	return body


def collect_indented_block(
	lines: list[str], start: int, indent: int
) -> tuple[list[str], int]:
	"""Collect consecutive lines indented at least ``indent`` spaces."""
	collected: list[str] = []
	i = start
	while i < len(lines):
		line = lines[i]
		if line.strip() == "":
			collected.append("")
			i += 1
			continue
		leading = len(line) - len(line.lstrip(" "))
		# Also accept tabs as indent units (rare in these notes).
		if leading < indent and not line.startswith("\t" * (indent // 4 or 1)):
			# Allow tab-indented content roughly equivalent to spaces.
			if line.startswith("\t"):
				tab_count = len(line) - len(line.lstrip("\t"))
				if tab_count * 4 < indent:
					break
				collected.append(line[tab_count:])
				i += 1
				continue
			break
		collected.append(line[indent:] if leading >= indent else line.lstrip(" "))
		i += 1
	return collected, i


def notion_indent_block(text: str, tabs: int = 1) -> str:
	"""Indent block children for Notion; keep blank lines indented so nesting holds."""
	prefix = "\t" * tabs
	out: list[str] = []
	for line in text.splitlines():
		if line.strip() == "":
			out.append(f"{prefix}<empty-block/>")
		else:
			out.append(prefix + line)
	return "\n".join(out)


_ADMON_LINE_RE = re.compile(
	r"^(?P<indent>[ \t]*)"
	r"(?P<markers>[!?]{3})(?P<expanded>\+?)"
	r"\s*(?P<type>\w+)"
	r"(?P<rest>.*?)\s*$"
)
_ADMON_INLINE_RE = re.compile(r"\binline(?:\s+end)?\b", re.IGNORECASE)
_ADMON_TITLE_RE = re.compile(r'"([^"]*)"')


def _parse_admonition_rest(rest: str) -> tuple[str | None, bool]:
	"""Parse optional inline flag + quoted title from the remainder of an admonition header."""
	rest = rest.strip()
	if not rest:
		return None, False
	inline = bool(_ADMON_INLINE_RE.search(rest))
	# Strip inline markers before / after title.
	cleaned = _ADMON_INLINE_RE.sub(" ", rest)
	cleaned = re.sub(r"\s+", " ", cleaned).strip()
	title_match = _ADMON_TITLE_RE.search(cleaned)
	title = title_match.group(1) if title_match else None
	return title, inline


def convert_admonitions_and_tabs(text: str) -> str:
	"""Convert Material admonitions and content tabs to Notion markup."""
	lines = text.splitlines()
	out: list[str] = []
	i = 0
	tab_re = re.compile(r'^([ \t]*)===\s+"([^"]+)"\s*$')

	while i < len(lines):
		line = lines[i]
		ad_match = _ADMON_LINE_RE.match(line)
		if ad_match:
			indent_ws = ad_match.group("indent") or ""
			indent = len(indent_ws.replace("\t", "    "))
			markers = ad_match.group("markers")
			ad_type = ad_match.group("type")
			title, _inline = _parse_admonition_rest(ad_match.group("rest") or "")
			# Material body is indented 4 spaces beyond the admonition marker line.
			body_indent = indent + 4
			block_lines, i = collect_indented_block(lines, i + 1, body_indent)
			inner = convert_admonitions_and_tabs("\n".join(block_lines).strip("\n"))
			if markers.startswith("?"):
				summary = title or ad_type.capitalize()
				block = (
					f"<details>\n<summary>{summary}</summary>\n"
					f"{notion_indent_block(inner)}\n</details>"
				)
			else:
				color, icon = ADMONITION_STYLES.get(ad_type, ("gray_bg", "📌"))
				# Inline admonitions have no Notion float equivalent → normal callout.
				header = f"**{title}**\n" if title else ""
				block = (
					f'<callout icon="{icon}" color="{color}">\n'
					f"{notion_indent_block(header + inner)}\n"
					"</callout>"
				)
			out.append(block)
			continue

		tab_match = tab_re.match(line)
		if tab_match:
			label = tab_match.group(2)
			indent_ws = tab_match.group(1) or ""
			indent = len(indent_ws.replace("\t", "    "))
			block_lines, i = collect_indented_block(lines, i + 1, indent + 4)
			inner = convert_admonitions_and_tabs("\n".join(block_lines).strip("\n"))
			out.append(f"### {label}")
			out.append(inner)
			continue

		out.append(line)
		i += 1

	return "\n".join(out)


def convert_inline_math(text: str) -> str:
	"""Adapt KaTeX-style math delimiters for Notion."""

	def repl_block(match: re.Match[str]) -> str:
		return f"$`{match.group(1).strip()}`$"

	text = re.sub(r"\$\$([\s\S]+?)\$\$", lambda m: f"$${m.group(1)}$$", text)
	text = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)", repl_block, text)
	return text


def convert_html_blocks(text: str) -> str:
	"""Convert known HTML embeds and strip HTML comments."""
	text = re.sub(
		r'<div\s+class="responsive-video-container">\s*'
		r'<iframe[^>]+src="([^"]+)"[^>]*>\s*</iframe>\s*</div>',
		lambda m: f'<video src="{m.group(1)}">Video</video>',
		text,
		flags=re.IGNORECASE | re.DOTALL,
	)
	text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
	return text


def resolve_local_asset_path(
	raw: str, source_file: Path, docs_root: Path
) -> Path | None:
	"""Resolve a relative or site-absolute asset path under ``docs_root``."""
	raw = raw.strip()
	if not raw or raw.startswith(("http://", "https://")):
		return None
	if raw.startswith("/"):
		candidate = (docs_root / raw.lstrip("/")).resolve()
	else:
		candidate = (source_file.parent / raw).resolve()
	try:
		candidate.relative_to(docs_root.resolve())
	except ValueError:
		return None
	return candidate if candidate.exists() else None


def resolve_image_url(
	raw: str, source_file: Path, site_url: str, docs_root: Path
) -> str:
	"""Build an absolute site URL for an image reference."""
	raw = raw.strip()
	if raw.startswith(("http://", "https://")):
		return raw
	if raw.startswith("/"):
		rel = docs_rel(raw.lstrip("/"))
	else:
		candidate = resolve_local_asset_path(raw, source_file, docs_root)
		if candidate is not None:
			rel = docs_rel(str(candidate.relative_to(docs_root)))
		else:
			rel = docs_rel(
				str((source_file.parent / raw).resolve().relative_to(docs_root))
			)
	encoded = "/".join(quote(part, safe="") for part in rel.split("/"))
	return f"{site_url.rstrip('/')}/{encoded}"


def resolve_internal_target(raw: str, source_file: Path, docs_root: Path) -> str:
	"""Resolve an internal markdown link to a docs-relative path."""
	target = raw.split("#", 1)[0].strip()
	if not target:
		return ""
	if target.startswith("/"):
		resolved = (docs_root / target.lstrip("/")).resolve()
	else:
		resolved = (source_file.parent / target).resolve()
	try:
		rel = docs_rel(str(resolved.relative_to(docs_root)))
	except ValueError:
		return target
	if rel.endswith(".ipynb"):
		rel = rel[:-6] + ".md"
	return rel


def convert_images(
	text: str,
	source_file: Path,
	site_url: str,
	docs_root: Path,
	upload_local: Callable[[Path], Any] | None = None,
) -> str:
	"""Rewrite image markdown; optionally upload local files via ``upload_local``."""

	def repl(match: re.Match[str]) -> str:
		alt = match.group(1) or ""
		src = match.group(2).strip()
		if upload_local is not None and not src.startswith(("http://", "https://")):
			local = resolve_local_asset_path(src, source_file, docs_root)
			if local is not None:
				uploaded = upload_local(local)
				if uploaded:
					if str(uploaded).startswith("file-upload://"):
						return f'<image src="{uploaded}">{alt}</image>'
					return f"\n\n{uploaded}\n\n"
		url = resolve_image_url(src, source_file, site_url, docs_root)
		return f"![{alt}]({url})"

	return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, text)


def convert_links(
	text: str,
	source_file: Path,
	page_map: dict[str, dict[str, str]],
	docs_root: Path,
) -> str:
	"""Rewrite internal links to Notion ``mention-page`` when mapped."""

	def repl(match: re.Match[str]) -> str:
		label = match.group(1)
		raw = match.group(2)
		if raw.startswith(("http://", "https://")):
			return match.group(0)
		anchor = ""
		if "#" in raw:
			path_part, anchor = raw.split("#", 1)
		else:
			path_part = raw
		if not path_part:
			return match.group(0)
		rel = resolve_internal_target(path_part, source_file, docs_root)
		if rel in page_map and page_map[rel].get("url"):
			url = page_map[rel]["url"]
			if anchor:
				url = f"{url}#{anchor}"
			return f'<mention-page url="{url}">{label}</mention-page>'
		return f"[{label}]({raw})"

	return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)


def ipynb_to_markdown(path: Path) -> tuple[dict[str, Any], str]:
	"""Convert a Jupyter notebook to markdown (cells only; no raw JSON)."""
	data = json.loads(path.read_text(encoding="utf-8"))
	meta: dict[str, Any] = {}
	nb_meta = data.get("metadata") or {}
	# Prefer explicit title from notebook metadata when present.
	if isinstance(nb_meta.get("title"), str):
		meta["title"] = nb_meta["title"]

	parts: list[str] = []
	for cell in data.get("cells") or []:
		ctype = cell.get("cell_type")
		source = cell.get("source") or []
		if isinstance(source, list):
			text = "".join(source)
		else:
			text = str(source)
		text = text.rstrip("\n")
		if not text.strip():
			continue
		if ctype == "markdown":
			parts.append(text)
		elif ctype == "code":
			lang = ""
			kernelspec = nb_meta.get("kernelspec") or {}
			language = kernelspec.get("language") or ""
			if language:
				lang = str(language)
			else:
				lang = "python"
			parts.append(f"```{lang}\n{text}\n```")
			# Include plain-text / stream outputs when useful.
			outputs = cell.get("outputs") or []
			out_chunks: list[str] = []
			for out in outputs:
				otype = out.get("output_type")
				if otype == "stream":
					text_out = out.get("text") or ""
					if isinstance(text_out, list):
						text_out = "".join(text_out)
					if str(text_out).strip():
						out_chunks.append(str(text_out).rstrip())
				elif otype in ("execute_result", "display_data"):
					data_out = out.get("data") or {}
					if "text/plain" in data_out:
						plain = data_out["text/plain"]
						if isinstance(plain, list):
							plain = "".join(plain)
						if str(plain).strip():
							out_chunks.append(str(plain).rstrip())
					elif "text/markdown" in data_out:
						md = data_out["text/markdown"]
						if isinstance(md, list):
							md = "".join(md)
						if str(md).strip():
							out_chunks.append(str(md).rstrip())
			if out_chunks:
				parts.append("```\n" + "\n".join(out_chunks) + "\n```")
		# skip raw cells
	body = "\n\n".join(parts).strip() + "\n"
	return meta, body


def normalize_blockquotes_for_notion(text: str) -> str:
	"""Drop MkDocs blank quote markers (`>` alone) and collapse quote runs for Notion.

	In MkDocs/Material, a lone `>` between quote lines acts as a paragraph/line break
	and does not render as an empty citation. Notion treats that line as an empty
	quote block. Convert each contiguous `>` run into a single Notion multi-line
	quote using ``<br>``, omitting blank quote lines.
	"""
	lines = text.splitlines()
	out: list[str] = []
	i = 0
	quote_re = re.compile(r"^([ \t]*)>([ \t]?)(.*)$")
	fence_re = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")

	while i < len(lines):
		line = lines[i]
		fence = fence_re.match(line)
		if fence:
			marker = fence.group(2)
			ch = marker[0]
			n = len(marker)
			out.append(line)
			i += 1
			while i < len(lines):
				out.append(lines[i])
				close = fence_re.match(lines[i])
				if (
					close
					and close.group(2)[0] == ch
					and len(close.group(2)) >= n
					and close.group(3).strip() == ""
				):
					i += 1
					break
				i += 1
			continue

		m = quote_re.match(line)
		if not m:
			out.append(line)
			i += 1
			continue

		indent = m.group(1)
		parts: list[str] = []
		while i < len(lines):
			qm = quote_re.match(lines[i])
			if not qm or qm.group(1) != indent:
				break
			body = qm.group(3)
			# Lone `>` / `> ` → MkDocs line break; skip for Notion.
			if body.strip() == "":
				i += 1
				continue
			parts.append(body)
			i += 1

		if not parts:
			continue
		# Notion multi-line quote: one `>` line with <br> separators.
		out.append(f"{indent}> {'<br>'.join(parts)}")

	return "\n".join(out)


_TABLE_SEP_CELL_RE = re.compile(r"^:?-+:?$")
_FENCE_LINE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")


def is_gfm_table_separator_row(line: str) -> bool:
	"""True for GFM alignment rows like ``|:-:|``, ``|:-|``, ``|-:|``, ``| --- | :---: |``."""
	s = line.strip()
	if "|" not in s:
		return False
	core = s.removeprefix("|")
	core = core.removesuffix("|")
	cells = core.split("|")
	if not cells:
		return False
	for cell in cells:
		if not _TABLE_SEP_CELL_RE.fullmatch(cell.strip()):
			return False
	return True


def strip_gfm_table_separators(text: str) -> str:
	"""Drop GFM table alignment rows so Notion does not insert them as data rows.

	Markdown renderers ignore ``|:-:|`` / ``|:-|`` / ``|-:|`` separator lines; Notion's
	markdown ingest treats them as ordinary table rows.
	"""
	lines = text.splitlines()
	out: list[str] = []
	i = 0
	while i < len(lines):
		line = lines[i]
		fence = _FENCE_LINE_RE.match(line)
		if fence:
			marker = fence.group(2)
			ch = marker[0]
			n = len(marker)
			out.append(line)
			i += 1
			while i < len(lines):
				out.append(lines[i])
				close = _FENCE_LINE_RE.match(lines[i])
				if (
					close
					and close.group(2)[0] == ch
					and len(close.group(2)) >= n
					and close.group(3).strip() == ""
				):
					i += 1
					break
				i += 1
			continue
		if is_gfm_table_separator_row(line):
			i += 1
			continue
		out.append(line)
		i += 1
	return "\n".join(out)


def convert_markdown_file(
	file_path: Path,
	site_url: str,
	page_map: dict[str, dict[str, str]],
	docs_root: Path,
	upload_local: Callable[[Path], Any] | None = None,
) -> tuple[str, str, dict[str, Any]]:
	"""Convert a markdown or notebook file to Notion-ready markdown.

	Args:
	    file_path: Source ``.md`` or ``.ipynb`` path.
	    site_url: Public site base URL for absolute image links.
	    page_map: Docs-relative path → ``{"id", "url"}`` for mention links.
	    docs_root: Documentation root used for path resolution.
	    upload_local: Optional callback that accepts a local ``Path`` and returns
	        an upload token / placeholder string.

	Returns:
	    Tuple of ``(title, body, frontmatter_meta)``.
	"""
	if file_path.suffix.lower() == ".ipynb":
		meta, body = ipynb_to_markdown(file_path)
		title = str(meta.get("title") or title_from_path(file_path)).strip()
	else:
		raw = file_path.read_text(encoding="utf-8")
		meta, body = parse_frontmatter(raw)
		title = str(meta.get("title") or title_from_path(file_path)).strip()
		body = strip_duplicate_h1(title, body)

	body = convert_html_blocks(body)
	body = normalize_blockquotes_for_notion(body)
	body = convert_admonitions_and_tabs(body)
	body = convert_inline_math(body)
	body = convert_images(
		body, file_path, site_url, docs_root, upload_local=upload_local
	)
	body = convert_links(body, file_path, page_map, docs_root)
	body = strip_gfm_table_separators(body)
	body = re.sub(r"\n{3,}", "\n\n", body).strip()
	return title, body, meta


def page_has_local_images(source: Path) -> bool:
	"""Return True if the file contains any non-http(s) image references."""
	text = source.read_text(encoding="utf-8", errors="ignore")
	for _, src in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text):
		raw = src.strip()
		if not raw.startswith(("http://", "https://")):
			return True
	return False


def md_references_asset(source: Path, asset_rel: str, docs_root: Path) -> bool:
	"""Cheap check: whether markdown likely references a docs-relative asset."""
	text = source.read_text(encoding="utf-8", errors="ignore")
	name = Path(asset_rel).name
	if name not in text:
		return False
	for _, src in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text):
		local = resolve_local_asset_path(src.strip(), source, docs_root)
		if local is None:
			continue
		if docs_rel(str(local.relative_to(docs_root))) == asset_rel:
			return True
	return False
