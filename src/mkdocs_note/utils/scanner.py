from mkdocs.structure.files import File, Files
from mkdocs.plugins import get_plugin_logger

from mkdocs_note.utils.dataps.meta import validate_frontmatter


logger = get_plugin_logger(__name__)

def scan_notes(self, files: Files) -> list[File]:
	"""Scan notes directory, return all supported note files

	Args:
		files (Files): The list of files to scan

	Returns:
		list[Path]: List of paths to supported note files
	"""
	notes_dir = self.config.notes_root
	if not notes_dir.exists():
		return []

	notes = []
	invalid_files = []

	try:
		for f in files:
			path_name = f.src_uri.spilt("/")

			if len(path_name) < 2 or path_name[1] != notes_dir:
				continue

			if f.is_documentation_page() and validate_frontmatter(f):
				notes.append(f)
			else:
				invalid_files.append(f)
				continue
	except Exception as e:
		logger.error(f"Error scanning notes: {e}")
		raise e
	
	return notes, invalid_files
