import posixpath

from typing import Dict
from mkdocs.structure.files import File
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page

from .core.note_manager import NoteLinkedMap

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
