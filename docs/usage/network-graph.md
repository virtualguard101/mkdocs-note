# Network Graph Visualization

The MkDocs Note plugin now includes an interactive network graph feature that visualizes the relationships between your notes. This feature helps you understand the structure and connections in your documentation.

## Overview

The network graph feature provides:

- **Interactive Visualization**: Drag, zoom, and explore your note relationships
- **Multiple Layout Algorithms**: Force-directed, hierarchical, and circular layouts
- **Smart Connections**: Automatic link generation based on keywords, hierarchy, and references
- **Customizable Appearance**: Theme integration with Material for MkDocs
- **Performance Optimized**: Efficient rendering for large note collections

## Configuration

### Basic Setup

To enable the network graph, add the following to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note:
      enable_network_graph: true
```

### Advanced Configuration

```yaml
plugins:
  - mkdocs-note:
      enable_network_graph: true
      graph_config:
        name: "title"              # Node naming: "title" or "file_name"
        debug: false              # Enable debug logging
        show_on_index: true       # Show graph on index page
        max_nodes: 100            # Maximum nodes to display
        layout: "force"           # Layout algorithm
        show_assets: false        # Include asset files as nodes
        link_threshold: 2         # Minimum shared keywords for links
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | `"title"` | Node naming strategy: `"title"` or `"file_name"` |
| `debug` | boolean | `false` | Enable debug logging for graph generation |
| `show_on_index` | boolean | `true` | Show graph on the notes index page |
| `max_nodes` | integer | `100` | Maximum number of nodes to display |
| `layout` | string | `"force"` | Graph layout algorithm: `"force"`, `"hierarchical"`, `"circular"` |
| `show_assets` | boolean | `false` | Include asset files as nodes in the graph |
| `link_threshold` | integer | `2` | Minimum number of shared keywords to create links |

## Usage

### Automatic Display

When enabled, the network graph automatically appears on your notes index page between the recent notes markers:

```markdown
<!-- recent_notes_start -->
<!-- Network graph will be inserted here -->
<!-- recent_notes_end -->
```

### CLI Commands

#### Generate Graph Data

```bash
# Generate graph data in JSON format
mkdocs-note graph

# Export to file
mkdocs-note graph --output graph.json

# Show statistics
mkdocs-note graph --stats

# Validate configuration
mkdocs-note graph --validate
```

#### Export Formats

```bash
# JSON format (default)
mkdocs-note graph --format json --output graph.json

# HTML format
mkdocs-note graph --format html --output graph.html

# Markdown format
mkdocs-note graph --format markdown --output graph.md
```

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

## Link Generation

The plugin automatically generates links between notes based on:

### 1. Hierarchical Relationships
- Notes in the same directory are connected
- Parent-child directory relationships

### 2. Keyword Similarity
- Shared keywords extracted from note titles
- Configurable threshold for minimum shared keywords

### 3. Reference Links (Future)
- Internal markdown links
- Tag-based connections
- Custom relationship definitions

## Performance Considerations

### Large Note Collections

For collections with many notes:

1. **Limit Node Count**: Use `max_nodes` to limit displayed nodes
2. **Disable Assets**: Set `show_assets: false` to reduce complexity
3. **Adjust Threshold**: Increase `link_threshold` to reduce connections

### Example for Large Collections

```yaml
plugins:
  - mkdocs-note:
      enable_network_graph: true
      graph_config:
        max_nodes: 50
        show_assets: false
        link_threshold: 3
        layout: "hierarchical"
```

## Troubleshooting

### Graph Not Appearing

1. **Check Configuration**: Ensure `enable_network_graph: true`
2. **Verify Markers**: Make sure index page has recent notes markers
3. **Check Logs**: Enable debug mode to see generation logs

```yaml
plugins:
  - mkdocs-note:
      enable_network_graph: true
      graph_config:
        debug: true
```

### Performance Issues

1. **Reduce Complexity**: Lower `max_nodes` and increase `link_threshold`
2. **Disable Assets**: Set `show_assets: false`
3. **Use Hierarchical Layout**: Set `layout: "hierarchical"`

### Browser Compatibility

The network graph requires:
- Modern browser with SVG support
- JavaScript enabled
- D3.js library (automatically included)

## Examples

### Basic Configuration

```yaml
# mkdocs.yml
site_name: My Notes
theme:
  name: material

plugins:
  - mkdocs-note:
      enable_network_graph: true
      notes_dir: "docs/notes"
      index_file: "docs/notes/index.md"
```

### Advanced Configuration

```yaml
# mkdocs.yml
plugins:
  - mkdocs-note:
      enable_network_graph: true
      graph_config:
        name: "file_name"
        max_nodes: 75
        layout: "hierarchical"
        show_assets: true
        link_threshold: 1
        debug: false
```

### Custom Styling

```css
/* extra.css */
:root {
  --md-graph-node-color: #e91e63;
  --md-graph-link-color: #9c27b0;
}

.network-graph-container {
  border: 2px solid var(--md-primary-fg-color);
  border-radius: 1rem;
  padding: 2rem;
}
```

## Integration with Other Features

The network graph works seamlessly with other plugin features:

- **Recent Notes**: Graph appears alongside recent notes list
- **Asset Management**: Can include asset files as nodes
- **Template System**: Respects note templates and frontmatter
- **CLI Tools**: Full CLI support for graph generation and export

## Future Enhancements

Planned features include:

- **Interactive Filtering**: Filter nodes by type, date, or keywords
- **Search Integration**: Highlight search results in the graph
- **Export Options**: PNG, SVG, and PDF export
- **Custom Relationships**: User-defined note connections
- **Real-time Updates**: Live graph updates during development
