"""
Data models for mkdocs-note plugin.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NoteFrontmatter:
    """Frontmatter metadata for notes.
    
    This class stores frontmatter metadata extracted from note files.
    It supports both standard fields and custom fields for extensibility.
    
    Attributes:
        date: Creation or publication date
        permalink: Custom permalink for the note
        publish: Whether the note should be published
        custom: Dictionary for storing custom metadata fields
    """
    date: Optional[str] = None
    permalink: Optional[str] = None
    publish: Optional[bool] = True
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert frontmatter to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of frontmatter
        """
        result = {}
        
        # Add standard fields
        if self.date is not None:
            result['date'] = self.date
        if self.permalink is not None:
            result['permalink'] = self.permalink
        if self.publish is not None:
            result['publish'] = self.publish
        
        # Add custom fields
        result.update(self.custom)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoteFrontmatter':
        """Create frontmatter from dictionary.
        
        Args:
            data: Dictionary containing frontmatter data
            
        Returns:
            NoteFrontmatter: The frontmatter object
        """
        # Extract standard fields
        date = data.get('date')
        permalink = data.get('permalink')
        publish = data.get('publish', True)
        
        # Extract custom fields (everything else)
        custom = {
            k: v for k, v in data.items()
            if k not in ('date', 'permalink', 'publish')
        }
        
        return cls(
            date=date,
            permalink=permalink,
            publish=publish,
            custom=custom
        )


@dataclass
class NoteInfo:
    """Note information data class
    
    Attributes:
        file_path: Path to the note file
        title: Title extracted from the note
        relative_url: Relative URL for the note in the site
        modified_date: Last modified date (formatted string)
        file_size: File size in bytes
        modified_time: Last modified time (Unix timestamp)
        assets_list: List of assets associated with the note
        frontmatter: Frontmatter metadata (optional)
    """
    file_path: Path
    title: str
    relative_url: str
    modified_date: str
    file_size: int
    modified_time: float
    assets_list: List['AssetsInfo']
    frontmatter: Optional[NoteFrontmatter] = None


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
