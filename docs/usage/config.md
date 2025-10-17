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
| `max_notes` | int | `11` | Maximum number of recent notes to display (including index page, but display not including the index page itself) |
| `start_marker` | str | `"<!-- recent_notes_start -->"` | Start marker for notes insertion |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | End marker for notes insertion |
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | File extensions to include as notes |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | File name patterns to exclude from plugin management (within `notes_dir` scope). Excluded files cannot be created, scanned, listed, moved, or managed by the asset system |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | Directory names to exclude from note scanning |
| `use_git_timestamps` | bool | `true` | Use Git commit timestamps for sorting instead of file system timestamps |
| `timestamp_zone` | str | `"UTC+0"` | Timezone for timestamp display (e.g., 'UTC+0', 'UTC+8', 'UTC-5'). Ensures consistent timestamp display across different deployment environments |
| `assets_dir` | Path | `"docs/notes/assets"` | Directory for storing note assets. Uses tree-based structure with `.assets` suffix on first-level subdirectories |
| `notes_template` | Path | `"overrides/templates/default.md"` | Template file for new notes. Supports variables: `{{title}}`, `{{date}}`, `{{note_name}}` |
| `cache_size` | int | `256` | Size of the cache for performance optimization |

## Configuration Options Details
