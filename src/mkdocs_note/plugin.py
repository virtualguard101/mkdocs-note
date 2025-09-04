from __future__ import annotations

import posixpath
import click
import re
import html

from typing import Dict, List
from pathlib import Path
from mkdocs.structure.files import File, Files
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page
from mkdocs.utils import get_relative_url

from mkdocs_note.core.note_manager import (
    NoteLinkedMap,init_note_path, 
    create_new_note, 
    transform_notes_links,
    insert_recent_notes
)
from mkdocs_note.parsers.config_parser import PluginConfig
from mkdocs_note.logger import logger
from mkdocs_note.core.file_manager import process_attachment
from mkdocs_note.parsers.note_parser import parse_note_metadata

class MkdocsNotePlugin(BasePlugin[PluginConfig]):
    """MkDocs plugin for managing notes.

    Attributes:
        _notes_lists (Dict[str, File]): A dictionary to store all notes, mapping their permalinks to their file objects which are sorted in reverse chronological order
        _note_link_name_map (Dict[str, File]): A dictionary to store all note links, mapping their names to their file objects
        _note_link_path_map (Dict[str, NoteLinkedMap]): A dictionary to store all note links, mapping their paths to their linked map objects
        _normal_docs (List[File]): A list to store normal documentation files, which are not regarded as notes.
    """
    def __init__(self):
        super().__init__()
        self._notes_lists: Dict[str, File] = {}
        self._note_link_name_map: Dict[str, File] = {}
        self._note_link_path_map: Dict[str, NoteLinkedMap] = {}
        self._normal_docs: List[File] = []

    def get_command(self) -> None:
        """Get the command group for managing notes.
        """
        @click.group()
        def note():
            """Manage notes (custom plugin commands)."""
            pass

        @note.command("init")
        def init_note():
            """Initialize the note directory.
            """
            path = self.config.notes_root_path[0] if self.config.notes_root_path else "notes"
            res = init_note_path(path)
            if res == 0:
                logger.info(f"Successfully initialized the note directory at {path}")
            else:
                logger.error(f"Failed to initialize the note directory at {path}")

        @note.command("new")
        @click.argument("path", type=click.Path())
        def new_note(path: Path):
            """Create a new note.

            Args:
                path (Path): The path to the new note.
            """
            res = create_new_note(path, self.config.notes_root_path, self.config.notes_template)
            if res == 0:
                logger.info(f"Successfully created a new note at {path}")
            else:
                logger.error(f"Failed to create a new note at {path}")
        
    @property
    def plugin_enabled(self) -> bool:
        """Check if the plugin is enabled.

        Returns:
            bool: True if the plugin is enabled, False otherwise.
        """
        return self.config.enabled

    @event_priority(100)
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Handle the configuration for the plugin.

        Args:
            config (MkDocsConfig): The MkDocs configuration object.
        """
        if not self.plugin_enabled:
            logger.debug("MkDocs-Note plugin is disabled.")
            return config

        # 确保 toc 配置存在，为 wiki 链接的 heading id 生成提供支持
        if 'toc' not in config.mdx_configs:
            config.mdx_configs['toc'] = {}
        
        # 只在完全缺失时设置默认配置，优先保持用户配置
        toc_config = config.mdx_configs['toc']
        
        # 确保 separator 存在（如果用户未配置）
        if 'separator' not in toc_config:
            toc_config['separator'] = '-'
            
        # 只在 slugify 完全缺失时设置默认值
        if 'slugify' not in toc_config:
            try:
                # 优先尝试使用 pymdownx.slugs.slugify（与 Material 主题兼容）
                from pymdownx.slugs import slugify
                toc_config['slugify'] = slugify
                logger.debug("Using pymdownx.slugs.slugify for better Material theme compatibility")
            except ImportError:
                # 回退到标准 slugify
                from markdown.extensions.toc import slugify
                toc_config['slugify'] = slugify
                logger.debug("Using markdown.extensions.toc.slugify as fallback")

        logger.info("Adding MkDocs-Note plugin to the list.")
        logger.debug(f"TOC config: separator='{toc_config.get('separator')}', slugify={toc_config.get('slugify').__name__ if hasattr(toc_config.get('slugify'), '__name__') else 'custom'}")
        return config

    @event_priority(100)
    def on_files(self, files: Files, config: MkDocsConfig) -> Files | None:
        """Process the files in the documentation.

        Args:
            files (Files): The collection of files in the documentation.
            config (MkDocsConfig): The MkDocs configuration object.

        Returns:
            Files | None: The processed files or None if the plugin is disabled.
        """
        if not self.plugin_enabled:
            return files

        logger.info("Processing files for MkDocs-Note plugin.")

        # Clear existing mappings
        self._note_link_name_map.clear()
        self._note_link_path_map.clear()
        self._notes_lists.clear()
        self._normal_docs.clear()

        invalid_notes: List[File] = []

        for f in files:
            path_name = f.src_uri.split('/')

            # ignore the files which out of notes_root_path
            if not any(f.src_uri.startswith(p) for p in self.config.notes_root_path):
                self._normal_docs.append(f)
                continue

            # ignore the files which in path_blacklist
            if any(posixpath.commonpath([f.src_uri, p]) == p for p in self.config.path_blacklist):
                invalid_notes.append(f)
                continue

            # through out and process notes and attachments
            if path_name[1] == self.config.attachment_path:
                process_attachment(f, self.config)
            elif f.is_documentation_page() and parse_note_metadata(f):
                self._notes_lists[f.src_uri] = f

            # process individual note/docs
            if f.is_documentation_page() and f not in self._normal_docs:
                if not parse_note_metadata(f):
                    invalid_notes.append(f)
                    continue

            self._note_link_name_map[posixpath.basename(f.src_path)] = f
            self._note_link_path_map[f.src_uri] = NoteLinkedMap(f)

        self._notes_lists = dict(sorted(self._notes_lists.items(), key=lambda item: item[1].note_date, reverse=True))
        logger.info(f"Found {len(self._notes_lists)} valid notes and {len(self._normal_docs)} normal docs.")

        for invalid in invalid_notes:
            # logger.warning(f"Invalid note found: {invalid.src_uri}")
            files.remove(invalid)

        return files

    def on_page_markdown(self, markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str | None:
        """Process the markdown content of a page.

        Args:
            markdown (str): The markdown content of the page.
            page (Page): The page object.
            config (MkDocsConfig): The MkDocs configuration object.
            files (Files): The collection of files in the documentation.

        Returns:
            str | None: The processed markdown content or None if the plugin is disabled.
        """
        markdown = transform_notes_links(
            markdown,
            page,
            config,
            self._note_link_name_map,
            self._note_link_path_map
        )

        if page.is_homepage:
            markdown = insert_recent_notes(
                markdown,
                self._notes_lists
            )
        return markdown

    @event_priority(50)
    def on_post_page(self, output: str, page: Page, config: MkDocsConfig) -> str | None:
        """Process the HTML output of a page after it has been rendered.

        Args:
            output (str): The HTML output of the page.
            page (Page): The page object.
            config (MkDocsConfig): The MkDocs configuration object.

        Returns:
            str | None: The processed HTML output or None if the plugin is disabled.
        """
        note_links = self._note_link_path_map.get(page.file.src_uri)
        if note_links is None:
            return

        assert note_links.node == page.file, "NoteLinkedMap node does not match the current page file."

        # get and sort reverse links by note date
        inverse_links_files: List[File] = []
        head = note_links.inverse_links
        while head.next != None:
            inverse_links_files.append(head.next.node)
            head = head.next

        inverse_links_files.sort(key=lambda f: f.note_date, reverse=True)

        links_html = r'<br><details class="tip" open><summary>反向链接</summary><ul>'
        for link_file in inverse_links_files:
            href = get_relative_url(link_file.url, page.url)
            links_html += rf'<li><a href="{href}">{html.escape(link_file.title)}</a></li>'
        links_html += r'</ul></details>'
        return re.sub(r'(<h2 id=\"__comments\">.*?<\/h2>)?\s*?<\/article>', rf'{links_html}\g<0>', output, count=1)
