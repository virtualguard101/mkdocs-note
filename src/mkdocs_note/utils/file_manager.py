from mkdocs_note.logger import Logger
from mkdocs_note.config import PluginConfig
from pathlib import Path
from typing import List

class NoteScanner:
    """Note file scanner - Legacy class for backward compatibility.
    
    This class is deprecated and will be removed in future versions.
    Use RecentNotesScanner from recent_notes_manager.py for new functionality.
    """
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.logger.warning("NoteScanner is deprecated. Use RecentNotesScanner instead.")
    
    def scan_notes(self) -> List[Path]:
        """Scan notes directory, return all supported note files.
        
        This method is deprecated and maintained for backward compatibility.
        """
        # Try to use recent_notes_scan_field if available, fallback to notes_dir
        scan_field = getattr(self.config, 'recent_notes_scan_field', None)
        if scan_field:
            # Use the new recent notes scanner
            from mkdocs_note.utils.notes.recent_notes_manager import RecentNotesScanner
            new_scanner = RecentNotesScanner(self.config, self.logger)
            return new_scanner.scan_recent_notes()
        
        # Fallback to old behavior for backward compatibility
        notes_dir = getattr(self.config, 'notes_dir', 'docs/notes')
        notes_dir = Path(notes_dir)
        
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
    """Asset scanner - Legacy class for backward compatibility.
    
    This class is deprecated and will be removed in future versions.
    Assets are now managed using co-located structure.
    """
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.logger.warning("AssetScanner is deprecated. Assets now use co-located structure.")
    
    def scan_assets(self) -> List[Path]:
        """Scan assets directory, return all assets files.
        
        This method is deprecated and maintained for backward compatibility.
        Assets are now managed using co-located structure.

        Returns:
            List[Path]: The list of valid asset files
        """
        # Try to use assets_dir if available for backward compatibility
        assets_dir_path = getattr(self.config, 'assets_dir', None)
        if not assets_dir_path:
            self.logger.warning("No assets directory configured. Assets now use co-located structure.")
            return []
        
        assets_dir = Path(assets_dir_path)
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
