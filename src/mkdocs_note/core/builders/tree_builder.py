"""
Tree Builder

负责从文件系统目录结构构建笔记树。
"""

import sys
from pathlib import Path
from typing import List, Callable, Optional
from ..models.note_node import NoteNode
from ..parsers.metadata_parser import MetadataParser


class TreeBuilder:
    """
    树构建器，负责从文件系统目录结构构建笔记树。
    
    提供配置选项来自定义构建行为：
    - 文件过滤
    - 元数据解析
    - 构建进度回调
    """

    def __init__(
        self, 
        parse_metadata: bool = True,
        skip_hidden: bool = True,
        file_filter: Optional[Callable[[Path], bool]] = None,
        progress_callback: Optional[Callable[[Path], None]] = None
    ):
        """
        初始化树构建器。
        
        Args:
            parse_metadata: 是否解析Markdown文件的元数据
            skip_hidden: 是否跳过隐藏文件和目录
            file_filter: 自定义文件过滤器函数
            progress_callback: 构建进度回调函数
        """
        self.parse_metadata = parse_metadata
        self.skip_hidden = skip_hidden
        self.file_filter = file_filter
        self.progress_callback = progress_callback
        
        if self.parse_metadata:
            self.metadata_parser = MetadataParser()

    def build_tree(self, root_path: Path) -> NoteNode:
        """
        递归构建笔记树。
        
        Args:
            root_path: 根目录路径
            
        Returns:
            构建的笔记树根节点
        """
        if not root_path.exists():
            raise ValueError(f"Root path does not exist: {root_path}")

        return self._build_node(root_path)

    def _build_node(self, path: Path) -> NoteNode:
        """
        构建单个节点及其子节点。
        
        Args:
            path: 节点路径
            
        Returns:
            构建的笔记节点
        """
        if self.progress_callback:
            self.progress_callback(path)

        node = NoteNode(path)
        
        # 解析元数据（如果是笔记文件）
        if node.is_note and self.parse_metadata:
            try:
                metadata = self.metadata_parser.parse(path)
                node.set_metadata(metadata)
            except Exception as e:
                print(f"Error parsing metadata for {path}: {e}", file=sys.stderr)

        # 处理目录的子项
        if path.is_dir():
            try:
                children = self._get_child_paths(path)
                for child_path in children:
                    if self._should_include_path(child_path):
                        child_node = self._build_node(child_path)
                        node.add_child(child_node)
            except PermissionError as e:
                print(f"Permission denied accessing directory {path}: {e}", file=sys.stderr)

        return node

    def _get_child_paths(self, dir_path: Path) -> List[Path]:
        """
        获取目录的子路径列表。
        
        Args:
            dir_path: 目录路径
            
        Returns:
            排序后的子路径列表
        """
        try:
            children = list(dir_path.iterdir())
            # 按名称排序，目录在前
            return sorted(children, key=lambda p: (p.is_file(), p.name.lower()))
        except (PermissionError, OSError) as e:
            print(f"Error reading directory {dir_path}: {e}", file=sys.stderr)
            return []

    def _should_include_path(self, path: Path) -> bool:
        """
        判断是否应该包含某个路径。
        
        Args:
            path: 要检查的路径
            
        Returns:
            如果应该包含返回True，否则返回False
        """
        # 跳过隐藏文件和目录
        if self.skip_hidden and path.name.startswith('.'):
            return False

        # 应用自定义过滤器
        if self.file_filter and not self.file_filter(path):
            return False

        return True

    def build_with_stats(self, root_path: Path) -> tuple[NoteNode, dict]:
        """
        构建树并返回统计信息。
        
        Args:
            root_path: 根目录路径
            
        Returns:
            (根节点, 统计信息字典)
        """
        stats = {
            'total_files': 0,
            'total_directories': 0,
            'note_files': 0,
            'files_with_metadata': 0,
            'errors': 0
        }

        def count_callback(path: Path):
            if path.is_file():
                stats['total_files'] += 1
                if path.suffix == '.md':
                    stats['note_files'] += 1
            else:
                stats['total_directories'] += 1

        # 临时设置回调来收集统计信息
        original_callback = self.progress_callback
        self.progress_callback = count_callback
        
        try:
            root_node = self.build_tree(root_path)
            
            # 计算有元数据的文件数量
            if self.parse_metadata:
                stats['files_with_metadata'] = self._count_files_with_metadata(root_node)
            
            return root_node, stats
        finally:
            self.progress_callback = original_callback

    def _count_files_with_metadata(self, node: NoteNode) -> int:
        """
        递归计算有元数据的文件数量。
        
        Args:
            node: 要检查的节点
            
        Returns:
            有元数据的文件数量
        """
        count = 0
        if node.is_note and node.metadata:
            count = 1
        
        for child in node.children:
            count += self._count_files_with_metadata(child)
        
        return count
