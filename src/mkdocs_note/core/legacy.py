"""
Legacy Functions

为了向后兼容，保留原始的函数式接口。
这些函数封装了新的面向对象架构。
"""

from pathlib import Path
from .models.note_node import NoteNode
from .models.note_graph import NoteGraph
from .builders.tree_builder import TreeBuilder
from .builders.graph_builder import GraphBuilder
from .parsers.link_parser import LinkParser


def build_tree(root_path: Path) -> NoteNode:
    """
    递归构建笔记树（兼容性函数）。
    
    Args:
        root_path: 根目录路径
        
    Returns:
        构建的笔记树根节点
    """
    builder = TreeBuilder()
    return builder.build_tree(root_path)


def parse_note_links(note_path: Path) -> list[str]:
    """
    解析Markdown笔记中的[[维基链接]]（兼容性函数）。
    
    Args:
        note_path: Markdown文件路径
        
    Returns:
        笔记中引用的所有目标文件的绝对路径列表
    """
    parser = LinkParser()
    return parser.parse(note_path)


def build_note_graph(root: NoteNode) -> NoteGraph:
    """
    从笔记树构建笔记图（兼容性函数）。
    
    Args:
        root: 笔记树的根节点
        
    Returns:
        构建的笔记图
    """
    builder = GraphBuilder()
    return builder.build_graph(root)