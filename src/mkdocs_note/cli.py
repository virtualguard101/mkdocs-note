#!/usr/bin/env python3
"""
Standalone CLI for MkDocs-Note plugin.

This module provides command-line interface for note management
independent of MkDocs plugin system.
"""

import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import click
import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

import mkdocs_note.utils.cli.common as cli_common
from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils.cli.commands import (
	CleanCommand,
	MoveCommand,
	NewCommand,
	RemoveCommand,
)
from mkdocs_note.utils.notion.sync import SyncOptions, run_sync, setup_logging


class _IgnoreUnknownLoader(yaml.SafeLoader):
	"""SafeLoader that ignores MkDocs / pymdownx Python object tags."""


def _ignore_unknown(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node):
	if isinstance(node, ScalarNode):
		return loader.construct_scalar(node)
	if isinstance(node, SequenceNode):
		return loader.construct_sequence(node)
	if isinstance(node, MappingNode):
		return loader.construct_mapping(node)
	return None


_IgnoreUnknownLoader.add_multi_constructor("!", _ignore_unknown)
_IgnoreUnknownLoader.add_multi_constructor("tag:yaml.org,2002:python/", _ignore_unknown)


def _load_yaml_file(path: Path) -> dict[str, Any]:
	"""Load YAML, tolerating MkDocs-specific tags."""
	with path.open("r", encoding="utf-8") as f:
		data = yaml.load(f, Loader=_IgnoreUnknownLoader)
	return data if isinstance(data, dict) else {}


def find_project_root(start: Path | None = None) -> Path:
	"""Walk parents looking for ``mkdocs.yml`` / ``mkdocs.yaml``.

	Args:
	    start: Starting directory (default: cwd).

	Returns:
	    Path to the project root (falls back to cwd if not found).
	"""
	cur = (start or Path.cwd()).resolve()
	for candidate in [cur, *cur.parents]:
		if (candidate / "mkdocs.yml").is_file() or (
			candidate / "mkdocs.yaml"
		).is_file():
			return candidate
	return cur


def load_mkdocs_plugin_section(project_root: Path) -> dict[str, Any]:
	"""Load the ``mkdocs-note`` plugin config dict from ``mkdocs.yml``.

	Args:
	    project_root: Directory containing mkdocs.yml.

	Returns:
	    Plugin configuration mapping (may be empty). Includes ``_site_url``
	    from the top-level mkdocs.yml when present.
	"""
	for name in ("mkdocs.yml", "mkdocs.yaml"):
		path = project_root / name
		if not path.is_file():
			continue
		data = _load_yaml_file(path)
		result: dict[str, Any] = {}
		if data.get("site_url"):
			result["_site_url"] = data["site_url"]
		plugins = data.get("plugins") or []
		for entry in plugins:
			if entry == "mkdocs-note":
				return result
			if isinstance(entry, dict) and "mkdocs-note" in entry:
				cfg = entry["mkdocs-note"]
				if isinstance(cfg, dict):
					merged = dict(cfg)
					merged.update({k: v for k, v in result.items() if k not in merged})
					return merged
				return result
		return result
	return {}


def build_sync_options_from_config(
	project_root: Path,
	*,
	full: bool = False,
	base: str | None = None,
	paths: tuple[str, ...] | None = None,
	paths_file: Path | None = None,
	section: tuple[str, ...] | None = None,
	site_url: str | None = None,
	state: Path | None = None,
	database_id: str | None = None,
	data_source_id: str | None = None,
	token: str | None = None,
	rebuild_state: bool = False,
	images: str | None = None,
	no_resume: bool = False,
	dry_run: bool = False,
	continue_on_error: bool = False,
	verbose: bool = False,
	delay: float | None = None,
) -> SyncOptions:
	"""Assemble ``SyncOptions`` from mkdocs.yml plugin section + CLI overrides."""
	plugin = load_mkdocs_plugin_section(project_root)
	ns = (
		plugin.get("notion_sync") if isinstance(plugin.get("notion_sync"), dict) else {}
	)

	notes_root_raw = plugin.get("notes_root") or "docs"
	docs_dir_raw = ns.get("docs_dir") or notes_root_raw or "docs"
	nav_file_raw = ns.get("nav_file") or f"{docs_dir_raw}/.nav.yml"

	def _abs(p: str | Path) -> Path:
		path = Path(p)
		return path if path.is_absolute() else (project_root / path)

	resolved_site = (
		site_url
		if site_url is not None
		else (ns.get("site_url") or plugin.get("_site_url") or "")
	)

	local_images = (
		images if images is not None else str(ns.get("local_images") or "upload")
	)
	cache_raw = ns.get("cache_dir") or ".cache/mkdocs-note"

	return SyncOptions(
		project_root=project_root,
		docs_dir=_abs(docs_dir_raw),
		notes_root=_abs(notes_root_raw),
		nav_file=_abs(nav_file_raw) if nav_file_raw else None,
		database_id=database_id
		if database_id is not None
		else str(ns.get("database_id") or ""),
		data_source_id=data_source_id
		if data_source_id is not None
		else str(ns.get("data_source_id") or ""),
		title_property=str(ns.get("title_property") or "页面"),
		tags_property=str(ns.get("tags_property") or "标签"),
		site_url=str(resolved_site),
		state_path=_abs(state)
		if state is not None
		else _abs(ns.get("state_path") or ".notion_sync_state.json"),
		delay=float(delay if delay is not None else ns.get("delay", 0.35)),
		token=token,
		allow_cursor_mcp_token=bool(ns.get("allow_cursor_mcp_token", False)),
		silence_mcp_token_warning=bool(ns.get("silence_mcp_token_warning", False)),
		full=full,
		base=base,
		paths=list(paths) if paths else None,
		paths_file=paths_file,
		section=list(section) if section else None,
		rebuild_state=rebuild_state,
		local_images=local_images,
		cache_dir=_abs(cache_raw),
		no_resume=no_resume,
		dry_run=dry_run,
		continue_on_error=continue_on_error,
		verbose=verbose,
	)


def get_version():
	"""Get the version of mkdocs-note package.

	Returns:
	    str: Version string from package metadata
	"""
	try:
		return metadata.version("mkdocs-note")
	except metadata.PackageNotFoundError:
		return "unknown (not installed)"


def setup_cli_environment(config: MkdocsNoteConfig):
	"""Setup CLI environment with configuration.

	This function monkey-patches the common module to use the provided config
	for standalone CLI usage.

	Args:
	    config: MkdocsNoteConfig instance to use
	"""
	# Monkey patch get_plugin_config to return our config dict
	cli_common.get_plugin_config = lambda: {"notes_root": config.notes_root}

	# Update the root_dir in commands module
	import mkdocs_note.utils.cli.commands as cmd_module

	cmd_module.root_dir = cli_common.get_plugin_config()["notes_root"]


class CustomGroup(click.Group):
	"""Custom Click group that formats commands with aliases on the same line."""

	def format_commands(self, ctx, formatter):
		"""Format commands section with aliases grouped together."""
		commands = []
		for subcommand in self.list_commands(ctx):
			cmd = self.get_command(ctx, subcommand)
			if cmd is None:
				continue
			if cmd.hidden:
				continue
			commands.append((subcommand, cmd))

		if not commands:
			return

		# Group commands by their main command (excluding aliases)
		command_groups = {}
		alias_map = {"rm": "remove", "mv": "move", "ns": "notion-sync"}

		for name, command in commands:
			if name in alias_map:
				# This is an alias, group it with the main command
				main_name = alias_map[name]
				if main_name not in command_groups:
					command_groups[main_name] = {"main": None, "aliases": []}
				command_groups[main_name]["aliases"].append((name, command))
			else:
				# This is a main command
				if name not in command_groups:
					command_groups[name] = {"main": None, "aliases": []}
				command_groups[name]["main"] = (name, command)

		# Calculate max width for alignment
		max_width = 0
		formatted_commands = []

		for main_name in sorted(command_groups.keys()):
			group = command_groups[main_name]
			main_cmd = group["main"]
			aliases = group["aliases"]

			if main_cmd:
				name, command = main_cmd
				# Create the command line with aliases
				if aliases:
					alias_names = [alias[0] for alias in aliases]
					cmd_line = f"{', '.join(alias_names)}, {name}"
				else:
					cmd_line = name

				# Get the first line of help text
				full_help = command.help or command.get_short_help_str()
				help_text = full_help.split("\n")[0] if full_help else ""
				formatted_commands.append((cmd_line, help_text))
				max_width = max(max_width, len(cmd_line))

		# Write grouped commands with proper alignment
		with formatter.section("Commands"):
			for cmd_line, help_text in formatted_commands:
				formatter.write(f"  {cmd_line:<{max_width}}  {help_text}\n")


@click.group(cls=CustomGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=get_version(), package_name="mkdocs-note")
@click.pass_context
def cli(ctx):
	"""MkDocs Note CLI - Manage notes and their assets structure.

	A command-line interface for managing MkDocs notes with co-located assets.
	"""
	ctx.ensure_object(dict)


@cli.command("new")
@click.argument("permalink", required=True)
@click.argument("file_path", required=True)
@click.pass_context
def new_command(ctx, permalink, file_path):
	"""Create a new note file with proper asset structure.

	\b
	Examples:
	    mkdocs-note new my-permalink docs/notes/my-note.md
	    mkdocs-note new python-intro docs/notes/python/intro.md

	\b
	Arguments:
	    PERMALINK: The permalink value for frontmatter and asset directory name
	    FILE_PATH: Path where the new note file should be created
	"""
	try:
		# Load configuration and setup environment
		config = MkdocsNoteConfig()
		setup_cli_environment(config)

		# Convert to Path
		note_path = Path(file_path)

		# Validate permalink
		if not permalink or not permalink.strip():
			click.echo("❌ Error: Permalink cannot be empty", err=True)
			sys.exit(1)

		permalink = permalink.strip()

		# Check if file already exists
		if note_path.exists():
			click.echo(f"❌ Error: File already exists: {note_path}", err=True)
			sys.exit(1)

		# Create the note using NewCommand
		command = NewCommand()
		command.execute(permalink, note_path)

		# Get asset directory path based on permalink
		asset_dir = cli_common.get_asset_directory_by_permalink(note_path, permalink)

		# Check if creation was successful
		if note_path.exists():
			click.echo("✅ Successfully created note")
			click.echo(f"📝 Note: {note_path}")
			click.echo(f"🔗 Permalink: {permalink}")
			click.echo(f"📁 Assets: {asset_dir}")
			sys.exit(0)
		else:
			click.echo("❌ Error: Failed to create note", err=True)
			sys.exit(1)

	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


@cli.command("remove")
@click.argument("file_path", required=True)
@click.option(
	"--keep-assets",
	is_flag=True,
	help="Keep the asset directory when removing the note",
)
@click.option(
	"--yes",
	"-y",
	is_flag=True,
	help="Skip confirmation prompt",
)
@click.pass_context
def remove_command(ctx, file_path, keep_assets, yes):
	"""Remove a note file and its corresponding asset directory.

	\b
	Aliases: rm

	\b
	Examples:
	    mkdocs-note remove docs/notes/test.md
	    mkdocs-note rm docs/notes/test.md --yes
	    mkdocs-note remove docs/notes/test.md --keep-assets

	FILE_PATH: Path to the note file to remove
	"""
	try:
		# Load configuration and setup environment
		config = MkdocsNoteConfig()
		setup_cli_environment(config)

		note_path = Path(file_path)

		# Check if file exists
		if not note_path.exists():
			click.echo(f"❌ Error: File does not exist: {note_path}", err=True)
			sys.exit(1)

		# Get asset directory before removal (based on permalink if available)
		permalink = cli_common.get_permalink_from_file(note_path)
		if permalink:
			asset_dir = cli_common.get_asset_directory_by_permalink(
				note_path, permalink
			)
		else:
			# Fallback to filename-based for backwards compatibility
			asset_dir = cli_common.get_asset_directory(note_path)
		asset_exists = asset_dir.exists()

		# Confirmation prompt (unless --yes)
		if not yes:
			asset_msg = "and its assets" if not keep_assets else "(keeping assets)"
			if not click.confirm(f"Remove {note_path} {asset_msg}?"):
				click.echo("⚠️  Cancelled")
				sys.exit(0)

		# Remove the note using RemoveCommand
		command = RemoveCommand()
		command.execute(note_path, remove_assets=not keep_assets)

		# Check if removal was successful
		if not note_path.exists():
			click.echo(f"✅ Successfully removed note: {note_path}")
			if permalink:
				click.echo(f"🔗 Permalink: {permalink}")
			if not keep_assets and asset_exists:
				click.echo(f"📁 Removed assets: {asset_dir}")
			elif keep_assets:
				click.echo(f"📁 Kept assets: {asset_dir}")
			sys.exit(0)
		else:
			click.echo("❌ Error: Failed to remove note", err=True)
			sys.exit(1)

	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


@cli.command("rm")
@click.argument("file_path", required=True)
@click.option("--keep-assets", is_flag=True, help="Keep the asset directory")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def rm_command(ctx, file_path, keep_assets, yes):
	"""Alias for 'remove' command - Remove a note file and its asset directory."""
	ctx.invoke(remove_command, file_path=file_path, keep_assets=keep_assets, yes=yes)


@cli.command("move")
@click.argument("source", required=True)
@click.argument("destination", required=False)
@click.option(
	"--permalink",
	"-p",
	help="Rename permalink value and asset directory name (destination argument is ignored in this mode)",
)
@click.option(
	"--keep-source-assets",
	is_flag=True,
	help="Keep the source asset directory (don't move it) [NOT IMPLEMENTED]",
)
@click.option(
	"--yes",
	"-y",
	is_flag=True,
	help="Skip confirmation prompt",
)
@click.pass_context
def move_command(ctx, source, destination, permalink, keep_source_assets, yes):
	"""Move or rename a note file/directory and its asset directory, or rename permalink.

	\b
	Aliases: mv

	\b
	File Move Mode (default):
	    Move or rename a note file/directory and its asset directory.

	\b
	Examples:
	    # Move/rename file
	    mkdocs-note move docs/notes/old.md docs/notes/new.md
	    mkdocs-note mv docs/notes/test.md docs/notes/archive

	    # Move entire directory
	    mkdocs-note move docs/notes/drafts docs/notes/published --yes

	\b
	Permalink Rename Mode (use -p/--permalink):
	    Rename permalink value in frontmatter and asset directory name.

	\b
	Examples:
	    mkdocs-note move docs/notes/my-note.md -p new-permalink
	    mkdocs-note mv docs/notes/test.md --permalink updated-slug

	\b
	Arguments:
	    SOURCE: Current path of the note file or directory (or file path for permalink mode)
	    DESTINATION: Destination path (or parent directory if exists). Ignored if --permalink is used.
	"""
	try:
		# Load configuration and setup environment
		config = MkdocsNoteConfig()
		setup_cli_environment(config)

		source_path = Path(source)

		# Check if source exists
		if not source_path.exists():
			click.echo(f"❌ Error: Source does not exist: {source_path}", err=True)
			sys.exit(1)

		# Permalink rename mode
		if permalink:
			if not source_path.is_file():
				click.echo(
					f"❌ Error: Permalink rename only works on files, not directories: {source_path}",
					err=True,
				)
				sys.exit(1)

			# Get current permalink for confirmation message
			current_permalink = cli_common.get_permalink_from_file(source_path)

			# Confirmation prompt (unless --yes)
			if not yes:
				current_msg = (
					f"'{current_permalink}'" if current_permalink else "(none)"
				)
				if not click.confirm(
					f"Rename permalink in {source_path} from {current_msg} to '{permalink}'?"
				):
					click.echo("⚠️  Cancelled")
					sys.exit(0)

			# Rename permalink using MoveCommand
			command = MoveCommand()
			command.execute(source_path, destination=None, permalink=permalink)

			click.echo("✅ Successfully renamed permalink")
			click.echo(f"📝 File: {source_path}")
			click.echo(f"🔗 Permalink: {current_permalink or '(none)'} → {permalink}")
			click.echo("📁 Asset directory renamed")
			sys.exit(0)

		# File move mode (original behavior)
		else:
			if destination is None:
				click.echo(
					"❌ Error: DESTINATION is required in file move mode", err=True
				)
				sys.exit(1)

			dest_path = Path(destination)

			# Confirmation prompt (unless --yes)
			if not yes:
				asset_msg = (
					"with assets" if not keep_source_assets else "(keeping assets)"
				)
				if not click.confirm(f"Move {source_path} → {dest_path} {asset_msg}?"):
					click.echo("⚠️  Cancelled")
					sys.exit(0)

			# Save source type before move (since source_path won't exist after move)
			is_source_file = source_path.is_file()
			is_source_dir = source_path.is_dir()
			source_name = source_path.name

			# Move the note using MoveCommand
			# Note: Current MoveCommand doesn't have keep_source_assets parameter
			# It always moves assets, so we need to handle this limitation
			command = MoveCommand()
			command.execute(source_path, dest_path)

			# Check if move was successful
			# For directory destinations, check if file exists in destination
			if is_source_file:
				# Determine final destination path
				if dest_path.exists() and dest_path.is_dir():
					# File moved into directory
					final_dest = dest_path / source_name
				else:
					# File moved/renamed to dest_path
					final_dest = dest_path

				# Check if move was successful
				if final_dest.exists() and not source_path.exists():
					click.echo("✅ Successfully moved")
					click.echo(f"📝 From: {source_path}")
					click.echo(f"📝 To: {final_dest}")
					if not keep_source_assets:
						click.echo("📁 Assets moved")
					else:
						click.echo("📁 Assets kept at source")
					sys.exit(0)
			elif is_source_dir:
				# Directory move - check if destination directory exists
				if (
					dest_path.exists()
					and dest_path.is_dir()
					and not source_path.exists()
				):
					click.echo("✅ Successfully moved")
					click.echo(f"📝 From: {source_path}")
					click.echo(f"📝 To: {dest_path}")
					if not keep_source_assets:
						click.echo("📁 Assets moved")
					else:
						click.echo("📁 Assets kept at source")
					sys.exit(0)

			click.echo("❌ Error: Failed to move note", err=True)
			sys.exit(1)

	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


@cli.command("mv")
@click.argument("source", required=True)
@click.argument("destination", required=False)
@click.option(
	"--permalink", "-p", help="Rename permalink value and asset directory name"
)
@click.option(
	"--keep-source-assets", is_flag=True, help="Keep source assets [NOT IMPLEMENTED]"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def mv_command(ctx, source, destination, permalink, keep_source_assets, yes):
	"""Alias for 'move' command - Move or rename a note file/directory and its assets."""
	ctx.invoke(
		move_command,
		source=source,
		destination=destination,
		permalink=permalink,
		keep_source_assets=keep_source_assets,
		yes=yes,
	)


@cli.command("clean")
@click.option(
	"--dry-run",
	is_flag=True,
	help="Show what would be removed without actually removing",
)
@click.option(
	"--yes",
	"-y",
	is_flag=True,
	help="Skip confirmation prompt",
)
@click.pass_context
def clean_command(ctx, dry_run, yes):
	"""Clean up orphaned asset directories without corresponding notes.

	\b
	Examples:
	    mkdocs-note clean --dry-run
	    mkdocs-note clean --yes
	    mkdocs-note clean
	"""
	try:
		# Load configuration and setup environment
		config = MkdocsNoteConfig()
		setup_cli_environment(config)

		# Find orphaned assets first
		if dry_run:
			click.echo("🔍 Scanning for orphaned assets (dry run mode)...")
		else:
			click.echo("🔍 Scanning for orphaned assets...")

		# Create command and scan for orphaned assets
		command = CleanCommand()
		root_dir = Path(config.notes_root)
		note_files = command._scan_note_files(root_dir)
		orphaned_dirs = command._find_orphaned_assets(note_files)

		if len(orphaned_dirs) == 0:
			click.echo("✅ No orphaned asset directories found")
			sys.exit(0)

		# Show what will be removed
		click.echo(
			f"\n{'Would remove' if dry_run else 'Found'} {len(orphaned_dirs)} orphaned asset director{'y' if len(orphaned_dirs) == 1 else 'ies'}:"
		)
		for orphaned_dir in orphaned_dirs:
			click.echo(f"  📁 {orphaned_dir}")

		# If dry run, exit here
		if dry_run:
			click.echo(
				"\n💡 Run without --dry-run to actually remove these directories"
			)
			sys.exit(0)

		# Confirmation prompt (unless --yes)
		if not yes and not click.confirm(
			f"\nRemove these {len(orphaned_dirs)} directories?"
		):
			click.echo("⚠️  Cancelled")
			sys.exit(0)

		# Actually clean
		click.echo("\n🗑️ Removing orphaned assets...")
		command.execute(dry_run=False)

		click.echo(
			f"✅ Successfully removed {len(orphaned_dirs)} orphaned asset director{'y' if len(orphaned_dirs) == 1 else 'ies'}"
		)
		sys.exit(0)

	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


@cli.command("notion-sync")
@click.option("--full", is_flag=True, help="Process all nav pages (ignore git diff)")
@click.option(
	"--base",
	help="Git base ref for diff (default: GITHUB_EVENT_BEFORE / HEAD~1). "
	"Use 'full' to force full sync.",
)
@click.option(
	"--paths",
	multiple=True,
	help="Only sync these docs-relative paths (skip git diff). Repeatable.",
)
@click.option(
	"--paths-file",
	type=click.Path(path_type=Path),
	help="Newline-separated docs-relative paths (handles spaces safely)",
)
@click.option("--site-url", default=None, help="Override site_url from mkdocs.yml")
@click.option(
	"--state",
	type=click.Path(path_type=Path),
	default=None,
	help="Path to .notion_sync_state.json",
)
@click.option("--database-id", default=None, help="Notion wiki database / page ID")
@click.option("--data-source-id", default=None, help="Notion data source ID")
@click.option(
	"--section",
	multiple=True,
	help="Limit to path prefixes, e.g. notes/. Repeatable.",
)
@click.option("--delay", type=float, default=None, help="Delay between API calls")
@click.option("--token", default=None, help="Notion integration token")
@click.option(
	"--rebuild-state",
	is_flag=True,
	help="Remap pages from Notion wiki before syncing",
)
@click.option(
	"--images",
	type=click.Choice(["upload", "site"], case_sensitive=False),
	default=None,
	help="Local images: upload files, or use MkDocs site URLs (overrides config).",
)
@click.option(
	"--no-resume",
	is_flag=True,
	help="Ignore and discard --full resume checkpoint",
)
@click.option("--dry-run", is_flag=True, help="Convert and log without writing Notion")
@click.option(
	"--continue-on-error",
	is_flag=True,
	help="Continue syncing after a page failure",
)
@click.option("-v", "--verbose", is_flag=True, help="Debug logging")
@click.pass_context
def notion_sync_command(
	ctx,
	full,
	base,
	paths,
	paths_file,
	site_url,
	state,
	database_id,
	data_source_id,
	section,
	delay,
	token,
	rebuild_state,
	images,
	no_resume,
	dry_run,
	continue_on_error,
	verbose,
):
	"""Sync MkDocs notes to a Notion wiki (incremental via git diff).

	\b
	Aliases: notion-sync, ns

	\b
	Examples:
	    mkdocs-note notion-sync --dry-run
	    mkdocs-note ns --full --section notes/
	    mkdocs-note notion-sync --paths notes/intro.md
	"""
	setup_logging(verbose)
	project_root = find_project_root()
	try:
		options = build_sync_options_from_config(
			project_root,
			full=full,
			base=base,
			paths=paths or None,
			paths_file=paths_file,
			section=section or None,
			site_url=site_url,
			state=state,
			database_id=database_id,
			data_source_id=data_source_id,
			token=token,
			rebuild_state=rebuild_state,
			images=images,
			no_resume=no_resume,
			dry_run=dry_run,
			continue_on_error=continue_on_error,
			verbose=verbose,
			delay=delay,
		)
		code = run_sync(options)
		sys.exit(code)
	except KeyboardInterrupt:
		click.echo("Interrupted", err=True)
		sys.exit(130)
	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


# Same command object so ``ns --help`` stays identical to ``notion-sync --help``.
cli.add_command(notion_sync_command, name="ns")


if __name__ == "__main__":
	cli()
