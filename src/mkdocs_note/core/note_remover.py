"""
Note remover for deleting notes and their associated assets.
"""

import shutil
from pathlib import Path
from typing import List, Tuple

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.assets_manager import get_note_relative_path


class NoteRemover:
    """Note remover for deleting note files and their asset directories."""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def remove_note(self, note_path: Path, remove_assets: bool = True) -> int:
        """Remove a note file and optionally its asset directory.
        
        Args:
            note_path (Path): The path of the note file to remove
            remove_assets (bool): Whether to also remove the asset directory
        
        Returns:
            int: 0 if successful, 1 if failed
        """
        try:
            # Validate the note file exists
            if not note_path.exists():
                self.logger.error(f"Note file does not exist: {note_path}")
                return 1
            
            if not note_path.is_file():
                self.logger.error(f"Path is not a file: {note_path}")
                return 1
            
            # Get the asset directory before removing the note
            asset_dir = None
            if remove_assets:
                asset_dir = self._get_asset_directory(note_path)
            
            # Remove the note file
            self.logger.info(f"Removing note file: {note_path}")
            note_path.unlink()
            self.logger.info(f"Successfully removed note file: {note_path}")
            
            # Remove the asset directory if requested and exists
            if remove_assets and asset_dir and asset_dir.exists():
                self.logger.info(f"Removing asset directory: {asset_dir}")
                shutil.rmtree(asset_dir)
                self.logger.info(f"Successfully removed asset directory: {asset_dir}")
                
                # Clean up empty parent directories
                self._cleanup_empty_parent_dirs(asset_dir.parent)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to remove note: {e}")
            return 1
    
    def remove_multiple_notes(self, note_paths: List[Path], remove_assets: bool = True) -> Tuple[int, int]:
        """Remove multiple note files and their asset directories.
        
        Args:
            note_paths (List[Path]): List of note file paths to remove
            remove_assets (bool): Whether to also remove asset directories
        
        Returns:
            Tuple[int, int]: (number of successful removals, number of failed removals)
        """
        success_count = 0
        failed_count = 0
        
        for note_path in note_paths:
            result = self.remove_note(note_path, remove_assets)
            if result == 0:
                success_count += 1
            else:
                failed_count += 1
        
        return success_count, failed_count
    
    def _get_asset_directory(self, note_file_path: Path) -> Path:
        """Get the asset directory path for a note file.
        
        Args:
            note_file_path (Path): The path of the note file
            
        Returns:
            Path: The asset directory path
        """
        notes_dir = Path(self.config.notes_dir)
        note_relative_path = get_note_relative_path(note_file_path, notes_dir)
        
        assets_dir = Path(self.config.assets_dir)
        return assets_dir / note_relative_path
    
    def _cleanup_empty_parent_dirs(self, directory: Path) -> None:
        """Recursively clean up empty parent directories.
        
        Args:
            directory (Path): The directory to start cleanup from
        """
        try:
            assets_dir = Path(self.config.assets_dir).resolve()
            current_dir = directory.resolve()
            
            # Don't remove the assets root directory
            if current_dir <= assets_dir:
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

