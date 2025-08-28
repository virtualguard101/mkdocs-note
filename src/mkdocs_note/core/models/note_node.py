"""
NoteNode Model

笔记文件节点类(继承自FileNode)，表示知识库中的笔记文件(.md)。
"""

from pathlib import Path
from typing import List, Dict, Any
from .file_node import FileNode


class NoteNode(FileNode):
    """
    笔记文件节点类(继承自FileNode)

    表示知识库中的笔记文件(.md)，扩展了文件节点的笔记特定属性。

    Attributes:
        is_note (bool): 是否为Markdown笔记文件
        metadata (Dict[str, Any]): 解析的YAML front matter元数据
        out_links (List[str]): 本笔记指向的绝对路径列表（出链）
        backlinks (List[str]): 指向本笔记的绝对路径列表（反链/入链）
    
    继承关系：
        NoteNode → FileNode
    """

    def __init__(self, path: Path):
        super().__init__(path)
        self.is_note = path.suffix == '.md'
        self.metadata: Dict[str, Any] = {}
        self.out_links: List[str] = []
        self.backlinks: List[str] = []

    def add_child(self, child: 'NoteNode') -> None:
        """Add a child NoteNode to this node."""
        super().add_child(child)

    def add_out_link(self, link_path: str) -> None:
        """Add an outbound link to this note."""
        if link_path not in self.out_links:
            self.out_links.append(link_path)

    def add_backlink(self, link_path: str) -> None:
        """Add a backlink to this note."""
        if link_path not in self.backlinks:
            self.backlinks.append(link_path)

    def remove_out_link(self, link_path: str) -> None:
        """Remove an outbound link from this note."""
        if link_path in self.out_links:
            self.out_links.remove(link_path)

    def remove_backlink(self, link_path: str) -> None:
        """Remove a backlink from this note."""
        if link_path in self.backlinks:
            self.backlinks.remove(link_path)

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the metadata for this note."""
        self.metadata = metadata

    def get_title(self) -> str:
        """Get the title of the note from metadata or filename."""
        return self.metadata.get('title', self.path.stem)

    def get_tags(self) -> List[str]:
        """Get the tags of the note from metadata."""
        tags = self.metadata.get('tags', [])
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(',')]
        return tags if isinstance(tags, list) else []

    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary representation."""
        base = super().to_dict()
        base.update({
            'is_note': self.is_note,
            'metadata': self.metadata,
            'out_links': self.out_links,
            'backlinks': self.backlinks,
            'title': self.get_title(),
            'tags': self.get_tags()
        })
        return base

    def __repr__(self) -> str:
        return f"NoteNode(path={self.path}, is_note={self.is_note}, links={len(self.out_links)})"
