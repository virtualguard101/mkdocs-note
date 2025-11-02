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
	notes_dir = config.notes_root
	if not notes_dir.exists():
		return [], []

	notes = []
	invalid_files = []

	try:
		for f in files:
			path_name = f.src_uri.split("/")

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
