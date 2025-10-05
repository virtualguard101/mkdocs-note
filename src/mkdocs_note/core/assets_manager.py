import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.data_models import NoteInfo, AssetsInfo


def get_note_relative_path(note_file: Path, notes_dir: Path, use_assets_suffix: bool = True) -> str:
    """Get the relative path of a note file from notes directory.
    
    This function calculates the relative path of a note file with respect to
    the notes directory, excluding the file extension. This relative path is used
    as the unique identifier for the note and its assets directory.
    
    When use_assets_suffix is True, the first-level subdirectory will have '.assets'
    suffix added for better identification in the assets tree structure.
    
    Args:
        note_file (Path): The absolute or relative path of the note file
        notes_dir (Path): The absolute or relative path of the notes directory
        use_assets_suffix (bool): Whether to add '.assets' suffix to first-level subdirectory
    
    Returns:
        str: The relative path without extension
    
    Examples:
        >>> get_note_relative_path(Path("docs/notes/dsa/anal/iter.md"), Path("docs/notes"))
        'dsa.assets/anal/iter'
        >>> get_note_relative_path(Path("docs/notes/dsa/intro.md"), Path("docs/notes"))
        'dsa.assets/intro'
        >>> get_note_relative_path(Path("docs/notes/test.md"), Path("docs/notes"))
        'test'
    """
    try:
        # Ensure both paths are absolute for accurate relative path calculation
        note_file_abs = note_file.resolve()
        notes_dir_abs = notes_dir.resolve()
        
        # Get relative path from notes_dir to note_file
        relative = note_file_abs.relative_to(notes_dir_abs)
        
        # Get path without extension
        path_without_ext = relative.with_suffix('')
        
        # Add .assets suffix to first-level subdirectory if applicable
        if use_assets_suffix:
            parts = path_without_ext.parts
            if len(parts) > 1:
                # Has subdirectories, add .assets to first level
                first_level = parts[0] + '.assets'
                remaining = parts[1:]
                modified_path = Path(first_level).joinpath(*remaining)
                return modified_path.as_posix()
        
        return path_without_ext.as_posix()
    except ValueError:
        # If note_file is not under notes_dir, fall back to stem only
        return note_file.stem


class AssetsCatalogTree:
    """Assets catalog class, whose data structure is a **file system tree**.
    
    This class manages assets using a tree structure that mirrors the notes directory
    hierarchy. Each note is identified by its relative path from the notes directory,
    preventing conflicts between notes with the same name in different subdirectories.
    
    The first-level subdirectories in the assets tree have '.assets' suffix added for
    better identification and module categorization.
    
    Example structure:
        notes/
        ├── dsa/
        │   ├── anal/
        │   │   ├── iter_and_recu.md  → assets/dsa.assets/anal/iter_and_recu/
        │   │   └── space.md          → assets/dsa.assets/anal/space/
        │   └── ds/
        │       └── intro.md          → assets/dsa.assets/ds/intro/
        ├── language/
        │   └── cpp/
        │       └── intro.md          → assets/language.assets/cpp/intro/
        └── test.md                   → assets/test/
    """
    def __init__(self, root_path: Path, notes_dir: Path):
        """Initialize the assets catalog tree.
        
        Args:
            root_path (Path): The root path of assets directory
            notes_dir (Path): The root path of notes directory
        """
        self._root = root_path
        self._notes_dir = notes_dir
        self._catalog: Dict[str, List[AssetsInfo]] = {}
    
    def add_node(self, note_relative_path: str, assets_list: List[AssetsInfo]):
        """Add assets for a specific note to the tree.

        Args:
            note_relative_path (str): The relative path of the note (e.g., "python/intro")
            assets_list (List[AssetsInfo]): The list of assets for this note
        """
        self._catalog[note_relative_path] = assets_list
    
    def get_assets(self, note_relative_path: str) -> List[AssetsInfo]:
        """Get assets for a specific note.

        Args:
            note_relative_path (str): The relative path of the note

        Returns:
            List[AssetsInfo]: The list of assets for this note
        """
        return self._catalog.get(note_relative_path, [])
    
    def get_all_assets(self) -> Dict[str, List[AssetsInfo]]:
        """Get all assets in the catalog.

        Returns:
            Dict[str, List[AssetsInfo]]: All assets organized by note relative path
        """
        return self._catalog.copy()
    
    def get_asset_dir_for_note(self, note_file: Path) -> Path:
        """Get the asset directory path for a note file.
        
        Args:
            note_file (Path): The path of the note file
        
        Returns:
            Path: The asset directory path for this note
        """
        note_relative_path = get_note_relative_path(note_file, self._notes_dir)
        return self._root / note_relative_path


class AssetsManager:
    """Assets manager class, who contains the generator, 
    updater and so on of each catalogs of assets in order
    to manage the assets tree of the notebook efficiently.
    """
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.catalog_tree = AssetsCatalogTree(
            Path(config.assets_dir), 
            Path(config.notes_dir)
        )

    def catalog_generator(self, assets_list: List[AssetsInfo], note_info: NoteInfo) -> str:
        """Generate catalog of assets

        Args:
            assets_list (List[AssetsInfo]): The list of assets information
            note_info (NoteInfo): The note information

        Returns:
            str: The catalog of assets
        """
        note_relative_path = get_note_relative_path(
            note_info.file_path, 
            Path(self.config.notes_dir)
        )
        self.catalog_tree.add_node(note_relative_path, assets_list)
        
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
            # Get the note's relative path from notes_dir
            notes_dir = Path(self.config.notes_dir)
            note_relative_path = get_note_relative_path(note_file, notes_dir)
            
            # Determine the asset directory structure
            assets_dir = Path(self.config.assets_dir)
            note_assets_dir = assets_dir / note_relative_path
            
            # Construct the full asset file path
            asset_file = note_assets_dir / image_path
            
            # Construct the relative path for markdown references
            # This should be relative to the notes directory
            relative_path = f"assets/{note_relative_path}/{image_path}"
            
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
        """Update markdown content to use correct asset paths.
        
        This method converts relative asset references to paths that MkDocs
        can correctly resolve. The paths are relative to the note file's location.
        
        Args:
            content (str): The original markdown content
            note_file (Path): The note file path (absolute or relative to project root)
            
        Returns:
            str: The updated markdown content with corrected asset paths
        """
        def replace_image_path(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Skip external URLs and absolute paths
            if image_path.startswith(('http://', 'https://', '//', '/')):
                return match.group(0)
            
            # Get the note's relative path from notes_dir
            notes_dir = Path(self.config.notes_dir)
            note_relative_path = get_note_relative_path(note_file, notes_dir)
            
            # Calculate the depth of the note file (how many levels deep from notes_dir)
            # This determines how many "../" we need to go up
            try:
                note_file_abs = note_file.resolve() if not note_file.is_absolute() else note_file
                notes_dir_abs = notes_dir.resolve() if not notes_dir.is_absolute() else notes_dir
                relative_to_notes = note_file_abs.relative_to(notes_dir_abs)
                depth = len(relative_to_notes.parent.parts)
            except (ValueError, AttributeError):
                # Fallback: count slashes in relative path
                depth = note_relative_path.replace('.assets', '').count('/')
            
            # Build the relative path from note file to assets directory
            # Go up to notes_dir, then into assets directory
            up_levels = '../' * depth if depth > 0 else ''
            assets_path = f"{up_levels}assets/{note_relative_path}/{image_path}"
            
            return f"![{alt_text}]({assets_path})"
        
        return self.image_pattern.sub(replace_image_path, content)
