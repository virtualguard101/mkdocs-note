"""
Link Parser

解析Markdown文件中的维基链接 [[link]] 格式。
"""

import re
import sys
from pathlib import Path
from typing import List
from .base_parser import BaseParser


class LinkParser(BaseParser):
    """
    解析Markdown笔记中的[[维基链接]]的解析器。
    
    支持多种链接格式：
    - [[filename]] - 简单文件名链接
    - [[filename|display text]] - 带显示文本的链接
    - [[path/to/filename]] - 带路径的链接
    """

    def __init__(self):
        super().__init__()
        # 匹配 [[link]] 或 [[link|display]] 格式
        self.wiki_link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file (only .md files)."""
        return super().can_parse(file_path) and file_path.suffix == '.md'

    def parse(self, file_path: Path) -> List[str]:
        """
        解析Markdown笔记中的[[维基链接]]并返回绝对目标路径
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            List[str]: 笔记中引用的所有目标文件的绝对路径列表
        """
        if not self.can_parse(file_path):
            return []

        content = self._read_file_safely(file_path)
        if not content:
            return []

        return self._extract_links(content, file_path.parent)

    def _extract_links(self, content: str, base_dir: Path) -> List[str]:
        """
        从内容中提取所有维基链接。
        
        Args:
            content: 文件内容
            base_dir: 基础目录，用于解析相对路径
            
        Returns:
            链接的绝对路径列表
        """
        links = []
        matches = self.wiki_link_pattern.findall(content)
        
        for match in matches:
            link_target = match[0].strip()  # 第一个组是链接目标
            # 第二个组是显示文本(如果存在)，我们不需要它来解析路径
            
            if link_target:
                absolute_path = self._resolve_link_path(link_target, base_dir)
                if absolute_path:
                    links.append(absolute_path)
        
        return links

    def _resolve_link_path(self, link_target: str, base_dir: Path) -> str:
        """
        解析链接目标到绝对路径。
        
        Args:
            link_target: 链接目标（可能是相对路径或文件名）
            base_dir: 基础目录
            
        Returns:
            解析后的绝对路径字符串，如果无法解析则返回空字符串
        """
        try:
            # 如果没有扩展名，默认添加 .md
            if not Path(link_target).suffix:
                link_target = f"{link_target}.md"
            
            # 构建绝对路径
            target_path = base_dir / link_target
            return str(target_path.absolute())
            
        except Exception as e:
            print(f"Error resolving link path '{link_target}': {e}", file=sys.stderr)
            return ""

    def extract_link_info(self, content: str) -> List[dict]:
        """
        提取链接的详细信息，包括显示文本。
        
        Args:
            content: 文件内容
            
        Returns:
            链接信息字典列表，包含 'target' 和 'display' 字段
        """
        link_info = []
        matches = self.wiki_link_pattern.findall(content)
        
        for match in matches:
            target = match[0].strip()
            display = match[1].strip() if match[1] else target
            
            link_info.append({
                'target': target,
                'display': display,
                'original': f"[[{match[0]}{f'|{match[1]}' if match[1] else ''}]]"
            })
        
        return link_info