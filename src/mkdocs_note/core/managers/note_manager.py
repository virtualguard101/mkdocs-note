"""
Note Manager

高级笔记管理器，协调各个组件实现完整的笔记管理功能。
"""

import time
from pathlib import Path
from typing import Optional, Dict, List, Set, Callable
from ..models.note_node import NoteNode
from ..models.note_graph import NoteGraph
from ..builders.tree_builder import TreeBuilder
from ..builders.graph_builder import GraphBuilder
from ..parsers.link_parser import LinkParser
from ..parsers.metadata_parser import MetadataParser
from .file_manager import FileManager


class NoteManager:
    """
    笔记管理器，提供完整的笔记管理功能。
    
    整合了以下功能：
    - 笔记树构建和维护
    - 笔记图构建和维护
    - 链接解析和验证
    - 元数据管理
    - 文件监控和增量更新
    """

    def __init__(
        self,
        root_path: Path,
        auto_parse_metadata: bool = True,
        auto_verify_links: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """
        初始化笔记管理器。
        
        Args:
            root_path: 笔记根目录路径
            auto_parse_metadata: 是否自动解析元数据
            auto_verify_links: 是否自动验证链接
            progress_callback: 进度回调函数
        """
        self.root_path = Path(root_path).absolute()
        self.auto_parse_metadata = auto_parse_metadata
        self.auto_verify_links = auto_verify_links
        self.progress_callback = progress_callback
        
        # 初始化组件
        self.file_manager = FileManager(self.root_path)
        self.tree_builder = TreeBuilder(
            parse_metadata=auto_parse_metadata,
            progress_callback=self._tree_progress_callback
        )
        self.graph_builder = GraphBuilder(
            verify_links=auto_verify_links,
            progress_callback=self._graph_progress_callback
        )
        self.link_parser = LinkParser()
        self.metadata_parser = MetadataParser()
        
        # 状态
        self._tree: Optional[NoteNode] = None
        self._graph: Optional[NoteGraph] = None
        self._last_scan_time: float = 0
        self._is_initialized = False

    def initialize(self) -> bool:
        """
        初始化笔记管理器，构建完整的树和图结构。
        
        Returns:
            初始化成功返回True，否则返回False
        """
        try:
            if self.progress_callback:
                self.progress_callback("正在构建笔记树...")
            
            # 构建树
            self._tree = self.tree_builder.build_tree(self.root_path)
            
            if self.progress_callback:
                self.progress_callback("正在构建笔记图...")
            
            # 构建图
            self._graph = self.graph_builder.build_graph(self._tree)
            
            self._last_scan_time = time.time()
            self._is_initialized = True
            
            if self.progress_callback:
                self.progress_callback("初始化完成")
            
            return True
            
        except Exception as e:
            print(f"Error initializing note manager: {e}")
            return False

    def refresh(self, force: bool = False) -> bool:
        """
        刷新笔记管理器状态。
        
        Args:
            force: 是否强制全量刷新
            
        Returns:
            刷新成功返回True，否则返回False
        """
        try:
            if not self._is_initialized or force:
                return self.initialize()
            
            # 检查是否有文件变化
            current_time = time.time()
            changed_files = self.file_manager.find_changed_files(self._last_scan_time)
            
            if not changed_files:
                return True  # 没有变化，无需刷新
            
            if self.progress_callback:
                self.progress_callback(f"检测到 {len(changed_files)} 个文件变化，正在更新...")
            
            # 重新构建树（对于变化的文件，我们简单地重建整个树）
            self._tree = self.tree_builder.build_tree(self.root_path)
            
            # 部分更新图
            absolute_changed_files = {
                str((self.root_path / f).absolute()) for f in changed_files
            }
            self._graph = self.graph_builder.rebuild_partial_graph(
                self._tree, absolute_changed_files
            )
            
            self._last_scan_time = current_time
            
            if self.progress_callback:
                self.progress_callback("刷新完成")
            
            return True
            
        except Exception as e:
            print(f"Error refreshing note manager: {e}")
            return False

    def get_tree(self) -> Optional[NoteNode]:
        """获取笔记树。"""
        return self._tree

    def get_graph(self) -> Optional[NoteGraph]:
        """获取笔记图。"""
        return self._graph

    def get_note(self, relative_path: str) -> Optional[NoteNode]:
        """
        通过相对路径获取笔记节点。
        
        Args:
            relative_path: 相对于根目录的文件路径
            
        Returns:
            笔记节点，如果不存在返回None
        """
        if not self._graph:
            return None
        
        absolute_path = str((self.root_path / relative_path).absolute())
        return self._graph.get_node(absolute_path)

    def search_notes(self, query: str, in_content: bool = False) -> List[NoteNode]:
        """
        搜索笔记。
        
        Args:
            query: 搜索查询
            in_content: 是否在内容中搜索
            
        Returns:
            匹配的笔记节点列表
        """
        if not self._graph:
            return []
        
        results = []
        query_lower = query.lower()
        
        for node in self._graph.get_all_nodes():
            if not node.is_note:
                continue
            
            # 在标题和标签中搜索
            title = node.get_title().lower()
            tags = [tag.lower() for tag in node.get_tags()]
            
            if (query_lower in title or 
                any(query_lower in tag for tag in tags)):
                results.append(node)
                continue
            
            # 在内容中搜索（如果启用）
            if in_content:
                content = self.file_manager.read_file(
                    str(node.path.relative_to(self.root_path))
                )
                if content and query_lower in content.lower():
                    results.append(node)
        
        return results

    def get_backlinks(self, relative_path: str) -> List[NoteNode]:
        """
        获取指向指定笔记的反向链接。
        
        Args:
            relative_path: 目标笔记的相对路径
            
        Returns:
            链接到目标笔记的笔记节点列表
        """
        if not self._graph:
            return []
        
        absolute_path = str((self.root_path / relative_path).absolute())
        backlink_paths = self._graph.get_backlinks(absolute_path)
        
        backlink_nodes = []
        for path in backlink_paths:
            node = self._graph.get_node(path)
            if node:
                backlink_nodes.append(node)
        
        return backlink_nodes

    def get_outlinks(self, relative_path: str) -> List[NoteNode]:
        """
        获取指定笔记的出链。
        
        Args:
            relative_path: 源笔记的相对路径
            
        Returns:
            被源笔记链接的笔记节点列表
        """
        if not self._graph:
            return []
        
        absolute_path = str((self.root_path / relative_path).absolute())
        outlink_paths = self._graph.get_outlinks(absolute_path)
        
        outlink_nodes = []
        for path in outlink_paths:
            node = self._graph.get_node(path)
            if node:
                outlink_nodes.append(node)
        
        return outlink_nodes

    def create_note(
        self, 
        relative_path: str, 
        content: str = "", 
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        创建新笔记。
        
        Args:
            relative_path: 新笔记的相对路径
            content: 笔记内容
            metadata: 笔记元数据
            
        Returns:
            创建成功返回True，否则返回False
        """
        try:
            # 确保路径以.md结尾
            if not relative_path.endswith('.md'):
                relative_path = f"{relative_path}.md"
            
            # 准备内容
            final_content = content
            if metadata:
                import yaml
                yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
                final_content = f"---\n{yaml_content}---\n\n{content}"
            
            # 创建文件
            success = self.file_manager.create_file(relative_path, final_content)
            
            if success:
                # 刷新状态
                self.refresh()
            
            return success
            
        except Exception as e:
            print(f"Error creating note {relative_path}: {e}")
            return False

    def delete_note(self, relative_path: str) -> bool:
        """
        删除笔记。
        
        Args:
            relative_path: 要删除的笔记相对路径
            
        Returns:
            删除成功返回True，否则返回False
        """
        success = self.file_manager.delete_file(relative_path)
        
        if success:
            # 刷新状态
            self.refresh()
        
        return success

    def get_statistics(self) -> Dict[str, any]:
        """
        获取笔记库统计信息。
        
        Returns:
            统计信息字典
        """
        if not self._graph:
            return {}
        
        return {
            'total_notes': self._graph.get_note_count(),
            'total_links': self._graph.get_link_count(),
            'orphaned_notes': len(self._graph.find_orphaned_notes()),
            'broken_links': len(self._graph.find_broken_links()),
            'connected_components': len(self._graph.get_connected_components())
        }

    def validate_links(self) -> Dict[str, List]:
        """
        验证所有链接。
        
        Returns:
            验证结果字典
        """
        if not self._graph:
            return {'broken_links': [], 'orphaned_notes': []}
        
        return {
            'broken_links': self._graph.find_broken_links(),
            'orphaned_notes': self._graph.find_orphaned_notes()
        }

    def _tree_progress_callback(self, path: Path) -> None:
        """树构建进度回调。"""
        if self.progress_callback:
            rel_path = path.relative_to(self.root_path) if path != self.root_path else Path(".")
            self.progress_callback(f"正在处理: {rel_path}")

    def _graph_progress_callback(self, node: NoteNode) -> None:
        """图构建进度回调。"""
        if self.progress_callback and node.is_note:
            rel_path = node.path.relative_to(self.root_path)
            self.progress_callback(f"正在解析链接: {rel_path}")

    def __enter__(self):
        """上下文管理器进入。"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出。"""
        # 清理资源（如果需要）
        pass
