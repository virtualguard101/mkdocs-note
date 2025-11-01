from pathlib import Path

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


class AssetScanner:
	"""Asset scanner"""

	def scan_assets(self) -> list[Path]:
		"""Scan assets directory, return all assets files

		Returns:
		    list[Path]: The list of valid asset files
		"""
		assets_dir = Path(self.config.assets_dir)
		if not assets_dir.exists():
			self.logger.warning(f"Assets directory does not exist: {assets_dir}")
			return []

		assets = []

		try:
			for file_path in assets_dir.rglob("*"):
				if self._is_valid_asset_file(file_path):
					assets.append(file_path)
		except PermissionError as e:
			self.logger.error(f"Permission denied while scanning {assets_dir}: {e}")
			return []

		self.logger.debug(f"Found {len(assets)} asset files")
		return assets

	def _is_valid_asset_file(self, file_path: Path) -> bool:
		"""Check if file is a valid asset file

		Args:
		    file_path (Path): The path of the file to check

		Returns:
		    bool: True if the file is a valid asset file, False otherwise
		"""
		if not file_path.is_file():
			return False

		return True
