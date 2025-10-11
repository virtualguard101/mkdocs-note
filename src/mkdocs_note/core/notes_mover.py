"""
Note mover for relocating or renaming notes with their assets.
"""
import shutil
from pathlib import Path

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.file_manager import NoteScanner
from mkdocs_note.core.assets_manager import get_note_relative_path



class NoteMover:
    """Mover for relocating or renaming notes with their assets."""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.note_scanner = NoteScanner(config, logger)
    
    def move_note_or_directory(self, source_path: Path, dest_path: Path, move_assets: bool = True) -> int:
        """Move a note file or directory (with all notes inside) and their assets.
        
        This method mimics the behavior of shell 'mv' command:
        - If destination doesn't exist, rename source to destination
        - If destination exists and is a directory, move source into destination
        
        Args:
            source_path (Path): The current path (file or directory)
            dest_path (Path): The destination path
            move_assets (bool): Whether to also move the asset directories
        
        Returns:
            int: 0 if successful, 1 if failed
        """
        try:
            # Adjust destination path if it exists and is a directory
            # This mimics shell 'mv' behavior: mv source dest/ → dest/source
            if dest_path.exists() and dest_path.is_dir():
                dest_path = dest_path / source_path.name
                self.logger.info(f"Destination is a directory, moving to: {dest_path}")
            
            # Check if adjusted destination exists
            if dest_path.exists():
                self.logger.error(f"Destination already exists: {dest_path}")
                return 1
            
            # Check if source is a directory
            if source_path.is_dir():
                return self.move_directory(source_path, dest_path, move_assets)
            else:
                return self.move_note(source_path, dest_path, move_assets)
        except Exception as e:
            self.logger.error(f"Failed to move: {e}")
            return 1
    
    def move_directory(self, source_dir: Path, dest_dir: Path, move_assets: bool = True) -> int:
        """Move a directory with all notes and their assets.
        
        Args:
            source_dir (Path): The current directory path
            dest_dir (Path): The destination directory path
            move_assets (bool): Whether to also move the asset directories
        
        Returns:
            int: 0 if successful, 1 if failed
        """
        try:
            # Validate source directory exists
            if not source_dir.exists():
                self.logger.error(f"Source directory does not exist: {source_dir}")
                return 1
            
            if not source_dir.is_dir():
                self.logger.error(f"Source path is not a directory: {source_dir}")
                return 1
            
            # Validate destination doesn't already exist
            if dest_dir.exists():
                self.logger.error(f"Destination already exists: {dest_dir}")
                return 1
            
            # Get all note files in the source directory
            notes_dir = Path(self.config.notes_dir).resolve()
            source_dir_resolved = source_dir.resolve()
            
            # Find all notes in the source directory
            all_note_files = []
            for file_path in source_dir_resolved.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.config.supported_extensions:
                    # Check if it's not in excluded patterns
                    if file_path.name not in self.config.exclude_patterns:
                        all_note_files.append(file_path)
            
            if not all_note_files:
                self.logger.warning(f"No note files found in directory: {source_dir}")
            
            self.logger.info(f"Found {len(all_note_files)} note file(s) to move")
            
            # Create destination directory
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Move each note file
            failed_count = 0
            for note_file in all_note_files:
                # Calculate relative path from source directory
                try:
                    rel_path = note_file.relative_to(source_dir_resolved)
                except ValueError:
                    self.logger.error(f"Could not calculate relative path for {note_file}")
                    failed_count += 1
                    continue
                
                # Calculate destination path
                dest_note_path = dest_dir / rel_path
                
                # Move the note
                result = self.move_note(note_file, dest_note_path, move_assets)
                if result != 0:
                    failed_count += 1
            
            # Move any remaining non-note files
            for item in source_dir_resolved.iterdir():
                if item.is_file() and item not in all_note_files:
                    # Move non-note files (like images, etc.)
                    dest_item = dest_dir / item.name
                    if not dest_item.exists():
                        shutil.move(str(item), str(dest_item))
            
            # Remove the source directory if it's empty or only has empty subdirs
            if source_dir_resolved.exists():
                try:
                    # Try to remove the directory tree if empty
                    if not any(source_dir_resolved.rglob('*')):
                        shutil.rmtree(source_dir_resolved)
                    else:
                        self.logger.debug(f"Source directory still has files: {source_dir_resolved}")
                except Exception as e:
                    self.logger.debug(f"Could not remove source directory: {e}")
            
            if failed_count > 0:
                self.logger.warning(f"Failed to move {failed_count} note file(s)")
                return 1
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to move directory: {e}")
            return 1
    
    def move_note(self, source_path: Path, dest_path: Path, move_assets: bool = True) -> int:
        """Move or rename a note file and its asset directory.
        
        Args:
            source_path (Path): The current path of the note file
            dest_path (Path): The destination path for the note file
            move_assets (bool): Whether to also move the asset directory
        
        Returns:
            int: 0 if successful, 1 if failed
        """
        try:
            # Validate source file exists
            if not source_path.exists():
                self.logger.error(f"Source note file does not exist: {source_path}")
                return 1
            
            if not source_path.is_file():
                self.logger.error(f"Source path is not a file: {source_path}")
                return 1
            
            # Validate destination doesn't already exist
            if dest_path.exists():
                self.logger.error(f"Destination already exists: {dest_path}")
                return 1
            
            # Ensure destination parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get asset directories before moving
            source_asset_dir = None
            dest_asset_dir = None
            if move_assets:
                source_asset_dir = self._get_asset_directory(source_path)
                dest_asset_dir = self._get_asset_directory(dest_path)
            
            # Move the note file
            self.logger.info(f"Moving note file: {source_path} → {dest_path}")
            shutil.move(str(source_path), str(dest_path))
            self.logger.info(f"Successfully moved note file")
            
            # Move the asset directory if requested and exists
            if move_assets and source_asset_dir and source_asset_dir.exists():
                # Ensure destination asset parent directory exists
                dest_asset_dir.parent.mkdir(parents=True, exist_ok=True)
                
                self.logger.info(f"Moving asset directory: {source_asset_dir} → {dest_asset_dir}")
                shutil.move(str(source_asset_dir), str(dest_asset_dir))
                self.logger.info(f"Successfully moved asset directory")
                
                # Clean up empty parent directories in source
                self._cleanup_empty_parent_dirs(source_asset_dir.parent)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to move note: {e}")
            # Try to rollback if possible
            try:
                if dest_path.exists():
                    self.logger.info("Attempting to rollback changes...")
                    if not source_path.exists():
                        shutil.move(str(dest_path), str(source_path))
                    if move_assets and dest_asset_dir and dest_asset_dir.exists():
                        if source_asset_dir and not source_asset_dir.exists():
                            shutil.move(str(dest_asset_dir), str(source_asset_dir))
                    self.logger.info("Rollback completed")
            except Exception as rollback_error:
                self.logger.error(f"Rollback failed: {rollback_error}")
            return 1
    
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


