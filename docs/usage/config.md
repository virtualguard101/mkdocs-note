---
date: 2026-08-03 00:35:00
title: Configuration Options
description: Full reference for mkdocs-note plugin options including recent notes, graph, link preview, page encryption, and Notion sync.
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
      preview_config:
        enabled: false
        mode: summary
        delay_ms: 300
        max_chars: 200
        include_fragments: true
        mobile: false
        scope: linked_only
      encryption_config:
        kdf_iterations: 600000
        remember: session
        strict: auto
        rerender: true
        audit: true
        labels: {}
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
        local_images: upload
        cache_dir: .cache/mkdocs-note
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

## Same-site link preview

See [Same-site Link Preview](link-preview.md).

| Option | Default | Description |
|--------|---------|-------------|
| `preview_config.enabled` | `false` | Enable hover/focus previews (full no-op when false) |
| `preview_config.mode` | `summary` | `summary` or `excerpt` |
| `preview_config.delay_ms` | `300` | Hover delay in milliseconds |
| `preview_config.max_chars` | `200` | Plain-text truncation length |
| `preview_config.include_fragments` | `true` | Emit `#heading` keys in excerpt mode |
| `preview_config.mobile` | `false` | Touch preview strategy |
| `preview_config.scope` | `linked_only` | `linked_only` (link targets + recent notes + notes-index out-links + soft graph nodes) or `all` |

## Page encryption

Encryption itself is opt-in per note with the frontmatter flag `encrypt: true`
(see [Page Encryption](encryption.md) and [Metadata](meta.md)). The
`encryption_config` block only tunes the runtime; it is not needed to turn the
feature on.

| Option | Default | Description |
|--------|---------|-------------|
| `encryption_config.kdf_iterations` | `600000` | PBKDF2-HMAC-SHA256 iterations used by the browser to derive the key |
| `encryption_config.remember` | `session` | Remembered key storage: `session` (tab), `local` (browser), or `none` |
| `encryption_config.strict` | `auto` | Fail the build for plaintext or undecryptable flagged notes. `auto` follows the `CI` environment variable |
| `encryption_config.rerender` | `true` | Re-run Material's `document$` subscribers after unlocking |
| `encryption_config.audit` | `true` | Search the built site for plaintext of encrypted notes and warn |
| `encryption_config.labels` | English strings | Override the lock form UI text (`title`, `prompt`, `placeholder`, `submit`, `error`, `unsupported`, `noscript`, `toc`, `unavailable`) |

## Notion sync

!!! warning "Deprecated since 3.5.0"

    The `notion_sync` block and the `notion-sync` / `ns` command will be
    removed in 4.0.0. They still work in 3.5.x; notes with `encrypt: true` are
    skipped by the sync.

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
| `notion_sync.local_images` | `upload` | `upload` local files, or `site` to use MkDocs URLs |
| `notion_sync.cache_dir` | `.cache/mkdocs-note` | `--full` resume checkpoint directory |

Token is never stored in `mkdocs.yml` — use environment variables or local token files.
