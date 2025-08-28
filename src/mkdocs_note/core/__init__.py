"""
MkDocs Note Core Module

提供笔记树构建、链接解析和图结构生成的核心功能。

重构后的模块化架构：
- models: 数据模型层(FileNode, NoteNode, NoteGraph)
- parsers: 解析器层(LinkParser, MetadataParser)
- builders: 构建器层(TreeBuilder, GraphBuilder)
- managers: 管理器层(FileManager, NoteManager)

主要组件：
1. NoteManager - 高级笔记管理器，提供完整的笔记管理功能
2. TreeBuilder - 树构建器，从文件系统构建笔记树
3. GraphBuilder - 图构建器，从笔记树构建链接图
4. 各种解析器 - 解析链接和元数据

该模块负责将文件系统目录结构转换为笔记树，解析笔记间的链接关系，
并构建双向链接图结构用于知识图谱展示。
"""

# 导入主要的公共接口
from .models import FileNode, NoteNode, NoteGraph
from .builders import TreeBuilder, GraphBuilder
from .parsers import LinkParser, MetadataParser
from .managers import FileManager, NoteManager

# 为了向后兼容，也导出旧的函数接口
from .legacy import build_tree, parse_note_links, build_note_graph

__all__ = [
    # 核心模型
    'FileNode',
    'NoteNode', 
    'NoteGraph',
    
    # 构建器
    'TreeBuilder',
    'GraphBuilder',
    
    # 解析器
    'LinkParser',
    'MetadataParser',
    
    # 管理器
    'FileManager',
    'NoteManager',
    
    # 向后兼容的函数
    'build_tree',
    'parse_note_links',
    'build_note_graph'
]