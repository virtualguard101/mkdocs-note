"""
Note creator for creating new note files with proper asset structure.

Refactored to use MkdocsNoteConfig and simplified validation logic.
"""

import re
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone, timedelta

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils.cli.common import (
	OperationResult,
	get_asset_directory,
	is_supported_note,
	is_excluded_name,
	ensure_parent_directory,
	get_logger,
)


logger = get_logger(__name__)


class NoteCreator:
	"""Note creator for creating new note files with asset management."""

	def __init__(self, config: MkdocsNoteConfig):
		"""Initialize note creator.

		Args:
		    config: Plugin configuration instance
		"""
		self.config = config
		self._timezone = self._parse_timezone(config.timestamp_zone)

	def _parse_timezone(self, timezone_str: str) -> timezone:
		"""Parse timezone string to timezone object.

		Args:
		    timezone_str: Timezone string in format 'UTC+X' or 'UTC-X'

		Returns:
		    timezone: The timezone object
		"""
		try:
			# Match pattern like 'UTC+8', 'UTC-5', 'UTC+0'
			match = re.match(r"UTC([+-])(\d+(?:\.\d+)?)", timezone_str)
			if match:
				sign = match.group(1)
				hours = float(match.group(2))
				offset_hours = hours if sign == "+" else -hours
				return timezone(timedelta(hours=offset_hours))
			else:
				logger.warning(
					f"Invalid timezone format: {timezone_str}, using UTC+0"
				)
				return timezone.utc
		except Exception as e:
			logger.warning(f"Error parsing timezone {timezone_str}: {e}, using UTC+0")
			return timezone.utc

	def create_new_note(
		self, file_path: Path, template_path: Optional[Path] = None
	) -> OperationResult:
		"""Create a new note file with proper asset structure.

		Args:
		    file_path: The path where the new note should be created
		    template_path: Path to template file. If None, uses default template.

		Returns:
		    OperationResult: Result with success status and message
		"""
		try:
			logger.debug(f"Creating new note: {file_path}")

			# Validate note creation
			validation_result = self.validate_note_creation(file_path)
			if not validation_result.success:
				return validation_result

			# Ensure parent directory exists
			ensure_parent_directory(file_path)

			# Generate note content
			note_content = self._generate_note_content(file_path, template_path)

			# Create the note file
			file_path.write_text(note_content, encoding="utf-8")

			# Create corresponding asset directory
			asset_dir = get_asset_directory(file_path)
			asset_dir.mkdir(parents=True, exist_ok=True)

			logger.info(f"Successfully created note: {file_path}")
			logger.debug(f"Asset directory created: {asset_dir}")

			return OperationResult(
				success=True,
				message=f"Note created successfully: {file_path}",
				data={"note_path": file_path, "asset_dir": asset_dir},
			)

		except Exception as e:
			error_msg = f"Failed to create new note: {e}"
			logger.error(error_msg)
			return OperationResult(success=False, message=error_msg)

	def validate_note_creation(self, file_path: Path) -> OperationResult:
		"""Validate if a note can be created at the given path.

		Args:
		    file_path: The path where the note should be created

		Returns:
		    OperationResult: Validation result with success status and message
		"""
		try:
			# Check if file name is in exclude_patterns
			if is_excluded_name(file_path.name, self.config.exclude_patterns):
				return OperationResult(
					success=False,
					message=(
						f"Cannot create note: '{file_path.name}' is in exclude_patterns. "
						f"Files matching exclude_patterns ({', '.join(sorted(self.config.exclude_patterns))}) "
						"are not managed by the plugin. "
						"Please use a different filename or update the exclude_patterns configuration."
					),
				)

			# Check if file already exists
			if file_path.exists():
				return OperationResult(
					success=False, message=f"File already exists: {file_path}"
				)

			# Check file extension
			if not is_supported_note(file_path, self.config.supported_extensions):
				supported = ", ".join(self.config.supported_extensions)
				return OperationResult(
					success=False,
					message=f"Unsupported file extension: {file_path.suffix}. Supported: {supported}",
				)

			# Check if destination is within notes_root
			notes_root = (
				Path(self.config.notes_root)
				if isinstance(self.config.notes_root, str)
				else self.config.notes_root
			)
			try:
				file_path.resolve().relative_to(notes_root.resolve())
			except ValueError:
				return OperationResult(
					success=False,
					message=f"Note path {file_path} is outside notes_root {notes_root}",
				)

			return OperationResult(success=True, message="Validation passed")

		except Exception as e:
			return OperationResult(success=False, message=f"Validation error: {e}")

	def _generate_note_content(
		self, file_path: Path, template_path: Optional[Path] = None
	) -> str:
		"""Generate content for the new note file.

		Args:
		    file_path: The path of the note file
		    template_path: Path to template file

		Returns:
		    str: The generated note content
		"""
		# Determine which template to use
		template_content = self._load_template(template_path)

		# Prepare template variables
		note_name = file_path.stem
		current_date = datetime.now(tz=self._timezone).strftime(
			self.config.output_date_format
		)
		title = note_name.replace("-", " ").replace("_", " ").title()

		# Replace variables in template
		content = template_content.replace("{{title}}", title)
		content = content.replace("{{date}}", current_date)
		content = content.replace("{{note_name}}", note_name)

		return content

	def _load_template(self, template_path: Optional[Path] = None) -> str:
		"""Load template content from file or use default.

		Args:
		    template_path: Optional custom template path

		Returns:
		    str: Template content
		"""
		# Try custom template path first
		if template_path and template_path.exists():
			try:
				return template_path.read_text(encoding="utf-8")
			except Exception as e:
				logger.warning(f"Failed to read custom template {template_path}: {e}")

		# Try default template from config
		default_template_path = Path(self.config.notes_template)
		if default_template_path.exists():
			try:
				return default_template_path.read_text(encoding="utf-8")
			except Exception as e:
				logger.warning(
					f"Failed to read default template {default_template_path}: {e}"
				)

		# Fallback to built-in template
		return self._get_builtin_template()

	def _get_builtin_template(self) -> str:
		"""Get the built-in fallback template.

		Returns:
		    str: Built-in template content with frontmatter
		"""
		return """---
date: {{date}}
title: {{title}}
permalink: 
publish: true
---

# {{title}}

Start writing your note content...
"""
