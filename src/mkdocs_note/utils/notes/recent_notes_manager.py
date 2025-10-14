"""
Recent Notes Management System

This module provides an independent and enhanced recent notes insertion functionality,
separated from other plugin features for better maintainability and flexibility.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.data_models import NoteInfo
from mkdocs_note.utils.frontmatter.frontmatter_manager import FrontmatterManager


class RecentNotesScanner:
    """Recent notes scanner with flexible scanning strategies.
    
    Supports multiple scanning modes:
    - Directory scanning: 'docs/notes'
    - Pattern scanning: 'docs/**/*.md'
    - Metadata filtering: 'metadata.publish=true'
    """
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.frontmatter_manager = FrontmatterManager()
    
    def scan_recent_notes(self) -> List[Path]:
        """Scan for recent notes based on configuration.
        
        Returns:
            List[Path]: List of note file paths
        """
        scan_field = self.config.recent_notes_scan_field
        
        try:
            if self._is_directory_scan(scan_field):
                return self._scan_directory(Path(scan_field))
            elif self._is_pattern_scan(scan_field):
                return self._scan_pattern(scan_field)
            elif self._is_metadata_scan(scan_field):
                return self._scan_by_metadata(scan_field)
            else:
                # Default to directory scanning
                return self._scan_directory(Path(scan_field))
        except Exception as e:
            self.logger.error(f"Error scanning recent notes: {e}")
            return []
    
    def _is_directory_scan(self, scan_field: str) -> bool:
        """Check if scan field is a directory path."""
        return not ('*' in scan_field or scan_field.startswith('metadata.'))
    
    def _is_pattern_scan(self, scan_field: str) -> bool:
        """Check if scan field is a file pattern."""
        return '*' in scan_field
    
    def _is_metadata_scan(self, scan_field: str) -> bool:
        """Check if scan field is a metadata filter."""
        return scan_field.startswith('metadata.')
    
    def _scan_directory(self, directory: Path) -> List[Path]:
        """Scan a specific directory for note files.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List[Path]: List of note file paths
        """
        if not directory.exists():
            self.logger.warning(f"Directory does not exist: {directory}")
            return []
        
        notes = []
        try:
            for file_path in directory.rglob('*'):
                if self._is_valid_note_file(file_path):
                    notes.append(file_path)
        except PermissionError as e:
            self.logger.error(f"Permission denied while scanning {directory}: {e}")
            return []
        
        self.logger.debug(f"Found {len(notes)} note files in directory: {directory}")
        return notes
    
    def _scan_pattern(self, pattern: str) -> List[Path]:
        """Scan using file pattern.
        
        Args:
            pattern: File pattern to match (e.g., 'docs/**/*.md')
            
        Returns:
            List[Path]: List of note file paths
        """
        # Convert pattern to glob pattern
        if pattern.startswith('docs/'):
            pattern = pattern[6:]  # Remove 'docs/' prefix
        
        # Find docs directory
        docs_dir = Path('docs')
        if not docs_dir.exists():
            self.logger.warning(f"Docs directory does not exist: {docs_dir}")
            return []
        
        notes = []
        try:
            for file_path in docs_dir.glob(pattern):
                if file_path.is_file() and self._is_valid_note_file(file_path):
                    notes.append(file_path)
        except Exception as e:
            self.logger.error(f"Error scanning pattern {pattern}: {e}")
            return []
        
        self.logger.debug(f"Found {len(notes)} note files matching pattern: {pattern}")
        return notes
    
    def _scan_by_metadata(self, metadata_filter: str) -> List[Path]:
        """Scan notes by metadata criteria.
        
        Args:
            metadata_filter: Metadata filter (e.g., 'metadata.publish=true')
            
        Returns:
            List[Path]: List of note file paths
        """
        # Parse metadata filter
        # Format: metadata.field=value
        if not metadata_filter.startswith('metadata.'):
            self.logger.error(f"Invalid metadata filter format: {metadata_filter}")
            return []
        
        filter_part = metadata_filter[9:]  # Remove 'metadata.' prefix
        if '=' not in filter_part:
            self.logger.error(f"Invalid metadata filter format: {metadata_filter}")
            return []
        
        field_name, expected_value = filter_part.split('=', 1)
        
        # Scan all markdown files in docs directory
        docs_dir = Path('docs')
        if not docs_dir.exists():
            self.logger.warning(f"Docs directory does not exist: {docs_dir}")
            return []
        
        notes = []
        try:
            for file_path in docs_dir.rglob('*.md'):
                if self._matches_metadata_criteria(file_path, field_name, expected_value):
                    notes.append(file_path)
        except Exception as e:
            self.logger.error(f"Error scanning by metadata: {e}")
            return []
        
        self.logger.debug(f"Found {len(notes)} note files matching metadata filter: {metadata_filter}")
        return notes
    
    def _matches_metadata_criteria(self, file_path: Path, field_name: str, expected_value: str) -> bool:
        """Check if a file matches metadata criteria.
        
        Args:
            file_path: Path to the file to check
            field_name: Metadata field name
            expected_value: Expected field value
            
        Returns:
            bool: True if file matches criteria
        """
        try:
            frontmatter, _ = self.frontmatter_manager.parse_file(file_path)
            
            # Check if field exists and matches expected value
            actual_value = frontmatter.get(field_name)
            if actual_value is None:
                return False
            
            # Convert expected value to appropriate type
            if isinstance(actual_value, bool):
                expected_bool = expected_value.lower() in ('true', '1', 'yes', 'on')
                return actual_value == expected_bool
            elif isinstance(actual_value, (int, float)):
                try:
                    expected_numeric = type(actual_value)(expected_value)
                    return actual_value == expected_numeric
                except ValueError:
                    return False
            else:
                return str(actual_value) == expected_value
                
        except Exception as e:
            self.logger.debug(f"Error checking metadata for {file_path}: {e}")
            return False
    
    def _is_valid_note_file(self, file_path: Path) -> bool:
        """Check if file is a valid note file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if file is a valid note file
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


class RecentNotesUpdater:
    """Recent notes updater for index file modification."""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def update_index_content(self, content: str, notes: List[NoteInfo]) -> str:
        """Update index file content with recent notes.
        
        Args:
            content: Original content of the index file
            notes: List of recent notes
            
        Returns:
            str: Updated content with recent notes inserted
        """
        start_marker = self.config.recent_notes_start_marker
        end_marker = self.config.recent_notes_end_marker
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            self.logger.error(
                f"Markers not found. Please add {start_marker} "
                f"and {end_marker} to the index file."
            )
            return content
        
        # Ensure end marker is after start marker
        if end_idx <= start_idx:
            self.logger.error("End marker found before start marker")
            return content
        
        # Generate new notes section
        new_section = self._generate_notes_section(notes)
        
        # Replace content between markers
        start_pos = start_idx + len(start_marker)
        end_pos = end_idx
        
        return (
            content[:start_pos] + 
            '\n' + new_section + '\n' + 
            content[end_pos:]
        )
    
    def _generate_notes_section(self, notes: List[NoteInfo]) -> str:
        """Generate HTML section for recent notes.
        
        Args:
            notes: List of recent notes
            
        Returns:
            str: HTML content for recent notes
        """
        if not notes:
            return '<p><em>No recent notes found.</em></p>'
        
        lines = []
        lines.append('<div class="recent-notes">')
        lines.append('<h3>Recent Notes</h3>')
        lines.append('<ul>')
        
        for note in notes:
            # Skip the index page itself
            if 'index.md' in note.file_path.name:
                continue
                
            lines.append(f'<li>')
            lines.append(f'  <a href="{note.relative_url}">{note.title}</a>')
            lines.append(f'  <small class="note-date">({note.modified_date})</small>')
            lines.append(f'</li>')
        
        lines.append('</ul>')
        lines.append('</div>')
        
        return '\n'.join(lines)


class RecentNotesManager:
    """Main recent notes management class.
    
    Coordinates scanning, processing, and updating of recent notes.
    """
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.scanner = RecentNotesScanner(config, logger)
        self.updater = RecentNotesUpdater(config, logger)
        self.note_processor = None  # Will be initialized when needed
    
    def get_recent_notes(self) -> List[NoteInfo]:
        """Get recent notes based on configuration.
        
        Returns:
            List[NoteInfo]: List of recent notes information
        """
        try:
            # Scan for note files
            note_files = self.scanner.scan_recent_notes()
            
            if not note_files:
                self.logger.warning("No note files found for recent notes")
                return []
            
            # Process note files to get NoteInfo objects
            if self.note_processor is None:
                from mkdocs_note.utils.notes.note_manager import NoteProcessor
                self.note_processor = NoteProcessor(self.config, self.logger)
            
            notes = []
            for file_path in note_files:
                note_info = self.note_processor.process_note(file_path)
                if note_info:
                    notes.append(note_info)
            
            # Sort by modified time and limit count
            notes.sort(key=lambda n: n.modified_time, reverse=True)
            recent_notes = notes[:self.config.recent_notes_max_count]
            
            self.logger.info(f"Found {len(recent_notes)} recent notes")
            return recent_notes
            
        except Exception as e:
            self.logger.error(f"Error getting recent notes: {e}")
            return []
    
    def update_index_file(self, notes: List[NoteInfo]) -> bool:
        """Update the index file with recent notes.
        
        Args:
            notes: List of recent notes to insert
            
        Returns:
            bool: True if update was successful
        """
        try:
            index_file = Path(self.config.recent_notes_index_file)
            
            if not index_file.exists():
                self.logger.warning(f"Index file does not exist: {index_file}")
                return False
            
            # Read current content
            content = index_file.read_text(encoding='utf-8')
            
            # Update content with recent notes
            updated_content = self.updater.update_index_content(content, notes)
            
            if updated_content != content:
                # Write updated content
                index_file.write_text(updated_content, encoding='utf-8')
                self.logger.info(f"Updated index file: {index_file}")
                return True
            else:
                self.logger.debug("Index file content unchanged")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating index file: {e}")
            return False
    
    def process_recent_notes(self) -> bool:
        """Complete recent notes processing pipeline.
        
        Returns:
            bool: True if processing was successful
        """
        try:
            # Get recent notes
            notes = self.get_recent_notes()
            
            if not notes:
                self.logger.info("No recent notes to process")
                return True
            
            # Update index file
            success = self.update_index_file(notes)
            
            if success:
                self.logger.info(f"Successfully processed {len(notes)} recent notes")
            else:
                self.logger.error("Failed to update index file")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in recent notes processing pipeline: {e}")
            return False
