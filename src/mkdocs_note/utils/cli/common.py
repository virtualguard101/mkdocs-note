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


def update_permalink_in_file(note_path: Path, new_permalink: str) -> bool:
	"""Update permalink value in note file's frontmatter.

	This function preserves the original frontmatter format as much as possible.

	Args:
	    note_path: Path to the note file
	    new_permalink: New permalink value to set

	Returns:
	    bool: True if update was successful, False otherwise

	Examples:
	    >>> update_permalink_in_file(Path("docs/notes/my-note.md"), "new-permalink")
	    True
	"""
	try:
		content = note_path.read_text(encoding="utf-8")

		# Check if file has frontmatter
		if not content.startswith("---\n"):
			log.error(f"File {note_path} does not have frontmatter")
			return False

		# Find frontmatter end marker
		frontmatter_end = content.find("\n---\n", 4)
		if frontmatter_end == -1:
			log.error(f"File {note_path} has invalid frontmatter format")
			return False

		frontmatter_section = content[4:frontmatter_end]  # Skip initial "---\n"
		markdown_content = content[frontmatter_end + 5 :]  # Skip "\n---\n"

		# Parse frontmatter to get current values
		_, frontmatter = meta.get_data(content)

		# Update permalink in frontmatter dict
		frontmatter["permalink"] = new_permalink.strip()

		# Reconstruct frontmatter section
		# Try to preserve original format by updating only the permalink line
		lines = frontmatter_section.split("\n")
		updated = False
		new_lines = []

		for line in lines:
			# Match permalink line (with or without value, with various spacing)
			if line.strip().startswith("permalink:"):
				# Preserve indentation
				indent = len(line) - len(line.lstrip())
				new_lines.append(" " * indent + f"permalink: {new_permalink.strip()}")
				updated = True
			else:
				new_lines.append(line)

		# If permalink line wasn't found, add it (at a reasonable position)
		if not updated:
			# Find where to insert permalink (after date, before publish if exists)
			insert_pos = len(new_lines)
			for i, line in enumerate(new_lines):
				if line.strip().startswith("publish:"):
					insert_pos = i
					break
				elif line.strip().startswith("title:"):
					# Insert after title
					insert_pos = i + 1

			# Use same indentation as surrounding lines
			indent = 0
			if insert_pos > 0 and insert_pos < len(new_lines):
				indent = len(new_lines[insert_pos - 1]) - len(
					new_lines[insert_pos - 1].lstrip()
				)

			new_lines.insert(
				insert_pos, " " * indent + f"permalink: {new_permalink.strip()}"
			)

		# Reconstruct full content
		new_content = "---\n" + "\n".join(new_lines) + "\n---\n" + markdown_content

		# Write back to file
		note_path.write_text(new_content, encoding="utf-8")
		log.debug(f"Updated permalink in {note_path} to: {new_permalink}")
		return True
	except Exception as e:
		log.error(f"Error updating permalink in {note_path}: {e}")
		return False


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
