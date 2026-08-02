"""Metadata helpers for note frontmatter.

Supports both MkDocs ``File`` objects (plugin build path) and plain text / path
APIs used by CLI tools such as Notion sync.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import File
from mkdocs.utils import meta as mkdocs_meta

logger = get_plugin_logger(__name__)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
	"""Split markdown text into frontmatter dict and body.

	Args:
	    text: Full file contents.

	Returns:
	    Tuple of (metadata dict, body without frontmatter).
	"""
	if not text.startswith("---"):
		return {}, text
	end = text.find("\n---", 3)
	if end == -1:
		return {}, text
	raw = text[3:end].strip()
	body = text[end + 4 :].lstrip("\n")
	if not raw:
		return {}, body
	try:
		loaded = yaml.safe_load(raw)
		meta_dict = loaded if isinstance(loaded, dict) else {}
	except (yaml.YAMLError, AttributeError, TypeError):
		# Fallback: flat key: value (no nested lists).
		meta_dict = {}
		for line in raw.splitlines():
			if ":" not in line:
				continue
			key, value = line.split(":", 1)
			key = key.strip()
			value = value.strip()
			if value.startswith('"') and value.endswith('"'):
				value = value[1:-1]
			meta_dict[key] = value
	return meta_dict, body


def parse_frontmatter_file(path: Path) -> tuple[dict[str, Any], str]:
	"""Read a file and parse its frontmatter.

	Args:
	    path: Path to a markdown (or text) file.

	Returns:
	    Tuple of (metadata dict, body).
	"""
	raw = path.read_text(encoding="utf-8")
	return parse_frontmatter(raw)


def extract_tags(meta_dict: dict[str, Any]) -> list[str]:
	"""Normalize frontmatter ``tags`` / ``tag`` into a list of non-empty strings.

	Args:
	    meta_dict: Parsed frontmatter mapping.

	Returns:
	    List of tag strings.
	"""
	raw = meta_dict.get("tags", meta_dict.get("tag", None))
	if raw is None:
		return []
	if isinstance(raw, str):
		parts = [p.strip() for p in re.split(r"[,;]", raw)]
		return [p for p in parts if p]
	if isinstance(raw, (list, tuple)):
		out: list[str] = []
		for item in raw:
			if item is None:
				continue
			s = str(item).strip()
			if s:
				out.append(s)
		return out
	s = str(raw).strip()
	return [s] if s else []


def validate_frontmatter(f: File) -> bool:
	"""Validate the frontmatter of the file.

	Args:
	    f: The file to validate.

	Returns:
	    bool: True if the frontmatter is valid, False otherwise.
	"""
	try:
		_, frontmatter = mkdocs_meta.get_data(f.content_string)

		if not frontmatter.get("publish", False):
			logger.debug(f"Skipping {f.src_uri} because it is not published")
			return False

		if "date" not in frontmatter:
			logger.error(f"Invalid frontmatter for {f.src_uri}: 'date' is required")
			return False

		date = frontmatter["date"]
		if not isinstance(date, datetime):
			logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'date' must be a datetime object"
			)
			return False

		f.note_date = date

		if "title" not in frontmatter:
			logger.error(f"Invalid frontmatter for {f.src_uri}: 'title' is required")
			return False

		title = frontmatter["title"]
		if not isinstance(title, str):
			logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'title' must be a string"
			)
			return False

		f.note_title = title
		return True

	except Exception as e:
		logger.error(f"Error validating frontmatter for {f.src_uri}: {e}")
		raise


def extract_date(f: File) -> datetime | None:
	"""Extract date from docs file.

	Args:
	    f: The file to extract date from.

	Returns:
	    Optional[datetime]: The date if successful, None otherwise.
	"""
	try:
		return f.note_date
	except AttributeError:
		return None


def extract_title(f: File) -> str | None:
	"""Extract title from docs file.

	Args:
	    f: The file to extract title from.

	Returns:
	    Optional[str]: The title if successful, None otherwise.
	"""
	try:
		return f.note_title
	except AttributeError:
		return None
