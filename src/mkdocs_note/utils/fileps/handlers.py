from mkdocs_note.logger import Logger
from mkdocs_note.config import PluginConfig
from pathlib import Path
from typing import List

class NoteScanner:
    """Note file scanner"""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def scan_notes(self) -> List[Path]:
        """Scan notes directory, return all supported note files
        """
        notes_dir = Path(self.config.notes_dir)
        if not notes_dir.exists():
            self.logger.warning(f"Notes directory does not exist: {notes_dir}")
            return []
        
        notes = []
        
        try:
            for file_path in notes_dir.rglob('*'):
                if self._is_valid_note_file(file_path):
                    notes.append(file_path)
        except PermissionError as e:
            self.logger.error(f"Permission denied while scanning {notes_dir}: {e}")
            return []
        
        self.logger.debug(f"Found {len(notes)} note files")
        return notes
    
    def _is_valid_note_file(self, file_path: Path) -> bool:
        """Check if file is a valid note file

        Args:
            file_path (Path): The path of the file to check

        Returns:
            bool: True if the file is a valid note file, False otherwise
        """
        if not file_path.is_file():
            return False
        
        # Check extension
        if file_path.suffix.lower() not in self.config.supported_extensions:
            return False
        
        # Check exclude patterns
        if file_path.name in self.config.exclude_patterns:
            return False
        
        # Check exclude directories
        for part in file_path.parts:
            if part in self.config.exclude_dirs:
                return False
        
        return True

class AssetScanner:
    """Asset scanner"""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def scan_assets(self) -> List[Path]:
        """Scan assets directory, return all assets files

        Returns:
            List[Path]: The list of valid asset files
        """
        assets_dir = Path(self.config.assets_dir)
        if not assets_dir.exists():
            self.logger.warning(f"Assets directory does not exist: {assets_dir}")
            return []
        
        assets = []
        
        try:
            for file_path in assets_dir.rglob('*'):
                if self._is_valid_asset_file(file_path):
                    assets.append(file_path)
        except PermissionError as e:
            self.logger.error(f"Permission denied while scanning {assets_dir}: {e}")
            return []
        
        self.logger.debug(f"Found {len(assets)} asset files")
        return assets
    
    def _is_valid_asset_file(self, file_path: Path) -> bool:
        """Check if file is a valid asset file

        Args:
            file_path (Path): The path of the file to check

        Returns:
            bool: True if the file is a valid asset file, False otherwise
        """
        if not file_path.is_file():
            return False
        
        return True
