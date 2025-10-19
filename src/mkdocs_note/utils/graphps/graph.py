"""Graph data structure and manipulation."""

import os
import re
from typing import Iterator, Optional
from urllib.parse import unquote, urlsplit
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_note.logger import Logger

log = Logger()


class Graph:
	"""Represents the connection graph between files."""

	LINK_PATTERN = r"\[[^\]]+\]\((?P<url>.*?)\)|\[\[(?P<wikilink>[^\]]+)\]\]"

	def __init__(self, config):
		"""Initializes the graph data structure."""
		if config.get("debug", False):
			log.setLevel("DEBUG")
		log.debug("Graph initialized")
		self.nodes = []
		self.edges = []
		self.config = config

	def _create_nodes(self, files: Files):
		"""Create nodes from the file collection."""
		log.debug("Creating nodes...")
		documentation_pages = list(files.documentation_pages())
		log.debug(f"Found {len(documentation_pages)} documentation pages")
		for file in documentation_pages:
			if file.page:
				name = self._get_name_from_config(file.page)
				self.nodes.append(
					{
						"id": file.src_path,
						"path": file.abs_src_path,
						"name": name,
						"url": file.url,
					},
				)
		log.info(f"Created {len(self.nodes)} nodes")

	def _get_name_from_config(self, page: Page) -> str:
		"""Return the name of the node based on the plugin configuration."""
		if self.config["name"] == "title":
			log.debug(f"Using 'title' for node name for page '{page.title}'")
			if "title" in page.meta:
				return str(page.meta["title"])
			if page.title is not None:
				return str(page.title)
		log.debug(f"Using 'file_name' for node name for page '{page.title}'")
		return page.file.name

	def _unescape_url(self, url: str) -> str:
		"""Unescape a URL."""
		# Strip angle brackets if present (for links like [text](<url>))
		if url.startswith("<") and url.endswith(">"):
			url = url[1:-1]
		return unquote(url)

	def _normalize_link(self, match: re.Match) -> Optional[str]:
		"""Normalize the URL from a regex match."""
		url = match.group("url") or match.group("wikilink")
		if not url:
			return None

		# For wikilinks, add the .md extension
		if match.group("wikilink") and not url.endswith(".md"):
			url += ".md"
		url = self._unescape_url(url)

		# Remove query and fragment from the URL
		url = urlsplit(url).path

		return url

	def _find_links(self, markdown: str, node_id: str, files: Files) -> Iterator[dict]:
		"""Find all links in a markdown string and yield resolved edges."""
		for match in re.finditer(self.LINK_PATTERN, markdown):
			url = self._normalize_link(match)
			if not url:
				continue

			target_path = os.path.normpath(os.path.join(os.path.dirname(node_id), url))

			# Check if the target is a node in the graph
			if any(node["id"] == target_path for node in self.nodes):
				yield {"source": node_id, "target": target_path}

	def _create_edges(self, files: Files):
		"""Create edges by parsing links from markdown files."""
		log.debug("Creating edges...")
		for node in self.nodes:
			log.debug(f"Parsing file {node['path']} for links")
			try:
				with open(node["path"], "r", encoding="utf-8") as f:
					markdown = f.read()
				self.edges.extend(self._find_links(markdown, node["id"], files))
			except FileNotFoundError:
				log.warning(f"File not found: {node['path']}")
				# This should not happen if the file is in the `files` collection
				pass
		log.info(f"Created {len(self.edges)} edges")

	def __call__(self, files: Files):
		"""Build the graph from the file collection."""
		log.info("Building graph...")
		self._create_nodes(files)
		self._create_edges(files)
		return self

	def to_dict(self):
		"""Return the graph as a dictionary."""
		return {"nodes": self.nodes, "edges": self.edges}
