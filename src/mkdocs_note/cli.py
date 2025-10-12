#!/usr/bin/env python3
"""
Standalone CLI for MkDocs-Note plugin.

This module provides command-line interface for note management
independent of MkDocs plugin system.
"""

import sys
import os
from pathlib import Path
from typing import Optional
import click

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mkdocs_note.config import PluginConfig, load_config_from_mkdocs_yml
from mkdocs_note.logger import Logger
from mkdocs_note.core.note_initializer import NoteInitializer
from mkdocs_note.core.note_creator import NoteCreator
from mkdocs_note.core.note_remover import NoteRemover
from mkdocs_note.core.note_cleaner import NoteCleaner
from mkdocs_note.core.notes_mover import NoteMover


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to mkdocs.yml config file')
@click.pass_context
def cli(ctx, config):
    """MkDocs-Note CLI - Manage notes and their asset structure."""
    # Load configuration
    ctx.ensure_object(dict)
    logger = Logger()
    
    try:
        if config:
            # Load config from specified file
            plugin_config = load_config_from_mkdocs_yml(Path(config))
            logger.debug(f"Loaded configuration from: {config}")
        else:
            # Try to find and load mkdocs.yml automatically
            plugin_config = load_config_from_mkdocs_yml()
            if plugin_config:
                logger.debug("Automatically found and loaded mkdocs.yml configuration")
    except FileNotFoundError as e:
        logger.error(str(e))
        click.echo(f"❌ {e}")
        raise click.Abort()
    except ValueError as e:
        logger.error(f"Failed to parse config: {e}")
        click.echo(f"❌ {e}")
        raise click.Abort()
    
    ctx.obj['config'] = plugin_config
    ctx.obj['logger'] = logger


@cli.command("init")
@click.option(
    "--path", 
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help="Path to the notes directory to initialize (defaults to config.notes_dir)"
)
@click.pass_context
def init_note(ctx, path: Optional[str] = None):
    """Initialize the note directory with proper asset tree structure.
    
    This command will:
    - Create the notes directory if it doesn't exist
    - Analyze existing asset structures
    - Fix non-compliant asset trees to match the plugin's design
    - Create an index file with proper markers
    
    \b
    Examples:
        mkdocs-note init
        mkdocs-note init --path docs/notes
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    notes_dir = Path(path) if path else Path(config.notes_dir)
    
    logger.info(f"Initializing note directory: {notes_dir}")
    
    initializer = NoteInitializer(config, logger)
    result = initializer.initialize_note_directory(notes_dir)
    
    if result == 0:
        # logger.info(f"Successfully initialized the note directory at {notes_dir}")
        click.echo(f"✅ Note directory initialized successfully at {notes_dir}")
        
        # Check template file status
        template_path = Path(config.notes_template)
        if template_path.exists():
            click.echo(f"📄 Template file found: {template_path}")
        else:
            click.echo(f"⚠️  Template file not found: {template_path}")
            click.echo("💡 Please create the template file or update the 'notes_template' configuration")
    else:
        # logger.error(f"Failed to initialize the note directory at {notes_dir}")
        click.echo(f"❌ Failed to initialize the note directory at {notes_dir}")
        raise click.Abort()


@cli.command("new")
@click.argument("file_path", type=click.Path())
@click.option(
    "--template",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to a custom template file"
)
@click.pass_context
def new_note(ctx, file_path: str, template: Optional[str] = None):
    """Create a new note file with proper asset structure.
    
    This command will:
    - Validate that the asset tree structure is compliant
    - Create the note file with template content
    - Create the corresponding asset directory
    - Set up proper asset management structure
    
    \b
    Examples:
        mkdocs-note new docs/notes/my-note.md
        mkdocs-note new docs/notes/python/intro.md
        mkdocs-note new docs/notes/test.md --template custom-template.md
    
    FILE_PATH: Path where the new note file should be created
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    note_path = Path(file_path)
    template_path = Path(template) if template else None
    
    creator = NoteCreator(config, logger)
    
    # Validate before creating
    is_valid, error_msg = creator.validate_note_creation(note_path)
    if not is_valid:
        # logger.error(f"Cannot create note: {error_msg}")
        click.echo(f"❌ Cannot create note: {error_msg}")
        click.echo("💡 Try running 'mkdocs-note init' first to initialize the directory structure")
        raise click.Abort()
    
    logger.info(f"Creating new note: {note_path}")
    
    result = creator.create_new_note(note_path, template_path)
    
    if result == 0:
        # logger.info(f"Successfully created a new note at {note_path}")
        click.echo(f"✅ Successfully created note: {note_path}")
        click.echo(f"📁 Asset directory created: {creator._get_asset_directory(note_path)}")
    else:
        # logger.error(f"Failed to create a new note at {note_path}")
        click.echo(f"❌ Failed to create note at {note_path}")
        raise click.Abort()


@cli.command("validate")
@click.option(
    "--path", 
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the notes directory to validate (defaults to config.notes_dir)"
)
@click.pass_context
def validate_notes(ctx, path: Optional[str] = None):
    """Validate the asset tree structure compliance.
    
    This command checks if the current asset tree structure
    complies with the plugin's design requirements.
    
    \b
    Examples:
        mkdocs-note validate
        mkdocs-note validate --path docs/notes
    """
    from mkdocs_note.core.file_manager import NoteScanner
    
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    notes_dir = Path(path) if path else Path(config.notes_dir)
    
    logger.info(f"Validating asset tree structure: {notes_dir}")
    
    # Scan and display note count
    scanner = NoteScanner(config, logger)
    note_files = scanner.scan_notes()
    click.echo(f"📝 Found {len(note_files)} note files")
    
    # Validate asset tree structure
    initializer = NoteInitializer(config, logger)
    is_compliant, error_messages = initializer.validate_asset_tree_compliance(notes_dir)
    
    if is_compliant:
        # logger.info("Asset tree structure is compliant")
        click.echo("✅ Asset tree structure is compliant with plugin design")
    else:
        # logger.warning("Asset tree structure is not compliant")
        click.echo("❌ Asset tree structure is not compliant:")
        for error in error_messages:
            click.echo(f"  • {error}")
        click.echo("💡 Run 'mkdocs-note init' to fix the structure")


@cli.command("template")
@click.option(
    "--check", 
    is_flag=True,
    help="Check if the configured template file exists"
)
@click.option(
    "--create", 
    is_flag=True,
    help="Create the template file if it doesn't exist"
)
@click.pass_context
def template_command(ctx, check: bool = False, create: bool = False):
    """Manage the note template file.
    
    This command helps you check and create the template file
    configured in your mkdocs.yml.
    
    \b
    Examples:
        mkdocs-note template
        mkdocs-note template --check
        mkdocs-note template --create
    """
    config = ctx.obj['config']
    
    template_path = Path(config.notes_template)
    
    if check or not (check or create):
        # Default behavior: check template status
        if template_path.exists():
            click.echo(f"✅ Template file exists: {template_path}")
            try:
                content = template_path.read_text(encoding='utf-8')
                click.echo(f"📄 Template size: {len(content)} characters")
                if "{{title}}" in content and "{{date}}" in content:
                    click.echo("✅ Template contains required variables ({{title}}, {{date}})")
                else:
                    click.echo("⚠️  Template may be missing required variables ({{title}}, {{date}})")
            except Exception as e:
                click.echo(f"❌ Error reading template file: {e}")
        else:
            click.echo(f"❌ Template file not found: {template_path}")
            click.echo("💡 Use 'mkdocs-note template --create' to create it")
    
    if create:
        # Create template file
        if template_path.exists():
            click.echo(f"⚠️  Template file already exists: {template_path}")
            if not click.confirm("Do you want to overwrite it?"):
                return
        
        # Ensure parent directory exists
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Use new frontmatter-style template
            template_content = """---
date: {{date}}
title: {{title}}
permalink: 
publish: true
---

# {{title}}

Start writing your note content..."""
            template_path.write_text(template_content, encoding='utf-8')
            click.echo(f"✅ Template file created: {template_path}")
        except Exception as e:
            click.echo(f"❌ Failed to create template file: {e}")
            raise click.Abort()


@cli.command("remove")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--keep-assets",
    is_flag=True,
    help="Keep the asset directory (only remove the note file)"
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Skip confirmation prompt"
)
@click.pass_context
def remove_note(ctx, file_path: str, keep_assets: bool = False, yes: bool = False):
    """Remove a note file and its corresponding asset directory.
    
    \b
    Aliases: rm
    
    This command will:
    - Delete the specified note file
    - Delete the corresponding asset directory (unless --keep-assets is specified)
    - Clean up empty parent directories
    
    \b
    Examples:
        mkdocs-note remove docs/notes/test.md
        mkdocs-note rm docs/notes/test.md --yes
        mkdocs-note remove docs/notes/test.md --keep-assets
    
    FILE_PATH: Path to the note file to remove
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    note_path = Path(file_path)
    
    # Validate it's a note file
    if note_path.suffix.lower() not in config.supported_extensions:
        logger.error(f"Not a supported note file: {note_path}")
        click.echo(f"❌ Not a supported note file: {note_path}")
        click.echo(f"💡 Supported extensions: {', '.join(config.supported_extensions)}")
        raise click.Abort()
    
    # Show what will be removed
    remover = NoteRemover(config, logger)
    asset_dir = remover._get_asset_directory(note_path)
    
    click.echo(f"📝 Note file: {note_path}")
    if not keep_assets and asset_dir.exists():
        click.echo(f"📁 Asset directory: {asset_dir}")
    elif not keep_assets:
        click.echo(f"📁 Asset directory: {asset_dir} (doesn't exist)")
    
    # Confirm removal
    if not yes:
        if not click.confirm("⚠️  Are you sure you want to remove this note?"):
            click.echo("❌ Operation cancelled")
            return
    
    # Perform removal
    logger.info(f"Removing note: {note_path}")
    result = remover.remove_note(note_path, remove_assets=not keep_assets)
    
    if result == 0:
        click.echo(f"✅ Successfully removed note: {note_path}")
        if not keep_assets and asset_dir.exists():
            click.echo(f"✅ Successfully removed asset directory: {asset_dir}")
    else:
        click.echo(f"❌ Failed to remove note")
        raise click.Abort()


@cli.command("clean")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be removed without actually removing"
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Skip confirmation prompt"
)
@click.pass_context
def clean_orphaned(ctx, dry_run: bool = False, yes: bool = False):
    """Clean up orphaned asset directories without corresponding notes.
    
    This command will:
    - Scan all note files in the notes directory
    - Scan all asset directories
    - Find asset directories that don't have corresponding note files
    - Remove orphaned asset directories (unless --dry-run is specified)
    - Clean up empty parent directories
    
    \b
    Examples:
        mkdocs-note clean --dry-run
        mkdocs-note clean --yes
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    logger.info("Scanning for orphaned asset directories...")
    click.echo("🔍 Scanning for orphaned asset directories...")
    
    cleaner = NoteCleaner(config, logger)
    orphaned_dirs = cleaner.find_orphaned_assets()
    
    if not orphaned_dirs:
        logger.info("No orphaned asset directories found")
        click.echo("✅ No orphaned asset directories found")
        return
    
    # Show what will be removed
    click.echo(f"\n📦 Found {len(orphaned_dirs)} orphaned asset director{'y' if len(orphaned_dirs) == 1 else 'ies'}:")
    for asset_dir in orphaned_dirs:
        click.echo(f"  • {asset_dir}")
    
    # Confirm removal
    if not dry_run and not yes:
        click.echo(f"\n⚠️  This will remove {len(orphaned_dirs)} asset director{'y' if len(orphaned_dirs) == 1 else 'ies'}")
        if not click.confirm("Are you sure you want to continue?"):
            click.echo("❌ Operation cancelled")
            return
    
    # Perform cleanup
    count, removed = cleaner.clean_orphaned_assets(dry_run=dry_run)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would remove {count} orphaned asset directories")
        click.echo(f"\n💡 [DRY RUN] Would remove {count} orphaned asset director{'y' if count == 1 else 'ies'}")
        click.echo("Run without --dry-run to actually remove them")
    else:
        logger.info(f"Successfully removed {count} orphaned asset directories")
        click.echo(f"\n✅ Successfully removed {count} orphaned asset director{'y' if count == 1 else 'ies'}")


@cli.command("move")
@click.argument("source", type=click.Path(exists=True))
@click.argument("destination", type=click.Path())
@click.option(
    "--keep-source-assets",
    is_flag=True,
    help="Keep the source asset directory (only move the note file/directory)"
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Skip confirmation prompt"
)
@click.pass_context
def move_note(ctx, source: str, destination: str, keep_source_assets: bool = False, yes: bool = False):
    """Move or rename a note file/directory and its asset directory.
    
    \b
    Aliases: mv
    
    This command mimics shell 'mv' behavior:
    - If destination doesn't exist: rename source to destination
    - If destination exists and is a directory: move source into destination
    - Move the corresponding asset directories (unless --keep-source-assets is specified)
    - Support moving entire directories with all notes inside
    - Create necessary parent directories
    - Clean up empty parent directories in the source location
    
    \b
    Examples:
        # Rename a note or directory
        mkdocs-note move docs/notes/old.md docs/notes/new.md
        mkdocs-note mv docs/notes/dsa/tree docs/notes/dsa/trees
        
        # Move into an existing directory
        mkdocs-note mv docs/notes/dsa/ds/trees docs/notes/dsa
        # → moves to docs/notes/dsa/trees
        
        mkdocs-note move docs/notes/test.md docs/notes/archive
        # → moves to docs/notes/archive/test.md
        
        # Move a directory with all notes inside
        mkdocs-note move docs/notes/old_category docs/notes/new_category
        
        # Move without moving assets
        mkdocs-note mv docs/notes/test.md docs/notes/new.md --keep-source-assets
    
    \b
    Arguments:
        SOURCE: Current path of the note file or directory
        DESTINATION: Destination path (or parent directory if exists)
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    source_path = Path(source)
    dest_path = Path(destination)
    
    # Show what will be moved
    mover = NoteMover(config, logger)
    
    # Adjust destination path if it exists and is a directory (mimics shell mv behavior)
    original_dest = dest_path
    if dest_path.exists() and dest_path.is_dir():
        dest_path = dest_path / source_path.name
        click.echo(f"💡 Destination is a directory, will move to: {dest_path}")
    
    # Validate adjusted destination doesn't exist
    if dest_path.exists():
        logger.error(f"Destination already exists: {dest_path}")
        click.echo(f"❌ Destination already exists: {dest_path}")
        raise click.Abort()
    
    if source_path.is_dir():
        # Moving a directory
        click.echo(f"📁 Source directory: {source_path}")
        click.echo(f"📁 Destination directory: {dest_path}")
        
        # Count notes in directory
        note_count = 0
        for file_path in source_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in config.supported_extensions:
                if file_path.name not in config.exclude_patterns:
                    note_count += 1
        
        if note_count == 0:
            click.echo(f"⚠️  No note files found in directory: {source_path}")
            if not yes and not click.confirm("Continue anyway?"):
                click.echo("❌ Operation cancelled")
                return
        else:
            click.echo(f"📝 Found {note_count} note file(s) to move")
    else:
        # Moving a single file
        source_asset_dir = mover._get_asset_directory(source_path)
        dest_asset_dir = mover._get_asset_directory(dest_path)
        
        click.echo(f"📝 Source note: {source_path}")
        click.echo(f"📝 Destination note: {dest_path}")
        
        if not keep_source_assets:
            if source_asset_dir.exists():
                click.echo(f"📁 Source assets: {source_asset_dir}")
                click.echo(f"📁 Destination assets: {dest_asset_dir}")
            else:
                click.echo(f"📁 No existing asset directory to move")
    
    # Confirm move
    if not yes:
        prompt = "\n⚠️  Are you sure you want to move this "
        prompt += "directory?" if source_path.is_dir() else "note?"
        if not click.confirm(prompt):
            click.echo("❌ Operation cancelled")
            return
    
    # Perform move
    if source_path.is_dir():
        logger.info(f"Moving directory: {source_path} → {dest_path}")
    else:
        logger.info(f"Moving note: {source_path} → {dest_path}")
    
    result = mover.move_note_or_directory(source_path, original_dest, move_assets=not keep_source_assets)
    
    if result == 0:
        if source_path.is_dir():
            click.echo(f"✅ Successfully moved directory: {source_path} → {dest_path}")
        else:
            click.echo(f"✅ Successfully moved note: {source_path} → {dest_path}")
        
        if not keep_source_assets:
            click.echo(f"✅ Successfully moved asset directories")
    else:
        click.echo(f"❌ Failed to move")
        raise click.Abort()


# Add aliases for common commands
@cli.command("rm")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--keep-assets", is_flag=True, help="Keep the asset directory")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def rm_note(ctx, file_path: str, keep_assets: bool = False, yes: bool = False):
    """Alias for 'remove' command - Remove a note file and its asset directory."""
    ctx.invoke(remove_note, file_path=file_path, keep_assets=keep_assets, yes=yes)


@cli.command("mv")
@click.argument("source", type=click.Path(exists=True))
@click.argument("destination", type=click.Path())
@click.option("--keep-source-assets", is_flag=True, help="Keep the source asset directory")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def mv_note(ctx, source: str, destination: str, keep_source_assets: bool = False, yes: bool = False):
    """Alias for 'move' command - Move or rename a note file/directory and its assets."""
    ctx.invoke(move_note, source=source, destination=destination, 
               keep_source_assets=keep_source_assets, yes=yes)


if __name__ == '__main__':
    cli()
