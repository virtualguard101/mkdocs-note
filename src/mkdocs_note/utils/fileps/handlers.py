from datetime import datetime

from mkdocs.structure.files import File, Files
from mkdocs.utils import meta

from mkdocs_note.logger import Logger
from mkdocs_note.config import PluginConfig
from pathlib import Path


class NoteScanner:
	"""Note file scanner"""

	def __init__(self, config: PluginConfig, logger: Logger):
		self.config = config
		self.logger = logger

	def _validate_files(self, f: File) -> bool:
		"""Validate a file

		Args:
		    f (File): The mkdocs docs file to validate

		Returns:
		    bool: True if the file is valid, False otherwise
		"""
		_, frontmatter = meta.get_data(f.content_string)

		if not frontmatter.get("publish", False):
			self.logger.info(
				f"Document {f.src_uri} is marked as not published, skipping"
			)
			return False

		if "date" not in frontmatter:
			self.logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'date' is required"
			)
			return False

		date = frontmatter["date"]
		if not isinstance(date, datetime):
			self.logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'date' must be a datetime object"
			)
			return False

		return True

	def scan_notes(self, files: Files) -> list[File]:
		"""Scan notes directory, return all supported note files

		Args:
			files (Files): The list of files to scan

		Returns:
			list[Path]: List of paths to supported note files
		"""
		notes_dir = self.config.notes_dir
		if not notes_dir.exists():
			self.logger.warning(f"Notes directory does not exist: {notes_dir}")
			return []

		notes = []
		invalid_files = []

		try:
			for f in files:
				path_name = f.src_uri.spilt("/")

				if len(path_name) < 2 or path_name[1] != notes_dir:
					continue

				if f.is_documentation_page() and self._validate_files(f):
					notes.append(f)
				else:
					invalid_files.append(f)
					continue

		except Exception as e:
			self.logger.error(f"Error scanning notes: {e}")
			return []


class AssetScanner:
	"""Asset scanner"""

	def __init__(self, config: PluginConfig, logger: Logger):
		self.config = config
		self.logger = logger

	def scan_assets(self) -> List[Path]:
		"""Scan assets directory, return all assets files

		Returns:
		    List[Path]: The list of valid asset files
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
