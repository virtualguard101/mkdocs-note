import posixpath
import click

from typing import Dict
from pathlib import Path
from mkdocs.structure.files import File
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page

from mkdocsnote.core.note_manager import NoteLinkedMap, create_new_note
from .logger import logger

class MkdocsNotePlugin(BasePlugin):
    """MkDocs plugin for managing notes.

    Attributes:
        _notes_lists (Dict[str, File]): A dictionary to store all notes, mapping their permalinks to their file objects which are sorted in reverse chronological order
        _note_link_name_map (Dict[str, File]): A dictionary to store all note links, mapping their names to their file objects
        _note_link_path_map (Dict[str, NoteLinkedMap]): A dictionary to store all note links, mapping their paths to their linked map objects
    """
    def __init__(self):
        super().__init__()
        self._notes_lists: Dict[str, File] = {}
        self._note_link_name_map: Dict[str, File] = {}
        self._note_link_path_map: Dict[str, NoteLinkedMap] = {}

    def get_command(self):
        """Get the command group for managing notes.
        """
        @click.group()
        def note():
            """Manage notes (custom plugin commands)."""
            pass

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
