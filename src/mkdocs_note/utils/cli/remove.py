"""
Note remover for deleting notes and their associated assets.

Refactored to use MkdocsNoteConfig and OperationResult.
"""

from pathlib import Path
from typing import Optional

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils.cli.common import (
	OperationResult,
	get_asset_directory,
	cleanup_empty_directories,
	get_logger,
)


logger = get_logger(__name__)


class NoteRemover:
	"""Note remover for deleting note files and their asset directories."""

	def __init__(self, config: MkdocsNoteConfig):
		"""Initialize note remover.

		Args:
		    config: Plugin configuration instance
		"""
		self.config = config

	def remove_note(
		self, note_path: Path, remove_assets: bool = True
	) -> OperationResult:
		"""Remove a note file and optionally its asset directory.

		Args:
		    note_path: The path of the note file to remove
		    remove_assets: Whether to also remove the asset directory

		Returns:
		    OperationResult: Result with success status and message
		"""
		try:
			# Validate the note file exists
			if not note_path.exists():
				return OperationResult(
					success=False, message=f"Note file does not exist: {note_path}"
				)

			if not note_path.is_file():
				return OperationResult(
					success=False, message=f"Path is not a file: {note_path}"
				)

			# Get the asset directory before removing the note
			asset_dir: Optional[Path] = None
			if remove_assets:
				asset_dir = get_asset_directory(note_path)

			# Remove the note file
			logger.info(f"Removing note file: {note_path}")
			note_path.unlink()
			logger.info(f"Successfully removed note file: {note_path}")

			removed_assets = False
			# Remove the asset directory if requested and exists
			if remove_assets and asset_dir and asset_dir.exists():
				logger.info(f"Removing asset directory: {asset_dir}")
				import shutil

				shutil.rmtree(asset_dir)
				logger.info(f"Successfully removed asset directory: {asset_dir}")
				removed_assets = True

				# Clean up empty parent directories
				notes_root = (
					Path(self.config.notes_root)
					if isinstance(self.config.notes_root, str)
					else self.config.notes_root
				)
				cleanup_empty_directories(asset_dir.parent, notes_root)

			return OperationResult(
				success=True,
				message=f"Note removed successfully: {note_path}",
				data={
					"note_path": note_path,
					"asset_dir": asset_dir,
					"removed_assets": removed_assets,
				},
			)

		except Exception as e:
			error_msg = f"Failed to remove note: {e}"
			logger.error(error_msg)
			return OperationResult(success=False, message=error_msg)

	def remove_multiple_notes(
		self, note_paths: list[Path], remove_assets: bool = True
	) -> OperationResult:
		"""Remove multiple note files and their asset directories.

		Args:
		    note_paths: List of note file paths to remove
		    remove_assets: Whether to also remove asset directories

		Returns:
		    OperationResult: Result with counts of successful/failed removals
		"""
		success_count = 0
		failed_count = 0
		failed_paths = []

		for note_path in note_paths:
			result = self.remove_note(note_path, remove_assets)
			if result.success:
				success_count += 1
			else:
				failed_count += 1
				failed_paths.append(note_path)

		if failed_count == 0:
			return OperationResult(
				success=True,
				message=f"Successfully removed {success_count} note(s)",
				data={"success_count": success_count, "failed_count": 0},
			)
		else:
			return OperationResult(
				success=False,
				message=f"Removed {success_count} note(s), failed {failed_count}",
				data={
					"success_count": success_count,
					"failed_count": failed_count,
					"failed_paths": failed_paths,
				},
			)
