from pathlib import Path
from datetime import datetime

from mkdocs.plugins import get_plugin_logger

from mkdocs_note.utils.cli import common

log = get_plugin_logger(__name__)


class NewCommand:
	"""Command to create a new note."""

	timestamp_format: str = "%Y-%m-%d %H:%M:%S"

	def _generate_note_basic_meta(self, file_path: Path) -> str:
		"""Generate the note meta."""
		log.debug(f"Generating note meta for: {file_path}")

		return f"""---
date: {datetime.now().strftime(self.timestamp_format)}
title: {file_path.stem.replace("-", " ").replace("_", " ").title()}
permalink: 
publish: true
---
"""

	def _validate_before_execution(self, file_path: Path) -> bool:
		"""Validate before executing the new command.
		
		Args:
			file_path (Path): The path to the new note file

		Returns:
			bool: True if the validation is successful, False otherwise
		"""
		try:
			# Check if file already exists
			if file_path.exists():
				log.error(f"File already exists: {file_path}")
				return False
		except Exception as e:
			log.error(f"Error validating before execution: {e}")
			return False

	def execute(self, file_path: Path) -> None:
		"""Execute the new command.

		Args:
			file_path (Path): The path to the new note file
		"""
		try:
			if self._validate_before_execution(file_path):
				# Ensure parent directory exists
				common.ensure_parent_directory(file_path)

				# Generate note meta
				note_meta = self._generate_note_basic_meta(file_path)

				# Create note file
				file_path.write_text(note_meta, encoding="utf-8")

				# Create corresponding asset directory
				asset_dir = common.get_asset_directory(file_path)
				asset_dir.mkdir(parents=True, exist_ok=True)
			else:
				log.error(f"Validation failed for: {file_path}")
				return
			# Create corresponding asset directory
			asset_dir = common.get_asset_directory(file_path)
			asset_dir.mkdir(parents=True, exist_ok=True)

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
				log.error(f"Path is a file: {path}")
				return 1
		except Exception as e:
			log.error(f"Error validating before execution: {e}")
			return 0

	def _remove_single_document(
		self,
		path: Path,
		remove_assets: bool = True
	) -> None:
		"""Remove a single document.

		Args:
			path (Path): The path to the note file to remove
			remove_assets (bool): Whether to remove the asset directory
		"""
		try:
			# Get the corresponding asset directory
			asset_dir = common.get_asset_directory(path)

			# Remove the document
			path.unlink()
			log.info(f"Successfully removed document: {path}")

			# Remove the asset directory if requested and exists
			if remove_assets and asset_dir.exists():
				import shutil
				shutil.rmtree(asset_dir)
				log.info(f"Successfully removed asset directory: {asset_dir}")
			else:
				log.warning(f"Asset directory does not exist: {asset_dir}, skipping removal")
		except Exception as e:
			log.error(f"Error removing single document: {e}")

	def _remove_docs_directory(
		self,
		directory: Path,
		remove_assets: bool = True
	) -> None:
		"""Remove a directory of documents.

		Args:
			directory (Path): The path to the directory of documents to remove
			remove_assets (bool): Whether to remove the asset directories
		"""
		try:
			# Get the list of documents in the directory
			documents = [p for p in directory.iterdir() if p.is_file() and (p.suffix == ".md" or p.suffix == ".ipynb")]

			# Remove each document
			for document in documents:
				self._remove_single_document(document, remove_assets)
		except Exception as e:
			log.error(f"Error removing directory of documents: {e}")

	def execute(
		self,
		path: Path,
		remove_assets: bool = True
	) -> None:
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

	def _validate_before_execution(
		self,
		source: Path,
		destination: Path
	) -> int:
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
				return 1
			
			# Check if destination exists
			if destination.exists():
				log.error(f"Destination already exists: {destination}")
				return 0
		except Exception as e:
			log.error(f"Error validating before execution: {e}")
			return 0

	def _move_single_document(
		self,
		source: Path,
		destination: Path
	) -> None:
		"""Move a single document.

		Args:
			source (Path): The path to the source note file to move
			destination (Path): The path to the destination note file to move
		"""
		try:
			pass
		except Exception as e:
			log.error(f"Error moving single document: {e}")

	def _move_docs_directory(
		self,
		source: Path,
		destination: Path
	) -> None:
		"""Move a directory of documents.

		Args:
			source (Path): The path to the source directory of documents to move
			destination (Path): The path to the destination directory of documents to move
		"""
		try:
			pass
		except Exception as e:
			log.error(f"Error moving directory of documents: {e}")

	def execute(
		self,
		source: Path,
		destination: Path
	) -> None:
		"""Execute the move command.

		Args:
			source (Path): The path to the source note file(s) to move
			destination (Path): The path to the destination note file(s) to move
		"""
		pass
