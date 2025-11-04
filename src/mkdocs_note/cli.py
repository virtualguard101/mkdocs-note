#!/usr/bin/env python3
"""
Standalone CLI for MkDocs-Note plugin.

This module provides command-line interface for note management
independent of MkDocs plugin system.
"""

import sys
import click
from pathlib import Path
from importlib import metadata

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils.cli.new import NoteCreator
from mkdocs_note.utils.cli.remove import NoteRemover
from mkdocs_note.utils.cli.move import NoteMover
from mkdocs_note.utils.cli.clean import NoteCleaner


def get_version():
	"""Get the version of mkdocs-note package.

	Returns:
	    str: Version string from package metadata
	"""
	try:
		return metadata.version("mkdocs-note")
	except metadata.PackageNotFoundError:
		return "unknown (not installed)"


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
		alias_map = {"rm": "remove", "mv": "move"}

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
@click.argument("file_path", required=True)
@click.option(
	"--template",
	"-t",
	type=click.Path(exists=True, path_type=Path),
	help="Custom template file to use",
)
@click.pass_context
def new_command(ctx, file_path, template):
	"""Create a new note file with proper asset structure.

	\b
	Examples:
	    mkdocs-note new docs/notes/my-note.md
	    mkdocs-note new docs/notes/python/intro.md

	FILE_PATH: Path where the new note file should be created
	"""
	try:
		# Load configuration
		config = MkdocsNoteConfig()
		creator = NoteCreator(config)

		# Convert to Path
		note_path = Path(file_path)

		# Create the note
		result = creator.create_new_note(note_path, template_path=template)

		if result.success:
			click.echo(f"✅ {result.message}")
			click.echo(f"📝 Note: {result.data['note_path']}")
			click.echo(f"📁 Assets: {result.data['asset_dir']}")
			sys.exit(0)
		else:
			click.echo(f"❌ Error: {result.message}", err=True)
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
		note_path = Path(file_path)

		# Check if file exists
		if not note_path.exists():
			click.echo(f"❌ Error: File does not exist: {note_path}", err=True)
			sys.exit(1)

		# Confirmation prompt (unless --yes)
		if not yes:
			asset_msg = "and its assets" if not keep_assets else "(keeping assets)"
			if not click.confirm(f"Remove {note_path} {asset_msg}?"):
				click.echo("⚠️  Cancelled")
				sys.exit(0)

		# Load configuration
		config = MkdocsNoteConfig()
		remover = NoteRemover(config)

		# Remove the note
		result = remover.remove_note(note_path, remove_assets=not keep_assets)

		if result.success:
			click.echo(f"✅ {result.message}")
			if result.data["removed_assets"]:
				click.echo(f"📁 Removed assets: {result.data['asset_dir']}")
			else:
				click.echo(f"📁 Kept assets: {result.data['asset_dir']}")
			sys.exit(0)
		else:
			click.echo(f"❌ Error: {result.message}", err=True)
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
@click.argument("destination", required=True)
@click.option(
	"--keep-source-assets",
	is_flag=True,
	help="Keep the source asset directory (don't move it)",
)
@click.option(
	"--yes",
	"-y",
	is_flag=True,
	help="Skip confirmation prompt",
)
@click.pass_context
def move_command(ctx, source, destination, keep_source_assets, yes):
	"""Move or rename a note file/directory and its asset directory.

	\b
	Aliases: mv

	\b
	Examples:
	    mkdocs-note move docs/notes/old.md docs/notes/new.md
	    mkdocs-note mv docs/notes/test.md docs/notes/archive
	    mkdocs-note move docs/notes/drafts docs/notes/published --yes

	\b
	Arguments:
	    SOURCE: Current path of the note file or directory
	    DESTINATION: Destination path (or parent directory if exists)
	"""
	try:
		source_path = Path(source)
		dest_path = Path(destination)

		# Check if source exists
		if not source_path.exists():
			click.echo(f"❌ Error: Source does not exist: {source_path}", err=True)
			sys.exit(1)

		# Confirmation prompt (unless --yes)
		if not yes:
			asset_msg = "with assets" if not keep_source_assets else "(keeping assets)"
			if not click.confirm(f"Move {source_path} → {dest_path} {asset_msg}?"):
				click.echo("⚠️  Cancelled")
				sys.exit(0)

		# Load configuration
		config = MkdocsNoteConfig()
		mover = NoteMover(config)

		# Move the note or directory
		result = mover.move_note_or_directory(
			source_path, dest_path, move_assets=not keep_source_assets
		)

		if result.success:
			click.echo(f"✅ {result.message}")
			if "source" in result.data and "destination" in result.data:
				click.echo(f"📝 From: {result.data['source']}")
				click.echo(f"📝 To: {result.data['destination']}")
				if "asset_moved" in result.data:
					if result.data["asset_moved"]:
						click.echo("📁 Assets moved")
					else:
						click.echo("📁 Assets kept at source")
			sys.exit(0)
		else:
			click.echo(f"❌ Error: {result.message}", err=True)
			sys.exit(1)

	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


@cli.command("mv")
@click.argument("source", required=True)
@click.argument("destination", required=True)
@click.option("--keep-source-assets", is_flag=True, help="Keep source assets")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def mv_command(ctx, source, destination, keep_source_assets, yes):
	"""Alias for 'move' command - Move or rename a note file/directory and its assets."""
	ctx.invoke(
		move_command,
		source=source,
		destination=destination,
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
		# Load configuration
		config = MkdocsNoteConfig()
		cleaner = NoteCleaner(config)

		# Find orphaned assets
		if dry_run:
			click.echo("🔍 Scanning for orphaned assets (dry run mode)...")
		else:
			click.echo("🔍 Scanning for orphaned assets...")

		result = cleaner.clean_orphaned_assets(dry_run=True)

		if result.data["removed_count"] == 0:
			click.echo("✅ No orphaned asset directories found")
			sys.exit(0)

		# Show what will be removed
		click.echo(
			f"\n{'Would remove' if dry_run else 'Found'} {result.data['removed_count']} orphaned asset director{'y' if result.data['removed_count'] == 1 else 'ies'}:"
		)
		for orphaned_dir in result.data["orphaned_dirs"]:
			click.echo(f"  📁 {orphaned_dir}")

		# If dry run, exit here
		if dry_run:
			click.echo(
				"\n💡 Run without --dry-run to actually remove these directories"
			)
			sys.exit(0)

		# Confirmation prompt (unless --yes)
		if not yes:
			if not click.confirm(
				f"\nRemove these {result.data['removed_count']} directories?"
			):
				click.echo("⚠️  Cancelled")
				sys.exit(0)

		# Actually clean
		click.echo("\n🗑️  Removing orphaned assets...")
		result = cleaner.clean_orphaned_assets(dry_run=False)

		if result.success:
			click.echo(f"✅ {result.message}")
			sys.exit(0)
		else:
			click.echo(f"❌ Error: {result.message}", err=True)
			sys.exit(1)

	except Exception as e:
		click.echo(f"❌ Unexpected error: {e}", err=True)
		sys.exit(1)


if __name__ == "__main__":
	cli()
