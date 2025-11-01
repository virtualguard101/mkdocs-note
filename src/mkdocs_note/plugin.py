from __future__ import annotations
from pathlib import Path

from mkdocs.structure.files import Files, File
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority, get_plugin_logger
from mkdocs.structure.pages import Page
from mkdocs.structure.nav import Navigation

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils import scanner
from mkdocs_note.utils import page as page_utils
from mkdocs_note.utils.meta import extract_title, extract_date


log = get_plugin_logger(__name__)

class MkdocsNotePlugin(BasePlugin[MkdocsNoteConfig]):
	"""Mkdocs Note Plugin entry point."""

	notes_list: list[File] = []
	

	@event_priority(100)
	def on_files(self, files: Files, config: MkDocsConfig) -> Files:
		"""Handle file processing."""
		self.notes_list.clear()
		invalid_files: list[File] = []

		self.notes_list, invalid_files = scanner.scan_notes(files)

		self.notes_list.sort(key=lambda f: f.note_date, reverse=True)

		for f in invalid_files:
			files.remove(f)

		return files

	def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
		"""Handle plugin configuration."""
		return config


	def on_page_markdown(
		self,
		markdown: str,
		page: Page,
		config: MkDocsConfig,
		files: Files,
	) -> str:
		"""Handle page markdown.

		Args:
			markdown (str): _description_
			page (Page): _description_
			config (MkDocsConfig): _description_
			files (Files): _description_

		Returns:
			str: _description_
		"""
		if self.config.recent_notes_config.enabled:
			if self.is_note_index_page(page.file):
				markdown = page_utils.insert_recent_note_links(
					markdown=markdown,
					notes_list=self.notes_list,
					insert_num=self.config.recent_notes_config.insert_num,
					replace_marker=self.config.recent_notes_config.insert_marker,
				)
			else:
				log.warning("Recent notes are not supported on non-note index pages.")
				markdown = markdown
		else:
			log.debug("Recent notes insertion are disabled.")
			markdown = markdown

		return markdown

	def is_note_index_page(self, f: File) -> bool:
		"""Check if the page is a note index page.

		Args:
			page (Page): The page to check.

		Returns:
			bool: True if the page is a note index page, False otherwise.
		"""
		return f.src_uri == str(Path(self.config.notes_root) / "index.md")



def insert_recent_note_links(
    markdown: str,
    notes_list: list[File],
    insert_num: int,
    replace_marker: str,
) -> str:
    """Insert recent note links into the markdown.

    Args:
        markdown (str): The markdown content.
        notes_list (list[File]): The list of valid notes.
        insert_num (int): The number of recent notes to insert.
        replace_marker (str): The marker to replace.

    Returns:
        str: The markdown content with recent note links inserted.
    """

    content = ""
    for f in notes_list[:insert_num]:
        title = extract_title(f)
        date = extract_date(f).strftime("%Y-%m-%d %H:%M:%S")
        content += f"- <div class='recent-notes'><a href='{f.page.abs_url}'>{title}</a><small>{date}</small></div>\n"
    return markdown.replace(replace_marker, content)


