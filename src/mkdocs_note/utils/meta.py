import posixpath
from datetime import datetime
from typing import Optional, Union, Callable

from mkdocs.utils import meta
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import File


logger = get_plugin_logger(__name__)


def set_file_dest_uri(f: File, value: Union[str, Callable[[str], str]]) -> None:
	"""Set the uri of the mkdocs object file.

	Args:
		f (File): The documentation file to set the uri for.
		value (Union[str, Callable[[str], str]]): The uri to set. If a string, it will be used as is. If a callable, it will be called with the current uri and should return the new uri.
	"""
	f.dest_uri = value if isinstance(value, str) else value(f.dest_uri)

	def delattr_if_exists(obj, attr):
		if hasattr(obj, attr):
			delattr(obj, attr)

	# 删掉 cached_property 的缓存
	delattr_if_exists(f, "url")
	delattr_if_exists(f, "abs_dest_path")


def validate_frontmatter(f: File) -> bool:
	"""Validate the frontmatter of the file

	Args:
	    file (File): The file to validate

	Returns:
	    bool: True if the frontmatter is valid, False otherwise
	"""
	try:
		_, frontmatter = meta.get_data(f.content_string)

		if not frontmatter.get("publish", False):
			logger.debug(f"Skipping {f.src_uri} because it is not published")
			return False

		if "date" not in frontmatter:
			logger.error(f"Invalid frontmatter for {f.src_uri}: 'date' is required")
			return False

		date = frontmatter["date"]
		if not isinstance(date, datetime):
			logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'date' must be a datetime object"
			)
			return False

		setattr(f, "note_date", date)

		if "title" not in frontmatter:
			logger.error(f"Invalid frontmatter for {f.src_uri}: 'title' is required")
			return False

		if "permalink" not in frontmatter:
			logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'permalink' is required"
			)
			return False

		permalink = frontmatter["permalink"]

		if not f.use_directory_urls:
			set_file_dest_uri(f, posixpath.join("p", permalink + ".html"))
		else:
			set_file_dest_uri(f, posixpath.join("p", permalink, "index.html"))

		title = frontmatter["title"]
		if not isinstance(title, str):
			logger.error(
				f"Invalid frontmatter for {f.src_uri}: 'title' must be a string"
			)
			return False

		setattr(f, "note_title", title)
		return True

	except Exception as e:
		logger.error(f"Error validating frontmatter for {f.src_uri}: {e}")
		raise e


def extract_date(f: File) -> Optional[datetime]:
	"""Extract date from docs file
	Args:
	    f (File): The file to extract date from

	Returns:
	    Optional[datetime]: The date if successful, None otherwise
	"""
	try:
		return f.note_date
	except Exception:
		return None


def extract_title(f: File) -> Optional[str]:
	"""Extract title from docs file

	Args:
	    f (File): The file to extract title from

	Returns:
	    Optional[str]: The title if successful, None otherwise
	"""
	try:
		return f.note_title
	except Exception:
		return None
