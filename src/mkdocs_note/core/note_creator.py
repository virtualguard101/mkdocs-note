"""
Note creator for creating new note files with proper asset structure.
"""

import re
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.note_initializer import NoteInitializer
from mkdocs_note.core.frontmatter_manager import FrontmatterManager


class NoteCreator:
    """Note creator for creating new note files with asset management."""
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.initializer = NoteInitializer(config, logger)
        self.frontmatter_manager = FrontmatterManager()
        self._timezone = self._parse_timezone(config.timestamp_zone)
    
    def _parse_timezone(self, timezone_str: str) -> timezone:
        """Parse timezone string to timezone object.
        
        Args:
            timezone_str (str): Timezone string in format 'UTC+X' or 'UTC-X'
            
        Returns:
            timezone: The timezone object
        """
        try:
            # Match pattern like 'UTC+8', 'UTC-5', 'UTC+0'
            match = re.match(r'UTC([+-])(\d+(?:\.\d+)?)', timezone_str)
            if match:
                sign = match.group(1)
                hours = float(match.group(2))
                offset_hours = hours if sign == '+' else -hours
                return timezone(timedelta(hours=offset_hours))
            else:
                self.logger.warning(f"Invalid timezone format: {timezone_str}, using UTC+0")
                return timezone.utc
        except Exception as e:
            self.logger.warning(f"Error parsing timezone {timezone_str}: {e}, using UTC+0")
            return timezone.utc
    
    def create_new_note(self, file_path: Path, template_path: Optional[Path] = None) -> int:
        """Create a new note file with proper asset structure.
        
        Args:
            file_path (Path): The path where the new note should be created
            template_path (Optional[Path]): Path to template file. If None, uses default template.
        
        Returns:
            int: 0 if successful, 1 if failed
        """
        try:
            self.logger.debug(f"Creating new note: {file_path}")
            
            # Validate asset tree compliance first
            # Use configured notes_dir instead of file_path.parent to ensure consistent validation
            notes_dir = Path(self.config.notes_dir)
            is_compliant, error_messages = self.initializer.validate_asset_tree_compliance(notes_dir)
            
            if not is_compliant:
                self.logger.error("Asset tree structure is not compliant with plugin design")
                for error in error_messages:
                    self.logger.error(f"  - {error}")
                self.logger.error("Please run 'mkdocs note init' to initialize the directory structure")
                return 1
            
            # Ensure the notes directory exists
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if file_path.exists():
                self.logger.error(f"Note file already exists: {file_path}")
                return 1
            
            # Create the note file
            note_content = self._generate_note_content(file_path, template_path)
            file_path.write_text(note_content, encoding='utf-8')
            
            # Create corresponding asset directory
            self._create_asset_directory(file_path)
            
            self.logger.debug(f"Successfully created note: {file_path}")
            self.logger.debug(f"Asset directory created: {self._get_asset_directory(file_path)}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to create new note: {e}")
            return 1
    
    def _generate_note_content(self, file_path: Path, template_path: Optional[Path] = None) -> str:
        """Generate content for the new note file.
        
        This method generates note content with frontmatter. Template variables
        are replaced only in the frontmatter section, keeping the body clean.
        
        Args:
            file_path (Path): The path of the note file
            template_path (Optional[Path]): Path to template file
            
        Returns:
            str: The generated note content with frontmatter
        """
        # Determine which template to use
        actual_template_path = None
        if template_path and template_path.exists():
            actual_template_path = template_path
        else:
            default_template_path = self._get_default_template_path()
            if default_template_path.exists():
                actual_template_path = default_template_path
        
        # If no template file exists, use fallback template
        if not actual_template_path:
            template_content = self._get_default_template()
            return self._generate_legacy_template_content(file_path, template_content)
        
        # Parse template to extract frontmatter and body
        template_fm, template_body = self.frontmatter_manager.parse_file(actual_template_path)
        
        # If template has no frontmatter, handle old-style template
        if not template_fm:
            template_content = actual_template_path.read_text(encoding='utf-8')
            return self._generate_legacy_template_content(file_path, template_content)
        
        # Prepare template variables
        note_name = file_path.stem
        current_date = datetime.now(tz=self._timezone).strftime(self.config.output_date_format)
        title = note_name.replace('-', ' ').replace('_', ' ').title()
        
        template_vars = {
            'title': title,
            'date': current_date,
            'note_name': note_name
        }
        
        # Replace variables in frontmatter
        processed_fm = self._replace_variables_in_dict(template_fm, template_vars)
        
        # Replace variables in body (for compatibility)
        processed_body = self._replace_variables_in_text(template_body, template_vars)
        
        # Generate final content
        content, errors = self.frontmatter_manager.create_note_content(
            processed_fm, 
            processed_body, 
            validate=True
        )
        
        if errors:
            self.logger.warning(f"Frontmatter validation warnings: {', '.join(errors)}")
        
        return content
    
    def _replace_variables_in_dict(
        self, 
        data: Dict[str, Any], 
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """Replace template variables in dictionary values.
        
        Args:
            data: Dictionary to process
            variables: Variable replacements
            
        Returns:
            Dict[str, Any]: Dictionary with replaced values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._replace_variables_in_text(value, variables)
            elif isinstance(value, dict):
                result[key] = self._replace_variables_in_dict(value, variables)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_variables_in_text(item, variables) 
                    if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def _replace_variables_in_text(self, text: str, variables: Dict[str, str]) -> str:
        """Replace template variables in text.
        
        Args:
            text: Text to process
            variables: Variable replacements
            
        Returns:
            str: Text with replaced variables
        """
        result = text
        for var_name, var_value in variables.items():
            result = result.replace(f'{{{{{var_name}}}}}', var_value)
        return result
    
    def _generate_legacy_template_content(self, file_path: Path, template_content: str) -> str:
        """Generate content for old-style templates without frontmatter.
        
        Args:
            file_path: Path to the note file
            template_content: Template content
            
        Returns:
            str: Generated content
        """
        note_name = file_path.stem
        current_date = datetime.now(tz=self._timezone).strftime(self.config.output_date_format)
        
        content = template_content.replace('{{title}}', note_name.replace('-', ' ').replace('_', ' ').title())
        content = content.replace('{{date}}', current_date)
        content = content.replace('{{note_name}}', note_name)
        
        return content
    
    def _get_default_template_path(self) -> Path:
        """Get the path to the default template.
        
        Returns:
            Path: Path to the default template
        """
        return Path(self.config.notes_template)
    
    def _get_default_template(self) -> str:
        """Get the default note template from config.
        
        Returns:
            str: The default template content
        """
        template_path = Path(self.config.notes_template)
        
        if template_path.exists():
            try:
                return template_path.read_text(encoding='utf-8')
            except Exception as e:
                self.logger.warning(f"Failed to read template file {template_path}: {e}")
        
        # Fallback template if config template doesn't exist
        return "# {{title}}\n\nCreated on {{date}}\n\nNote: {{note_name}}"
    
    def _create_asset_directory(self, note_file_path: Path) -> None:
        """Create asset directory for the note.
        
        Args:
            note_file_path (Path): The path of the note file
        """
        asset_dir = self._get_asset_directory(note_file_path)
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        ## Create empty README file in the asset directory
        # readme_file = asset_dir / "README.md"
        # if not readme_file.exists():
        #     readme_file.write_text("", encoding='utf-8')
    
    def _get_asset_directory(self, note_file_path: Path) -> Path:
        """Get the asset directory path for a note file.
        
        This method calculates the asset directory using the note's relative path
        from the notes directory, ensuring that notes in different subdirectories
        with the same name don't conflict.
        
        Args:
            note_file_path (Path): The path of the note file
            
        Returns:
            Path: The asset directory path
            
        Examples:
            For note: docs/notes/python/intro.md
            Returns: docs/notes/assets/python/intro/
            
            For note: docs/notes/javascript/intro.md
            Returns: docs/notes/assets/javascript/intro/
        """
        from mkdocs_note.core.assets_manager import get_note_relative_path
        
        notes_dir = Path(self.config.notes_dir)
        note_relative_path = get_note_relative_path(note_file_path, notes_dir)
        
        assets_dir = Path(self.config.assets_dir)
        return assets_dir / note_relative_path
    
    def validate_note_creation(self, file_path: Path) -> Tuple[bool, str]:
        """Validate if a note can be created at the given path.
        
        Args:
            file_path (Path): The path where the note should be created
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check if file already exists
            if file_path.exists():
                return False, f"File already exists: {file_path}"
            
            # Check if parent directory exists
            parent_dir = file_path.parent
            if not parent_dir.exists():
                return False, f"Parent directory does not exist: {parent_dir}"
            
            # Validate asset tree compliance
            # Use configured notes_dir instead of file_path.parent to ensure consistent validation
            notes_dir = Path(self.config.notes_dir)
            is_compliant, error_messages = self.initializer.validate_asset_tree_compliance(notes_dir)
            
            if not is_compliant:
                error_msg = "Asset tree structure is not compliant. " + "; ".join(error_messages)
                return False, error_msg
            
            # Check file extension
            if file_path.suffix.lower() not in self.config.supported_extensions:
                return False, f"Unsupported file extension: {file_path.suffix}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {e}"
