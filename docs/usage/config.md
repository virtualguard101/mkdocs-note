---
date: 2025-10-17 11:19:45
title: Configuration Options
permalink: 
publish: true
---

# Configuration Options

`mkdocs-note` provides a flexible way to configure the plugin's behavior. You can configure the plugin's behavior by configuring the `mkdocs.yml` file.

## Overview

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable the plugin |
| `notes_dir` | Path | `"docs"` | Directory containing your notes |
| `index_file` | Path | `"docs/index.md"` | Index file where recent notes will be displayed |
| `max_notes` | int | `10` | Maximum number of recent notes to display (including index page, but display not including the index page itself) |
| `start_marker` | str | `"<!-- recent_notes_start -->"` | Start marker for notes insertion |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | End marker for notes insertion |
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | File extensions to include as notes |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | File name patterns to exclude from plugin management (within `notes_dir` scope). Excluded files cannot be created, scanned, listed, moved, or managed by the asset system |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | Directory names to exclude from note scanning |
| `use_git_timestamps` | bool | `true` | Use Git commit timestamps for sorting instead of file system timestamps |
| `timestamp_zone` | str | `"UTC+0"` | Timezone for timestamp display (e.g., 'UTC+0', 'UTC+8', 'UTC-5'). Ensures consistent timestamp display across different deployment environments |
| `assets_dir` | Path | `"docs/notes/assets"` | Directory for storing note assets. Uses tree-based structure with `.assets` suffix on first-level subdirectories |
| `enable_asset_fallback` | bool | `true` | Whether to fallback to original asset paths when assets with processed uri are not found. When enabled, if a processed asset file doesn't exist, the original asset path will be preserved instead of being replaced |
| `notes_template` | Path | `"overrides/templates/default.md"` | Template file for new notes. Supports variables: `{{title}}`, `{{date}}`, `{{note_name}}` |
| `cache_size` | int | `256` | Size of the cache for performance optimization |
| `enable_network_graph` | bool | `false` | Enable or disable the network graph |
| `graph_config` | dict | `{"name": "title", "debug": false}` | Configuration for the network graph visualization. Available options: `name`: Node naming strategy ("title" or "file_name"), `debug`: Enable debug logging for graph generation |

## Configuration Options Details

### Basic Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable the plugin |
| `notes_dir` | Path | `"docs"` | Directory containing your notes |
| `index_file` | Path | `"docs/index.md"` | Index file where recent notes will be displayed |
| `max_notes` | int | `10` | Maximum number of recent notes to display (including index page, but display not including the index page itself) |

### Marker Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `start_marker` | str | `"<!-- recent_notes_start -->"` | Start marker for notes insertion |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | End marker for notes insertion |

### File Filter Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | File extensions to include as notes |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | File name patterns to exclude from plugin management (within `notes_dir` scope). Excluded files cannot be created, scanned, listed, moved, or managed by the asset system |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | Directory names to exclude from note scanning |

### Timestamp Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `use_git_timestamps` | bool | `true` | Use Git commit timestamps for sorting instead of file system timestamps |
| `timestamp_zone` | str | `"UTC+0"` | Timezone for timestamp display (e.g., 'UTC+0', 'UTC+8', 'UTC-5'). Ensures consistent timestamp display across different deployment environments |

#### Important Notes for CI/CD Deployment

When using `use_git_timestamps: true` (default), ensure your CI/CD environment fetches the full Git history. Most CI/CD platforms (Vercel, GitHub Actions, GitLab CI, etc.) use shallow clones by default, which can cause inconsistent timestamps.

**For Vercel:**

Update your build script to fetch full git history:

```bash
#!/bin/bash

# Unshallow the git repository to get full commit history
if [ -d .git ]; then
    echo "Fetching full git history..."
    git fetch --unshallow || echo "Repository is already complete"
    git fetch --all
fi

# Your build command
mkdocs build
```

**For GitHub Actions:**

Add `fetch-depth: 0` to your checkout step:

```yaml
- name: Checkout
  uses: actions/checkout@v5
  with:
    fetch-depth: 0  # Fetch full git history
```

**For GitLab CI:**

Set `GIT_DEPTH` to `0` in your `.gitlab-ci.yml`:

```yaml
variables:
  GIT_DEPTH: 0  # Fetch full git history
```

If you cannot fetch full git history in your CI/CD environment, consider setting `use_git_timestamps: false` to use file system timestamps instead.

### Template and Asset Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `assets_dir` | Path | `"docs/notes/assets"` | Directory for storing note assets. Uses tree-based structure with `.assets` suffix on first-level subdirectories |
| `enable_asset_fallback` | bool | `true` | Whether to fallback to original asset paths when assets with processed uri are not found. When enabled, if a processed asset file doesn't exist, the original asset path will be preserved instead of being replaced |
| `notes_template` | Path | `"overrides/templates/default.md"` | Template file for new notes. Supports variables: `{{title}}`, `{{date}}`, `{{note_name}}` |

### Logging Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_level` | str | `"INFO"` | Logging level for the plugin (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Network Graph Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_network_graph` | bool | `false` | Enable or disable the network graph |
| `graph_config` | dict | `{"name": "title", "debug": false}` | Configuration for the network graph visualization. Available options: `name`: Node naming strategy ("title" or "file_name"), `debug`: Enable debug logging for graph generation |
