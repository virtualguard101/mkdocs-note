"""
Common utilities and data structures for CLI operations.
"""

from pathlib import Path
from typing import Optional

from mkdocs.plugins import get_plugin_logger
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.utils import meta

from mkdocs_note.plugin import MkdocsNotePlugin as plugin


log = get_plugin_logger(__name__)


def get_plugin_config() -> MkDocsConfig:
	"""Get the plugin configuration.

	Returns:
		MkdocsNoteConfig: The plugin configuration
	"""
	return plugin.config


def get_asset_directory(note_path: Path) -> Path:
	"""Get the asset directory path for a note file based on filename.

	Uses co-located asset structure: note_file.parent / "assets" / note_file.stem
	__This is the legacy method based on filename stem__.

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


def get_asset_directory_by_permalink(note_path: Path, permalink: str) -> Path:
	"""Get the asset directory path for a note file based on permalink.

	Uses co-located asset structure: note_file.parent / "assets" / permalink

	Args:
	    note_path: Path to the note file
	    permalink: The permalink value from frontmatter

	Returns:
	    Path: The asset directory path

	Examples:
	    >>> get_asset_directory_by_permalink(Path("docs/notes/my-note.md"), "my-permalink")
	    PosixPath('docs/notes/assets/my-permalink')
	"""
	return note_path.parent / "assets" / permalink


def get_permalink_from_file(note_path: Path) -> Optional[str]:
	"""Extract permalink value from note file's frontmatter.

	Args:
	    note_path: Path to the note file

	Returns:
	    Optional[str]: The permalink value if found, None otherwise

	Examples:
	    >>> get_permalink_from_file(Path("docs/notes/my-note.md"))
	    'my-permalink'
	"""
	try:
		content = note_path.read_text(encoding="utf-8")
		_, frontmatter = meta.get_data(content)
		permalink = frontmatter.get("permalink")
		if permalink and isinstance(permalink, str) and permalink.strip():
			return permalink.strip()
		return None
	except Exception as e:
		log.error(f"Error reading permalink from {note_path}: {e}")
		return None


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
					log.debug(f"Removing empty directory: {current}")
					current.rmdir()
					# Recursively clean up parent
					cleanup_empty_directories(current.parent, stop)
			except OSError:
				# Directory not empty or other error, stop cleanup
				pass
	except Exception as e:
		log.error(f"Error during directory cleanup: {e}")
