"""Shared markdown / wiki link normalization helpers.

Used by the network graph and same-site link hover preview so both features
speak the same URL dialect.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from urllib.parse import unquote, urlsplit

LINK_PATTERN = r"\[[^\]]+\]\((?P<url>.*?)\)|\[\[(?P<wikilink>[^\]]+)\]\]"


def unescape_url(url: str) -> str:
	"""Strip angle brackets and percent-decode a markdown link URL.

	Args:
	    url: Raw URL from a markdown or wiki link.

	Returns:
	    Decoded URL string.
	"""
	if url.startswith("<") and url.endswith(">"):
		url = url[1:-1]
	return unquote(url)


def normalize_link(match: re.Match[str]) -> str | None:
	"""Normalize a ``LINK_PATTERN`` match to a relative path (no query/fragment).

	Wikilinks without a ``.md`` suffix get ``.md`` appended. Query strings and
	fragments are dropped so callers can resolve page identity; use
	:func:`split_href` when the fragment is needed.

	Args:
	    match: Regex match from :data:`LINK_PATTERN`.

	Returns:
	    Normalized relative path, or ``None`` if the match has no URL.
	"""
	url = match.group("url") or match.group("wikilink")
	if not url:
		return None

	# Wikilink may be ``Page#heading`` — only the page part gets ``.md``.
	if match.group("wikilink"):
		page_part, _, _frag = url.partition("#")
		if not page_part.endswith(".md"):
			page_part += ".md"
		url = page_part
	else:
		url = urlsplit(unescape_url(url)).path
		return url or None

	return urlsplit(unescape_url(url)).path or None


def split_href(href: str) -> tuple[str, str]:
	"""Split an href into path and fragment (without ``#``).

	Args:
	    href: Link target, possibly with query/fragment.

	Returns:
	    ``(path, fragment)`` where fragment may be empty.
	"""
	href = unescape_url(href)
	parts = urlsplit(href)
	return parts.path, (parts.fragment or "")


def resolve_target_src(source_src_path: str, link_path: str) -> str:
	"""Resolve a relative link path against the source page ``src_path``.

	Args:
	    source_src_path: Source file path relative to docs (MkDocs ``src_path``).
	    link_path: Normalized link path from :func:`normalize_link`.

	Returns:
	    Normpath of the target ``src_path``.
	"""
	return os.path.normpath(os.path.join(os.path.dirname(source_src_path), link_path))


def iter_markdown_links(markdown: str) -> Iterator[tuple[str, str]]:
	"""Yield ``(path, fragment)`` for each markdown / wiki link in text.

	Path is normalized (wikilink ``.md``, unescaped, no query). Fragment comes
	from ``#…`` on markdown URLs or ``Page#heading`` wikilinks.

	Args:
	    markdown: Full markdown source (may include frontmatter).

	Yields:
	    Pairs of ``(normalized_path, fragment)``.
	"""
	for match in re.finditer(LINK_PATTERN, markdown):
		raw = match.group("url") or match.group("wikilink")
		if not raw:
			continue

		fragment = ""
		if match.group("wikilink"):
			page_part, sep, frag = raw.partition("#")
			if sep:
				fragment = frag
			path_src = page_part
			if not path_src.endswith(".md"):
				path_src += ".md"
			path = urlsplit(unescape_url(path_src)).path
		else:
			path, fragment = split_href(raw)

		if path:
			yield path, fragment


def find_link_targets(
	markdown: str,
	source_src_path: str,
	known_src_paths: set[str],
) -> Iterator[tuple[str, str]]:
	"""Yield resolved ``(target_src_path, fragment)`` for links that exist.

	Args:
	    markdown: Source markdown.
	    source_src_path: Current page ``src_path``.
	    known_src_paths: Set of documentation page ``src_path`` values.

	Yields:
	    ``(target_src_path, fragment)`` for in-site targets only.
	"""
	for link_path, fragment in iter_markdown_links(markdown):
		target = resolve_target_src(source_src_path, link_path)
		if target in known_src_paths:
			yield target, fragment
