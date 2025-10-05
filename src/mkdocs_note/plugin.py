from __future__ import annotations

import re
import subprocess
import click
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from mkdocs.structure.files import File, Files
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.file_manager import NoteScanner, AssetScanner
from mkdocs_note.core.note_manager import NoteProcessor
from mkdocs_note.core.data_models import NoteInfo
from mkdocs_note.core.assets_manager import AssetsProcessor
from mkdocs_note.core.note_initializer import NoteInitializer
from mkdocs_note.core.note_creator import NoteCreator


class MkdocsNotePlugin(BasePlugin[PluginConfig]):
    """MkDocs plugin for managing notes.
    
    This plugin automatically inserts recent notes into the index page
    of the configured notes directory.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self._recent_notes: List[NoteInfo] = []
        self._assets_processor = None

    def get_command(self) -> click.Group:
        """Get the command group for managing notes.
        
        Returns:
            click.Group: The click command group for note management
        """
        # Initialize the backend components
        initializer = NoteInitializer(self.config, self.logger)
        creator = NoteCreator(self.config, self.logger)
        
        @click.group()
        def note():
            """Manage notes and their asset structure.
            
            This command group provides tools for initializing note directories
            and creating new notes with proper asset management.
            """
            pass

        @note.command("init")
        @click.option(
            "--path", 
            type=click.Path(exists=False, file_okay=False, dir_okay=True),
            help="Path to the notes directory to initialize (defaults to config.notes_dir)"
        )
        def init_note(path: Optional[str] = None):
            """Initialize the note directory with proper asset tree structure.
            
            This command will:
            - Create the notes directory if it doesn't exist
            - Analyze existing asset structures
            - Fix non-compliant asset trees to match the plugin's design
            - Create an index file with proper markers
            """
            notes_dir = Path(path) if path else Path(self.config.notes_dir)
            
            self.logger.info(f"Initializing note directory: {notes_dir}")
            
            result = initializer.initialize_note_directory(notes_dir)
            
            if result == 0:
                self.logger.info(f"Successfully initialized the note directory at {notes_dir}")
                click.echo(f"✅ Note directory initialized successfully at {notes_dir}")
                
                # Check template file status
                template_path = Path(self.config.notes_template)
                if template_path.exists():
                    click.echo(f"📄 Template file found: {template_path}")
                else:
                    click.echo(f"⚠️  Template file not found: {template_path}")
                    click.echo("💡 Please create the template file or update the 'notes_template' configuration")
            else:
                self.logger.error(f"Failed to initialize the note directory at {notes_dir}")
                click.echo(f"❌ Failed to initialize the note directory at {notes_dir}")
                raise click.Abort()

        @note.command("new")
        @click.argument("file_path", type=click.Path())
        @click.option(
            "--template",
            type=click.Path(exists=True, file_okay=True, dir_okay=False),
            help="Path to a custom template file"
        )
        def new_note(file_path: str, template: Optional[str] = None):
            """Create a new note file with proper asset structure.
            
            This command will:
            - Validate that the asset tree structure is compliant
            - Create the note file with template content
            - Create the corresponding asset directory
            - Set up proper asset management structure
            
            FILE_PATH: Path where the new note file should be created
            """
            note_path = Path(file_path)
            template_path = Path(template) if template else None
            
            # Validate before creating
            is_valid, error_msg = creator.validate_note_creation(note_path)
            if not is_valid:
                self.logger.error(f"Cannot create note: {error_msg}")
                click.echo(f"❌ Cannot create note: {error_msg}")
                click.echo("💡 Try running 'mkdocs note init' first to initialize the directory structure")
                raise click.Abort()
            
            self.logger.info(f"Creating new note: {note_path}")
            
            result = creator.create_new_note(note_path, template_path)
            
            if result == 0:
                self.logger.info(f"Successfully created a new note at {note_path}")
                click.echo(f"✅ Successfully created note: {note_path}")
                click.echo(f"📁 Asset directory created: {creator._get_asset_directory(note_path)}")
            else:
                self.logger.error(f"Failed to create a new note at {note_path}")
                click.echo(f"❌ Failed to create note at {note_path}")
                raise click.Abort()
        
        @note.command("validate")
        @click.option(
            "--path", 
            type=click.Path(exists=True, file_okay=False, dir_okay=True),
            help="Path to the notes directory to validate (defaults to config.notes_dir)"
        )
        def validate_notes(path: Optional[str] = None):
            """Validate the asset tree structure compliance.
            
            This command checks if the current asset tree structure
            complies with the plugin's design requirements.
            """
            notes_dir = Path(path) if path else Path(self.config.notes_dir)
            
            self.logger.info(f"Validating asset tree structure: {notes_dir}")
            
            is_compliant, error_messages = initializer.validate_asset_tree_compliance(notes_dir)
            
            if is_compliant:
                self.logger.info("Asset tree structure is compliant")
                click.echo("✅ Asset tree structure is compliant with plugin design")
            else:
                self.logger.warning("Asset tree structure is not compliant")
                click.echo("❌ Asset tree structure is not compliant:")
                for error in error_messages:
                    click.echo(f"  • {error}")
                click.echo("💡 Run 'mkdocs note init' to fix the structure")
        
        @note.command("template")
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
        def template_command(check: bool = False, create: bool = False):
            """Manage the note template file.
            
            This command helps you check and create the template file
            configured in your mkdocs.yml.
            """
            template_path = Path(self.config.notes_template)
            
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
                    click.echo("💡 Use 'mkdocs note template --create' to create it")
            
            if create:
                # Create template file
                if template_path.exists():
                    click.echo(f"⚠️  Template file already exists: {template_path}")
                    if not click.confirm("Do you want to overwrite it?"):
                        return
                
                # Ensure parent directory exists
                template_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    template_path.write_text("", encoding='utf-8')
                    click.echo(f"✅ Template file created: {template_path}")
                except Exception as e:
                    click.echo(f"❌ Failed to create template file: {e}")
                    raise click.Abort()
        
        return note
    
    @property
    def plugin_enabled(self) -> bool:
        """Check if the plugin is enabled.
        """
        return self.config.enabled
    
    @event_priority(100)
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Handle the configuration for the plugin.

        Args:
            config (MkDocsConfig): The MkDocs configuration

        Returns:
            MkDocsConfig | None: The updated MkDocs configuration
        """
        if not self.plugin_enabled:
            self.logger.debug("MkDocs-Note plugin is disabled.")
            return config
        
        # Ensure toc configuration exists
        if 'toc' not in config.mdx_configs:
            config.mdx_configs['toc'] = {}
        
        toc_config = config.mdx_configs['toc']
        
        # Ensure separator exists
        if 'separator' not in toc_config:
            toc_config['separator'] = '-'
            
        # Set slugify function
        if 'slugify' not in toc_config:
            try:
                from pymdownx.slugs import slugify
                toc_config['slugify'] = slugify
                self.logger.debug("Using pymdownx.slugs.slugify for better Material theme compatibility")
            except ImportError:
                from markdown.extensions.toc import slugify
                toc_config['slugify'] = slugify
                self.logger.debug("Using markdown.extensions.toc.slugify as fallback")

        # Initialize assets processor
        self._assets_processor = AssetsProcessor(self.config, self.logger)
        
        self.logger.info("MkDocs-Note plugin initialized successfully.")
        return config
    
    @event_priority(100)
    def on_files(self, files: Files, config: MkDocsConfig) -> Files | None:
        """Process files and collect recent notes.

        Args:
            files (Files): The files to check
            config (MkDocsConfig): The MkDocs configuration

        Returns:
            Files | None: The updated files
        """
        if not self.plugin_enabled:
            self.logger.debug("MkDocs-Note plugin is disabled.")
            return files
        
        self.logger.info("Processing files for recent notes...")
        
        try:
            # Use FileScanner to scan note files
            file_scanner = NoteScanner(self.config, self.logger)
            note_files = file_scanner.scan_notes()
            
            if not note_files:
                self.logger.warning("No note files found")
                return files
            
            # Use NoteProcessor to process note files
            note_processor = NoteProcessor(self.config, self.logger)
            notes = []
            
            for file_path in note_files:
                note_info = note_processor.process_note(file_path)
                if note_info:
                    notes.append(note_info)
            
            # Sort by modified time, get recent notes
            notes.sort(key=lambda n: n.modified_time, reverse=True)
            self._recent_notes = notes[:self.config.max_notes]
            
            self.logger.info(f"Found {len(self._recent_notes)} recent notes")
            
        except Exception as e:
            self.logger.error(f"Error processing notes: {e}")
        
        return files
    
    def on_page_markdown(self, markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str | None:
        """Process page markdown content.

        Args:
            markdown (str): The markdown content to process
            page (Page): The page to check
            config (MkDocsConfig): The MkDocs configuration
            files (Files): The files to check

        Returns:
            str | None: The updated markdown content
        """
        if not self.plugin_enabled:
            self.logger.debug("MkDocs-Note plugin is disabled.")
            return markdown
        
        self.logger.debug(f"Processing page: {page.file.src_path}")
        
        # Process assets for note pages
        if self._is_note_page(page):
            markdown = self._process_page_assets(markdown, page)
        
        # Check if it is the index page of the notes directory
        if self._is_notes_index_page(page):
            self.logger.info(f"Found notes index page: {page.file.src_path}")
            markdown = self._insert_recent_notes(markdown)
        
        return markdown
    
    def _is_notes_index_page(self, page: Page) -> bool:
        """Check if the page is the notes index page.

        Args:
            page (Page): The page to check

        Returns:
            bool: True if the page is the notes index page, False otherwise
        """
        try:
            # Check if the page path matches the configured index file
            page_src_path = page.file.src_path
            index_file_path = str(self.config.index_file)
            
            # Convert absolute path to relative path from docs directory
            if index_file_path.startswith('/'):
                # It's an absolute path, extract the relative part
                if 'docs/' in index_file_path:
                    index_relative = index_file_path.split('docs/')[1]
                else:
                    # Fallback: use the filename
                    index_relative = Path(index_file_path).name
            else:
                # It's already a relative path
                if index_file_path.startswith('docs/'):
                    index_relative = index_file_path[5:]  # Remove 'docs/' prefix
                else:
                    index_relative = index_file_path
            
            is_match = page_src_path == index_relative
            self.logger.debug(f"Page matching: '{page_src_path}' == '{index_relative}' = {is_match}")
            return is_match
        except Exception as e:
            self.logger.error(f"Error in page matching: {e}")
            return False
    
    def _insert_recent_notes(self, markdown: str) -> str:
        """Insert recent notes list into markdown content.

        Args:
            markdown (str): The markdown content to insert recent notes into

        Returns:
            str: The updated markdown content
        """
        if not self._recent_notes:
            return markdown
        
        # Generate HTML list for recent notes
        notes_html = self._generate_notes_html()
        
        # Replace content between markers
        start_marker = self.config.start_marker
        end_marker = self.config.end_marker
        
        start_idx = markdown.find(start_marker)
        end_idx = markdown.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            self.logger.warning(
                f"Markers not found in index file. Please add {start_marker} "
                f"and {end_marker} to enable recent notes insertion."
            )
            return markdown
        
        if end_idx <= start_idx:
            self.logger.error("End marker found before start marker")
            return markdown
        
        # Replace content
        start_pos = start_idx + len(start_marker)
        end_pos = end_idx
        
        updated_markdown = (
            markdown[:start_pos] + 
            '\n' + notes_html + '\n' + 
            markdown[end_pos:]
        )
        
        self.logger.info(f"Inserted {len(self._recent_notes) - 1} recent notes into index page")
        return updated_markdown
    
    def _generate_notes_html(self) -> str:
        """Generate HTML list for recent notes.

        Returns:
            str: The HTML list for recent notes
        """
        items = []
        for note in self._recent_notes:
            items.append(
                f'<li><div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<a href="{note.relative_url}">{note.title}</a>'
                f'<span style="font-size:0.8em; color:#666;">{note.modified_date}</span>'
                '</div></li>'
            )
        
        return '<ul>\n' + '\n'.join(items) + '\n</ul>'
    
    def _is_note_page(self, page: Page) -> bool:
        """Check if the page is a note page.

        Args:
            page (Page): The page to check

        Returns:
            bool: True if the page is a note page, False otherwise
        """
        try:
            page_src_path = page.file.src_path
            
            # Check if the page is in the notes directory
            notes_dir = str(self.config.notes_dir)
            if notes_dir.startswith('docs/'):
                notes_relative = notes_dir[5:]  # Remove 'docs/' prefix
            else:
                notes_relative = notes_dir
            
            # Check if the page path starts with the notes directory
            is_note_page = page_src_path.startswith(notes_relative) and not page_src_path.endswith('index.md')
            
            self.logger.debug(f"Note page check: '{page_src_path}' starts with '{notes_relative}' = {is_note_page}")
            return is_note_page
        except Exception as e:
            self.logger.error(f"Error in note page check: {e}")
            return False
    
    def _process_page_assets(self, markdown: str, page: Page) -> str:
        """Process assets for a note page.

        Args:
            markdown (str): The markdown content to process
            page (Page): The page to process

        Returns:
            str: The updated markdown content with processed asset paths
        """
        try:
            # Convert page path to Path object
            page_path = Path(page.file.src_path)
            
            # Process assets in the markdown content
            updated_markdown = self._assets_processor.update_markdown_content(markdown, page_path)
            
            if updated_markdown != markdown:
                self.logger.debug(f"Processed assets for page: {page.file.src_path}")
            
            return updated_markdown
        except Exception as e:
            self.logger.error(f"Error processing assets for page {page.file.src_path}: {e}")
            return markdown

