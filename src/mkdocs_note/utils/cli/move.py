"""
Note mover for relocating or renaming notes with their assets.

Refactored to use MkdocsNoteConfig and OperationResult.
"""

import shutil
from pathlib import Path

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils.cli.common import (
	OperationResult,
	get_asset_directory,
	is_excluded_name,
	ensure_parent_directory,
	cleanup_empty_directories,
	get_logger,
)


logger = get_logger(__name__)


class NoteMover:
	"""Mover for relocating or renaming notes with their assets."""

	def __init__(self, config: MkdocsNoteConfig):
		"""Initialize note mover.

		Args:
		    config: Plugin configuration instance
		"""
		self.config = config

	def move_note_or_directory(
		self, source_path: Path, dest_path: Path, move_assets: bool = True
	) -> OperationResult:
		"""Move a note file or directory (with all notes inside) and their assets.

		This method mimics the behavior of shell 'mv' command:
		- If destination doesn't exist, rename source to destination
		- If destination exists and is a directory, move source into destination

		Args:
		    source_path: The current path (file or directory)
		    dest_path: The destination path
		    move_assets: Whether to also move the asset directories

		Returns:
		    OperationResult: Result with success status and message
		"""
		try:
			# Adjust destination path if it exists and is a directory
			if dest_path.exists() and dest_path.is_dir():
				dest_path = dest_path / source_path.name
				logger.info(f"Destination is a directory, moving to: {dest_path}")

			# Check if adjusted destination exists
			if dest_path.exists():
				return OperationResult(
					success=False, message=f"Destination already exists: {dest_path}"
				)

			# Check if source is a directory
			if source_path.is_dir():
				return self._move_directory(source_path, dest_path, move_assets)
			else:
				return self._move_note(source_path, dest_path, move_assets)

		except Exception as e:
			error_msg = f"Failed to move: {e}"
			logger.error(error_msg)
			return OperationResult(success=False, message=error_msg)

	def _move_directory(
		self, source_dir: Path, dest_dir: Path, move_assets: bool = True
	) -> OperationResult:
		"""Move a directory with all notes and their assets.

		Args:
		    source_dir: The current directory path
		    dest_dir: The destination directory path
		    move_assets: Whether to also move the asset directories

		Returns:
		    OperationResult: Result with success status and message
		"""
		try:
			# Validate source directory exists
			if not source_dir.exists():
				return OperationResult(
					success=False,
					message=f"Source directory does not exist: {source_dir}",
				)

			if not source_dir.is_dir():
				return OperationResult(
					success=False,
					message=f"Source path is not a directory: {source_dir}",
				)

			# Validate destination doesn't already exist
			if dest_dir.exists():
				return OperationResult(
					success=False, message=f"Destination already exists: {dest_dir}"
				)

			# Get all note files in the source directory
			source_dir_resolved = source_dir.resolve()
			all_note_files = []

			for file_path in source_dir_resolved.rglob("*"):
				if (
					file_path.is_file()
					and file_path.suffix.lower() in self.config.supported_extensions
				):
					# Check if it's not in excluded patterns
					if file_path.name not in self.config.exclude_patterns:
						all_note_files.append(file_path)

			if not all_note_files:
				logger.warning(f"No note files found in directory: {source_dir}")

			logger.info(f"Found {len(all_note_files)} note file(s) to move")

			# Create destination directory
			dest_dir.mkdir(parents=True, exist_ok=True)

			# Move each note file
			failed_count = 0
			for note_file in all_note_files:
				# Calculate relative path from source directory
				try:
					rel_path = note_file.relative_to(source_dir_resolved)
				except ValueError:
					logger.error(f"Could not calculate relative path for {note_file}")
					failed_count += 1
					continue

				# Calculate destination path
				dest_note_path = dest_dir / rel_path

				# Move the note
				result = self._move_note(note_file, dest_note_path, move_assets)
				if not result.success:
					failed_count += 1

			# Move any remaining non-note files
			if source_dir_resolved.exists():
				for item in source_dir_resolved.iterdir():
					if item.is_file() and item not in all_note_files:
						dest_item = dest_dir / item.name
						if not dest_item.exists():
							shutil.move(str(item), str(dest_item))

				# Remove the source directory if empty
				try:
					if not any(source_dir_resolved.rglob("*")):
						shutil.rmtree(source_dir_resolved)
				except Exception as e:
					logger.debug(f"Could not remove source directory: {e}")

			if failed_count > 0:
				return OperationResult(
					success=False,
					message=f"Failed to move {failed_count} note file(s)",
					data={"failed_count": failed_count},
				)

			return OperationResult(
				success=True,
				message=f"Successfully moved directory: {source_dir} → {dest_dir}",
				data={"source": source_dir, "destination": dest_dir},
			)

		except Exception as e:
			error_msg = f"Failed to move directory: {e}"
		logger.error(error_msg)
		return OperationResult(success=False, message=error_msg)

	def _move_note(
		self, source_path: Path, dest_path: Path, move_assets: bool = True
	) -> OperationResult:
		"""Move or rename a note file and its asset directory.

		Args:
		    source_path: The current path of the note file
		    dest_path: The destination path for the note file
		    move_assets: Whether to also move the asset directory

		Returns:
		    OperationResult: Result with success status and message
		"""
		try:
			# Validate source file exists
			if not source_path.exists():
				return OperationResult(
					success=False,
					message=f"Source note file does not exist: {source_path}",
				)

			if not source_path.is_file():
				return OperationResult(
					success=False, message=f"Source path is not a file: {source_path}"
				)

			# Validate destination doesn't already exist
			if dest_path.exists():
				return OperationResult(
					success=False, message=f"Destination already exists: {dest_path}"
				)

			# Check if destination filename is in exclude_patterns
			if is_excluded_name(dest_path.name, self.config.exclude_patterns):
				return OperationResult(
					success=False,
					message=(
						f"Cannot move note to excluded filename: {dest_path.name}. "
						f"Files matching exclude_patterns ({', '.join(sorted(self.config.exclude_patterns))}) "
						"are not managed by the plugin."
					),
				)

			# Ensure destination parent directory exists
			ensure_parent_directory(dest_path)

			# Get asset directories before moving
			source_asset_dir = None
			dest_asset_dir = None
			if move_assets:
				source_asset_dir = get_asset_directory(source_path)
				dest_asset_dir = get_asset_directory(dest_path)

			# Move the note file
			logger.info(f"Moving note file: {source_path} → {dest_path}")
			shutil.move(str(source_path), str(dest_path))
			logger.info("Successfully moved note file")

			# Move the asset directory if requested and exists
			if move_assets and source_asset_dir and source_asset_dir.exists():
				# Ensure destination asset parent directory exists
				ensure_parent_directory(dest_asset_dir / "dummy")

				logger.info(
					f"Moving asset directory: {source_asset_dir} → {dest_asset_dir}"
				)
				shutil.move(str(source_asset_dir), str(dest_asset_dir))
				logger.info("Successfully moved asset directory")

				# Clean up empty parent directories in source
				notes_root = (
					Path(self.config.notes_root)
					if isinstance(self.config.notes_root, str)
					else self.config.notes_root
				)
				cleanup_empty_directories(source_asset_dir.parent, notes_root)

			return OperationResult(
				success=True,
				message=f"Note moved successfully: {source_path} → {dest_path}",
				data={
					"source": source_path,
					"destination": dest_path,
					"asset_moved": move_assets
					and source_asset_dir
					and source_asset_dir.exists(),
				},
			)

		except Exception as e:
			error_msg = f"Failed to move note: {e}"
			logger.error(error_msg)

			# Try to rollback if possible
			try:
				if dest_path.exists():
					logger.info("Attempting to rollback changes...")
					if not source_path.exists():
						shutil.move(str(dest_path), str(source_path))
					if move_assets and dest_asset_dir and dest_asset_dir.exists():
						if source_asset_dir and not source_asset_dir.exists():
							shutil.move(str(dest_asset_dir), str(source_asset_dir))
					logger.info("Rollback completed")
			except Exception as rollback_error:
				logger.error(f"Rollback failed: {rollback_error}")

			return OperationResult(success=False, message=error_msg)
