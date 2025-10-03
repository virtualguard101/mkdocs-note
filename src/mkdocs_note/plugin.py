from __future__ import annotations

import re
import subprocess
from typing import List
from pathlib import Path
from datetime import datetime
from mkdocs.structure.files import File, Files
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.file_manager import FileScanner
from mkdocs_note.core.note_manager import NoteProcessor, NoteInfo


class MkdocsNotePlugin(BasePlugin[PluginConfig]):
    """MkDocs plugin for managing notes.
    
    This plugin automatically inserts recent notes into the index page
    of the configured notes directory.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self._recent_notes: List[NoteInfo] = []
    
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
            file_scanner = FileScanner(self.config, self.logger)
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
        """Insert recent notes into the index page.

        Args:
            markdown (str): The markdown content to insert recent notes into
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
        
        self.logger.info(f"Inserted {len(self._recent_notes)} recent notes into index page")
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

