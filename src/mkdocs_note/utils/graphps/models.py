"""Data models for network graph visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class GraphNode:
	"""Represents a node in the network graph."""

	id: str
	"""Unique identifier for the node."""

	label: str
	"""Display label for the node."""

	url: str
	"""URL to the note page."""

	file_path: Path
	"""Path to the note file."""

	node_type: str = "note"
	"""Type of node: 'note', 'asset', 'index'."""

	size: int = 1
	"""Node size for visualization."""

	color: str = "#1976d2"
	"""Node color for visualization."""

	metadata: Dict[str, Any] = field(default_factory=dict)
	"""Additional metadata for the node."""


@dataclass
class GraphLink:
	"""Represents a link between nodes in the network graph."""

	source: str
	"""Source node ID."""

	target: str
	"""Target node ID."""

	weight: float = 1.0
	"""Link weight/strength."""

	link_type: str = "reference"
	"""Type of link: 'reference', 'keyword', 'hierarchical'."""

	metadata: Dict[str, Any] = field(default_factory=dict)
	"""Additional metadata for the link."""


@dataclass
class GraphData:
	"""Complete graph data structure."""

	nodes: List[GraphNode]
	"""List of all nodes in the graph."""

	links: List[GraphLink]
	"""List of all links in the graph."""

	metadata: Dict[str, Any] = field(default_factory=dict)
	"""Graph-level metadata."""

	def to_dict(self) -> Dict[str, Any]:
		"""Convert graph data to dictionary format for JSON serialization."""
		return {
			"nodes": [
				{
					"id": node.id,
					"label": node.label,
					"url": node.url,
					"file_path": str(node.file_path),
					"node_type": node.node_type,
					"size": node.size,
					"color": node.color,
					"metadata": node.metadata,
				}
				for node in self.nodes
			],
			"links": [
				{
					"source": link.source,
					"target": link.target,
					"weight": link.weight,
					"link_type": link.link_type,
					"metadata": link.metadata,
				}
				for link in self.links
			],
			"metadata": self.metadata,
		}

	def get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
		"""Get a node by its ID."""
		for node in self.nodes:
			if node.id == node_id:
				return node
		return None

	def get_links_for_node(self, node_id: str) -> List[GraphLink]:
		"""Get all links connected to a specific node."""
		return [
			link
			for link in self.links
			if link.source == node_id or link.target == node_id
		]

	def add_node(self, node: GraphNode) -> None:
		"""Add a node to the graph."""
		if not any(n.id == node.id for n in self.nodes):
			self.nodes.append(node)

	def add_link(self, link: GraphLink) -> None:
		"""Add a link to the graph."""
		if not any(
			existing_link.source == link.source and existing_link.target == link.target 
			for existing_link in self.links
		):
			self.links.append(link)
