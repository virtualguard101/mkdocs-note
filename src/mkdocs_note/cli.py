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

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.note_initializer import NoteInitializer
from mkdocs_note.core.note_creator import NoteCreator


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to mkdocs.yml config file')
@click.pass_context
def cli(ctx, config):
    """MkDocs-Note CLI - Manage notes and their asset structure."""
    # Load configuration
    if config:
        # TODO: Parse mkdocs.yml to extract plugin config
        pass
    
    ctx.ensure_object(dict)
    ctx.obj['config'] = PluginConfig()
    ctx.obj['logger'] = Logger()


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
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    notes_dir = Path(path) if path else Path(config.notes_dir)
    
    logger.info(f"Initializing note directory: {notes_dir}")
    
    initializer = NoteInitializer(config, logger)
    result = initializer.initialize_note_directory(notes_dir)
    
    if result == 0:
        logger.info(f"Successfully initialized the note directory at {notes_dir}")
        click.echo(f"✅ Note directory initialized successfully at {notes_dir}")
        
        # Check template file status
        template_path = Path(config.notes_template)
        if template_path.exists():
            click.echo(f"📄 Template file found: {template_path}")
        else:
            click.echo(f"⚠️  Template file not found: {template_path}")
            click.echo("💡 Please create the template file or update the 'notes_template' configuration")
    else:
        logger.error(f"Failed to initialize the note directory at {notes_dir}")
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
        logger.error(f"Cannot create note: {error_msg}")
        click.echo(f"❌ Cannot create note: {error_msg}")
        click.echo("💡 Try running 'mkdocs-note init' first to initialize the directory structure")
        raise click.Abort()
    
    logger.info(f"Creating new note: {note_path}")
    
    result = creator.create_new_note(note_path, template_path)
    
    if result == 0:
        logger.info(f"Successfully created a new note at {note_path}")
        click.echo(f"✅ Successfully created note: {note_path}")
        click.echo(f"📁 Asset directory created: {creator._get_asset_directory(note_path)}")
    else:
        logger.error(f"Failed to create a new note at {note_path}")
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
    """
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    notes_dir = Path(path) if path else Path(config.notes_dir)
    
    logger.info(f"Validating asset tree structure: {notes_dir}")
    
    initializer = NoteInitializer(config, logger)
    is_compliant, error_messages = initializer.validate_asset_tree_compliance(notes_dir)
    
    if is_compliant:
        logger.info("Asset tree structure is compliant")
        click.echo("✅ Asset tree structure is compliant with plugin design")
    else:
        logger.warning("Asset tree structure is not compliant")
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
            template_content = "# {{title}}\n\nCreated on {{date}}\n\nNote: {{note_name}}"
            template_path.write_text(template_content, encoding='utf-8')
            click.echo(f"✅ Template file created: {template_path}")
        except Exception as e:
            click.echo(f"❌ Failed to create template file: {e}")
            raise click.Abort()


if __name__ == '__main__':
    cli()
