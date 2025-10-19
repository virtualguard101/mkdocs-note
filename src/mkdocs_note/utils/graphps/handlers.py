import os
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse
import importlib.resources

from mkdocs.config.defaults import MkDocsConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.graphps.graph import Graph

logger = Logger()


class GraphHandler:
	def __init__(self, config):
		self.config = config
		# Create graph configuration with necessary fields
		graph_config = {
			"name": "title",  # Use title as node name
			"debug": config.get("debug", False),
		}
		self._graph = Graph(graph_config)

	def add_static_resources(self, config: MkDocsConfig):
		"""Add static resources into mkdocs config for network graph."""
		# Use importlib.resources to get the correct path to static files
		try:
			# For Python 3.9+, use importlib.resources.files
			if hasattr(importlib.resources, "files"):
				static_package = importlib.resources.files(
					"mkdocs_note.utils.graphps.static"
				)
				# Convert to Path object for proper path handling
				# Handle MultiplexedPath objects by converting to string first
				if hasattr(static_package, "__fspath__"):
					self.static_dir = Path(static_package.__fspath__())
				else:
					self.static_dir = Path(str(static_package))
			else:
				# Fallback for older Python versions
				import pkg_resources

				self.static_dir = Path(
					pkg_resources.resource_filename(
						"mkdocs_note.utils.graphps", "static"
					)
				)
		except Exception as e:
			# Fallback to the old method if importlib.resources fails
			logger.warning(
				f"Failed to get static resources path using importlib.resources: {e}"
			)
			self.static_dir = Path(os.path.dirname(__file__)) / "static"

		config["extra_javascript"].append("https://d3js.org/d3.v7.min.js")

		if "js/graph.js" not in config["extra_javascript"]:
			config["extra_javascript"].append("js/graph.js")
		if "css/graph.css" not in config["extra_css"]:
			config["extra_css"].append("css/graph.css")

	def _write_graph_file(self, config):
		"""Write the graph data to a file."""
		logger.debug("Writing graph data to file...")
		output_dir = Path(config["site_dir"]) / "graph"
		output_dir.mkdir(parents=True, exist_ok=True)
		graph_file = output_dir / "graph.json"
		with open(graph_file, "w") as f:
			json.dump(self._graph.to_dict(), f)

	def inject_graph_options(self, config):
		"""Inject the graph options script into the HTML page."""
		site_url = config.get("site_url", "")
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
			f"    debug: {str(config.get('debug', False)).lower()},"
			f"    base_path: '{base_path}'"
			f"}};"
			"</script>"
		)
		return options_script

	def copy_static_assets(self, config):
		"""Copy static assets to the site directory."""
		logger.debug("Copying static assets...")
		try:
			# Copy JS
			js_output_dir = Path(config["site_dir"]) / "js"
			js_output_dir.mkdir(parents=True, exist_ok=True)
			shutil.copy(self.static_dir / "graph.js", js_output_dir)

			# Copy CSS
			css_output_dir = Path(config["site_dir"]) / "css"
			css_output_dir.mkdir(parents=True, exist_ok=True)
			shutil.copy(self.static_dir / "graph.css", css_output_dir)
		except (IOError, OSError) as e:
			logger.error(f"Error copying static assets: {e}")

	def build_graph(self, files):
		"""Build the graph from the file collection."""
		self._graph = self._graph(files)
		return self._graph
