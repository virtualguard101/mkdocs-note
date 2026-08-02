---
date: 2026-08-03 00:35:00
title: Configuration Options
permalink: 
publish: true
---

# Configuration Options

Configure the plugin under `plugins` in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note:
      enabled: true
      notes_root: docs
      recent_notes_config:
        enabled: false
        insert_marker: "<!-- recent_notes -->"
        insert_num: 10
      graph_config:
        enabled: false
        name: title
        debug: false
      notion_sync:
        docs_dir: docs
        nav_file: docs/.nav.yml
        database_id: ""
        data_source_id: ""
        title_property: "页面"
        tags_property: "标签"
        site_url: ""
        state_path: ".notion_sync_state.json"
        delay: 0.35
```

## Core

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable or disable the plugin |
| `notes_root` | `docs` | Working directory for note scanning and CLI |

## Recent notes

| Option | Default | Description |
|--------|---------|-------------|
| `recent_notes_config.enabled` | `false` | Insert a recent-notes list |
| `recent_notes_config.insert_marker` | `<!-- recent_notes -->` | Marker in the index page |
| `recent_notes_config.insert_num` | `10` | How many notes to list |

## Network graph

| Option | Default | Description |
|--------|---------|-------------|
| `graph_config.enabled` | `false` | Enable graph visualization |
| `graph_config.name` | `title` | Node label: `title` or `file_name` |
| `graph_config.debug` | `false` | Extra graph logging |

## Notion sync

Used by `mkdocs-note notion-sync` / `ns`. See [Notion Sync](notion-sync.md).

| Option | Default | Description |
|--------|---------|-------------|
| `notion_sync.docs_dir` | `docs` | Docs root for paths / git diff |
| `notion_sync.nav_file` | `docs/.nav.yml` | awesome-nav file (fallback: directory scan) |
| `notion_sync.database_id` | `""` | Notion wiki database ID (or env) |
| `notion_sync.data_source_id` | `""` | Notion data source ID (or env) |
| `notion_sync.title_property` | `页面` | Title property name |
| `notion_sync.tags_property` | `标签` | Multi-select tags property |
| `notion_sync.site_url` | `""` | Public site URL; falls back to mkdocs `site_url` |
| `notion_sync.state_path` | `.notion_sync_state.json` | Local page map (gitignore) |
| `notion_sync.delay` | `0.35` | Delay between API calls (seconds) |

Token is never stored in `mkdocs.yml` — use environment variables or local token files.
