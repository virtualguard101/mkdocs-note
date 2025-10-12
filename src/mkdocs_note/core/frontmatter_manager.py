"""
Frontmatter management system with metadata registration.

This module provides a flexible and extensible frontmatter management system
that allows dynamic registration of metadata fields without modifying core code.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime

import yaml


# ============================================================================
# Metadata Field Definition
# ============================================================================

@dataclass
class MetadataField:
    """Definition of a metadata field.
    
    Attributes:
        name: Field name
        field_type: Python type of the field (str, bool, int, list, etc.)
        default: Default value for the field
        required: Whether the field is required
        validator: Optional validation function
        description: Field description for documentation
    """
    name: str
    field_type: Type
    default: Any = None
    required: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    
    def validate(self, value: Any) -> bool:
        """Validate field value.
        
        Args:
            value: The value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check type
        if value is not None and not isinstance(value, self.field_type):
            return False
        
        # Check required
        if self.required and value is None:
            return False
        
        # Custom validator
        if self.validator and value is not None:
            return self.validator(value)
        
        return True


# ============================================================================
# Metadata Registry
# ============================================================================

class MetadataRegistry:
    """Registry for metadata fields.
    
    Provides a centralized place to register and manage metadata fields.
    This design allows extending metadata without modifying core code.
    """
    
    def __init__(self):
        self._fields: Dict[str, MetadataField] = {}
        self._register_default_fields()
    
    def _register_default_fields(self):
        """Register default metadata fields."""
        # Date field
        self.register(MetadataField(
            name="date",
            field_type=str,
            default=None,
            required=False,
            description="Creation or publication date"
        ))
        
        # Permalink field
        self.register(MetadataField(
            name="permalink",
            field_type=str,
            default=None,
            required=False,
            description="Custom permalink for the note"
        ))
        
        # Publish field
        self.register(MetadataField(
            name="publish",
            field_type=bool,
            default=True,
            required=False,
            description="Whether the note should be published"
        ))
    
    def register(self, field: MetadataField) -> None:
        """Register a new metadata field.
        
        Args:
            field: The metadata field to register
            
        Raises:
            ValueError: If field with same name already exists
        """
        if field.name in self._fields:
            raise ValueError(f"Metadata field '{field.name}' already registered")
        
        self._fields[field.name] = field
    
    def unregister(self, field_name: str) -> None:
        """Unregister a metadata field.
        
        Args:
            field_name: Name of the field to unregister
        """
        if field_name in self._fields:
            del self._fields[field_name]
    
    def get_field(self, field_name: str) -> Optional[MetadataField]:
        """Get a registered field by name.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Optional[MetadataField]: The field if found, None otherwise
        """
        return self._fields.get(field_name)
    
    def get_all_fields(self) -> Dict[str, MetadataField]:
        """Get all registered fields.
        
        Returns:
            Dict[str, MetadataField]: Dictionary of all fields
        """
        return self._fields.copy()
    
    def get_default_values(self) -> Dict[str, Any]:
        """Get default values for all fields.
        
        Returns:
            Dict[str, Any]: Dictionary of field names to default values
        """
        return {name: field.default for name, field in self._fields.items()}
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate metadata data against registered fields.
        
        Args:
            data: The metadata dictionary to validate
            
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Check all data fields against registered fields
        for field_name, value in data.items():
            field = self.get_field(field_name)
            if field is None:
                # Unknown field - could be a warning, but we'll allow it for flexibility
                continue
            
            if not field.validate(value):
                errors.append(f"Invalid value for field '{field_name}': {value}")
        
        # Check required fields
        for field_name, field in self._fields.items():
            if field.required and field_name not in data:
                errors.append(f"Required field '{field_name}' is missing")
        
        return len(errors) == 0, errors


# Global registry instance
_global_registry = MetadataRegistry()


def get_registry() -> MetadataRegistry:
    """Get the global metadata registry.
    
    Returns:
        MetadataRegistry: The global registry instance
    """
    return _global_registry


def register_field(field: MetadataField) -> None:
    """Register a metadata field to the global registry.
    
    This is a convenience function for registering fields.
    
    Args:
        field: The metadata field to register
    """
    _global_registry.register(field)


# ============================================================================
# Frontmatter Parser
# ============================================================================

class FrontmatterParser:
    """Parser for YAML frontmatter in markdown files.
    
    Handles parsing and generating frontmatter sections in markdown files.
    """
    
    # Regex pattern for frontmatter
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.DOTALL | re.MULTILINE
    )
    
    def __init__(self, registry: Optional[MetadataRegistry] = None):
        """Initialize parser.
        
        Args:
            registry: Metadata registry to use. If None, uses global registry.
        """
        self.registry = registry or get_registry()
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse markdown content and extract frontmatter.
        
        Args:
            content: The markdown content to parse
            
        Returns:
            tuple[Dict[str, Any], str]: (frontmatter_dict, body_content)
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        
        if match:
            # Extract frontmatter YAML
            yaml_content = match.group(1)
            body = content[match.end():]
            
            try:
                frontmatter = yaml.safe_load(yaml_content)
                if frontmatter is None:
                    frontmatter = {}
                elif not isinstance(frontmatter, dict):
                    # Invalid frontmatter format
                    return {}, content
                
                return frontmatter, body
            except yaml.YAMLError:
                # Invalid YAML, treat as no frontmatter
                return {}, content
        else:
            # No frontmatter found
            return {}, content
    
    def parse_file(self, file_path: Path) -> tuple[Dict[str, Any], str]:
        """Parse markdown file and extract frontmatter.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            tuple[Dict[str, Any], str]: (frontmatter_dict, body_content)
        """
        content = file_path.read_text(encoding='utf-8')
        return self.parse(content)
    
    def generate(self, frontmatter: Dict[str, Any], body: str) -> str:
        """Generate markdown content with frontmatter.
        
        Args:
            frontmatter: Dictionary of frontmatter data
            body: The body content
            
        Returns:
            str: Complete markdown content with frontmatter
        """
        if not frontmatter:
            return body
        
        # Generate YAML
        yaml_content = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
        
        return f"---\n{yaml_content}---\n\n{body}"
    
    def update_frontmatter(
        self,
        content: str,
        updates: Dict[str, Any],
        merge: bool = True
    ) -> str:
        """Update frontmatter in existing content.
        
        Args:
            content: The original markdown content
            updates: Dictionary of fields to update
            merge: If True, merge with existing frontmatter. If False, replace.
            
        Returns:
            str: Updated markdown content
        """
        existing_fm, body = self.parse(content)
        
        if merge:
            # Merge updates into existing frontmatter
            existing_fm.update(updates)
            new_fm = existing_fm
        else:
            # Replace with new frontmatter
            new_fm = updates
        
        return self.generate(new_fm, body)
    
    def update_file_frontmatter(
        self,
        file_path: Path,
        updates: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """Update frontmatter in a file.
        
        Args:
            file_path: Path to the markdown file
            updates: Dictionary of fields to update
            merge: If True, merge with existing frontmatter. If False, replace.
        """
        content = file_path.read_text(encoding='utf-8')
        updated_content = self.update_frontmatter(content, updates, merge)
        file_path.write_text(updated_content, encoding='utf-8')
    
    def remove_frontmatter(self, content: str) -> str:
        """Remove frontmatter from content.
        
        Args:
            content: The markdown content
            
        Returns:
            str: Content without frontmatter
        """
        _, body = self.parse(content)
        return body
    
    def validate_content(self, content: str) -> tuple[bool, List[str]]:
        """Validate frontmatter in content.
        
        Args:
            content: The markdown content
            
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        frontmatter, _ = self.parse(content)
        return self.registry.validate_data(frontmatter)


# ============================================================================
# Frontmatter Manager (Facade)
# ============================================================================

class FrontmatterManager:
    """High-level frontmatter management interface.
    
    This class provides a simplified facade for common frontmatter operations,
    combining the registry and parser functionalities.
    """
    
    def __init__(self, registry: Optional[MetadataRegistry] = None):
        """Initialize manager.
        
        Args:
            registry: Metadata registry to use. If None, uses global registry.
        """
        self.registry = registry or get_registry()
        self.parser = FrontmatterParser(self.registry)
    
    def register_field(self, field: MetadataField) -> None:
        """Register a new metadata field.
        
        Args:
            field: The metadata field to register
        """
        self.registry.register(field)
    
    def create_default_frontmatter(
        self,
        custom_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create frontmatter with default values.
        
        Args:
            custom_values: Optional custom values to override defaults
            
        Returns:
            Dict[str, Any]: Frontmatter dictionary with default values
        """
        frontmatter = self.registry.get_default_values()
        
        if custom_values:
            frontmatter.update(custom_values)
        
        return frontmatter
    
    def parse_file(self, file_path: Path) -> tuple[Dict[str, Any], str]:
        """Parse markdown file and extract frontmatter.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            tuple[Dict[str, Any], str]: (frontmatter_dict, body_content)
        """
        return self.parser.parse_file(file_path)
    
    def create_note_content(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        validate: bool = True
    ) -> tuple[str, List[str]]:
        """Create note content with frontmatter.
        
        Args:
            frontmatter: Frontmatter dictionary
            body: Note body content
            validate: Whether to validate frontmatter
            
        Returns:
            tuple[str, List[str]]: (content, validation_errors)
        """
        errors = []
        
        if validate:
            is_valid, errors = self.registry.validate_data(frontmatter)
            if not is_valid:
                return "", errors
        
        content = self.parser.generate(frontmatter, body)
        return content, errors
    
    def update_note_frontmatter(
        self,
        file_path: Path,
        updates: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """Update frontmatter in a note file.
        
        Args:
            file_path: Path to the note file
            updates: Dictionary of fields to update
            merge: If True, merge with existing frontmatter. If False, replace.
        """
        self.parser.update_file_frontmatter(file_path, updates, merge)
    
    def get_field_info(self, field_name: str) -> Optional[MetadataField]:
        """Get information about a registered field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Optional[MetadataField]: Field information if found
        """
        return self.registry.get_field(field_name)
    
    def list_all_fields(self) -> Dict[str, MetadataField]:
        """List all registered metadata fields.
        
        Returns:
            Dict[str, MetadataField]: Dictionary of all fields
        """
        return self.registry.get_all_fields()

