---
date: 2025-11-05 00:00:00
title: Network Graph Visualization
permalink: 
publish: true
---

# Network Graph Visualization

The MkDocs Note plugin includes an interactive network graph feature that visualizes the relationships between your notes. This feature helps you understand the structure and connections in your documentation.

## Overview

The network graph feature provides:

- **Interactive Visualization**: Drag, zoom, and explore your note relationships using D3.js
- **Automatic Link Detection**: Finds connections between notes based on markdown links and wiki-style links
- **Theme Integration**: Seamlessly integrates with Material for MkDocs theme
- **Real-time Generation**: Automatically generates graph data during the build process
- **Export Capabilities**: Export graph data in JSON format for further analysis

## Configuration

### Basic Setup

To enable the network graph, add the following to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note:
      graph_config:
        enabled: true
```

### Advanced Configuration

```yaml
plugins:
  - mkdocs-note:
      graph_config:
        enabled: true
        name: "title"              # Node naming: "title" or "file_name"
        debug: false              # Enable debug logging
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | `"title"` | Node naming strategy: `"title"` uses page title, `"file_name"` uses filename |
| `debug` | boolean | `false` | Enable debug logging for graph generation |

## Usage

### Automatic Display

When enabled, the network graph automatically appears on your notes index page. The graph is generated during the MkDocs build process and includes:

1. **Interactive Graph**: Visual representation of note relationships

2. **Graph Data**: JSON file containing nodes and edges information

3. **Static Assets**: CSS and JavaScript files for rendering

### Generated Files

When you build your documentation, the plugin creates:

- `site/graph/graph.json` - Graph data in JSON format

- `site/js/graph.js` - Interactive graph visualization script

- `site/css/graph.css` - Graph styling

### Integration

The network graph integrates with the existing recent notes feature and appears automatically when:

1. `enable_network_graph: true` is set in configuration

2. The plugin processes your documentation files

3. Links between notes are detected and visualized

## Customization

### CSS Variables

Customize the graph appearance using CSS variables in your `extra.css`:

```css
:root {
  /* Node colors */
  --md-graph-node-color: #1976d2;
  --md-graph-node-color--hover: #1565c0;
  --md-graph-node-color--current: #ff5722;
  --md-graph-node-color--asset: #757575;
  
  /* Link colors */
  --md-graph-link-color: #757575;
  --md-graph-link-color--hover: #424242;
  
  /* Text colors */
  --md-graph-text-color: #212121;
  --md-graph-text-color--light: #666666;
}
```

### Custom Styling

Override specific graph elements:

```css
/* Customize node appearance */
.graph-svg .nodes circle {
  stroke-width: 3px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

/* Customize link appearance */
.graph-svg .links line {
  stroke-width: 3px;
  stroke-dasharray: 5,5;
}

/* Customize labels */
.graph-svg .labels text {
  font-weight: bold;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}
```

## References

> [Credits](../about/credits.md)

Thanks to the original author of the [MkDocs Network Graph Plugin](https://github.com/develmusa/mkdocs-network-graph-plugin) for the inspiration and the underlying engine.
