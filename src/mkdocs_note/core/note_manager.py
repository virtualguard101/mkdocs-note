import os
import posixpath
import frontmatter

from pathlib import Path
from typing import Dict, Union, Callable, List
from mkdocs.structure.files import File, Files
from mkdocs.utils import meta, get_relative_url

from .file_manager import FileLinkedNode
from ..parsers.config_parser import PluginConfig
from ..logger import logger

class NoteLinkedMap(object):
    """Note linked map class, which use for recording the links of 
       an instance itself refer to other instances and the links of
       other instances refer to itself.

    Attributes:
        node (File): The file associated with this note.
        links (Dict[str, FileLinkedNode]): The links from this note to other notes, which is a dictionary mapping note IDs to their linked nodes.
        inverse_links (FileLinkedNode): The links from other notes to this note, which is a linked list with head node.
    """
    def __init__(self, node: File):
        self.node = node
        self.links: Dict[str, FileLinkedNode] = {}
        self.inverse_links = FileLinkedNode(None)

    def clear_links(self):
        """Clear all active links (i.e., links pointing to other 
           articles from oneself) and remove the relevant nodes from 
           the corresponding reverse linked list.
        """
        for link in self.links.values():
            link.remove()
        self.links.clear()

NOTES_ROOT_DIR: str = PluginConfig().notes_root_path
"""The root path of the notes"""

NOTES_TEMPLATE: str = PluginConfig().notes_template
"""The template used for new notes"""

def process_notes_path_node(file: File) -> List[str]:
    """Extract the notes path node, and remove its extension.

    Args:
        file (File): The file to process.

    Returns:
        List[str]: The processed nodes list.
    """
    original_uri = file.src_uri

    normalized = posixpath.normpath(original_uri).lstrip('/')

    # Split path nodes
    parts = normalized.split('/')

    # Remove the extension of the last node (filename)
    if parts and '.' in parts[-1]:
        filename = parts[-1]
        parts[-1] = posixpath.splitext(filename)[0]
    
    return [part for part in parts if part]

def set_note_permalink(file: File) -> List[str]:
    """Set the permalink for a note file.

    Args:
        file (File): The note file to set the permalink for.

    Returns:
        List[str]: The list with 2 elements: the first is first node of the processed path, and the second is the permalink formed by connecting various nodes through '-'.
    """
    nodes_list = process_notes_path_node(file)

    if not nodes_list:
        return []

    head = nodes_list[1]
    permalink = head
    for node in nodes_list[2:]:
        permalink += ('-' + node)

    return [nodes_list[0], permalink]

def create_new_note(path: Path) -> int:
    """Create a new note at the specified path using the defined template.

    Args:
        path (Path): The path where the new note will be created.
    """
    template_path = Path(NOTES_TEMPLATE)

    if not template_path.exists():
        return

    post = frontmatter.load(template_path)

    # Create a mock File object for permalink generation
    mock_file = type('MockFile', (), {'src_uri': str(path.relative_to(Path(NOTES_ROOT_DIR)))})()
    
    frontmatter_args = {
        "date": datetime.now().isoformat(timespec='seconds'),
        "permalink": set_note_permalink(mock_file)[1],
        "publish": False
    }

    for key, value in post.metadata.items():
        if key not in frontmatter_args:
            frontmatter_args[key] = value

    # Update post metadata with new frontmatter
    for key, value in frontmatter_args.items():
        post[key] = value

    with open(path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dump(post))

    return 0

def set_note_uri(file: File, dest_uri: Union[str, Callable[[str], str]]) -> None:
    """Set the URI for a note file.

    Args:
        file (File): The note file to set the URI for.
        dest_uri (Union[str, Callable[[str], str]]): The destination URI or a function to generate it.
    """
    file.dest_uri = dest_uri if isinstance(dest_uri, str) else dest_uri(file.dest_uri)

    # Helper function to delete an attribute if it exists
    def delattr_if_exists(obj, attr: str) -> None:
        if hasattr(obj, attr):
            delattr(obj, attr)

    # Delete the 'url' and 'abs_dest_path' attribute if it exists
    delattr_if_exists(file, 'url')
    delattr_if_exists(file, 'abs_dest_path')
