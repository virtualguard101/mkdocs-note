"""
Data models for mkdocs-note plugin.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class NoteInfo:
    """Note information data class
    """
    file_path: Path
    title: str
    relative_url: str
    modified_date: str
    file_size: int
    modified_time: float
    assets_list: List['AssetsInfo']


@dataclass
class AssetsInfo:
    """Assets information data class
    """
    file_path: Path
    file_name: str
    relative_path: str
    index_in_list: int
    exists: bool = True


@dataclass
class AssetTreeInfo:
    """Information about asset tree structure."""
    note_name: str
    asset_dir: Path
    expected_structure: List[Path]
    actual_structure: List[Path]
    is_compliant: bool
    missing_dirs: List[Path]
    extra_dirs: List[Path]
