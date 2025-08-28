"""
Metadata Parser

解析Markdown文件中的YAML front matter元数据。
"""

import re
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from .base_parser import BaseParser


class MetadataParser(BaseParser):
    """
    解析Markdown文件中的YAML front matter元数据。
    
    支持标准的YAML front matter格式：
    ---
    title: "Note Title"
    tags: [tag1, tag2]
    created: 2023-01-01
    ---
    """

    def __init__(self):
        super().__init__()
        # 匹配YAML front matter的正则表达式
        self.frontmatter_pattern = re.compile(
            r'^---\s*\n(.*?)\n---\s*\n',
            re.MULTILINE | re.DOTALL
        )

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file (only .md files)."""
        return super().can_parse(file_path) and file_path.suffix == '.md'

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        解析Markdown文件中的YAML front matter元数据。
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            Dict[str, Any]: 解析出的元数据字典
        """
        if not self.can_parse(file_path):
            return {}

        content = self._read_file_safely(file_path)
        if not content:
            return {}

        return self._extract_frontmatter(content)

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        从内容中提取YAML front matter。
        
        Args:
            content: 文件内容
            
        Returns:
            解析出的元数据字典
        """
        match = self.frontmatter_pattern.match(content)
        if not match:
            return {}

        yaml_content = match.group(1)
        return self._parse_yaml(yaml_content)

    def _parse_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """
        解析YAML内容。
        
        Args:
            yaml_content: YAML字符串
            
        Returns:
            解析出的数据字典
        """
        try:
            return yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML content: {e}", file=sys.stderr)
            return {}

    def extract_content_without_frontmatter(self, file_path: Path) -> str:
        """
        提取不包含front matter的内容。
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            去除front matter后的内容
        """
        if not self.can_parse(file_path):
            return ""

        content = self._read_file_safely(file_path)
        if not content:
            return ""

        # 移除front matter
        content_without_fm = self.frontmatter_pattern.sub('', content, count=1)
        return content_without_fm.strip()

    def has_frontmatter(self, file_path: Path) -> bool:
        """
        检查文件是否包含front matter。
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            如果包含front matter返回True，否则返回False
        """
        if not self.can_parse(file_path):
            return False

        content = self._read_file_safely(file_path)
        return bool(self.frontmatter_pattern.match(content))

    def update_metadata(self, file_path: Path, new_metadata: Dict[str, Any]) -> bool:
        """
        更新文件的元数据。
        
        Args:
            file_path: Markdown文件路径
            new_metadata: 新的元数据字典
            
        Returns:
            更新成功返回True，否则返回False
        """
        if not self.can_parse(file_path):
            return False

        try:
            content = self._read_file_safely(file_path)
            if not content:
                return False

            # 生成新的YAML front matter
            yaml_content = yaml.dump(new_metadata, default_flow_style=False, allow_unicode=True)
            new_frontmatter = f"---\n{yaml_content}---\n"

            # 移除旧的front matter（如果存在）
            content_without_fm = self.frontmatter_pattern.sub('', content, count=1)
            
            # 添加新的front matter
            new_content = new_frontmatter + content_without_fm.strip()

            # 写入文件
            file_path.write_text(new_content, encoding='utf-8')
            return True

        except Exception as e:
            print(f"Error updating metadata for {file_path}: {e}", file=sys.stderr)
            return False