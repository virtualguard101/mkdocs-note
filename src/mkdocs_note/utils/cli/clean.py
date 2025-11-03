"""
Note cleaner for managing orphaned assets.

Refactored to use MkdocsNoteConfig and OperationResult.
"""

import shutil
from pathlib import Path

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils.cli.common import (
	OperationResult,
	get_asset_directory,
	cleanup_empty_directories,
	get_logger,
)


logger = get_logger(__name__)


class NoteCleaner:
	"""Cleaner for managing orphaned assets."""

	def __init__(self, config: MkdocsNoteConfig):
		"""Initialize note cleaner.

		Args:
		    config: Plugin configuration instance
		"""
		self.config = config

	def find_orphaned_assets(self) -> list[Path]:
		"""Find asset directories that don't have corresponding note files.

		Returns:
		    list[Path]: List of orphaned asset directory paths
		"""
		notes_root = (
			Path(self.config.notes_root)
			if isinstance(self.config.notes_root, str)
			else self.config.notes_root
		)

		# Get all note files by scanning the notes_root
		note_files = self._scan_note_files(notes_root)

		# Build a set of expected asset directory paths
		expected_asset_dirs: set[str] = set()
		for note_file in note_files:
			# Calculate asset directory based on note file location
			asset_dir_path = get_asset_directory(note_file)
			expected_asset_dirs.add(str(asset_dir_path.resolve()))

		# Find all actual asset directories by scanning notes_root
		orphaned_dirs: list[Path] = []

		try:
			# Scan for 'assets' directories within notes_root
			for assets_subdir in notes_root.rglob("assets"):
				if not assets_subdir.is_dir():
					continue

				# Check all subdirectories within each assets directory
				for item in assets_subdir.iterdir():
					if item.is_dir():
						# Check if this is a leaf directory (no subdirectories)
						has_subdirs = any(child.is_dir() for child in item.iterdir())

						if not has_subdirs:
							# This is a leaf directory, check if it corresponds to a note
							item_resolved = str(item.resolve())
							if item_resolved not in expected_asset_dirs:
								orphaned_dirs.append(item)
		except Exception as e:
			logger.error(f"Error scanning asset directories: {e}")

		return orphaned_dirs

	def _scan_note_files(self, root_dir: Path) -> list[Path]:
		"""Scan directory for note files.

		Args:
		    root_dir: Root directory to scan

		Returns:
		    list[Path]: List of note file paths
		"""
		note_files = []

		try:
			for file_path in root_dir.rglob("*"):
				if (
					file_path.is_file()
					and file_path.suffix.lower() in self.config.supported_extensions
				):
					# Skip excluded files
					if file_path.name not in self.config.exclude_patterns:
						note_files.append(file_path)
		except Exception as e:
			logger.error(f"Error scanning note files: {e}")

		return note_files

	def clean_orphaned_assets(self, dry_run: bool = False) -> OperationResult:
		"""Remove orphaned asset directories.

		Args:
		    dry_run: If True, only report what would be removed without actually removing

		Returns:
		    OperationResult: Result with list of removed/would-be-removed directories
		"""
		orphaned_dirs = self.find_orphaned_assets()

		if not orphaned_dirs:
			logger.info("No orphaned asset directories found")
			return OperationResult(
				success=True,
				message="No orphaned asset directories found",
				data={"removed_count": 0, "orphaned_dirs": []},
			)

		removed_dirs: list[Path] = []

		for asset_dir in orphaned_dirs:
			if dry_run:
				logger.info(f"[DRY RUN] Would remove: {asset_dir}")
				removed_dirs.append(asset_dir)
			else:
				try:
					logger.info(f"Removing orphaned asset directory: {asset_dir}")
					shutil.rmtree(asset_dir)
					removed_dirs.append(asset_dir)

					# Clean up empty parent directories
					notes_root = (
						Path(self.config.notes_root)
						if isinstance(self.config.notes_root, str)
						else self.config.notes_root
					)
					cleanup_empty_directories(asset_dir.parent, notes_root)
				except Exception as e:
					logger.error(f"Failed to remove {asset_dir}: {e}")

		mode_str = "[DRY RUN] " if dry_run else ""
		message = f"{mode_str}Removed {len(removed_dirs)} orphaned asset director{'y' if len(removed_dirs) == 1 else 'ies'}"

		return OperationResult(
			success=True,
			message=message,
			data={"removed_count": len(removed_dirs), "orphaned_dirs": removed_dirs},
		)
