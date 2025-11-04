from pathlib import Path

from mkdocs.structure.files import File, Files
from mkdocs.plugins import get_plugin_logger

from mkdocs_note.utils.meta import validate_frontmatter


logger = get_plugin_logger(__name__)


def scan_notes(files: Files, config) -> tuple[list[File], list[File]]:
	"""Scan notes directory, return all supported note files

	Args:
		files (Files): The list of files to scan
		config: Plugin configuration

	Returns:
		tuple[list[File], list[File]]: (valid notes, invalid files)
	"""
	notes_dir = (
		Path(config.notes_root)
		if isinstance(config.notes_root, str)
		else config.notes_root
	)
	if not notes_dir.exists():
		logger.warning(f"Notes directory does not exist: {notes_dir}")
		return [], []

	notes = []
	invalid_files = []

	try:
		for f in files:
			# Skip non-documentation pages
			if not f.is_documentation_page():
				continue

			# Check if file is within notes_root by comparing absolute paths
			# f.abs_src_path is the absolute path to the source file
			try:
				file_path = Path(f.abs_src_path)
				# Check if the file is within the notes_root directory
				file_path.relative_to(notes_dir)
			except (ValueError, AttributeError):
				# File is not within notes_root
				continue

			# Validate frontmatter
			if validate_frontmatter(f):
				notes.append(f)
			else:
				invalid_files.append(f)
	except Exception as e:
		logger.error(f"Error scanning notes: {e}")
		raise e

	return notes, invalid_files
