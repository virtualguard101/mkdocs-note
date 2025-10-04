from dataclasses import dataclass
from pathlib import Path
from typing import List

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.note_manager import NoteInfo

@dataclass
class AssetsInfo:
    """Assets information data class
    """
    file_path: Path
    file_name: str
    index_in_list: int


class AssetsCatalogTree:
    """Assets catalog class, whose data structure
    is a **file system tree**.
    """
    def __init__(self, root_path: Path):
        self.root = root_path
    
    def add_node(self, node):
        """Add a node to the tree
        """
        pass
        # [ ] : implement add node logic


class AssetsManager:
    """Assets manager class, who contains the generator, 
    updater and so on of each catalogs of assets in order
    to manage the assets tree of the notebook efficiently.
    """
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger

    def catalog_generator(self, assets_list: List[AssetsInfo], note_info: NoteInfo) -> str:
        """Generate catalog of assets

        Args:
            assets_list (List[AssetsInfo]): The list of assets information
            note_info (NoteInfo): The note information

        Returns:
            str: The catalog of assets
        """
        pass
        # [ ] : implement catalog generator logic

    def catalog_updater(self, catalog: str) -> bool:
        """Update catalog of assets
        """
        pass
        # [ ] : implement catalog updater logic
    

class AssetsProcessor:
    """Assets processor
    """
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def process_assets(self, note_info: NoteInfo) -> List[AssetsInfo]:
        """Process assets from file name to full verbose uri

        Args:
            note_info (NoteInfo): The note information

        Returns:
            List[AssetsInfo]: The list of assets information
        """
        pass
        # [ ] : implement assets uri processing logic