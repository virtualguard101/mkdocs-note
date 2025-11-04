"""
Common utilities and data structures for CLI operations.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OperationResult:
	"""Result of a CLI operation.

	Attributes:
	    success: Whether the operation succeeded
	    message: Human-readable message describing the result
	    data: Optional additional data returned by the operation
	"""

	success: bool
	message: str = ""
	data: Any = None

	def __bool__(self) -> bool:
		"""Allow using result in boolean context."""
		return self.success


def get_asset_directory(note_path: Path) -> Path:
	"""Get the asset directory path for a note file.

	Uses co-located asset structure: note_file.parent / "assets" / note_file.stem

	Args:
	    note_path: Path to the note file

	Returns:
	    Path: The asset directory path

	Examples:
	    >>> get_asset_directory(Path("docs/usage/contributing.md"))
	    PosixPath('docs/usage/assets/contributing')

	    >>> get_asset_directory(Path("docs/notes/python/intro.md"))
	    PosixPath('docs/notes/python/assets/intro')
	"""
	return note_path.parent / "assets" / note_path.stem


def is_supported_note(path: Path, supported_extensions: list[str]) -> bool:
	"""Check if a file path has a supported extension.

	Args:
	    path: File path to check
	    supported_extensions: List of supported extensions (e.g., [".md", ".ipynb"])

	Returns:
	    bool: True if extension is supported
	"""
	return path.suffix.lower() in supported_extensions


def is_excluded_name(name: str, exclude_patterns: list[str]) -> bool:
	"""Check if a filename matches any exclude pattern.

	Args:
	    name: Filename to check
	    exclude_patterns: List of patterns to exclude (e.g., ["index.md", "README.md"])

	Returns:
	    bool: True if name should be excluded
	"""
	return name in exclude_patterns


def ensure_parent_directory(path: Path) -> None:
	"""Ensure the parent directory of a path exists.

	Args:
	    path: File path whose parent should be created

	Raises:
	    OSError: If directory creation fails
	"""
	path.parent.mkdir(parents=True, exist_ok=True)


def cleanup_empty_directories(start_dir: Path, stop_at: Path) -> None:
	"""Recursively remove empty parent directories up to a stop point.

	Args:
	    start_dir: Directory to start cleanup from
	    stop_at: Directory to stop at (won't be removed)
	"""
	try:
		current = start_dir.resolve()
		stop = stop_at.resolve()

		# Don't remove directories outside or at the stop point
		if not current.is_relative_to(stop) or current == stop:
			return

		# Check if directory exists and is empty
		if current.exists() and current.is_dir():
			try:
				if not any(current.iterdir()):
					logging.debug(f"Removing empty directory: {current}")
					current.rmdir()
					# Recursively clean up parent
					cleanup_empty_directories(current.parent, stop)
			except OSError:
				# Directory not empty or other error, stop cleanup
				pass
	except Exception as e:
		logging.debug(f"Error during directory cleanup: {e}")


def get_logger(name: str) -> logging.Logger:
	"""Get a logger instance for CLI operations.

	Args:
	    name: Logger name (typically __name__)

	Returns:
	    logging.Logger: Configured logger instance
	"""
	logger = logging.getLogger(name)
	if not logger.handlers:
		handler = logging.StreamHandler()
		formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.setLevel(logging.INFO)
	return logger
