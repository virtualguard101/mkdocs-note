"""
Note cleaner for managing orphaned assets and note movements.
"""

import shutil
from pathlib import Path
from typing import List, Set, Tuple

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.fileps.handlers import NoteScanner


class NoteCleaner:
    """Cleaner for managing orphaned assets."""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.note_scanner = NoteScanner(config, logger)
    
    def find_orphaned_assets(self) -> List[Path]:
        """Find asset directories that don't have corresponding note files.
        
        Returns:
            List[Path]: List of orphaned asset directory paths
        """
        notes_dir = Path(self.config.notes_dir)
        
        # Get all note files
        note_files = self.note_scanner.scan_notes()
        
        # Build a set of expected asset directory paths
        expected_asset_dirs: Set[str] = set()
        for note_file in note_files:
            # Calculate asset directory based on note file location
            asset_dir_path = note_file.parent / "assets" / note_file.stem
            expected_asset_dirs.add(str(asset_dir_path.resolve()))
        
        # Find all actual asset directories by scanning notes_dir
        orphaned_dirs: List[Path] = []
        
        try:
            # Scan for 'assets' directories within notes_dir
            for assets_subdir in notes_dir.rglob('assets'):
                if not assets_subdir.is_dir():
                    continue
                    
                # Check all subdirectories within each assets directory
                for item in assets_subdir.iterdir():
                    if item.is_dir():
                        # Check if this is a leaf directory (no subdirectories)
                        has_subdirs = any(child.is_dir() for child in item.iterdir())
                        
                        if not has_subdirs:
                            # This is a leaf directory, check if it corresponds to a note
                            item_resolved = str(item.resolve())
                            if item_resolved not in expected_asset_dirs:
                                orphaned_dirs.append(item)
        except Exception as e:
            self.logger.error(f"Error scanning asset directories: {e}")
        
        return orphaned_dirs
    
    def clean_orphaned_assets(self, dry_run: bool = False) -> Tuple[int, List[Path]]:
        """Remove orphaned asset directories.
        
        Args:
            dry_run (bool): If True, only report what would be removed without actually removing
        
        Returns:
            Tuple[int, List[Path]]: (number of removed directories, list of removed paths)
        """
        orphaned_dirs = self.find_orphaned_assets()
        
        if not orphaned_dirs:
            self.logger.info("No orphaned asset directories found")
            return 0, []
        
        removed_dirs: List[Path] = []
        
        for asset_dir in orphaned_dirs:
            if dry_run:
                self.logger.info(f"[DRY RUN] Would remove: {asset_dir}")
                removed_dirs.append(asset_dir)
            else:
                try:
                    self.logger.info(f"Removing orphaned asset directory: {asset_dir}")
                    shutil.rmtree(asset_dir)
                    removed_dirs.append(asset_dir)
                    
                    # Clean up empty parent directories
                    self._cleanup_empty_parent_dirs(asset_dir.parent)
                except Exception as e:
                    self.logger.error(f"Failed to remove {asset_dir}: {e}")
        
        return len(removed_dirs), removed_dirs
    
    def _cleanup_empty_parent_dirs(self, directory: Path) -> None:
        """Recursively clean up empty parent directories.
        
        This method removes empty 'assets' directories and their empty parent
        directories up to the note directory level.
        
        Args:
            directory (Path): The directory to start cleanup from
        """
        try:
            current_dir = directory.resolve()
            notes_dir = Path(self.config.notes_dir).resolve()
            
            # Don't remove directories outside or at the notes directory level
            if not current_dir.is_relative_to(notes_dir) or current_dir == notes_dir:
                return
            
            # Check if directory is empty
            if current_dir.exists() and current_dir.is_dir():
                try:
                    # Check if directory is empty (no files or subdirectories)
                    if not any(current_dir.iterdir()):
                        self.logger.debug(f"Removing empty directory: {current_dir}")
                        current_dir.rmdir()
                        # Recursively clean up parent
                        self._cleanup_empty_parent_dirs(current_dir.parent)
                except OSError:
                    # Directory not empty or other error, stop cleanup
                    pass
        except Exception as e:
            self.logger.debug(f"Error during directory cleanup: {e}")


