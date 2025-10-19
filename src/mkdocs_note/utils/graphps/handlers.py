import os
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

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
		self.static_dir = os.path.join(os.path.dirname(__file__), "static")

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
			js_output_dir = os.path.join(config["site_dir"], "js")
			os.makedirs(js_output_dir, exist_ok=True)
			shutil.copy(os.path.join(self.static_dir, "graph.js"), js_output_dir)

			# Copy CSS
			css_output_dir = os.path.join(config["site_dir"], "css")
			os.makedirs(css_output_dir, exist_ok=True)
			shutil.copy(os.path.join(self.static_dir, "graph.css"), css_output_dir)
		except (IOError, OSError) as e:
			logger.error(f"Error copying static assets: {e}")

	def build_graph(self, files):
		"""Build the graph from the file collection."""
		self._graph = self._graph(files)
		return self._graph
