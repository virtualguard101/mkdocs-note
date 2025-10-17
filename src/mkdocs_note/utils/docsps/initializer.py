"""
Note directory initializer for managing asset tree structure.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.fileps.handlers import NoteScanner
from mkdocs_note.utils.dataps.meta import AssetTreeInfo


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
        
        In the new design, asset directories are co-located with note files:
        - Note: docs/usage/contributing.md
        - Assets: docs/usage/assets/contributing/
        
        Args:
            notes_dir (Path): The notes directory
            note_files (List[Path]): List of note files
            
        Returns:
            List[AssetTreeInfo]: Analysis results for each note
        """
        analysis_results = []
        
        for note_file in note_files:
            # Calculate asset directory based on note file location
            # Asset directory is: note_file.parent / "assets" / note_file.stem
            note_asset_dir = note_file.parent / "assets" / note_file.stem
            
            # For display purposes, use relative path from notes_dir
            try:
                note_name = str(note_file.relative_to(notes_dir))
            except ValueError:
                note_name = note_file.name
            
            # Expected structure (based on our design)
            expected_structure = [note_asset_dir]
            
            # Actual structure
            actual_structure = []
            if note_asset_dir.exists():
                actual_structure = list(note_asset_dir.rglob('*'))
                actual_structure = [p for p in actual_structure if p.is_dir()]
            
            # Check compliance
            is_compliant = self._check_compliance(note_asset_dir, note_file)
            
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
    
    def _check_compliance(self, asset_dir: Path, note_file: Path) -> bool:
        """Check if asset directory complies with our co-located design.
        
        In the new design, asset directories are co-located with note files:
        - Note: /path/to/note.md
        - Assets: /path/to/assets/note/
        
        Args:
            asset_dir (Path): The asset directory to check
            note_file (Path): The corresponding note file
            
        Returns:
            bool: True if compliant, False otherwise
        """
        # Basic compliance check: asset directory should exist and be a directory
        if not asset_dir.exists() or not asset_dir.is_dir():
            return False
        
        # Check if asset_dir follows the pattern: note_file.parent / "assets" / note_file.stem
        expected_asset_dir = note_file.parent / "assets" / note_file.stem
        
        try:
            # Compare resolved paths for accuracy
            return asset_dir.resolve() == expected_asset_dir.resolve()
        except Exception:
            return False
    
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
        
        # Create template file with default content
        if should_create:
            default_template_content = """---
date: {{date}}
title: {{title}}
permalink: 
publish: true
---

# {{title}}

Start writing your note content..."""
            template_path.write_text(default_template_content, encoding='utf-8')
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
