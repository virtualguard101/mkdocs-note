"""Core graph processing handlers."""

from __future__ import annotations

from typing import List, Optional

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.dataps.meta import NoteInfo
from .generator import GraphDataGenerator
from .renderer import GraphRenderer, TemplateRenderer
from .models import GraphData


class GraphProcessor:
	"""Main processor for graph generation and rendering."""

	def __init__(self, config: PluginConfig, logger: Logger):
		"""Initialize the graph processor.

		Args:
		    config: Plugin configuration
		    logger: Logger instance
		"""
		self.config = config
		self.logger = logger
		self.graph_config = config.graph_config

		# Initialize components
		self.data_generator = GraphDataGenerator(config, logger)
		self.renderer = GraphRenderer(config, logger)
		self.template_renderer = TemplateRenderer(config, logger)

		# Cache for generated graph data
		self._cached_graph_data: Optional[GraphData] = None
		self._last_notes_hash: Optional[str] = None

	def is_enabled(self) -> bool:
		"""Check if network graph is enabled.

		Returns:
		    bool: True if network graph is enabled
		"""
		return self.config.enabled and self.config.enable_network_graph

	def should_generate_graph(self, notes: List[NoteInfo]) -> bool:
		"""Check if graph should be generated based on configuration and data.

		Args:
		    notes: List of note information

		Returns:
		    bool: True if graph should be generated
		"""
		if not self.is_enabled():
			return False

		if not notes:
			self.logger.debug("No notes available for graph generation")
			return False

		# Check if we have enough notes to make a meaningful graph
		min_notes = 2
		if len(notes) < min_notes:
			self.logger.debug(
				f"Not enough notes for graph ({len(notes)} < {min_notes})"
			)
			return False

		return True

	def generate_graph_data(self, notes: List[NoteInfo]) -> Optional[GraphData]:
		"""Generate graph data from notes.

		Args:
		    notes: List of note information

		Returns:
		    Optional[GraphData]: Generated graph data or None if not applicable
		"""
		if not self.should_generate_graph(notes):
			return None

		try:
			# Check if we can use cached data
			current_hash = self._calculate_notes_hash(notes)
			if (
				self._cached_graph_data is not None
				and self._last_notes_hash == current_hash
			):
				self.logger.debug("Using cached graph data")
				return self._cached_graph_data

			# Generate new graph data
			self.logger.info("Generating network graph data")
			graph_data = self.data_generator.generate_graph_data(notes)

			# Cache the result
			self._cached_graph_data = graph_data
			self._last_notes_hash = current_hash

			return graph_data

		except Exception as e:
			self.logger.error(f"Error generating graph data: {e}")
			return None

	def render_graph_for_page(
		self, graph_data: GraphData, page_type: str = "index"
	) -> str:
		"""Render graph for a specific page type.

		Args:
		    graph_data: Graph data to render
		    page_type: Type of page ("index", "note", etc.)

		Returns:
		    str: Rendered graph content
		"""
		if not graph_data:
			return self.template_renderer.render_graph_placeholder()

		try:
			if page_type == "index" and self.graph_config.get("show_on_index", True):
				return self.template_renderer.render_graph_section(graph_data)
			else:
				# For other page types, return minimal representation
				return f"<!-- Graph available with {len(graph_data.nodes)} nodes -->"

		except Exception as e:
			self.logger.error(f"Error rendering graph: {e}")
			return "<!-- Error rendering graph -->"

	def get_graph_json(self, graph_data: GraphData) -> Optional[str]:
		"""Get graph data as JSON string.

		Args:
		    graph_data: Graph data to convert

		Returns:
		    Optional[str]: JSON representation or None if error
		"""
		if not graph_data:
			return None

		try:
			return self.renderer.render_to_json(graph_data)
		except Exception as e:
			self.logger.error(f"Error converting graph to JSON: {e}")
			return None

	def _calculate_notes_hash(self, notes: List[NoteInfo]) -> str:
		"""Calculate hash of notes for caching purposes.

		Args:
		    notes: List of note information

		Returns:
		    str: Hash of the notes
		"""
		import hashlib

		# Create a string representation of the notes
		notes_str = ""
		for note in notes:
			notes_str += f"{note.file_path}:{note.modified_time}:{note.file_size}"

		# Calculate hash
		return hashlib.md5(notes_str.encode()).hexdigest()


class NetworkGraphManager:
	"""High-level manager for network graph functionality."""

	def __init__(self, config: PluginConfig, logger: Logger):
		"""Initialize the network graph manager.

		Args:
		    config: Plugin configuration
		    logger: Logger instance
		"""
		self.config = config
		self.logger = logger
		self.processor = GraphProcessor(config, logger)

	def process_notes_for_graph(self, notes: List[NoteInfo]) -> Optional[str]:
		"""Process notes and return graph content for insertion.

		Args:
		    notes: List of note information

		Returns:
		    Optional[str]: Graph content to insert or None if not applicable
		"""
		if not self.processor.is_enabled():
			return None

		# Generate graph data
		graph_data = self.processor.generate_graph_data(notes)
		if not graph_data:
			return None

		# Render for index page
		return self.processor.render_graph_for_page(graph_data, "index")

	def get_graph_statistics(self, notes: List[NoteInfo]) -> dict:
		"""Get statistics about the graph.

		Args:
		    notes: List of note information

		Returns:
		    dict: Graph statistics
		"""
		if not self.processor.is_enabled():
			return {"enabled": False}

		graph_data = self.processor.generate_graph_data(notes)
		if not graph_data:
			return {"enabled": True, "available": False}

		return {
			"enabled": True,
			"available": True,
			"nodes": len(graph_data.nodes),
			"links": len(graph_data.links),
			"metadata": graph_data.metadata,
		}

	def validate_configuration(self) -> List[str]:
		"""Validate graph configuration and return any issues.

		Returns:
		    List[str]: List of configuration issues (empty if valid)
		"""
		issues = []

		if not self.config.enable_network_graph:
			return issues  # No issues if disabled

		# Validate graph configuration
		graph_config = self.config.graph_config

		# Check max_nodes
		max_nodes = graph_config.get("max_nodes", 100)
		if not isinstance(max_nodes, int) or max_nodes < 1:
			issues.append("max_nodes must be a positive integer")

		# Check layout
		valid_layouts = ["force", "hierarchical", "circular"]
		layout = graph_config.get("layout", "force")
		if layout not in valid_layouts:
			issues.append(f"layout must be one of: {', '.join(valid_layouts)}")

		# Check name strategy
		valid_names = ["title", "file_name"]
		name = graph_config.get("name", "title")
		if name not in valid_names:
			issues.append(f"name must be one of: {', '.join(valid_names)}")

		return issues
