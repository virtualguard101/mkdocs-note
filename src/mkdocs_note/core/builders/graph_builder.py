"""
Graph Builder

负责从笔记树构建笔记图结构。
"""

import sys
from typing import Optional, Callable, Set
from ..models.note_node import NoteNode
from ..models.note_graph import NoteGraph
from ..parsers.link_parser import LinkParser


class GraphBuilder:
    """
    图构建器，负责从笔记树构建笔记图结构。
    
    提供以下功能：
    - 解析笔记间的链接关系
    - 构建有向图结构
    - 计算反向链接
    - 验证链接有效性
    """

    def __init__(
        self,
        verify_links: bool = True,
        progress_callback: Optional[Callable[[NoteNode], None]] = None
    ):
        """
        初始化图构建器。
        
        Args:
            verify_links: 是否验证链接的有效性
            progress_callback: 构建进度回调函数
        """
        self.verify_links = verify_links
        self.progress_callback = progress_callback
        self.link_parser = LinkParser()

    def build_graph(self, root_node: NoteNode) -> NoteGraph:
        """
        从笔记树构建笔记图。
        
        Args:
            root_node: 笔记树的根节点
            
        Returns:
            构建的笔记图
        """
        graph = NoteGraph()
        
        # 第一遍：添加所有节点
        self._add_all_nodes(root_node, graph)
        
        # 第二遍：解析链接并建立边
        self._build_edges(root_node, graph)
        
        # 第三遍：计算反向链接
        self._populate_backlinks(graph)
        
        return graph

    def _add_all_nodes(self, node: NoteNode, graph: NoteGraph) -> None:
        """
        递归添加所有节点到图中。
        
        Args:
            node: 当前节点
            graph: 目标图
        """
        if self.progress_callback:
            self.progress_callback(node)

        graph.add_node(node)
        
        for child in node.children:
            self._add_all_nodes(child, graph)

    def _build_edges(self, node: NoteNode, graph: NoteGraph) -> None:
        """
        递归解析链接并建立图的边。
        
        Args:
            node: 当前节点
            graph: 目标图
        """
        # 只处理笔记文件
        if node.is_note:
            try:
                # 解析出链
                out_links = self.link_parser.parse(node.path)
                node.out_links = out_links
                
                # 添加边到图中
                source_path = str(node.path.absolute())
                for target_path in out_links:
                    graph.add_edge(source_path, target_path)
                    
            except Exception as e:
                print(f"Error parsing links for {node.path}: {e}", file=sys.stderr)

        # 递归处理子节点
        for child in node.children:
            self._build_edges(child, graph)

    def _populate_backlinks(self, graph: NoteGraph) -> None:
        """
        为图中所有节点计算反向链接。
        
        Args:
            graph: 要处理的图
        """
        for node_path, node in graph.nodes.items():
            if node.is_note:
                node.backlinks = graph.get_backlinks(node_path)

    def build_with_validation(self, root_node: NoteNode) -> tuple[NoteGraph, dict]:
        """
        构建图并进行链接验证。
        
        Args:
            root_node: 笔记树的根节点
            
        Returns:
            (构建的图, 验证报告)
        """
        graph = self.build_graph(root_node)
        
        validation_report = {
            'total_nodes': len(graph.nodes),
            'total_links': graph.get_link_count(),
            'note_count': graph.get_note_count(),
            'broken_links': [],
            'orphaned_notes': [],
            'connected_components': 0
        }

        if self.verify_links:
            # 检查断开的链接
            broken_links = graph.find_broken_links()
            validation_report['broken_links'] = broken_links
            
            # 检查孤立的笔记
            orphaned_notes = graph.find_orphaned_notes()
            validation_report['orphaned_notes'] = orphaned_notes
            
            # 计算连通分量
            components = graph.get_connected_components()
            validation_report['connected_components'] = len(components)

        return graph, validation_report

    def update_node_links(self, node: NoteNode, graph: NoteGraph) -> None:
        """
        更新单个节点的链接信息。
        
        Args:
            node: 要更新的节点
            graph: 包含该节点的图
        """
        if not node.is_note:
            return

        try:
            # 获取节点路径
            node_path = str(node.path.absolute())
            
            # 移除旧的出链
            old_out_links = node.out_links.copy()
            for old_link in old_out_links:
                graph.remove_edge(node_path, old_link)
            
            # 解析新的出链
            new_out_links = self.link_parser.parse(node.path)
            node.out_links = new_out_links
            
            # 添加新的边
            for new_link in new_out_links:
                graph.add_edge(node_path, new_link)
            
            # 更新相关节点的反向链接
            affected_nodes = set(old_out_links + new_out_links)
            for affected_path in affected_nodes:
                affected_node = graph.get_node(affected_path)
                if affected_node:
                    affected_node.backlinks = graph.get_backlinks(affected_path)
            
        except Exception as e:
            print(f"Error updating links for {node.path}: {e}", file=sys.stderr)

    def rebuild_partial_graph(
        self, 
        root_node: NoteNode, 
        changed_files: Set[str]
    ) -> NoteGraph:
        """
        部分重建图，只更新发生变化的文件。
        
        Args:
            root_node: 笔记树的根节点
            changed_files: 发生变化的文件路径集合
            
        Returns:
            更新后的图
        """
        # 首先构建完整的图
        graph = self.build_graph(root_node)
        
        # 然后只更新变化的文件
        self._update_changed_nodes(root_node, graph, changed_files)
        
        return graph

    def _update_changed_nodes(
        self, 
        node: NoteNode, 
        graph: NoteGraph, 
        changed_files: Set[str]
    ) -> None:
        """
        递归更新发生变化的节点。
        
        Args:
            node: 当前节点
            graph: 要更新的图
            changed_files: 发生变化的文件路径集合
        """
        node_path = str(node.path.absolute())
        
        if node.is_note and node_path in changed_files:
            self.update_node_links(node, graph)
        
        for child in node.children:
            self._update_changed_nodes(child, graph, changed_files)