import shutil
from pathlib import Path
from datetime import datetime

from mkdocs.plugins import get_plugin_logger

from mkdocs_note.utils.cli import common

log = get_plugin_logger(__name__)


class NewCommand:
	"""Command to create a new note."""

	timestamp_format: str = "%Y-%m-%d %H:%M:%S"

	def _generate_note_basic_meta(self, file_path: Path, permalink: str) -> str:
		"""Generate the note meta.

		Args:
			file_path (Path): The path to the new note file
			permalink (str): The permalink value to use

		Returns:
			str: The generated frontmatter content
		"""
		log.debug(f"Generating note meta for: {file_path} with permalink: {permalink}")

		return f"""---
date: {datetime.now().strftime(self.timestamp_format)}
title: {file_path.stem.replace("-", " ").replace("_", " ").title()}
permalink: {permalink}
publish: true
---
"""

	def _validate_before_execution(self, file_path: Path, permalink: str) -> bool:
		"""Validate before executing the new command.

		Args:
			file_path (Path): The path to the new note file
			permalink (str): The permalink value

		Returns:
			bool: True if the validation is successful, False otherwise
		"""
		try:
			# Check if file already exists
			if file_path.exists():
				log.error(f"File already exists: {file_path}")
				return False

			# Check if permalink is empty or None
			if not permalink or not permalink.strip():
				log.error("Permalink cannot be empty")
				return False

			return True
		except Exception as e:
			log.error(f"Error validating before execution: {e}")
			return False

	def execute(self, permalink: str, file_path: Path) -> None:
		"""Execute the new command.

		Args:
			permalink (str): The permalink value to use for frontmatter and asset directory
			file_path (Path): The path to the new note file
		"""
		try:
			permalink = permalink.strip()
			if self._validate_before_execution(file_path, permalink):
				# Ensure parent directory exists
				common.ensure_parent_directory(file_path)

				# Generate note meta with permalink
				note_meta = self._generate_note_basic_meta(file_path, permalink)

				# Create note file
				file_path.write_text(note_meta, encoding="utf-8")

				# Create corresponding asset directory using permalink
				asset_dir = common.get_asset_directory_by_permalink(
					file_path, permalink
				)
				asset_dir.mkdir(parents=True, exist_ok=True)
			else:
				log.error(f"Validation failed for: {file_path}")
				return

		except Exception as e:
			log.error(f"Error executing new command: {e}")
			return


class RemoveCommand:
	"""Command to remove a note(s) and its(their)
	corresponding asset directory(ies) like `rm -rf`.
	"""

	def _validate_before_execution(self, path: Path) -> int:
		"""Validate before executing the remove command.

		Args:
			path (Path): The path to the note file(s) to remove

		Returns:
			int: The signal marking the result of the validation:
				0: Failed
				1: Single file remove request
				2: Multiple files that refer to a directory remove request
		"""
		try:
			# Check if path exist
			if not path.exists():
				log.error(f"Path does not exist: {path}")
				return 0
			# Check if path is a directory
			elif path.is_dir():
				return 2
			# Check if path is a file
			elif path.is_file():
				return 1
		except Exception as e:
			log.error(f"Error validating before execution: {e}")
			return 0

	def _remove_single_document(self, path: Path, remove_assets: bool = True) -> None:
		"""Remove a single document.

		Args:
			path (Path): The path to the note file to remove
			remove_assets (bool): Whether to remove the asset directory
		"""
		try:
			# Read permalink from document before deleting it
			permalink = common.get_permalink_from_file(path)

			# Determine asset directory based on permalink
			if permalink:
				# Use permalink-based asset directory
				asset_dir = common.get_asset_directory_by_permalink(path, permalink)
				log.debug(
					f"Using permalink-based asset directory: {asset_dir} (permalink: {permalink})"
				)
			else:
				# Fallback to filename-based asset directory for backwards compatibility
				asset_dir = common.get_asset_directory(path)
				log.debug(
					f"Using filename-based asset directory: {asset_dir} (no permalink found)"
				)

			# Remove the document
			path.unlink()
			log.info(f"Successfully removed document: {path}")

			# Remove the asset directory if requested and exists
			if remove_assets and asset_dir.exists():
				shutil.rmtree(asset_dir)
				log.info(f"Successfully removed asset directory: {asset_dir}")
				# Clean up empty parent directories in source
				root_dir = Path(common.get_plugin_config()["notes_root"])
				common.cleanup_empty_directories(asset_dir.parent, root_dir)
			elif remove_assets:
				log.warning(
					f"Asset directory does not exist: {asset_dir}, skipping removal"
				)
		except Exception as e:
			log.error(f"Error removing single document: {e}")

	def _remove_docs_directory(
		self, directory: Path, remove_assets: bool = True
	) -> None:
		"""Remove a directory of documents.

		Args:
			directory (Path): The path to the directory of documents to remove
			remove_assets (bool): Whether to remove the asset directories
		"""
		try:
			# Get the list of documents in the directory
			documents = [
				p
				for p in directory.iterdir()
				if p.is_file() and (p.suffix == ".md" or p.suffix == ".ipynb")
			]

			# Remove each document
			for document in documents:
				self._remove_single_document(document, remove_assets)
		except Exception as e:
			log.error(f"Error removing directory of documents: {e}")

	def execute(self, path: Path, remove_assets: bool = True) -> None:
		"""Execute the remove command.

		Args:
			path (Path): The path to the note file to remove
		"""
		try:
			# Validate before execution
			pre_check = self._validate_before_execution(path)
			if pre_check == 0:
				log.error(f"Validation failed for: {path}")
			elif pre_check == 1:
				self._remove_single_document(path, remove_assets)
			elif pre_check == 2:
				self._remove_docs_directory(path, remove_assets)
		except Exception as e:
			log.error(f"Error executing remove command: {e}")
			return


class MoveCommand:
	"""Command to move a note(s) and its(their)
	corresponding asset directory(ies) like `mv`.
	"""

	def _validate_before_execution(self, source: Path, destination: Path) -> int:
		"""Validate before executing the move command.

		Args:
			source (Path): The path to the source note file(s) to move
			destination (Path): The path to the destination note file(s) to move

		Returns:
			int: The signal marking the result of the validation:
				0: Failed
				1: Single file move request
				2: Multiple files that refer to a directory move request
		"""
		try:
			# Check if source exists
			if not source.exists():
				log.error(f"Source does not exist: {source}")
				return 0
			# Check if source is a directory
			elif source.is_dir():
				return 2
			# Check if source is a file
			elif source.is_file():
				# If destination exists and is a file (not a directory), it's an error
				# If destination exists and is a directory, that's OK (file will be moved into it)
				# If destination doesn't exist, it will be created
				if destination.exists() and destination.is_file():
					log.error(f"Destination already exists: {destination}")
					return 0
				return 1
		except Exception as e:
			log.error(f"Error validating before execution: {e}")
			return 0

	def _move_single_document(self, source: Path, destination: Path) -> None:
		"""Move a single document.

		Args:
			source (Path): The path to the source note file to move
			destination (Path): The path to the destination note file or directory to move to
		"""
		try:
			# If destination is a directory (exists and is a directory), construct the final destination path
			# (shutil.move will move source to destination/source.name)
			# If destination doesn't exist but its parent does, treat it as a file path
			if destination.exists() and destination.is_dir():
				final_destination = destination / source.name
			else:
				final_destination = destination

			# Ensure parent directory exists
			common.ensure_parent_directory(final_destination)

			# Read permalink from source document before moving it
			permalink = common.get_permalink_from_file(source)

			# Determine source asset directory based on permalink
			if permalink:
				# Use permalink-based asset directory
				source_asset_dir = common.get_asset_directory_by_permalink(
					source, permalink
				)
				# Resolve to absolute path to avoid issues with relative paths
				source_asset_dir = source_asset_dir.resolve()
				# Destination asset directory should also use permalink
				# (permalink stays the same after move)
				# Use final_destination to correctly calculate the asset directory
				dest_asset_dir = common.get_asset_directory_by_permalink(
					final_destination, permalink
				)
				dest_asset_dir = dest_asset_dir.resolve()
				log.debug(
					f"Using permalink-based asset directories: permalink={permalink}, source={source_asset_dir}, dest={dest_asset_dir}"
				)
			else:
				# Fallback to filename-based asset directory for backwards compatibility
				source_asset_dir = common.get_asset_directory(source)
				source_asset_dir = source_asset_dir.resolve()
				dest_asset_dir = common.get_asset_directory(final_destination)
				dest_asset_dir = dest_asset_dir.resolve()
				log.debug(
					f"Using filename-based asset directories (no permalink found): source={source.stem}, dest={final_destination.stem}, source_dir={source_asset_dir}, dest_dir={dest_asset_dir}"
				)

			# Move the document
			# Note: shutil.move handles both file and directory destinations correctly
			shutil.move(source, destination)
			log.info(f"Successfully moved document: {source} → {final_destination}")

			# Move the asset directory if it exists and source/dest are in different locations
			# Note: If source and dest are in the same directory, their asset directories
			# based on permalink will be the same, so no move is needed.
			if source_asset_dir != dest_asset_dir:
				if source_asset_dir.exists():
					# Ensure destination asset parent's parent directory exists
					# (e.g., for /tmp/assets/dest, ensure /tmp/assets/ exists)
					dest_asset_dir.parent.mkdir(parents=True, exist_ok=True)

					# If destination asset dir already exists, remove it first
					if dest_asset_dir.exists():
						shutil.rmtree(dest_asset_dir)

					shutil.move(str(source_asset_dir), str(dest_asset_dir))
					log.info(
						f"Successfully moved asset directory: {source_asset_dir} → {dest_asset_dir}"
					)
					# Clean up empty parent directories in source
					root_dir = Path(common.get_plugin_config()["notes_root"])
					common.cleanup_empty_directories(source_asset_dir.parent, root_dir)
				else:
					# If source asset dir doesn't exist, log a debug message
					log.debug(
						f"Source asset directory does not exist: {source_asset_dir}, skipping move"
					)
			else:
				# Source and dest are in the same directory, asset dir stays in place
				log.debug(
					f"Source and destination in same directory, asset directory unchanged: {source_asset_dir}"
				)
		except Exception as e:
			log.error(f"Error moving single document: {e}")
			# Try to rollback if possible
			try:
				if destination.exists():
					log.info("Attempting to rollback changes...")
					if not source.exists():
						shutil.move(str(destination), str(source))
					# Note: rollback asset directory only if it was moved
					# This is complex, so we'll just log the error
					log.warning(
						"Asset directory rollback not fully implemented. Manual cleanup may be required."
					)
					log.info("Rollback completed")
			except Exception as rollback_error:
				log.error(f"Rollback failed: {rollback_error}")

	def _move_docs_directory(self, source: Path, destination: Path) -> None:
		"""Move a directory of documents.

		Args:
			source (Path): The path to the source directory of documents to move
			destination (Path): The path to the destination directory of documents to move
		"""
		try:
			# Get all note files in the source directory
			source_dir_resolved = source.resolve()
			all_note_files = []

			for file_path in source_dir_resolved.rglob("*"):
				if file_path.is_file() and file_path.suffix.lower() in [
					".md",
					".ipynb",
				]:
					all_note_files.append(file_path)

			if not all_note_files:
				log.warning(f"No note files found in directory: {source}")

			log.info(f"Found {len(all_note_files)} note file(s) to move")

			# Move each note file
			for note_file in all_note_files:
				self._move_single_document(
					note_file, destination / note_file.relative_to(source_dir_resolved)
				)
		except Exception as e:
			log.error(f"Error moving directory of documents: {e}")

	def _rename_permalink(self, file_path: Path, new_permalink: str) -> None:
		"""Rename permalink value in a note file and its asset directory.

		Args:
			file_path (Path): The path to the note file
			new_permalink (str): The new permalink value
		"""
		try:
			# Validate file exists
			if not file_path.exists():
				log.error(f"File does not exist: {file_path}")
				return

			if not file_path.is_file():
				log.error(f"Path is not a file: {file_path}")
				return

			# Validate new permalink
			if not new_permalink or not new_permalink.strip():
				log.error("New permalink cannot be empty")
				return

			new_permalink = new_permalink.strip()

			# Get current permalink
			old_permalink = common.get_permalink_from_file(file_path)

			if not old_permalink:
				log.warning(
					f"No permalink found in {file_path}. Creating new permalink: {new_permalink}"
				)

			# Determine asset directories based on permalink
			if old_permalink:
				old_asset_dir = common.get_asset_directory_by_permalink(
					file_path, old_permalink
				)
				old_asset_dir = old_asset_dir.resolve()
			else:
				# Fallback to filename-based for backwards compatibility
				old_asset_dir = common.get_asset_directory(file_path)
				old_asset_dir = old_asset_dir.resolve()
				log.debug(
					f"No permalink found, using filename-based asset directory: {old_asset_dir}"
				)

			new_asset_dir = common.get_asset_directory_by_permalink(
				file_path, new_permalink
			)
			new_asset_dir = new_asset_dir.resolve()

			# Update permalink in file
			if common.update_permalink_in_file(file_path, new_permalink):
				log.info(
					f"Successfully updated permalink in {file_path}: {old_permalink or '(none)'} → {new_permalink}"
				)
			else:
				log.error(f"Failed to update permalink in {file_path}")
				return

			# Rename asset directory if it exists and name changed
			if old_asset_dir != new_asset_dir:
				if old_asset_dir.exists():
					# Ensure destination asset parent directory exists
					new_asset_dir.parent.mkdir(parents=True, exist_ok=True)

					# If destination asset dir already exists, remove it first
					if new_asset_dir.exists():
						shutil.rmtree(new_asset_dir)

					shutil.move(str(old_asset_dir), str(new_asset_dir))
					log.info(
						f"Successfully renamed asset directory: {old_asset_dir} → {new_asset_dir}"
					)
					# Clean up empty parent directories
					root_dir = Path(common.get_plugin_config()["notes_root"])
					common.cleanup_empty_directories(old_asset_dir.parent, root_dir)
				else:
					# Create new asset directory if old one doesn't exist
					if not new_asset_dir.exists():
						new_asset_dir.mkdir(parents=True, exist_ok=True)
						log.debug(f"Created new asset directory: {new_asset_dir}")
			else:
				# Permalink changed but asset directory name is the same (shouldn't happen, but handle it)
				log.debug(
					f"Permalink changed but asset directory unchanged: {new_asset_dir}"
				)
		except Exception as e:
			log.error(f"Error renaming permalink: {e}")

	def execute(
		self,
		source: Path,
		destination: Path | None = None,
		permalink: str | None = None,
	) -> None:
		"""Execute the move command.

		Args:
			source (Path): The path to the source note file(s) to move, or file to rename permalink
			destination (Path | None): The path to the destination note file(s) to move (ignored if permalink is provided)
			permalink (str | None): If provided, rename permalink instead of moving file
		"""
		try:
			if permalink:
				# Permalink rename mode: source is the file path, destination is ignored
				if not source.exists():
					log.error(f"Source does not exist: {source}")
					return
				if source.is_file():
					self._rename_permalink(source, permalink)
				else:
					log.error(
						f"Permalink rename only works on files, not directories: {source}"
					)
					return
			else:
				# File move mode: original behavior
				if destination is None:
					log.error("Destination is required in file move mode")
					return
				pre_check = self._validate_before_execution(source, destination)
				if pre_check == 0:
					log.error(f"Validation failed for: {source}")
				elif pre_check == 1:
					self._move_single_document(source, destination)
				elif pre_check == 2:
					self._move_docs_directory(source, destination)
		except Exception as e:
			log.error(f"Error executing move command: {e}")
			return


class CleanCommand:
	"""Command to clean up orphaned asset directories."""

	def _scan_note_files(self, root_dir: Path) -> list[Path]:
		"""Scan directory for note files.

		Args:
			root_dir (Path): Root directory to scan

		Returns:
			list[Path]: List of note file paths
		"""
		note_files = []

		try:
			for file_path in root_dir.rglob("*"):
				if file_path.is_file() and file_path.suffix.lower() in [
					".md",
					".ipynb",
				]:
					note_files.append(file_path)
		except Exception as e:
			log.error(f"Error scanning note files: {e}")

		return note_files

	def _find_orphaned_assets(self, note_files: list[Path]) -> list[Path]:
		"""Find orphaned asset directories.

		Args:
			note_files (list[Path]): List of note file paths

		Returns:
			list[Path]: List of orphaned asset directory paths
		"""
		root_dir = Path(common.get_plugin_config()["notes_root"])
		# Build a set of expected asset directory paths
		expected_asset_dirs: set[str] = set()
		for note_file in note_files:
			# Try to get permalink from file first
			permalink = common.get_permalink_from_file(note_file)
			if permalink:
				# Use permalink-based asset directory
				asset_dir = common.get_asset_directory_by_permalink(
					note_file, permalink
				)
			else:
				# Fallback to filename-based asset directory
				asset_dir = common.get_asset_directory(note_file)
			expected_asset_dirs.add(str(asset_dir.resolve()))

		# Find all actual asset directories by scanning root_dir
		orphaned_dirs: list[Path] = []
		try:
			# Scan for 'assets' directories within root_dir
			for asset_dir in root_dir.rglob("assets"):
				if not asset_dir.is_dir():
					continue
				# Check all subdirectories within each assets directory
				for item in asset_dir.iterdir():
					if item.is_dir():
						# Check if this is a leaf directory (no subdirectories)
						has_subdirs = any(child.is_dir() for child in item.iterdir())
						if not has_subdirs:
							# Check if this is a leaf directory that corresponds to a note
							item_resolved = str(item.resolve())
							if item_resolved not in expected_asset_dirs:
								orphaned_dirs.append(item)
		except Exception as e:
			log.error(f"Error finding orphaned assets: {e}")

		return orphaned_dirs

	def execute(self, dry_run: bool = False) -> None:
		"""Execute the clean command.

		Args:
			dry_run (bool): If True, only report what would be removed without actually removing
		"""
		try:
			root_dir = Path(common.get_plugin_config()["notes_root"])
			note_files = self._scan_note_files(root_dir)
			orphaned_dirs = self._find_orphaned_assets(note_files)
			if not orphaned_dirs:
				log.info("No orphaned asset directories found")

			log.info(f"Found {len(orphaned_dirs)} orphaned asset directory(ies)")

			removed_dirs: list[Path] = []

			for asset_dir in orphaned_dirs:
				if dry_run:
					log.info(f"[DRY RUN] Would remove: {asset_dir}")
					removed_dirs.append(asset_dir)
				else:
					shutil.rmtree(asset_dir)
					removed_dirs.append(asset_dir)
					log.info(
						f"Removed {len(removed_dirs)} orphaned asset directory(ies)"
					)
					# Clean up empty parent directories in source
					common.cleanup_empty_directories(asset_dir.parent, root_dir)
		except Exception as e:
			log.error(f"Error executing clean command: {e}")
			return
