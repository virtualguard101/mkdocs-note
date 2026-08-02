"""Notion wiki sync orchestration.

Token resolution, git incremental diff, page-map state, section ensure, and
``run_sync`` — the CLI entrypoint. Wiki IDs and site URL come from
``SyncOptions`` (or env fallbacks); nothing is hardcoded here.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mkdocs_note.utils.meta import extract_tags
from mkdocs_note.utils.notion.client import (
	TagsSchemaCache,
	attach_placeholder_images,
	create_page,
	list_wiki_pages,
	page_title,
	update_page_markdown,
	update_page_tags,
)
from mkdocs_note.utils.notion.convert import (
	ASSET_SUFFIXES,
	convert_markdown_file,
	md_references_asset,
)
from mkdocs_note.utils.tree import (
	TreeNode,
	build_page_tree,
	docs_rel,
	index_tree,
	is_index_doc,
)

# Alias for callers / docs that speak in nav terms.
NavItem = TreeNode

log = logging.getLogger("mkdocs_note.notion")


# ---------------------------------------------------------------------------
# Options & state
# ---------------------------------------------------------------------------


@dataclass
class SyncOptions:
	"""Configuration for a Notion sync run (assembled by CLI / mkdocs.yml)."""

	project_root: Path
	docs_dir: Path
	notes_root: Path
	nav_file: Path | None
	database_id: str
	data_source_id: str
	site_url: str
	state_path: Path
	delay: float
	title_property: str = "页面"
	tags_property: str = "标签"
	token: str | None = None
	allow_cursor_mcp_token: bool = False
	silence_mcp_token_warning: bool = False
	full: bool = False
	base: str | None = None
	paths: list[str] | None = None
	paths_file: Path | None = None
	section: list[str] | None = None
	rebuild_state: bool = False
	no_images: bool = False
	dry_run: bool = False
	continue_on_error: bool = False
	verbose: bool = False


@dataclass
class MigrationState:
	"""Local map of docs-relative keys → Notion page id/url."""

	root_page_id: str = ""
	data_source_id: str = ""
	title_property: str = "页面"
	pages: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class DiffSet:
	"""Incremental change set relative to ``docs_dir``."""

	md_changed: set[str] = field(default_factory=set)
	md_deleted: set[str] = field(default_factory=set)
	assets_changed: set[str] = field(default_factory=set)
	nav_changed: bool = False


# ---------------------------------------------------------------------------
# Logging & token
# ---------------------------------------------------------------------------


def setup_logging(verbose: bool = False) -> None:
	"""Configure root logging for CLI runs (stdout, no log files)."""
	level = logging.DEBUG if verbose else logging.INFO
	handler = logging.StreamHandler(sys.stdout)
	handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
	root = logging.getLogger()
	root.handlers.clear()
	root.addHandler(handler)
	root.setLevel(level)
	logging.getLogger("urllib3").setLevel(logging.WARNING)


def _load_dotenv(path: Path) -> None:
	"""Load KEY=VALUE lines into os.environ without overriding existing vars."""
	if not path.is_file():
		return
	for raw in path.read_text(encoding="utf-8").splitlines():
		line = raw.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, _, value = line.partition("=")
		key = key.strip()
		value = value.strip().strip("'").strip('"')
		if key and key not in os.environ:
			os.environ[key] = value


def _token_from_cursor_mcp() -> str | None:
	"""Reuse Notion token already configured for Cursor MCP (local dev)."""
	mcp_path = Path.home() / ".cursor" / "mcp.json"
	if not mcp_path.is_file():
		return None
	try:
		data = json.loads(mcp_path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		return None
	servers = data.get("mcpServers") or {}
	for name in ("notionApi", "Notion", "notion"):
		env = (servers.get(name) or {}).get("env") or {}
		for key in ("NOTION_TOKEN", "NOTION_API_KEY"):
			val = env.get(key)
			if val:
				return str(val).strip()
	for cfg in servers.values():
		env = (cfg or {}).get("env") or {}
		for key in ("NOTION_TOKEN", "NOTION_API_KEY"):
			val = env.get(key)
			if val:
				return str(val).strip()
	return None


def resolve_token(
	explicit: str | None,
	project_root: Path,
	allow_cursor_mcp_token: bool = False,
	silence_mcp_token_warning: bool = False,
) -> str | None:
	"""Resolve Notion token without requiring ``--token`` every run.

	Order: explicit → load ``.env`` from *project_root* (no override) →
	``NOTION_TOKEN`` / ``NOTION_API_KEY`` → ``project_root/.notion_token`` →
	``~/.config/notion/token`` → (only if *allow_cursor_mcp_token*) Cursor
	``mcp.json``.
	"""
	if explicit and explicit.strip():
		return explicit.strip()

	_load_dotenv(Path(project_root) / ".env")
	for key in ("NOTION_TOKEN", "NOTION_API_KEY"):
		val = os.environ.get(key)
		if val and val.strip():
			return val.strip()

	for path in (
		Path(project_root) / ".notion_token",
		Path.home() / ".config" / "notion" / "token",
	):
		if path.is_file():
			val = path.read_text(encoding="utf-8").strip()
			if val:
				return val

	if allow_cursor_mcp_token:
		token = _token_from_cursor_mcp()
		if token:
			if not silence_mcp_token_warning:
				log.warning(
					"Notion token loaded from Cursor MCP config "
					"(~/.cursor/mcp.json). This is not recommended unless you "
					"are a developer or have special needs. Set "
					"silence_mcp_token_warning: true to disable this warning."
				)
			return token
	return None


# ---------------------------------------------------------------------------
# Config / path helpers
# ---------------------------------------------------------------------------


def _docs_prefix(project_root: Path, docs_dir: Path) -> str:
	"""Repo-relative docs prefix with trailing slash (e.g. ``docs/``)."""
	root = Path(project_root).resolve()
	docs = Path(docs_dir).resolve()
	try:
		rel = docs.relative_to(root)
		return docs_rel(str(rel)).rstrip("/") + "/"
	except ValueError:
		return docs_rel(docs.name).rstrip("/") + "/"


def _apply_env_overrides(options: SyncOptions) -> SyncOptions:
	"""Fill empty option fields from environment variables."""
	database_id = (
		options.database_id or os.environ.get("NOTION_WIKI_DATABASE") or ""
	).strip()
	data_source_id = (
		options.data_source_id or os.environ.get("NOTION_WIKI_DATA_SOURCE") or ""
	).strip()
	title_property = (
		options.title_property or os.environ.get("NOTION_TITLE_PROPERTY") or "页面"
	).strip()
	tags_property = (
		options.tags_property or os.environ.get("NOTION_TAGS_PROPERTY") or "标签"
	).strip()
	state_raw = str(options.state_path) if options.state_path else ""
	if not state_raw.strip():
		state_raw = os.environ.get("NOTION_STATE_PATH") or ".notion_sync_state.json"
	state_path = Path(state_raw)
	if not state_path.is_absolute():
		state_path = Path(options.project_root) / state_path

	return SyncOptions(
		project_root=Path(options.project_root),
		docs_dir=Path(options.docs_dir),
		notes_root=Path(options.notes_root),
		nav_file=Path(options.nav_file) if options.nav_file else None,
		database_id=database_id,
		data_source_id=data_source_id,
		site_url=(options.site_url or "").rstrip("/"),
		state_path=state_path,
		delay=options.delay,
		title_property=title_property,
		tags_property=tags_property,
		token=options.token,
		allow_cursor_mcp_token=options.allow_cursor_mcp_token,
		silence_mcp_token_warning=options.silence_mcp_token_warning,
		full=options.full,
		base=options.base,
		paths=options.paths,
		paths_file=options.paths_file,
		section=options.section,
		rebuild_state=options.rebuild_state,
		no_images=options.no_images,
		dry_run=options.dry_run,
		continue_on_error=options.continue_on_error,
		verbose=options.verbose,
	)


def _strip_docs_prefix(path: str, docs_prefix: str) -> str:
	"""Normalize a path to docs-relative (strip configured or bare ``docs/``)."""
	rel = docs_rel(path)
	if rel.startswith(docs_prefix):
		return rel[len(docs_prefix) :]
	if docs_prefix != "docs/" and rel.startswith("docs/"):
		return rel[5:]
	return rel


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


def load_state(path: Path, default_title: str = "页面") -> MigrationState:
	"""Load migration state JSON, or return an empty state."""
	if not path.exists():
		return MigrationState(title_property=default_title)
	data = json.loads(path.read_text(encoding="utf-8"))
	return MigrationState(
		root_page_id=data.get("root_page_id", ""),
		data_source_id=data.get("data_source_id", ""),
		title_property=data.get("title_property", default_title),
		pages=data.get("pages", {}),
	)


def save_state(path: Path, state: MigrationState) -> None:
	"""Persist migration state JSON."""
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(
		json.dumps(
			{
				"root_page_id": state.root_page_id,
				"data_source_id": state.data_source_id,
				"title_property": state.title_property,
				"pages": state.pages,
			},
			ensure_ascii=False,
			indent=2,
		),
		encoding="utf-8",
	)


def rebuild_state_from_wiki(
	token: str,
	*,
	data_source_id: str,
	database_id: str,
	title_property: str = "页面",
	tree: list[TreeNode] | None = None,
	nav_file: Path | None = None,
	notes_root: Path | None = None,
	docs_dir: Path | None = None,
	sections: list[str] | None = None,
) -> MigrationState:
	"""Match existing wiki pages to nav / directory tree keys (recovery).

	Pass *tree* when already built; otherwise call ``build_page_tree`` using
	*nav_file* / *notes_root* / *docs_dir*.
	"""
	state = MigrationState(
		root_page_id=database_id,
		data_source_id=data_source_id,
		title_property=title_property,
	)
	pages = list_wiki_pages(token, data_source_id)
	log.info("fetched %d pages from wiki for state rebuild", len(pages))

	by_parent: dict[str, list[dict[str, str]]] = {}
	for page in pages:
		title = page_title(page, title_property=title_property)
		parent = page.get("parent", {})
		if parent.get("type") == "page_id":
			parent_key = parent["page_id"]
		elif parent.get("type") == "database_id":
			parent_key = parent["database_id"]
		elif parent.get("type") == "data_source_id":
			parent_key = parent["data_source_id"]
		else:
			parent_key = database_id
		by_parent.setdefault(parent_key, []).append(
			{
				"id": page["id"],
				"title": title,
				"url": page.get(
					"url",
					f"https://www.notion.so/{page['id'].replace('-', '')}",
				),
			}
		)

	if tree is None:
		if notes_root is None or docs_dir is None:
			raise ValueError(
				"rebuild_state_from_wiki requires tree=… or notes_root=… and docs_dir=…"
			)
		tree, source = build_page_tree(
			nav_file=nav_file, notes_root=notes_root, docs_dir=docs_dir
		)
		log.info("page tree source for rebuild: %s", source)

	notebook = next((item for item in tree if item.title == "Notebook"), None)
	start_items = notebook.children if notebook else tree
	if notebook:
		state.pages[notebook.key] = {
			"id": database_id,
			"url": f"https://www.notion.so/{database_id.replace('-', '')}",
		}

	def section_allowed(item: NavItem) -> bool:
		if not sections:
			return True
		if item.file_rel:
			return any(item.file_rel.startswith(s) for s in sections)
		return any(section_allowed(c) for c in item.children)

	def match_items(items: list[NavItem], parent_page_id: str) -> None:
		unused = list(by_parent.get(parent_page_id, []))
		for item in items:
			if not section_allowed(item):
				continue
			match = next((c for c in unused if c["title"] == item.title), None)
			if match is None:
				log.warning("missing Notion page for %r title=%r", item.key, item.title)
				continue
			unused.remove(match)
			state.pages[item.key] = {"id": match["id"], "url": match["url"]}
			if item.children:
				match_items(item.children, match["id"])

	match_items(start_items, database_id)
	if data_source_id != database_id:
		match_items(
			[i for i in start_items if i.key not in state.pages],
			data_source_id,
		)
	return state


# ---------------------------------------------------------------------------
# Git diff (incremental)
# ---------------------------------------------------------------------------


def _run_git(project_root: Path, *args: str) -> str:
	"""Run git with *project_root* as cwd; disable quotepath for UTF-8 paths."""
	# core.quotepath=false: non-ASCII paths must be raw UTF-8. Default quoting
	# emits `"docs/...\350\256..."` which fails prefix checks and empties the
	# incremental diff for almost all Chinese note paths.
	result = subprocess.run(
		["git", "-c", "core.quotepath=false", *args],
		cwd=project_root,
		check=False,
		capture_output=True,
		text=True,
	)
	if result.returncode != 0:
		raise RuntimeError(
			f"git {' '.join(args)} failed ({result.returncode}): "
			f"{result.stderr.strip()}"
		)
	return result.stdout


def resolve_git_base(project_root: Path, explicit: str | None) -> str | None:
	"""Pick a base ref for incremental sync.

	Priority: explicit → ``GITHUB_EVENT_BEFORE`` → ``NOTION_SYNC_BASE`` →
	``HEAD~1``. Returns ``None`` when a full sync is required.
	"""
	if explicit:
		if explicit in ("", "0" * 40, "full"):
			return None
		return explicit

	before = os.environ.get("GITHUB_EVENT_BEFORE") or os.environ.get("NOTION_SYNC_BASE")
	if before:
		if before in ("", "0" * 40):
			return None
		return before

	try:
		_run_git(project_root, "rev-parse", "--verify", "HEAD~1")
		return "HEAD~1"
	except RuntimeError:
		return None


def git_diff(
	base: str | None,
	project_root: Path,
	docs_dir: Path,
) -> DiffSet:
	"""Collect docs changes between ``base...HEAD``. If *base* is None → full."""
	if base is None:
		# Caller will expand to all pages when nav_changed + full mode.
		return DiffSet(nav_changed=True)

	docs_prefix = _docs_prefix(project_root, docs_dir)
	pathspec = docs_prefix.rstrip("/")
	out = _run_git(
		project_root,
		"diff",
		"--name-status",
		"--find-renames",
		f"{base}...HEAD",
		"--",
		pathspec,
	)
	diff = DiffSet()
	for line in out.splitlines():
		if not line.strip():
			continue
		parts = line.split("\t")
		status = parts[0]
		paths = parts[1:]
		# Renames: R100\told\tnew
		if status.startswith("R") and len(paths) == 2:
			old, new = paths
			_classify_path(diff, old, docs_prefix, deleted=True)
			_classify_path(diff, new, docs_prefix, deleted=False)
			continue
		path = paths[0]
		deleted = status.startswith("D")
		_classify_path(diff, path, docs_prefix, deleted=deleted)
	return diff


def _classify_path(
	diff: DiffSet,
	path: str,
	docs_prefix: str,
	*,
	deleted: bool,
) -> None:
	"""Classify a repo-relative path into the diff set."""
	path = docs_rel(path)
	if path == f"{docs_prefix}.nav.yml" or path.endswith("/.nav.yml"):
		diff.nav_changed = True
		return
	if not path.startswith(docs_prefix):
		return
	rel = path[len(docs_prefix) :]
	suffix = Path(rel).suffix.lower()
	if suffix in (".md", ".ipynb"):
		if deleted:
			diff.md_deleted.add(rel)
		else:
			diff.md_changed.add(rel)
	elif suffix in ASSET_SUFFIXES and not deleted:
		diff.assets_changed.add(rel)


def expand_asset_dependents(
	assets: set[str],
	nav_index: dict[str, NavItem],
	docs_dir: Path,
	sections: list[str] | None,
) -> set[str]:
	"""Find nav-listed markdown files that reference changed assets (scoped)."""
	if not assets:
		return set()
	candidates: list[Path] = []
	for item in nav_index.values():
		if not item.file_rel or is_index_doc(item.file_rel):
			continue
		if sections and not any(item.file_rel.startswith(s) for s in sections):
			continue
		source = docs_dir / item.file_rel
		if source.exists():
			candidates.append(source)

	affected: set[str] = set()
	for source in candidates:
		rel = docs_rel(str(source.relative_to(docs_dir)))
		for asset in assets:
			if md_references_asset(source, asset, docs_dir):
				affected.add(rel)
				break
	return affected


# ---------------------------------------------------------------------------
# Sync orchestration
# ---------------------------------------------------------------------------


def filter_sections(rel: str, sections: list[str] | None) -> bool:
	"""True if *rel* is under any of the section prefixes (or no filter)."""
	if not sections:
		return True
	return any(rel.startswith(s) for s in sections)


def ensure_section(
	token: str,
	state: MigrationState,
	state_path: Path,
	nav_index: dict[str, NavItem],
	key: str,
	delay: float,
	dry_run: bool,
) -> str:
	"""Ensure a section (or Notebook root) exists; return Notion page id."""
	if key in state.pages:
		return state.pages[key]["id"]

	item = nav_index.get(key)
	if item is None:
		raise KeyError(f"nav key not found: {key}")

	# Notebook root maps to the wiki database itself.
	if item.title == "Notebook" and not item.parent_key:
		state.pages[key] = {
			"id": state.root_page_id,
			"url": f"https://www.notion.so/{state.root_page_id.replace('-', '')}",
		}
		if not dry_run:
			save_state(state_path, state)
		return state.root_page_id

	if item.parent_key:
		parent_id = ensure_section(
			token, state, state_path, nav_index, item.parent_key, delay, dry_run
		)
		parent_kind = "page"
	else:
		parent_id = state.data_source_id or state.root_page_id
		parent_kind = "data_source" if state.data_source_id else "database"

	log.info("create section %s (%s)", item.title, key)
	if dry_run:
		fake = f"dry-run-{key}"
		state.pages[key] = {"id": fake, "url": f"https://www.notion.so/{fake}"}
		return fake

	info = create_page(
		token,
		parent_id,
		item.title,
		title_property=state.title_property,
		parent_kind=parent_kind,
	)
	state.pages[key] = info
	save_state(state_path, state)
	time.sleep(delay)
	return info["id"]


def resolve_parent_id(
	token: str,
	state: MigrationState,
	state_path: Path,
	nav_index: dict[str, NavItem],
	parent_key: str,
	delay: float,
	dry_run: bool,
) -> tuple[str, str]:
	"""Resolve parent Notion id and kind for a content page."""
	if not parent_key:
		parent_id = state.data_source_id or state.root_page_id
		kind = "data_source" if state.data_source_id else "database"
		return parent_id, kind
	# Notebook root → wiki database / data source for children.
	parent_item = nav_index.get(parent_key)
	if parent_item and parent_item.title == "Notebook" and not parent_item.parent_key:
		state.pages.setdefault(
			parent_key,
			{
				"id": state.root_page_id,
				"url": (f"https://www.notion.so/{state.root_page_id.replace('-', '')}"),
			},
		)
		parent_id = state.data_source_id or state.root_page_id
		kind = "data_source" if state.data_source_id else "database"
		return parent_id, kind
	page_id = ensure_section(
		token, state, state_path, nav_index, parent_key, delay, dry_run
	)
	return page_id, "page"


def sync_one_page(
	token: str,
	state: MigrationState,
	state_path: Path,
	nav_index: dict[str, NavItem],
	item: NavItem,
	*,
	docs_dir: Path,
	site_url: str,
	delay: float,
	dry_run: bool,
	upload_images: bool,
	tags_property: str = "标签",
	tags_cache: TagsSchemaCache | None = None,
) -> str:
	"""Create or update one Notion page from a nav tree leaf."""
	assert item.file_rel
	source = docs_dir / item.file_rel
	if not source.exists():
		log.warning("skip missing file %s", item.file_rel)
		return "missing"

	parent_id, parent_kind = resolve_parent_id(
		token,
		state,
		state_path,
		nav_index,
		item.parent_key,
		delay,
		dry_run,
	)

	created = item.file_rel not in state.pages
	if created:
		log.info("create page %s", item.file_rel)
		if dry_run:
			state.pages[item.file_rel] = {
				"id": f"dry-run-{item.file_rel}",
				"url": "https://www.notion.so/dry-run",
			}
		else:
			info = create_page(
				token,
				parent_id,
				item.title,
				title_property=state.title_property,
				parent_kind=parent_kind,
			)
			state.pages[item.file_rel] = info
			save_state(state_path, state)
			time.sleep(delay)
	else:
		log.info("update page %s", item.file_rel)

	image_paths: list[Path] = []

	def upload_local(path: Path) -> str:
		if not upload_images:
			return ""
		image_paths.append(path)
		return f"⟦LOCALIMG:{len(image_paths) - 1}⟧"

	title_conv, content, meta = convert_markdown_file(
		source,
		site_url,
		state.pages,
		docs_dir,
		upload_local=upload_local if upload_images else None,
	)
	tags = extract_tags(meta)
	_ = title_conv

	if dry_run:
		log.info(
			"dry-run %s content=%d chars images=%d tags=%s",
			item.file_rel,
			len(content),
			len(image_paths),
			tags,
		)
		return "dry-run"

	page_id = state.pages[item.file_rel]["id"]
	update_page_markdown(token, page_id, content)
	applied_tags: list[str] = []
	try:
		applied_tags = update_page_tags(
			token,
			page_id,
			tags,
			property_name=tags_property,
			tags_cache=tags_cache,
		)
	except urllib.error.HTTPError as exc:
		body = getattr(exc, "reason", "") or ""
		log.warning("tags update failed for %s: %s %s", item.file_rel, exc.code, body)
	except RuntimeError as exc:
		log.warning("tags update failed for %s: %s", item.file_rel, exc)
	attached = 0
	if upload_images and image_paths:
		attached = attach_placeholder_images(token, page_id, image_paths)
	if set(applied_tags) == set(tags):
		tags_display: Any = applied_tags or "—"
	else:
		tags_display = f"FAILED wanted={tags} applied={applied_tags}"
	log.info(
		"ok %s (%s, images=%d/%d, tags=%s)",
		item.file_rel,
		"created" if created else "updated",
		attached,
		len(image_paths),
		tags_display,
	)
	time.sleep(delay)
	return "created" if created else "updated"


def collect_targets(
	*,
	full: bool,
	diff: DiffSet,
	nav_index: dict[str, NavItem],
	docs_dir: Path,
	sections: list[str] | None,
) -> tuple[list[NavItem], set[str]]:
	"""Return ``(pages to sync, deleted rel paths)``."""
	deleted = {
		p
		for p in diff.md_deleted
		if filter_sections(p, sections) and not is_index_doc(p)
	}

	def _include(rel: str) -> bool:
		if is_index_doc(rel):
			return False
		return filter_sections(rel, sections)

	if full:
		items = [
			item
			for item in nav_index.values()
			if item.file_rel
			and _include(item.file_rel)
			and (docs_dir / item.file_rel).exists()
		]
		return items, deleted

	wanted = set(diff.md_changed)
	if diff.assets_changed:
		wanted |= expand_asset_dependents(
			diff.assets_changed, nav_index, docs_dir, sections
		)

	items: list[NavItem] = []
	for rel in sorted(wanted):
		if is_index_doc(rel):
			log.info("skip index.md: %s", rel)
			continue
		if not filter_sections(rel, sections):
			continue
		item = nav_index.get(rel)
		if item is None or not item.file_rel:
			log.warning("changed file not in nav, skip: %s", rel)
			continue
		items.append(item)
	return items, deleted


def run_sync(options: SyncOptions) -> int:
	"""Main sync entry used by the CLI. Returns a process exit code."""
	options = _apply_env_overrides(options)
	if options.verbose:
		setup_logging(True)

	token = resolve_token(
		options.token,
		options.project_root,
		allow_cursor_mcp_token=options.allow_cursor_mcp_token,
		silence_mcp_token_warning=options.silence_mcp_token_warning,
	)
	if not token and not options.dry_run:
		log.error(
			"Notion token not found. Set NOTION_TOKEN, add a project .env / "
			".notion_token, or enable allow_cursor_mcp_token for developer use."
		)
		return 1

	if not options.database_id or not options.data_source_id:
		log.error(
			"database_id and data_source_id are required "
			"(mkdocs.yml notion_sync or NOTION_WIKI_DATABASE / "
			"NOTION_WIKI_DATA_SOURCE)."
		)
		return 1

	state_path = options.state_path
	sections = options.section
	docs_prefix = _docs_prefix(options.project_root, options.docs_dir)

	# Resolve what to sync.
	path_list: list[str] = []
	if options.paths:
		path_list.extend(options.paths)
	if options.paths_file is not None:
		raw = Path(options.paths_file).read_text(encoding="utf-8")
		path_list.extend(line.strip() for line in raw.splitlines() if line.strip())

	if path_list:
		normalized: set[str] = set()
		for p in path_list:
			normalized.add(_strip_docs_prefix(p, docs_prefix))
		diff = DiffSet(md_changed=normalized)
		base: str | None = "(paths)"
		full = False
	elif options.full:
		diff = DiffSet(nav_changed=True)
		base = None
		full = True
	else:
		base = resolve_git_base(options.project_root, options.base)
		full = base is None
		if full:
			log.info("no git base available → full sync")
			diff = DiffSet(nav_changed=True)
		else:
			log.info("incremental sync since %s", base)
			diff = git_diff(base, options.project_root, options.docs_dir)

	log.info(
		"diff: md=%d deleted=%d assets=%d nav_changed=%s full=%s",
		len(diff.md_changed),
		len(diff.md_deleted),
		len(diff.assets_changed),
		diff.nav_changed,
		full,
	)

	tree, tree_source = build_page_tree(
		nav_file=options.nav_file,
		notes_root=options.notes_root,
		docs_dir=options.docs_dir,
	)
	log.info("page tree source: %s", tree_source)
	nav_index = index_tree(tree)

	# Load / rebuild page map.
	state = load_state(state_path, default_title=options.title_property)
	need_rebuild = options.rebuild_state or not state.pages
	if need_rebuild:
		if options.dry_run and not token:
			log.warning("dry-run without token: empty state")
		else:
			assert token
			log.info("rebuilding page map from Notion wiki…")
			state = rebuild_state_from_wiki(
				token,
				data_source_id=options.data_source_id,
				database_id=options.database_id,
				title_property=options.title_property,
				tree=tree,
				sections=sections,
			)
			if not options.dry_run:
				save_state(state_path, state)
			log.info("mapped %d keys", len(state.pages))
	else:
		state.root_page_id = state.root_page_id or options.database_id
		state.data_source_id = state.data_source_id or options.data_source_id
		state.title_property = state.title_property or options.title_property

	targets, deleted = collect_targets(
		full=full,
		diff=diff,
		nav_index=nav_index,
		docs_dir=options.docs_dir,
		sections=sections,
	)

	if deleted:
		for rel in sorted(deleted):
			log.info("deleted locally (Notion page left intact): %s", rel)

	if not targets:
		log.info("nothing to sync")
		return 0

	tags_cache: TagsSchemaCache | None = None
	if not options.dry_run and token:
		tags_cache = TagsSchemaCache(
			data_source_id=state.data_source_id or options.data_source_id,
			property_name=options.tags_property,
		)

	log.info("syncing %d page(s)", len(targets))
	stats = {"created": 0, "updated": 0, "dry-run": 0, "missing": 0, "failed": 0}
	for item in targets:
		try:
			result = sync_one_page(
				token or "",
				state,
				state_path,
				nav_index,
				item,
				docs_dir=options.docs_dir,
				site_url=options.site_url,
				delay=options.delay,
				dry_run=options.dry_run,
				upload_images=not options.no_images,
				tags_property=options.tags_property,
				tags_cache=tags_cache,
			)
			stats[result] = stats.get(result, 0) + 1
		except urllib.error.HTTPError as exc:
			body = getattr(exc, "reason", "") or ""
			log.error("FAIL %s: %s %s", item.file_rel, exc.code, body)
			stats["failed"] += 1
			if not options.continue_on_error:
				return 1
		except Exception as exc:  # noqa: BLE001 - per-page catch-all for continue_on_error
			log.error("FAIL %s: %s", item.file_rel, exc)
			stats["failed"] += 1
			if not options.continue_on_error:
				return 1

	if not options.dry_run:
		save_state(state_path, state)
	log.info("done %s", json.dumps(stats, ensure_ascii=False))
	return 1 if stats["failed"] else 0
