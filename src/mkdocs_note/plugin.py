from __future__ import annotations

import posixpath
import click

from typing import Dict, List
from pathlib import Path
from mkdocs.structure.files import File, Files
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page

from mkdocs_note.core.note_manager import NoteLinkedMap,init_note_path , create_new_note
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
        @click.argument("path", type=click.Path())
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
            res = create_new_note(path)
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

        logger.info("Adding MkDocs-Note plugin to the list.")
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
            if any(posixpath.commonpath([f.src_uri, p]) == p for p in self.config.notes_root_path):
                self._normal_docs.append(f)
                continue

            # ignore the files which in path_blacklist
            if any(posixpath.commonpath([f.src_uri, p]) == p for p in self.config.path_blacklist):
                invalid_notes.append(f)
                continue

            # through out and process notes and attachments
            if path_name[1] == self.config.attachment_path:
                process_attachment(f)
            elif f.is_documentation_page() and parse_note_metadata(f):
                self._notes_lists.append(f)

            # process individual note/docs
            if f.is_documentation_page() and f not in self._normal_docs:
                if not parse_note_metadata(f):
                    invalid_notes.append(f)
                    continue

            self._note_link_name_map[posixpath.basename(f.src_path)] = f
            self._note_link_path_map[f.src_uri] = NoteLinkedMap(f)

        self._note_list.sort(key=lambda f: f.note_date, reverse=True)
        logger.info(f"Found {len(self._note_list)} valid notes and {len(self._normal_docs)} normal docs.")

        for invalid in invalid_notes:
            # logger.warning(f"Invalid note found: {invalid.src_uri}")
            files.remove(invalid)

        return files
