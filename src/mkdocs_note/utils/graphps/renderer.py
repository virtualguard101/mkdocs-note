"""Graph rendering utilities."""

from __future__ import annotations

import json

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from .models import GraphData


class GraphRenderer:
	"""Renders graph data into various formats."""

	def __init__(self, config: PluginConfig, logger: Logger):
		"""Initialize the graph renderer.

		Args:
		    config: Plugin configuration
		    logger: Logger instance
		"""
		self.config = config
		self.logger = logger
		self.graph_config = config.graph_config

	def render_to_json(self, graph_data: GraphData) -> str:
		"""Render graph data to JSON format.

		Args:
		    graph_data: Graph data to render

		Returns:
		    str: JSON representation of the graph
		"""
		return json.dumps(graph_data.to_dict(), indent=2, ensure_ascii=False)

	def render_to_html(
		self, graph_data: GraphData, container_id: str = "network-graph"
	) -> str:
		"""Render graph data to HTML with embedded JavaScript.

		Args:
		    graph_data: Graph data to render
		    container_id: HTML container ID for the graph

		Returns:
		    str: HTML with embedded graph visualization
		"""
		json_data = self.render_to_json(graph_data)

		html_template = f"""
<div id="{container_id}" class="network-graph-container">
    <div class="graph-controls">
        <button id="reset-zoom" class="graph-button">Reset Zoom</button>
        <button id="toggle-labels" class="graph-button">Toggle Labels</button>
        <div class="graph-info">
            <span id="node-count">{len(graph_data.nodes)} nodes</span>
            <span id="link-count">{len(graph_data.links)} links</span>
        </div>
    </div>
    <svg id="graph-svg" class="graph-svg"></svg>
</div>

<script>
// Graph data
const graphData = {json_data};

// Initialize graph when DOM is ready
document.addEventListener('DOMContentLoaded', function() {{
    initializeNetworkGraph('{container_id}', graphData);
}});
</script>
"""
		return html_template

	def render_to_markdown(
		self, graph_data: GraphData, container_id: str = "network-graph"
	) -> str:
		"""Render graph data to markdown with HTML block.

		Args:
		    graph_data: Graph data to render
		    container_id: HTML container ID for the graph

		Returns:
		    str: Markdown with HTML block for the graph
		"""
		html_content = self.render_to_html(graph_data, container_id)

		markdown_template = f"""
## Network Graph

Interactive visualization of your notes and their relationships.

{html_content}

---
"""
		return markdown_template


class TemplateRenderer:
	"""Renders graph data using template system."""

	def __init__(self, config: PluginConfig, logger: Logger):
		"""Initialize the template renderer.

		Args:
		    config: Plugin configuration
		    logger: Logger instance
		"""
		self.config = config
		self.logger = logger
		self.graph_config = config.graph_config

	def render_graph_section(self, graph_data: GraphData) -> str:
		"""Render a complete graph section for insertion into markdown.

		Args:
		    graph_data: Graph data to render

		Returns:
		    str: Complete graph section in markdown format
		"""
		if not graph_data.nodes:
			return "<!-- No notes available for graph visualization -->"

		# Generate the graph HTML
		renderer = GraphRenderer(self.config, self.logger)
		graph_html = renderer.render_to_html(graph_data)

		# Wrap in markdown structure
		markdown_content = f"""
## 📊 Notes Network Graph

Explore the relationships between your notes through this interactive visualization.

{graph_html}

### Graph Statistics

- **Total Notes**: {len(graph_data.nodes)}
- **Total Connections**: {len(graph_data.links)}
- **Generated**: {graph_data.metadata.get("generated_at", "Unknown")}

---
"""
		return markdown_content

	def render_graph_placeholder(self) -> str:
		"""Render a placeholder when graph is disabled or no data available.

		Returns:
		    str: Placeholder content
		"""
		return """
<!-- Network graph placeholder -->
<!-- Enable network graph in plugin configuration to see interactive visualization -->
"""
