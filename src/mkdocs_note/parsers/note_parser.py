import os
import datetime
import posixpath

from mkdocs.structure.files import File, Files
from mkdocs.utils import meta, get_relative_url

from mkdocs_note.logger import logger
from mkdocs_note.core import note_manager

def parse_note_metadata(file: File) -> bool:
    """Parse a note file and extract metadata.

    Args:
        file (File): The note file to parse.

    Returns:
        bool: True if the note was parsed successfully, False otherwise.
    """
    # ignore text content by assigning it with _ first
    try:
        with open(file.abs_src_path, 'r', encoding='utf-8') as f:
            _, metadata = meta.get_data(f.read())
    except Exception as e:
        logger.error(f"Error reading or parsing metadata for '{file.src_path}': {e}")
        return False

    if not metadata.get('publish', False):
        logger.debug(f"Note '{file.src_path}' is not published.")
        return False

    if 'date' not in metadata:
        logger.error(f"Note '{file.src_path}' is missing 'date' field.")
        return False

    date = metadata['date']
    if not isinstance(date, datetime.date):
        logger.error(f"Note '{file.src_path}' has invalid 'date' field.")
        return False

    head = note_manager.set_note_permalink(file)[0]
    permalink = metadata.get('permalink')
    if not isinstance(permalink, str):
        logger.error(f"Note '{file.src_path}' has invalid 'permalink' field.")
        return False

    setattr(file, 'note_date', date)

    if not file.use_directory_urls:
        note_manager.set_note_uri(file, posixpath.join(head, permalink + '.html'))
    else:
        note_manager.set_note_uri(file, posixpath.join(head, permalink, 'index.html'))

    return True
