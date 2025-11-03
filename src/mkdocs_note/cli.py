#!/usr/bin/env python3
"""
Standalone CLI for MkDocs-Note plugin.

This module provides command-line interface for note management
independent of MkDocs plugin system.
"""

import sys
import click
from importlib import metadata


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
@click.argument("file_path", required=False)
@click.pass_context
def new_command(ctx, file_path):
	"""Create a new note file with proper asset structure.

	\b
	Examples:
	    mkdocs-note new docs/notes/my-note.md
	    mkdocs-note new docs/notes/python/intro.md

	FILE_PATH: Path where the new note file should be created
	"""
	click.echo("⚠️  'new' command is not yet implemented")
	click.echo("💡 This feature is being refactored")
	sys.exit(1)


@cli.command("remove")
@click.argument("file_path", required=False)
@click.pass_context
def remove_command(ctx, file_path):
	"""Remove a note file and its corresponding asset directory.

	\b
	Aliases: rm

	\b
	Examples:
	    mkdocs-note remove docs/notes/test.md
	    mkdocs-note rm docs/notes/test.md --yes

	FILE_PATH: Path to the note file to remove
	"""
	click.echo("⚠️  'remove' command is not yet implemented")
	click.echo("💡 This feature is being refactored")
	sys.exit(1)


@cli.command("rm")
@click.argument("file_path", required=False)
@click.pass_context
def rm_command(ctx, file_path):
	"""Alias for 'remove' command - Remove a note file and its asset directory."""
	ctx.invoke(remove_command, file_path=file_path)


@cli.command("move")
@click.argument("source", required=False)
@click.argument("destination", required=False)
@click.pass_context
def move_command(ctx, source, destination):
	"""Move or rename a note file/directory and its asset directory.

	\b
	Aliases: mv

	\b
	Examples:
	    mkdocs-note move docs/notes/old.md docs/notes/new.md
	    mkdocs-note mv docs/notes/test.md docs/notes/archive

	\b
	Arguments:
	    SOURCE: Current path of the note file or directory
	    DESTINATION: Destination path (or parent directory if exists)
	"""
	click.echo("⚠️  'move' command is not yet implemented")
	click.echo("💡 This feature is being refactored")
	sys.exit(1)


@cli.command("mv")
@click.argument("source", required=False)
@click.argument("destination", required=False)
@click.pass_context
def mv_command(ctx, source, destination):
	"""Alias for 'move' command - Move or rename a note file/directory and its assets."""
	ctx.invoke(move_command, source=source, destination=destination)


@cli.command("clean")
@click.pass_context
def clean_command(ctx):
	"""Clean up orphaned asset directories without corresponding notes.

	\b
	Examples:
	    mkdocs-note clean --dry-run
	    mkdocs-note clean --yes
	"""
	click.echo("⚠️  'clean' command is not yet implemented")
	click.echo("💡 This feature is being refactored")
	sys.exit(1)


@cli.command("template")
@click.pass_context
def template_command(ctx):
	"""Manage the note template file.

	This command helps you check and create the template file
	configured in your mkdocs.yml.

	\b
	Examples:
	    mkdocs-note template
	    mkdocs-note template --check
	    mkdocs-note template --create
	"""
	click.echo("⚠️  'template' command is not yet implemented")
	click.echo("💡 This feature is being refactored")
	sys.exit(1)


if __name__ == "__main__":
	cli()
