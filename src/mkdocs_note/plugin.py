from __future__ import annotations

import os
import json

from mkdocs.structure.files import Files, File
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority, get_plugin_logger
from mkdocs.structure.pages import Page
from mkdocs.structure.nav import Navigation

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.utils import scanner
from mkdocs_note.utils.meta import extract_title, extract_date
from mkdocs_note.graph import (
	Graph,
	add_static_resouces,
	inject_graph_script,
	copy_static_assets,
)


log = get_plugin_logger(__name__)


class MkdocsNotePlugin(BasePlugin[MkdocsNoteConfig]):
	"""Mkdocs Note Plugin entry point."""

	notes_list: list[File] = []

	@event_priority(100)
	def on_files(self, files: Files, config: MkDocsConfig) -> Files:
		"""Handle file processing."""
		self.notes_list.clear()
		invalid_files: list[File] = []

		self.notes_list, invalid_files = scanner.scan_notes(files, self.config)

		self.notes_list.sort(key=lambda f: f.note_date, reverse=True)

		for f in invalid_files:
			files.remove(f)

		return files

	def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
		"""Handle plugin configuration."""
		self.static_dir = os.path.join(os.path.dirname(__file__), "static")

		add_static_resouces(config)

		return config

	def on_pre_build(self, *, config: dict, **kwagrs) -> None:
		"""Handle pre-build."""
		if self.config.graph_config["enabled"]:
			self._graph = Graph(self.config.graph_config)

	def on_nav(
		self,
		nav: Navigation,
		*,
		config: MkDocsConfig,
		files: Files,
	) -> Navigation:
		"""Handle navigation.

		Args:
			nav (Navigation): The navigation object.
			config (MkDocsConfig): The MkDocs configuration.
			files (Files): The files object.

		Returns:
			Navigation: The navigation object.
		"""
		self._files = files
		return nav

	def _write_graph_file(self, config: MkDocsConfig) -> None:
		"""Write the graph data to a file."""
		log.info("Writing graph data to file...")
		output_dir = os.path.join(config["site_dir"], "graph")
		try:
			os.makedirs(output_dir, exist_ok=True)
			graph_file = os.path.join(output_dir, "graph.json")
			with open(graph_file, "w") as f:
				json.dump(self._graph.to_dict(), f)
		except (IOError, OSError) as e:
			log.error(f"Error writing graph file: {e}")

	def on_post_page(
		self,
		output: str,
		*,
		page: Page,
		config: MkDocsConfig,
	) -> str:
		"""Handle post page.

		Args:
			output (str): The output content.
			page (Page): The page object.
			config (MkDocsConfig): The MkDocs configuration.

		Returns:
			str: The output content.
		"""
		debug = self.config.graph_config.get("debug", False)
		output = inject_graph_script(output=output, config=config, debug=debug)
		return output

	def on_post_build(
		self,
		*,
		config: MkDocsConfig,
		**kwargs,
	) -> None:
		"""Handle post build.

		Args:
			config (MkDocsConfig): The MkDocs configuration.
		"""
		# Build graph if enabled
		if hasattr(self, "_graph") and hasattr(self, "_files"):
			self._graph(self._files)
			self._write_graph_file(config=config)

		log.info("Copying static assets...")
		try:
			copy_static_assets(static_dir=self.static_dir, config=config)
		except (IOError, OSError) as e:
			log.error(f"Error copying static assets: {e}")

	def on_page_markdown(
		self,
		markdown: str,
		page: Page,
		config: MkDocsConfig,
		files: Files,
	) -> str:
		"""Handle page markdown.

		Args:
			markdown (str): The markdown content.
			page (Page): The page object.
			config (MkDocsConfig): The MkDocs configuration.
			files (Files): The files object.

		Returns:
			str: The markdown content.
		"""
		# Only process recent notes on the note index page
		if self.config.recent_notes_config["enabled"] and self.is_note_index_page(
			page.file
		):
			markdown = insert_recent_note_links(
				markdown=markdown,
				notes_list=self.notes_list,
				insert_num=self.config.recent_notes_config["insert_num"],
				replace_marker=self.config.recent_notes_config["insert_marker"],
			)
			log.debug(f"Recent notes inserted into {page.file.src_uri}")

		return markdown

	def is_note_index_page(self, f: File) -> bool:
		"""Check if the page is a note index page.

		Args:
			f (File): The file to check.

		Returns:
			bool: True if the page is a note index page, False otherwise.
		"""
		# src_uri is relative to docs_dir, so we just check for 'index.md'
		# when notes_root is the docs_dir itself
		return f.src_uri == "index.md"


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

	content = "<ul>\n"
	for f in notes_list[:insert_num]:
		title = extract_title(f)
		date = extract_date(f).strftime("%Y-%m-%d %H:%M:%S")
		# Use f.url (relative URL) or f.page.url if page is available
		url = f.page.url if hasattr(f, "page") and f.page else f.url
		# No indentation to avoid Markdown treating it as code block
		content += f'<li><div style="display:flex; justify-content:space-between; align-items:center;"><a href="{url}">{title}</a><span style="font-size:0.8em; color:#888;">{date}</span></div></li>\n'
	content += "</ul>\n"
	return markdown.replace(replace_marker, content)
