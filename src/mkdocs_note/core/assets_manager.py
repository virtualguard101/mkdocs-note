import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.data_models import NoteInfo, AssetsInfo


class AssetsCatalogTree:
    """Assets catalog class, whose data structure
    is a **file system tree**.
    """
    def __init__(self, root_path: Path):
        self._root = root_path
        self._catalog: Dict[str, List[AssetsInfo]] = {}
    
    def add_node(self, note_name: str, assets_list: List[AssetsInfo]):
        """Add assets for a specific note to the tree

        Args:
            note_name (str): The name of the note
            assets_list (List[AssetsInfo]): The list of assets for this note
        """
        self._catalog[note_name] = assets_list
    
    def get_assets(self, note_name: str) -> List[AssetsInfo]:
        """Get assets for a specific note

        Args:
            note_name (str): The name of the note

        Returns:
            List[AssetsInfo]: The list of assets for this note
        """
        return self._catalog.get(note_name, [])
    
    def get_all_assets(self) -> Dict[str, List[AssetsInfo]]:
        """Get all assets in the catalog

        Returns:
            Dict[str, List[AssetsInfo]]: All assets organized by note name
        """
        return self._catalog.copy()


class AssetsManager:
    """Assets manager class, who contains the generator, 
    updater and so on of each catalogs of assets in order
    to manage the assets tree of the notebook efficiently.
    """
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.catalog_tree = AssetsCatalogTree(Path(config.assets_dir))

    def catalog_generator(self, assets_list: List[AssetsInfo], note_info: NoteInfo) -> str:
        """Generate catalog of assets

        Args:
            assets_list (List[AssetsInfo]): The list of assets information
            note_info (NoteInfo): The note information

        Returns:
            str: The catalog of assets
        """
        note_name = note_info.file_path.stem
        self.catalog_tree.add_node(note_name, assets_list)
        
        if not assets_list:
            return ""
        
        catalog_lines = [f"## Assets for {note_info.title}"]
        catalog_lines.append("")
        
        for asset in assets_list:
            status = "✓" if asset.exists else "✗"
            catalog_lines.append(f"- {status} `{asset.file_name}` → `{asset.relative_path}`")
        
        return "\n".join(catalog_lines)

    def catalog_updater(self, catalog: str) -> bool:
        """Update catalog of assets
        
        Args:
            catalog (str): The catalog content to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # This could be used to update a catalog file if needed
            # For now, we just log the catalog
            self.logger.debug(f"Assets catalog updated: {len(catalog)} characters")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update assets catalog: {e}")
            return False
    

class AssetsProcessor:
    """Assets processor for handling image references in markdown files
    """
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    
    def process_assets(self, note_info: NoteInfo) -> List[AssetsInfo]:
        """Process assets from file name to full verbose uri

        Args:
            note_info (NoteInfo): The note information

        Returns:
            List[AssetsInfo]: The list of assets information
        """
        assets_list = []
        
        try:
            # Read the note file content
            content = note_info.file_path.read_text(encoding='utf-8')
            
            # Find all image references
            matches = self.image_pattern.findall(content)
            
            for idx, (alt_text, image_path) in enumerate(matches):
                # Skip external URLs
                if image_path.startswith(('http://', 'https://', '//')):
                    continue
                
                # Process local image references
                asset_info = self._process_image_reference(
                    image_path, note_info.file_path, idx
                )
                
                if asset_info:
                    assets_list.append(asset_info)
            
            self.logger.debug(f"Found {len(assets_list)} assets in {note_info.file_path.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to process assets for {note_info.file_path}: {e}")
        
        return assets_list
    
    def _process_image_reference(self, image_path: str, note_file: Path, index: int) -> Optional[AssetsInfo]:
        """Process a single image reference
        
        Args:
            image_path (str): The image path from markdown
            note_file (Path): The note file path
            index (int): The index of this asset in the list
            
        Returns:
            Optional[AssetsInfo]: The asset information if valid, None otherwise
        """
        try:
            # Determine the asset directory structure
            note_name = note_file.stem
            assets_dir = Path(self.config.assets_dir)
            note_assets_dir = assets_dir / note_name
            
            # Handle different path formats
            if '/' in image_path:
                # Path with subdirectories
                asset_file = note_assets_dir / image_path
                relative_path = f"assets/{note_name}/{image_path}"
            else:
                # Simple filename
                asset_file = note_assets_dir / image_path
                relative_path = f"assets/{note_name}/{image_path}"
            
            # Check if file exists
            exists = asset_file.exists()
            
            if not exists:
                self.logger.warning(f"Asset not found: {asset_file}")
            
            return AssetsInfo(
                file_path=asset_file,
                file_name=image_path,
                relative_path=relative_path,
                index_in_list=index,
                exists=exists
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process image reference '{image_path}': {e}")
            return None
    
    def update_markdown_content(self, content: str, note_file: Path) -> str:
        """Update markdown content to use full asset paths
        
        Args:
            content (str): The original markdown content
            note_file (Path): The note file path
            
        Returns:
            str: The updated markdown content with full asset paths
        """
        def replace_image_path(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Skip external URLs
            if image_path.startswith(('http://', 'https://', '//')):
                return match.group(0)
            
            # Convert to full path
            note_name = note_file.stem
            if '/' in image_path:
                new_path = f"assets/{note_name}/{image_path}"
            else:
                new_path = f"assets/{note_name}/{image_path}"
            
            return f"![{alt_text}]({new_path})"
        
        return self.image_pattern.sub(replace_image_path, content)
