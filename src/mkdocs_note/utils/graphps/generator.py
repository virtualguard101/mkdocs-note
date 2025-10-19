"""Graph data generation utilities."""

from __future__ import annotations

import re
from typing import List, Dict, Set

from mkdocs_note.utils.dataps.meta import NoteInfo
from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from .models import GraphNode, GraphLink, GraphData


class GraphDataGenerator:
	"""Generates graph data from note information."""

	def __init__(self, config: PluginConfig, logger: Logger):
		"""Initialize the graph data generator.

		Args:
		    config: Plugin configuration
		    logger: Logger instance
		"""
		self.config = config
		self.logger = logger
		self.graph_config = config.graph_config

	def generate_graph_data(self, notes: List[NoteInfo]) -> GraphData:
		"""Generate complete graph data from notes.

		Args:
		    notes: List of note information

		Returns:
		    GraphData: Complete graph data structure
		"""
		self.logger.debug(f"Generating graph data for {len(notes)} notes")

		# Limit number of nodes if configured
		max_nodes = self.graph_config.get("max_nodes", 100)
		if len(notes) > max_nodes:
			notes = notes[:max_nodes]
			self.logger.debug(f"Limited to {max_nodes} nodes")

		# Generate nodes
		nodes = self._generate_nodes(notes)

		# Generate links
		links = self._generate_links(notes, nodes)

		# Create graph data
		graph_data = GraphData(
			nodes=nodes,
			links=links,
			metadata={
				"total_notes": len(notes),
				"total_nodes": len(nodes),
				"total_links": len(links),
				"generated_at": self._get_timestamp(),
			},
		)

		self.logger.debug(
			f"Generated graph with {len(nodes)} nodes and {len(links)} links"
		)
		return graph_data

	def _generate_nodes(self, notes: List[NoteInfo]) -> List[GraphNode]:
		"""Generate nodes from notes.

		Args:
		    notes: List of note information

		Returns:
		    List[GraphNode]: Generated nodes
		"""
		nodes = []

		for note in notes:
			# Determine node label based on configuration
			name_strategy = self.graph_config.get("name", "title")
			if name_strategy == "file_name":
				label = note.file_path.stem
			else:
				label = note.title

			# Create node
			node = GraphNode(
				id=self._generate_node_id(note),
				label=label,
				url=note.relative_url,
				file_path=note.file_path,
				node_type="note",
				size=self._calculate_node_size(note),
				color=self._get_node_color(note),
				metadata={
					"title": note.title,
					"modified_date": note.modified_date,
					"file_size": note.file_size,
					"assets_count": len(note.assets_list),
				},
			)
			nodes.append(node)

			# Add asset nodes if configured
			if self.graph_config.get("show_assets", False):
				asset_nodes = self._generate_asset_nodes(note)
				nodes.extend(asset_nodes)

		return nodes

	def _generate_links(
		self, notes: List[NoteInfo], nodes: List[GraphNode]
	) -> List[GraphLink]:
		"""Generate links between nodes.

		Args:
		    notes: List of note information
		    nodes: List of generated nodes

		Returns:
		    List[GraphLink]: Generated links
		"""
		links = []

		# Create node lookup for efficient access
		node_lookup = {node.id: node for node in nodes}

		# Generate links based on different strategies
		links.extend(self._generate_hierarchical_links(notes, node_lookup))
		links.extend(self._generate_keyword_links(notes, node_lookup))
		links.extend(self._generate_reference_links(notes, node_lookup))

		return links

	def _generate_hierarchical_links(
		self, notes: List[NoteInfo], node_lookup: Dict[str, GraphNode]
	) -> List[GraphLink]:
		"""Generate hierarchical links based on directory structure.

		Args:
		    notes: List of note information
		    node_lookup: Dictionary mapping node IDs to nodes

		Returns:
		    List[GraphLink]: Hierarchical links
		"""
		links = []

		# Group notes by directory
		dir_groups = {}
		for note in notes:
			parent_dir = note.file_path.parent
			if parent_dir not in dir_groups:
				dir_groups[parent_dir] = []
			dir_groups[parent_dir].append(note)

		# Create links between notes in the same directory
		for dir_path, dir_notes in dir_groups.items():
			if len(dir_notes) > 1:
				for i, note1 in enumerate(dir_notes):
					for note2 in dir_notes[i + 1 :]:
						node1_id = self._generate_node_id(note1)
						node2_id = self._generate_node_id(note2)

						if node1_id in node_lookup and node2_id in node_lookup:
							link = GraphLink(
								source=node1_id,
								target=node2_id,
								weight=0.5,
								link_type="hierarchical",
								metadata={"directory": str(dir_path)},
							)
							links.append(link)

		return links

	def _generate_keyword_links(
		self, notes: List[NoteInfo], node_lookup: Dict[str, GraphNode]
	) -> List[GraphLink]:
		"""Generate links based on shared keywords.

		Args:
		    notes: List of note information
		    node_lookup: Dictionary mapping node IDs to nodes

		Returns:
		    List[GraphLink]: Keyword-based links
		"""
		links = []
		threshold = self.graph_config.get("link_threshold", 2)

		# Extract keywords from each note
		note_keywords = {}
		for note in notes:
			keywords = self._extract_keywords(note)
			note_keywords[self._generate_node_id(note)] = keywords

		# Find shared keywords and create links
		node_ids = list(note_keywords.keys())
		for i, node1_id in enumerate(node_ids):
			for node2_id in node_ids[i + 1 :]:
				shared_keywords = note_keywords[node1_id] & note_keywords[node2_id]
				if len(shared_keywords) >= threshold:
					weight = len(shared_keywords) / max(
						len(note_keywords[node1_id]), len(note_keywords[node2_id])
					)

					link = GraphLink(
						source=node1_id,
						target=node2_id,
						weight=weight,
						link_type="keyword",
						metadata={"shared_keywords": list(shared_keywords)},
					)
					links.append(link)

		return links

	def _generate_reference_links(
		self, notes: List[NoteInfo], node_lookup: Dict[str, GraphNode]
	) -> List[GraphLink]:
		"""Generate links based on markdown references.

		Args:
		    notes: List of note information
		    node_lookup: Dictionary mapping node IDs to nodes

		Returns:
		    List[GraphLink]: Reference-based links
		"""
		links = []

		# This is a placeholder for future implementation
		# Could analyze markdown content for internal links, tags, etc.

		return links

	def _generate_asset_nodes(self, note: NoteInfo) -> List[GraphNode]:
		"""Generate nodes for asset files.

		Args:
		    note: Note information

		Returns:
		    List[GraphNode]: Asset nodes
		"""
		asset_nodes = []

		for asset in note.assets_list:
			if asset.exists:
				asset_node = GraphNode(
					id=f"{self._generate_node_id(note)}_asset_{asset.index_in_list}",
					label=asset.file_name,
					url=f"{note.relative_url}#assets",
					file_path=asset.file_path,
					node_type="asset",
					size=0.5,
					color="#757575",
					metadata={
						"parent_note": note.title,
						"asset_index": asset.index_in_list,
					},
				)
				asset_nodes.append(asset_node)

		return asset_nodes

	def _generate_node_id(self, note: NoteInfo) -> str:
		"""Generate a unique node ID for a note.

		Args:
		    note: Note information

		Returns:
		    str: Unique node ID
		"""
		# Use relative path as ID, replacing path separators with underscores
		relative_path = str(note.file_path.relative_to(self.config.notes_dir))
		return (
			relative_path.replace("/", "_")
			.replace("\\", "_")
			.replace(".md", "")
			.replace(".ipynb", "")
		)

	def _calculate_node_size(self, note: NoteInfo) -> int:
		"""Calculate node size based on note properties.

		Args:
		    note: Note information

		Returns:
		    int: Node size
		"""
		# Base size
		size = 1

		# Increase size based on file size
		if note.file_size > 10000:  # 10KB
			size += 1
		if note.file_size > 50000:  # 50KB
			size += 1

		# Increase size based on number of assets
		if len(note.assets_list) > 5:
			size += 1
		if len(note.assets_list) > 10:
			size += 1

		return min(size, 5)  # Cap at 5

	def _get_node_color(self, note: NoteInfo) -> str:
		"""Get node color based on note properties.

		Args:
		    note: Note information

		Returns:
		    str: Node color
		"""
		# Default color
		return "#1976d2"

	def _extract_keywords(self, note: NoteInfo) -> Set[str]:
		"""Extract keywords from note title and content.

		Args:
		    note: Note information

		Returns:
		    Set[str]: Extracted keywords
		"""
		keywords = set()

		# Extract from title
		title_words = re.findall(r"\b\w+\b", note.title.lower())
		keywords.update(word for word in title_words if len(word) > 3)

		# Could also extract from file content in the future
		# For now, just use title-based keywords

		return keywords

	def _get_timestamp(self) -> str:
		"""Get current timestamp for metadata.

		Returns:
		    str: Current timestamp
		"""
		from datetime import datetime

		return datetime.now().isoformat()


class NodeLinkBuilder:
	"""Utility class for building node-link relationships."""

	@staticmethod
	def build_force_layout_data(graph_data: GraphData) -> Dict[str, any]:
		"""Build data structure optimized for D3.js force layout.

		Args:
		    graph_data: Complete graph data

		Returns:
		    Dict: Data structure for D3.js force layout
		"""
		return {
			"nodes": [
				{
					"id": node.id,
					"label": node.label,
					"url": node.url,
					"node_type": node.node_type,
					"size": node.size,
					"color": node.color,
					"metadata": node.metadata,
				}
				for node in graph_data.nodes
			],
			"links": [
				{
					"source": link.source,
					"target": link.target,
					"weight": link.weight,
					"link_type": link.link_type,
					"metadata": link.metadata,
				}
				for link in graph_data.links
			],
			"metadata": graph_data.metadata,
		}
