"""
FileNode Model

A class representing a file or directory in the file system.
"""

from pathlib import Path
from typing import List, Dict, Any


class FileNode:
    """
    A class representing a file or directory in the file system.

    Attributes:
        path (Path): The file system path.
        children (List[FileNode]): The child files and directories.
    """

    def __init__(self, path: Path):
        self.path = path
        self.children: List['FileNode'] = []

    def add_child(self, child: 'FileNode') -> None:
        """
        Adds a child file or directory to the current node.

        Args:
            child (FileNode): The child file or directory to add.
        """
        self.children.append(child)

    def is_directory(self) -> bool:
        """Check if this node represents a directory."""
        return len(self.children) > 0 or self.path.is_dir()

    def is_file(self) -> bool:
        """Check if this node represents a file."""
        return not self.is_directory()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary representation."""
        return {
            'name': self.path.name,
            'type': 'directory' if self.is_directory() else 'file',
            'path': str(self.path),
            'children': [child.to_dict() for child in self.children]
        }

    def __repr__(self) -> str:
        return f"FileNode(path={self.path}, children={len(self.children)})"