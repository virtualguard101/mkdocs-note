"""Graph data structure and manipulation.

Migrated from [mkdocs-network-graph-plugin](https://github.com/develmusa/mkdocs-network-graph-plugin/blob/main/src/mkdocs_graph_plugin/graph.py).
"""

import os
import re
import shutil
from typing import Iterator, Optional
from urllib.parse import unquote, urlsplit, urlparse

from mkdocs.plugins import get_plugin_logger
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

logger = get_plugin_logger(__name__)


class Graph:
	"""Represents the connection graph between files."""

	LINK_PATTERN = r"\[[^\]]+\]\((?P<url>.*?)\)|\[\[(?P<wikilink>[^\]]+)\]\]"

	def __init__(self, config):
		"""Initializes the graph data structure."""
		if config.get("debug", False):
			logger.setLevel("DEBUG")
		logger.debug("Graph initialized")
		self.nodes = []
		self.edges = []
		self.config = config

	def _create_nodes(self, files: Files):
		"""Create nodes from the file collection."""
		logger.debug("Creating nodes...")
		documentation_pages = list(files.documentation_pages())
		logger.debug(f"Found {len(documentation_pages)} documentation pages")
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
		logger.info(f"Created {len(self.nodes)} nodes")

	def _get_name_from_config(self, page: Page) -> str:
		"""Return the name of the node based on the plugin configuration."""
		if self.config["name"] == "title":
			logger.debug(f"Using 'title' for node name for page '{page.title}'")
			if "title" in page.meta:
				return str(page.meta["title"])
			if page.title is not None:
				return str(page.title)
		logger.debug(f"Using 'file_name' for node name for page '{page.title}'")
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
		logger.debug("Creating edges...")
		for node in self.nodes:
			logger.debug(f"Parsing file {node['path']} for links")
			try:
				with open(node["path"], "r", encoding="utf-8") as f:
					markdown = f.read()
				self.edges.extend(self._find_links(markdown, node["id"], files))
			except FileNotFoundError:
				logger.warning(f"File not found: {node['path']}")
				# This should not happen if the file is in the `files` collection
				pass
		logger.info(f"Created {len(self.edges)} edges")

	def __call__(self, files: Files):
		"""Build the graph from the file collection."""
		logger.info("Building graph...")
		self._create_nodes(files)
		self._create_edges(files)
		return self

	def to_dict(self):
		"""Return the graph as a dictionary."""
		return {"nodes": self.nodes, "edges": self.edges}


def add_static_resouces(config: MkDocsConfig) -> None:
	"""Add static resources into mkdocs config for network graph.

	Args:
		config (MkDocsConfig): The MkDocs configuration.
	"""
	config["extra_javascript"].append("https://d3js.org/d3.v7.min.js")

	if "js/graph.js" not in config["extra_javascript"]:
		config["extra_javascript"].append("js/graph.js")
	if "css/graph.css" not in config["extra_css"]:
		config["extra_css"].append("css/graph.css")


def inject_graph_script(output: str, config: MkDocsConfig, debug: bool = False) -> str:
	"""Inject the graph script into the HTML page.

	Args:
		output (str): The HTML output.
		config (MkDocsConfig): The MkDocs configuration.
		debug (bool): Whether to enable debug mode.

	Returns:
		str: The HTML with the graph script injected.
	"""
	site_url = config.get("site_url")
	if site_url:
		base_path = urlparse(site_url).path
		# Ensure base_path ends with a slash
		if not base_path.endswith("/"):
			base_path += "/"
	else:
		base_path = "/"

	options_script = (
		"<script>"
		f"window.graph_options = {{"
		f"    debug: {str(debug).lower()},"
		f"    base_path: '{base_path}'"
		f"}};"
		"</script>"
	)
	if "</body>" in output:
		return output.replace("</body>", f"{options_script}</body>")
	return output


def copy_static_assets(static_dir: str, config: MkDocsConfig) -> None:
	"""Copy static assets into the site directory.

	Args:
		config (MkDocsConfig): The MkDocs configuration.
	"""
	# Copy JS
	js_output_dir = os.path.join(config["site_dir"], "js")
	os.makedirs(js_output_dir, exist_ok=True)
	shutil.copy(os.path.join(static_dir, "graph.js"), js_output_dir)

	# Copy CSS
	css_output_dir = os.path.join(config["site_dir"], "css")
	os.makedirs(css_output_dir, exist_ok=True)
	shutil.copy(os.path.join(static_dir, "graph.css"), css_output_dir)
