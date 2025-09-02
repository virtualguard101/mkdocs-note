import os
import datetime
import posixpath

from mkdocs.structure.files import File, Files
from mkdocs.utils import meta, get_relative_url

from ..logger import logger
from ..core import note_manager

def parse_note_metadata(file: File) -> bool:
    """Parse a note file and extract metadata.

    Args:
        file (File): The note file to parse.

    Returns:
        bool: True if the note was parsed successfully, False otherwise.
    """
    # ignore text content by assigning it with _ first
    _, frontmatter = meta.get_data(file.content_string)

    if not frontmatter.get('publish', False):
        logger.debug(f"Note '{file.src_path}' is not published.")
        return False

    if 'data' not in frontmatter:
        logger.error(f"Note '{file.src_path}' is missing 'data' field.")
        return False

    date = frontmatter['date']
    if not isinstance(date, datetime.datetime):
        logger.error(f"Note '{file.src_path}' has invalid 'date' field.")
        return False

    head = note_manager.set_note_permalink(file)[0]
    permalink = frontmatter['permalink']
    if not isinstance(permalink, str):
        logger.error(f"Note '{file.src_path}' has invalid 'permalink' field.")
        return False

    setattr(file, 'note_date', date)

    if not file.use_directory_urls:
        note_manager.set_note_uri(file, posixpath.join(head, permalink + '.html'))
    else:
        note_manager.set_note_uri(file, posixpath.join(head, permalink + 'index.html'))

    return True
