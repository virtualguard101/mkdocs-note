from datetime import datetime

from mkdocs.utils import meta
from mkdocs.structure.files import File

from typing import Optional

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
				return False

			if "date" not in frontmatter:
				raise ValueError(
					f"Invalid frontmatter for {f.src_uri}: 'date' is required"
				)

			date = frontmatter["date"]
			if not isinstance(date, datetime):
				raise ValueError(
					f"Invalid frontmatter for {f.src_uri}: 'date' must be a datetime object"
				)

			setattr(f, "note_date", date)

			if "title" not in frontmatter:
				raise ValueError(
					f"Invalid frontmatter for {f.src_uri}: 'title' is required"
				)

			title = frontmatter["title"]
			if not isinstance(title, str):
				raise ValueError(
					f"Invalid frontmatter for {f.src_uri}: 'title' must be a string"
				)

			setattr(f, "note_title", title)

			return True
		except Exception as e:
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
