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

## Link Generation

The plugin automatically generates links between notes based on:

### 1. Markdown Links
- Standard markdown links: `[link text](target.md)`
- Relative path resolution from note location
- Automatic detection of internal documentation links

### 2. Wiki-style Links
- Wiki-style links: `[[target]]` or `[[target.md]]`
- Automatic `.md` extension addition when needed
- Path normalization and resolution

### 3. Link Processing
- Links are normalized and resolved relative to the source note
- Only links to other documentation pages are included
- External links and anchors are filtered out

## Performance Considerations

### Large Note Collections

The network graph automatically handles large collections by:

1. **Efficient Processing**: Only processes documentation pages, excluding assets and other files
2. **Link Filtering**: Automatically filters out external links and invalid references
3. **Memory Optimization**: Uses efficient data structures for node and edge storage

### Build Performance

The graph generation is integrated into the MkDocs build process and:

- Runs during the `on_post_build` event
- Processes only changed files (when using `--dirty` builds)
- Generates graph data in parallel with other build tasks

## Troubleshooting

### Graph Not Appearing

1. **Check Configuration**: Ensure `enable_network_graph: true` is set
2. **Verify Build Logs**: Check for errors during the build process
3. **Enable Debug Mode**: Set `debug: true` to see detailed generation logs

```yaml
plugins:
  - mkdocs-note:
      enable_network_graph: true
      graph_config:
        debug: true
```

### Missing Graph Files

If graph files are not generated:

1. **Check File Permissions**: Ensure the plugin can write to the site directory
2. **Verify Static Resources**: Check that CSS and JS files are copied correctly
3. **Review Build Output**: Look for error messages in the build log

### Browser Compatibility

The network graph requires:
- Modern browser with SVG support
- JavaScript enabled
- D3.js library (automatically included via CDN)

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
        name: "file_name"  # Use filename instead of title
        debug: false       # Disable debug logging
```

### Graph Data Structure

The generated `graph.json` file contains:

```json
{
  "nodes": [
    {
      "id": "getting-started.md",
      "path": "/path/to/getting-started.md",
      "name": "Getting Started",
      "url": "getting-started/"
    }
  ],
  "edges": [
    {
      "source": "getting-started.md",
      "target": "installation.md"
    }
  ]
}
```

## Integration with Other Features

The network graph works seamlessly with other plugin features:

- **Recent Notes**: Integrates with the existing recent notes functionality
- **Asset Management**: Respects the plugin's asset handling
- **Template System**: Works with note templates and frontmatter
- **Build Process**: Automatically generates during MkDocs build

## Technical Details

### Implementation

The network graph feature is implemented using:

- **Backend**: Python-based graph generation and data processing
- **Frontend**: D3.js for interactive visualization
- **Integration**: MkDocs plugin hooks for seamless integration
- **Architecture**: Modular design following the plugin's `graphps` pattern

### File Structure

```
src/mkdocs_note/
├── utils/graphps/
│   ├── __init__.py
│   ├── graph.py          # Graph data structure and processing
│   └── handlers.py       # Graph handler for plugin integration
└── static/
    ├── js/graph.js       # Frontend visualization
    └── stylesheet/graph.css  # Graph styling
```
