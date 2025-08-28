"""
NoteGraph Model

笔记图结构类，表示笔记及其链接关系的有向图结构。
"""

from typing import Dict, List, Optional, Set
from .note_node import NoteNode


class NoteGraph:
    """
    笔记图结构类

    表示笔记及其链接关系的有向图结构。

    Attributes:
        nodes (Dict[str, NoteNode]): 绝对路径到NoteNode的映射
        adjacency_list (Dict[str, List[str]]): 笔记链接的邻接表
            key: 源笔记绝对路径
            value: 目标笔记绝对路径列表
    """

    def __init__(self):
        self.nodes: Dict[str, NoteNode] = {}
        self.adjacency_list: Dict[str, List[str]] = {}

    def add_node(self, node: NoteNode) -> None:
        """Add a note node to the graph."""
        path_str = str(node.path.absolute())
        if path_str not in self.nodes:
            self.nodes[path_str] = node
            self.adjacency_list[path_str] = []

    def remove_node(self, node_path: str) -> None:
        """Remove a note node from the graph."""
        if node_path in self.nodes:
            # Remove all edges to this node
            for source_path in self.adjacency_list:
                if node_path in self.adjacency_list[source_path]:
                    self.adjacency_list[source_path].remove(node_path)
            
            # Remove the node and its edges
            del self.nodes[node_path]
            del self.adjacency_list[node_path]

    def add_edge(self, source_path: str, target_path: str) -> None:
        """Add a directed edge from source to target note."""
        if source_path in self.adjacency_list:
            if target_path not in self.adjacency_list[source_path]:
                self.adjacency_list[source_path].append(target_path)
        else:
            self.adjacency_list[source_path] = [target_path]

    def remove_edge(self, source_path: str, target_path: str) -> None:
        """Remove a directed edge from source to target note."""
        if source_path in self.adjacency_list:
            if target_path in self.adjacency_list[source_path]:
                self.adjacency_list[source_path].remove(target_path)

    def get_backlinks(self, note_path: str) -> List[str]:
        """Get all notes that link to the given note."""
        return [
            source for source, targets in self.adjacency_list.items()
            if note_path in targets
        ]

    def get_outlinks(self, note_path: str) -> List[str]:
        """Get all notes that the given note links to."""
        return self.adjacency_list.get(note_path, [])

    def get_node(self, note_path: str) -> Optional[NoteNode]:
        """Get a note node by its path."""
        return self.nodes.get(note_path)

    def get_all_nodes(self) -> List[NoteNode]:
        """Get all note nodes in the graph."""
        return list(self.nodes.values())

    def get_note_count(self) -> int:
        """Get the total number of notes in the graph."""
        return len([node for node in self.nodes.values() if node.is_note])

    def get_link_count(self) -> int:
        """Get the total number of links in the graph."""
        return sum(len(targets) for targets in self.adjacency_list.values())

    def find_orphaned_notes(self) -> List[str]:
        """Find notes that have no incoming or outgoing links."""
        orphaned = []
        for path, node in self.nodes.items():
            if node.is_note:
                if not self.adjacency_list[path] and not self.get_backlinks(path):
                    orphaned.append(path)
        return orphaned

    def find_broken_links(self) -> List[tuple[str, str]]:
        """Find links that point to non-existent notes."""
        broken = []
        for source_path, targets in self.adjacency_list.items():
            for target_path in targets:
                if target_path not in self.nodes:
                    broken.append((source_path, target_path))
        return broken

    def get_connected_components(self) -> List[Set[str]]:
        """Get connected components in the graph (treating it as undirected)."""
        visited = set()
        components = []
        
        def dfs(node_path: str, component: Set[str]) -> None:
            if node_path in visited:
                return
            visited.add(node_path)
            component.add(node_path)
            
            # Visit outbound links
            for target in self.adjacency_list.get(node_path, []):
                if target in self.nodes:  # Only consider existing nodes
                    dfs(target, component)
            
            # Visit inbound links
            for source in self.get_backlinks(node_path):
                dfs(source, component)
        
        for node_path in self.nodes:
            if node_path not in visited:
                component = set()
                dfs(node_path, component)
                if component:
                    components.append(component)
        
        return components

    def to_dict(self) -> Dict[str, any]:
        """Convert the graph to a dictionary representation."""
        return {
            'nodes': {path: node.to_dict() for path, node in self.nodes.items()},
            'edges': self.adjacency_list,
            'stats': {
                'note_count': self.get_note_count(),
                'link_count': self.get_link_count(),
                'orphaned_notes': len(self.find_orphaned_notes()),
                'broken_links': len(self.find_broken_links())
            }
        }

    def __repr__(self) -> str:
        return f"NoteGraph(nodes={len(self.nodes)}, links={self.get_link_count()})"