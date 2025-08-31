from typing import Dict
from mkdocs.structure.files import File, Files

from .file_manager import FileLinkedNode

class NoteLinkedMap(object):
    """Note linked map class, which use for recording the links of 
       an instance itself refer to other instances and the links of
       other instances refer to itself.

    Attributes:
        node: The file associated with this note.
        links: The links from this note to other notes, which is a dictionary mapping note IDs to their linked nodes.
        inverse_links: The links from other notes to this note, which is a linked list with head node.
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
