"""
Note directory initializer for managing asset tree structure.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.file_manager import NoteScanner
from mkdocs_note.core.data_models import AssetTreeInfo
from mkdocs_note.core.assets_manager import get_note_relative_path


class NoteInitializer:
    """Note directory initializer for asset tree management."""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.file_scanner = NoteScanner(config, logger)
    
    def initialize_note_directory(self, notes_dir: Optional[Path] = None) -> int:
        """Initialize note directory with proper asset tree structure.
        
        Args:
            notes_dir (Optional[Path]): The notes directory to initialize. 
                                      If None, uses config.notes_dir.
        
        Returns:
            int: 0 if successful, 1 if failed
        """
        try:
            # Use provided directory or config default
            target_dir = Path(notes_dir) if notes_dir else Path(self.config.notes_dir)
            
            self.logger.debug(f"Initializing note directory: {target_dir}")
            
            # Check if directory exists
            if not target_dir.exists():
                self.logger.debug(f"Creating notes directory: {target_dir}")
                target_dir.mkdir(parents=True, exist_ok=True)
            
            # Scan existing notes
            note_files = self.file_scanner.scan_notes()
            
            if not note_files:
                self.logger.warning("No note files found. Creating basic structure.")
                self._create_basic_structure(target_dir)
                return 0
            
            # Analyze current asset tree
            asset_tree_analysis = self._analyze_asset_tree(target_dir, note_files)
            
            # Check compliance and fix if needed
            non_compliant = [info for info in asset_tree_analysis if not info.is_compliant]
            
            if non_compliant:
                self.logger.debug(f"Found {len(non_compliant)} non-compliant asset structures")
                self._fix_asset_tree(target_dir, non_compliant)
            else:
                self.logger.debug("Asset tree structure is already compliant")
            
            # Create index file if it doesn't exist
            self._ensure_index_file(target_dir)
            
            self.logger.debug("Note directory initialization completed successfully")
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to initialize note directory: {e}")
            return 1
    
    def _create_basic_structure(self, notes_dir: Path) -> None:
        """Create basic directory structure for notes.
        
        Args:
            notes_dir (Path): The notes directory to create structure in
        """
        # Create assets directory
        assets_dir = notes_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Check and create template file
        self._ensure_template_file(notes_dir)
    
    def _analyze_asset_tree(self, notes_dir: Path, note_files: List[Path]) -> List[AssetTreeInfo]:
        """Analyze current asset tree structure.
        
        Args:
            notes_dir (Path): The notes directory
            note_files (List[Path]): List of note files
            
        Returns:
            List[AssetTreeInfo]: Analysis results for each note
        """
        analysis_results = []
        assets_dir = notes_dir / "assets"
        
        for note_file in note_files:
            # Use get_note_relative_path to calculate the tree-based path
            note_relative_path = get_note_relative_path(note_file, notes_dir)
            note_asset_dir = assets_dir / note_relative_path
            
            # For display purposes, use the full relative path as note name
            note_name = note_relative_path
            
            # Expected structure (based on our design)
            expected_structure = [note_asset_dir]
            
            # Actual structure
            actual_structure = []
            if note_asset_dir.exists():
                actual_structure = list(note_asset_dir.rglob('*'))
                actual_structure = [p for p in actual_structure if p.is_dir()]
            
            # Check compliance
            is_compliant = self._check_compliance(note_asset_dir, expected_structure)
            
            # Find missing and extra directories
            missing_dirs = []
            extra_dirs = []
            
            if not note_asset_dir.exists():
                missing_dirs = expected_structure
            
            analysis_results.append(AssetTreeInfo(
                note_name=note_name,
                asset_dir=note_asset_dir,
                expected_structure=expected_structure,
                actual_structure=actual_structure,
                is_compliant=is_compliant,
                missing_dirs=missing_dirs,
                extra_dirs=extra_dirs
            ))
        
        return analysis_results
    
    def _check_compliance(self, asset_dir: Path, expected_structure: List[Path]) -> bool:
        """Check if asset directory complies with our tree-based design.
        
        The tree-based design allows asset directories at any depth under assets/,
        mirroring the notes directory structure. The first-level subdirectories
        should have '.assets' suffix for better identification.
        
        Args:
            asset_dir (Path): The asset directory to check
            expected_structure (List[Path]): Expected directory structure
            
        Returns:
            bool: True if compliant, False otherwise
        """
        # Basic compliance check: asset directory should exist and be a directory
        if not asset_dir.exists() or not asset_dir.is_dir():
            return False
        
        # Check if asset_dir is under an 'assets' directory
        # Walk up the path to find 'assets' directory
        current = asset_dir
        found_assets = False
        while current.parent != current:  # Stop at root
            if current.parent.name == 'assets':
                found_assets = True
                break
            current = current.parent
        
        if not found_assets:
            return False
        
        # Additional check: if asset_dir is a first-level subdirectory under assets/
        # and it has multiple path components, it should have '.assets' suffix
        relative_to_assets = asset_dir.relative_to(current.parent)
        parts = relative_to_assets.parts
        
        # If there are multiple levels (e.g., 'dsa.assets/anal/iter')
        # the first level should have '.assets' suffix
        if len(parts) > 1 and not parts[0].endswith('.assets'):
            # This is a multi-level path but first level doesn't have .assets suffix
            # This might be an old flat structure
            return False
        
        return True
    
    def _fix_asset_tree(self, notes_dir: Path, non_compliant: List[AssetTreeInfo]) -> None:
        """Fix non-compliant asset tree structures.
        
        Args:
            notes_dir (Path): The notes directory
            non_compliant (List[AssetTreeInfo]): Non-compliant structures to fix
        """
        assets_dir = notes_dir / "assets"
        
        for info in non_compliant:
            self.logger.debug(f"Fixing asset structure for note: {info.note_name}")
            
            # Create missing directories
            for missing_dir in info.missing_dirs:
                missing_dir.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {missing_dir}")
            
            # Handle extra directories (warn but don't delete)
            if info.extra_dirs:
                self.logger.warning(
                    f"Note '{info.note_name}' has extra directories that don't match our design: "
                    f"{[str(d) for d in info.extra_dirs]}"
                )
                self.logger.debug("These directories will be preserved but may not be managed by the plugin")
    
    def _ensure_index_file(self, notes_dir: Path) -> None:
        """Ensure index file exists in notes directory.
        
        Args:
            notes_dir (Path): The notes directory
        """
        index_file = notes_dir / "index.md"
        
        if not index_file.exists():
            index_file.write_text("", encoding='utf-8')
            self.logger.debug(f"Created index file: {index_file}")
    
    def _ensure_template_file(self, notes_dir: Path) -> None:
        """Ensure template file exists based on config.
        
        Args:
            notes_dir (Path): The notes directory
        """
        template_path = Path(self.config.notes_template)
        
        # Check if template exists
        if template_path.exists():
            self.logger.debug(f"Template file found: {template_path}")
            return
        
        # Template doesn't exist, check if we should create it
        self.logger.warning(f"Template file not found: {template_path}")
        
        # Determine if we should create the template
        should_create = False
        
        # If template is in the notes directory, create it
        if str(template_path).startswith(str(notes_dir)):
            should_create = True
            # Ensure parent directory exists
            template_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create empty template file
        if should_create:
            template_path.write_text("", encoding='utf-8')
            self.logger.debug(f"Created template file: {template_path}")
        else:
            self.logger.warning(
                f"Template file not found and cannot be auto-created: {template_path}"
            )
            self.logger.debug(
                f"Please create the template file manually or update the 'notes_template' "
                f"configuration in mkdocs.yml"
            )
    
    def validate_asset_tree_compliance(self, notes_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
        """Validate if the current asset tree complies with our design.
        
        Args:
            notes_dir (Optional[Path]): The notes directory to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_compliant, error_messages)
        """
        try:
            target_dir = Path(notes_dir) if notes_dir else Path(self.config.notes_dir)
            
            if not target_dir.exists():
                return False, [f"Notes directory does not exist: {target_dir}"]
            
            # Scan existing notes
            note_files = self.file_scanner.scan_notes()
            
            if not note_files:
                return True, []  # No notes, so no compliance issues
            
            # Analyze asset tree
            asset_tree_analysis = self._analyze_asset_tree(target_dir, note_files)
            
            # Check for non-compliant structures
            non_compliant = [info for info in asset_tree_analysis if not info.is_compliant]
            
            if non_compliant:
                error_messages = []
                for info in non_compliant:
                    error_messages.append(
                        f"Note '{info.note_name}' has non-compliant asset structure: {info.asset_dir}"
                    )
                return False, error_messages
            
            return True, []
            
        except Exception as e:
            return False, [f"Error validating asset tree: {e}"]
