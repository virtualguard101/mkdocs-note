"""Hierarchical page-tree helpers shared by CLI tools and Notion sync.

Produces a uniform ``TreeNode`` shape from either ``.nav.yml`` (awesome-nav)
or a filesystem walk under ``notes_root`` (directory hierarchy preserved).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from mkdocs.plugins import get_plugin_logger

logger = get_plugin_logger(__name__)

CONTENT_SUFFIXES = {".md", ".ipynb"}


@dataclass
class TreeNode:
	"""A navigation / filesystem tree node.

	Leaf content pages set ``file_rel``; intermediate sections leave it ``None``.
	"""

	key: str
	title: str
	file_rel: str | None
	parent_key: str
	children: list[TreeNode] = field(default_factory=list)


def docs_rel(path: str) -> str:
	"""Normalize path separators to forward slashes."""
	return path.replace("\\", "/")


def title_from_path(path: Path) -> str:
	"""Default title from a file stem."""
	return path.stem


def is_index_doc(rel: str) -> bool:
	"""True for any docs-relative path whose basename is ``index.md``."""
	return Path(rel).name.lower() == "index.md"


def resolve_doc_path(raw: str, docs_prefix: str = "docs/") -> str:
	"""Strip optional docs prefix and quotes from a nav path entry."""
	raw = raw.strip().strip('"').strip("'")
	prefix = docs_prefix if docs_prefix.endswith("/") else f"{docs_prefix}/"
	# Also accept bare "docs/" when docs_dir is custom.
	if raw.startswith("docs/"):
		raw = raw[5:]
	elif prefix != "docs/" and raw.startswith(prefix):
		raw = raw[len(prefix) :]
	return docs_rel(raw)


def walk_tree(items: list[TreeNode]) -> list[TreeNode]:
	"""Depth-first flatten of a tree."""
	ordered: list[TreeNode] = []
	for item in items:
		ordered.append(item)
		ordered.extend(walk_tree(item.children))
	return ordered


def index_tree(tree: list[TreeNode]) -> dict[str, TreeNode]:
	"""Map node key → node for the entire tree."""
	return {item.key: item for item in walk_tree(tree)}


def load_nav_yaml(nav_path: Path) -> list[Any]:
	"""Load the ``nav`` list from an awesome-nav ``.nav.yml`` file."""
	with nav_path.open("r", encoding="utf-8") as f:
		data = yaml.safe_load(f) or {}
	if isinstance(data, dict):
		return data.get("nav", data) if isinstance(data.get("nav", data), list) else []
	if isinstance(data, list):
		return data
	return []


def build_nav_tree(
	nodes: list[Any],
	parent_key: str = "",
	*,
	docs_prefix: str = "docs/",
) -> list[TreeNode]:
	"""Build a ``TreeNode`` forest from awesome-nav YAML nodes."""
	items: list[TreeNode] = []
	for node in nodes:
		if isinstance(node, str):
			rel = resolve_doc_path(node, docs_prefix=docs_prefix)
			items.append(
				TreeNode(
					key=rel,
					title=title_from_path(Path(rel)),
					file_rel=rel,
					parent_key=parent_key,
				)
			)
			continue
		if not isinstance(node, dict):
			continue
		for title, child in node.items():
			title_s = str(title)
			if isinstance(child, str):
				rel = resolve_doc_path(child, docs_prefix=docs_prefix)
				items.append(
					TreeNode(
						key=rel,
						title=title_s,
						file_rel=rel,
						parent_key=parent_key,
					)
				)
			elif isinstance(child, list):
				section_key = f"{parent_key}/{title_s}" if parent_key else title_s
				section = TreeNode(
					key=section_key,
					title=title_s,
					file_rel=None,
					parent_key=parent_key,
					children=build_nav_tree(
						child, section_key, docs_prefix=docs_prefix
					),
				)
				items.append(section)
	return items


def build_directory_tree(
	root: Path,
	*,
	parent_key: str = "",
	rel_prefix: str = "",
) -> list[TreeNode]:
	"""Build a ``TreeNode`` forest from filesystem hierarchy under ``root``.

	Directories become sections; ``.md`` / ``.ipynb`` leaves become content pages.
	``index.md`` files are omitted from the tree (callers still skip them on sync).

	Args:
	    root: Absolute or relative notes root directory.
	    parent_key: Parent nav key for this level.
	    rel_prefix: Docs-relative path prefix for children.

	Returns:
	    Ordered list of tree nodes for this directory level.
	"""
	root = Path(root)
	if not root.is_dir():
		return []

	items: list[TreeNode] = []
	# Stable ordering: directories first (alpha), then files (alpha).
	entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
	for entry in entries:
		if entry.name.startswith("."):
			continue
		if entry.is_dir():
			# Skip co-located asset directories.
			if entry.name == "assets":
				continue
			rel = docs_rel(f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name)
			section_key = rel
			children = build_directory_tree(
				entry, parent_key=section_key, rel_prefix=rel
			)
			if not children:
				continue
			items.append(
				TreeNode(
					key=section_key,
					title=entry.name,
					file_rel=None,
					parent_key=parent_key,
					children=children,
				)
			)
			continue

		suffix = entry.suffix.lower()
		if suffix not in CONTENT_SUFFIXES:
			continue
		rel = docs_rel(f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name)
		if is_index_doc(rel):
			continue
		items.append(
			TreeNode(
				key=rel,
				title=title_from_path(entry),
				file_rel=rel,
				parent_key=parent_key,
			)
		)
	return items


def build_page_tree(
	*,
	nav_file: Path | None,
	notes_root: Path,
	docs_dir: Path,
) -> tuple[list[TreeNode], str]:
	"""Resolve page tree: prefer ``.nav.yml``, else ``notes_root`` directory scan.

	Args:
	    nav_file: Path to ``.nav.yml`` (may be None or missing).
	    notes_root: Notes directory for filesystem fallback.
	    docs_dir: Docs root used when stripping prefixes in nav paths.

	Returns:
	    Tuple of (tree, source_label) where source_label is ``"nav.yml"`` or
	    ``"directory"``.
	"""
	docs_prefix = docs_rel(str(docs_dir)).rstrip("/") + "/"
	if nav_file is not None and nav_file.is_file():
		nodes = load_nav_yaml(nav_file)
		return build_nav_tree(nodes, docs_prefix=docs_prefix), "nav.yml"

	logger.warning(
		"Navigation file not found (%s). Falling back to directory scan of "
		"'%s' (directory hierarchy preserved). For custom titles and grouping "
		"that match your site nav, install mkdocs-awesome-nav and add a "
		".nav.yml under your docs directory.",
		nav_file,
		notes_root,
	)
	return build_directory_tree(notes_root), "directory"
