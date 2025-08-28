"""
File Manager

负责文件系统操作和文件监控。
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Callable, Dict, Set
from ..models.file_node import FileNode


class FileManager:
    """
    文件管理器，负责文件系统操作和文件监控。
    
    提供以下功能：
    - 文件和目录的创建、删除、移动
    - 文件内容读写
    - 文件监控和变化检测
    - 批量文件操作
    """

    def __init__(self, root_path: Path):
        """
        初始化文件管理器。
        
        Args:
            root_path: 管理的根目录路径
        """
        self.root_path = Path(root_path).absolute()
        self._ensure_root_exists()

    def _ensure_root_exists(self) -> None:
        """确保根目录存在。"""
        if not self.root_path.exists():
            self.root_path.mkdir(parents=True, exist_ok=True)

    def create_file(self, relative_path: str, content: str = "") -> bool:
        """
        创建新文件。
        
        Args:
            relative_path: 相对于根目录的文件路径
            content: 文件内容
            
        Returns:
            创建成功返回True，否则返回False
        """
        try:
            file_path = self.root_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error creating file {relative_path}: {e}")
            return False

    def create_directory(self, relative_path: str) -> bool:
        """
        创建新目录。
        
        Args:
            relative_path: 相对于根目录的目录路径
            
        Returns:
            创建成功返回True，否则返回False
        """
        try:
            dir_path = self.root_path / relative_path
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {relative_path}: {e}")
            return False

    def delete_file(self, relative_path: str) -> bool:
        """
        删除文件。
        
        Args:
            relative_path: 相对于根目录的文件路径
            
        Returns:
            删除成功返回True，否则返回False
        """
        try:
            file_path = self.root_path / relative_path
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {relative_path}: {e}")
            return False

    def delete_directory(self, relative_path: str, recursive: bool = False) -> bool:
        """
        删除目录。
        
        Args:
            relative_path: 相对于根目录的目录路径
            recursive: 是否递归删除
            
        Returns:
            删除成功返回True，否则返回False
        """
        try:
            dir_path = self.root_path / relative_path
            if dir_path.exists() and dir_path.is_dir():
                if recursive:
                    shutil.rmtree(dir_path)
                else:
                    dir_path.rmdir()  # 只能删除空目录
                return True
            return False
        except Exception as e:
            print(f"Error deleting directory {relative_path}: {e}")
            return False

    def move_file(self, src_relative_path: str, dst_relative_path: str) -> bool:
        """
        移动文件。
        
        Args:
            src_relative_path: 源文件相对路径
            dst_relative_path: 目标文件相对路径
            
        Returns:
            移动成功返回True，否则返回False
        """
        try:
            src_path = self.root_path / src_relative_path
            dst_path = self.root_path / dst_relative_path
            
            if not src_path.exists():
                return False
                
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            return True
        except Exception as e:
            print(f"Error moving file from {src_relative_path} to {dst_relative_path}: {e}")
            return False

    def copy_file(self, src_relative_path: str, dst_relative_path: str) -> bool:
        """
        复制文件。
        
        Args:
            src_relative_path: 源文件相对路径
            dst_relative_path: 目标文件相对路径
            
        Returns:
            复制成功返回True，否则返回False
        """
        try:
            src_path = self.root_path / src_relative_path
            dst_path = self.root_path / dst_relative_path
            
            if not src_path.exists() or not src_path.is_file():
                return False
                
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src_path), str(dst_path))
            return True
        except Exception as e:
            print(f"Error copying file from {src_relative_path} to {dst_relative_path}: {e}")
            return False

    def read_file(self, relative_path: str) -> Optional[str]:
        """
        读取文件内容。
        
        Args:
            relative_path: 相对于根目录的文件路径
            
        Returns:
            文件内容，如果出错返回None
        """
        try:
            file_path = self.root_path / relative_path
            if file_path.exists() and file_path.is_file():
                return file_path.read_text(encoding='utf-8')
            return None
        except Exception as e:
            print(f"Error reading file {relative_path}: {e}")
            return None

    def write_file(self, relative_path: str, content: str) -> bool:
        """
        写入文件内容。
        
        Args:
            relative_path: 相对于根目录的文件路径
            content: 要写入的内容
            
        Returns:
            写入成功返回True，否则返回False
        """
        try:
            file_path = self.root_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error writing file {relative_path}: {e}")
            return False

    def file_exists(self, relative_path: str) -> bool:
        """
        检查文件是否存在。
        
        Args:
            relative_path: 相对于根目录的文件路径
            
        Returns:
            文件存在返回True，否则返回False
        """
        file_path = self.root_path / relative_path
        return file_path.exists() and file_path.is_file()

    def directory_exists(self, relative_path: str) -> bool:
        """
        检查目录是否存在。
        
        Args:
            relative_path: 相对于根目录的目录路径
            
        Returns:
            目录存在返回True，否则返回False
        """
        dir_path = self.root_path / relative_path
        return dir_path.exists() and dir_path.is_dir()

    def list_files(
        self, 
        relative_path: str = "", 
        pattern: str = "*",
        recursive: bool = False
    ) -> List[str]:
        """
        列出文件。
        
        Args:
            relative_path: 相对于根目录的目录路径
            pattern: 文件名模式
            recursive: 是否递归搜索
            
        Returns:
            相对路径的文件列表
        """
        try:
            search_path = self.root_path / relative_path
            if not search_path.exists() or not search_path.is_dir():
                return []
            
            if recursive:
                files = search_path.rglob(pattern)
            else:
                files = search_path.glob(pattern)
            
            # 返回相对于根目录的路径
            result = []
            for file_path in files:
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.root_path)
                    result.append(str(rel_path))
            
            return sorted(result)
        except Exception as e:
            print(f"Error listing files in {relative_path}: {e}")
            return []

    def get_file_stats(self, relative_path: str) -> Optional[Dict[str, any]]:
        """
        获取文件统计信息。
        
        Args:
            relative_path: 相对于根目录的文件路径
            
        Returns:
            文件统计信息字典，如果出错返回None
        """
        try:
            file_path = self.root_path / relative_path
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': file_path.is_file(),
                'is_directory': file_path.is_dir(),
                'absolute_path': str(file_path.absolute())
            }
        except Exception as e:
            print(f"Error getting stats for {relative_path}: {e}")
            return None

    def find_changed_files(self, since_timestamp: float) -> Set[str]:
        """
        查找自指定时间戳以来发生变化的文件。
        
        Args:
            since_timestamp: 起始时间戳
            
        Returns:
            发生变化的文件相对路径集合
        """
        changed_files = set()
        
        try:
            for file_path in self.root_path.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    if stat.st_mtime > since_timestamp:
                        rel_path = file_path.relative_to(self.root_path)
                        changed_files.add(str(rel_path))
        except Exception as e:
            print(f"Error finding changed files: {e}")
        
        return changed_files

    def backup_file(self, relative_path: str, backup_suffix: str = ".bak") -> bool:
        """
        备份文件。
        
        Args:
            relative_path: 要备份的文件相对路径
            backup_suffix: 备份文件后缀
            
        Returns:
            备份成功返回True，否则返回False
        """
        src_path = str(Path(relative_path))
        backup_path = f"{src_path}{backup_suffix}"
        return self.copy_file(src_path, backup_path)