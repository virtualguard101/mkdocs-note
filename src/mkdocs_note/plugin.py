from __future__ import annotations

from pathlib import Path
from typing import List

from mkdocs.structure.files import Files
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, event_priority
from mkdocs.structure.pages import Page
from mkdocs.structure.nav import Navigation as Nav

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.fileps.handlers import NoteScanner
from mkdocs_note.utils.docsps.handlers import NoteProcessor
from mkdocs_note.utils.dataps.meta import NoteInfo
from mkdocs_note.utils.assetps.handlers import AssetsProcessor
from mkdocs_note.utils.graphps.handlers import GraphHandler


class MkdocsNotePlugin(BasePlugin[PluginConfig]):
	"""MkDocs plugin for managing notes.

	This plugin automatically inserts recent notes into the index page
	of the configured notes directory.
	"""

	def __init__(self):
		super().__init__()
		self.logger = Logger()  # Will be updated with config in on_config
		self._recent_notes: List[NoteInfo] = []
		self._graph_handler = None
		self._assets_processor = None
		self._network_graph_manager = None
		self._docs_dir = None
		self._files = None

	@property
	def plugin_enabled(self) -> bool:
		"""Check if the plugin is enabled."""
		return self.config.enabled

	@event_priority(100)
	def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
		"""Handle the configuration for the plugin.

		Args:
		    config (MkDocsConfig): The MkDocs configuration

		Returns:
		    MkDocsConfig | None: The updated MkDocs configuration
		"""
		# Update logger level based on configuration
		self.logger.set_level(self.config.log_level)

		if not self.plugin_enabled:
			self.logger.debug("MkDocs-Note plugin is disabled.")
			return config

		# Fix project_root: use MkDocs config file's parent directory instead of plugin installation path
		# This is critical for git operations to work correctly in deployed environments
		if hasattr(config, "config_file_path") and config.config_file_path:
			try:
				# Ensure config_file_path is a valid path (not a Mock or other test object)
				config_path = str(config.config_file_path)
				actual_project_root = Path(config_path).parent
				self.config.project_root = actual_project_root
				self.logger.debug(f"Set project_root to: {actual_project_root}")
			except (TypeError, ValueError, OSError) as e:
				# Fallback to current working directory if path conversion fails
				self.logger.debug(
					f"Failed to get project root from config file path: {e}"
				)
				actual_project_root = Path.cwd()
				self.config.project_root = actual_project_root
				self.logger.debug(
					f"Set project_root to current working directory: {actual_project_root}"
				)
		else:
			# Fallback to current working directory
			actual_project_root = Path.cwd()
			self.config.project_root = actual_project_root
			self.logger.debug(
				f"Set project_root to current working directory: {actual_project_root}"
			)

		# Ensure toc configuration exists
		if "toc" not in config.mdx_configs:
			config.mdx_configs["toc"] = {}

		toc_config = config.mdx_configs["toc"]

		# Ensure separator exists
		if "separator" not in toc_config:
			toc_config["separator"] = "-"

		# Set slugify function
		if "slugify" not in toc_config:
			try:
				from pymdownx.slugs import slugify

				toc_config["slugify"] = slugify
				self.logger.debug(
					"Using pymdownx.slugs.slugify for better Material theme compatibility"
				)
			except ImportError:
				from markdown.extensions.toc import slugify

				toc_config["slugify"] = slugify
				self.logger.debug("Using markdown.extensions.toc.slugify as fallback")

		# Store docs_dir for path resolution
		self._docs_dir = Path(config.docs_dir)

		# Initialize assets processor
		self._assets_processor = AssetsProcessor(self.config, self.logger)

		# Initialize graph handler only if network graph is enabled
		if self.config.enable_network_graph:
			self._graph_handler = GraphHandler(self.config)
			self.logger.debug("Graph Handler initialized")
			# Add static resources into the mkdocs config for network graph
			self._graph_handler.add_static_resources(config)
		else:
			self.logger.debug("Graph Handler was disabled")
			self._graph_handler = None

		self.logger.info("MkDocs Note plugin initialized successfully.")
		return config

	def on_nav(self, nav: Nav, *, config: MkDocsConfig, files: Files) -> Nav:
		"""
		Handle the navigation for the plugin.

		Args:
		    nav (Nav): The navigation object
		    config (MkDocsConfig): The MkDocs configuration
		    files (Files): The files to check

		Returns:
		    Nav: The updated navigation object
		"""
		self.logger.info("Storing file collection")
		self._files = files
		return nav

	def on_post_page(self, output: str, *, page, config) -> str:
		"""
		Handle the post page for the plugin.

		Args:
		    output (str): The output of the page
		    page (Page): The page to check
		    config (MkDocsConfig): The MkDocs configuration

		Returns:
		    str: The updated output
		"""
		# Inject the graph options script into the HTML page if graph is enabled
		if self._graph_handler:
			options_script = self._graph_handler.inject_graph_options(config)
			if "</body>" in output:
				return output.replace("</body>", f"{options_script}</body>")
		return output

	def on_post_build(self, *, config, **kwargs):
		"""
		Handle the post build for the plugin.

		Args:
		    config (MkDocsConfig): The MkDocs configuration
		    **kwargs: Additional keyword arguments

		Returns:
		    None
		"""
		self.logger.debug("Starting on_post_build event")
		if self._graph_handler:
			self._graph_handler.build_graph(self._files)
			self._graph_handler._write_graph_file(config)
			self._graph_handler.copy_static_assets(config)
			self.logger.debug("Static assets copied successfully")

	@event_priority(100)
	def on_files(self, files: Files, config: MkDocsConfig) -> Files | None:
		"""
		Handle the files for the plugin.

		Args:
		    files (Files): The files to check
		    config (MkDocsConfig): The MkDocs configuration

		Returns:
		    Files | None: The updated files
		"""
		if not self.plugin_enabled:
			self.logger.debug("MkDocs-Note plugin is disabled.")
			return files

		self.logger.info("Processing files for recent notes...")

		try:
			# Use FileScanner to scan note files
			file_scanner = NoteScanner(self.config, self.logger)
			note_files = file_scanner.scan_notes()

			if not note_files:
				self.logger.warning("No note files found")
				return files

			# Use NoteProcessor to process note files
			note_processor = NoteProcessor(self.config, self.logger)
			notes = []

			for file_path in note_files:
				note_info = note_processor.process_note(file_path)
				if note_info:
					notes.append(note_info)

			# Sort by modified time, get recent notes
			notes.sort(key=lambda n: n.modified_time, reverse=True)
			self._recent_notes = notes[: self.config.max_notes]

			self.logger.info(f"Found {len(self._recent_notes)} recent notes.")

		except Exception as e:
			self.logger.error(f"Error processing notes: {e}")

		return files

	def on_page_markdown(
		self, markdown: str, page: Page, config: MkDocsConfig, files: Files
	) -> str | None:
		"""Process page markdown content.

		Args:
		    markdown (str): The markdown content to process
		    page (Page): The page to check
		    config (MkDocsConfig): The MkDocs configuration
		    files (Files): The files to check

		Returns:
		    str | None: The updated markdown content
		"""
		if not self.plugin_enabled:
			self.logger.debug("MkDocs-Note plugin is disabled.")
			return markdown

		self.logger.debug(f"Processing page: {page.file.src_path}")

		# Process assets for note pages
		if self._is_note_page(page):
			self.logger.debug(f"Processing assets for note page: {page.file.src_path}")
			markdown = self._process_page_assets(markdown, page)
		else:
			self.logger.debug(
				f"Skipping asset processing for non-note page: {page.file.src_path}"
			)

		# Check if it is the index page of the notes directory
		if self._is_notes_index_page(page):
			self.logger.info(f"Found notes index page: {page.file.src_path}")
			markdown = self._insert_recent_notes(markdown)

		return markdown

	def _is_notes_index_page(self, page: Page) -> bool:
		"""Check if the page is the notes index page.

		Args:
		    page (Page): The page to check

		Returns:
		    bool: True if the page is the notes index page, False otherwise
		"""
		try:
			# Check if the page path matches the configured index file
			page_src_path = page.file.src_path
			index_file_path = str(self.config.index_file)

			# Convert absolute path to relative path from docs directory
			if index_file_path.startswith("/"):
				# It's an absolute path, extract the relative part
				if "docs/" in index_file_path:
					index_relative = index_file_path.split("docs/")[1]
				else:
					# Fallback: use the filename
					index_relative = Path(index_file_path).name
			else:
				# It's already a relative path
				if index_file_path.startswith("docs/"):
					index_relative = index_file_path[5:]  # Remove 'docs/' prefix
				else:
					index_relative = index_file_path

			is_match = page_src_path == index_relative
			self.logger.debug(
				f"Page matching: '{page_src_path}' == '{index_relative}' = {is_match}"
			)
			return is_match
		except Exception as e:
			self.logger.error(f"Error in page matching: {e}")
			return False

	def _insert_recent_notes(self, markdown: str) -> str:
		"""Insert recent notes list and network graph into markdown content.

		Args:
		    markdown (str): The markdown content to insert recent notes into

		Returns:
		    str: The updated markdown content
		"""
		if not self._recent_notes:
			return markdown

		# Generate HTML list for recent notes
		notes_html = self._generate_notes_html()

		# Generate network graph content if enabled
		graph_content = ""
		if self._network_graph_manager and self.config.enable_network_graph:
			graph_content = self._network_graph_manager.process_notes_for_graph(
				self._recent_notes
			)
			if graph_content:
				self.logger.info("Generated network graph content")

		# Combine notes and graph content
		combined_content = notes_html
		if graph_content:
			combined_content += "\n\n" + graph_content

		# Replace content between markers
		start_marker = self.config.start_marker
		end_marker = self.config.end_marker

		start_idx = markdown.find(start_marker)
		end_idx = markdown.find(end_marker)

		if start_idx == -1 or end_idx == -1:
			self.logger.warning(
				f"Markers not found in index file. Please add {start_marker} "
				f"and {end_marker} to enable recent notes insertion."
			)
			return markdown

		if end_idx <= start_idx:
			self.logger.error("End marker found before start marker")
			return markdown

		# Replace content
		start_pos = start_idx + len(start_marker)
		end_pos = end_idx

		updated_markdown = (
			markdown[:start_pos] + "\n" + combined_content + "\n" + markdown[end_pos:]
		)

		self.logger.info(
			f"Inserted {len(self._recent_notes)} recent notes into index page"
		)
		return updated_markdown

	def _generate_notes_html(self) -> str:
		"""Generate HTML list for recent notes.

		Returns:
		    str: The HTML list for recent notes
		"""
		items = []
		for note in self._recent_notes:
			items.append(
				f'<li><div style="display:flex; justify-content:space-between; align-items:center;">'
				f'<a href="{note.relative_url}">{note.title}</a>'
				f'<span style="font-size:0.8em; color:#666;">{note.modified_date}</span>'
				"</div></li>"
			)

		return "<ul>\n" + "\n".join(items) + "\n</ul>"

	def _is_note_page(self, page: Page) -> bool:
		"""Check if the page is a note page.

		Args:
		    page (Page): The page to check

		Returns:
		    bool: True if the page is a note page, False otherwise
		"""
		try:
			page_src_path = page.file.src_path

			# Get notes directory relative to docs_dir
			notes_dir = Path(self.config.notes_dir)
			if self._docs_dir and notes_dir.is_absolute():
				# Convert absolute notes_dir to relative path from docs_dir
				try:
					notes_relative = str(notes_dir.relative_to(self._docs_dir))
				except ValueError:
					# notes_dir is not under docs_dir, extract the relative part
					notes_relative = notes_dir.name
			else:
				# notes_dir is already relative
				notes_dir_str = str(notes_dir)
				if notes_dir_str.startswith("docs/"):
					notes_relative = notes_dir_str[5:]  # Remove 'docs/' prefix
				else:
					notes_relative = notes_dir_str

			# Handle the case where notes_dir is 'docs' (default)
			# In this case, all pages under docs are considered note pages
			self.logger.debug(
				f"notes_dir: '{notes_dir}', str(notes_dir): '{str(notes_dir)}'"
			)
			if (
				str(notes_dir) == "docs"
				or str(notes_dir) == "."
				or notes_dir.name == "docs"
			):
				# All pages are note pages except index.md files
				is_note_page = not page_src_path.endswith("index.md")
			else:
				# Check if the page path starts with the notes directory
				is_note_page = page_src_path.startswith(
					notes_relative
				) and not page_src_path.endswith("index.md")

			self.logger.debug(
				f"Note page check: '{page_src_path}' -> is_note_page = {is_note_page}"
			)
			return is_note_page
		except Exception as e:
			self.logger.error(f"Error in note page check: {e}")
			return False

	def _process_page_assets(self, markdown: str, page: Page) -> str:
		"""Process assets for a note page.

		Args:
		    markdown (str): The markdown content to process
		    page (Page): The page to process

		Returns:
		    str: The updated markdown content with processed asset paths
		"""
		try:
			# Get absolute path of the note file
			# page.file.src_path is relative to docs_dir
			if self._docs_dir:
				page_abs_path = self._docs_dir / page.file.src_path
			else:
				# Fallback to using src_path as is
				page_abs_path = Path(page.file.src_path)

			self.logger.debug(f"Processing assets for: {page_abs_path}")

			# Process assets in the markdown content
			updated_markdown = self._assets_processor.update_markdown_content(
				markdown, page_abs_path
			)

			if updated_markdown != markdown:
				self.logger.debug(f"Updated asset paths for page: {page.file.src_path}")
			else:
				self.logger.debug(
					f"No asset paths to update for page: {page.file.src_path}"
				)

			return updated_markdown
		except Exception as e:
			self.logger.error(
				f"Error processing assets for page {page.file.src_path}: {e}"
			)
			return markdown
