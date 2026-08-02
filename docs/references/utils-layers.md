---
date: 2025-11-05 22:06:28
title: Utils Layers
permalink: 
publish: true
hide:
- navigation
---

# Utils Layers

This section is about the underlying utility functions that are used in the plugin, will be called by [plugin core](core-api.md) and [CLI](cli-api.md) directly.

And specifically, the `common` module of [CLI](cli-api.md) will call [plugin core](config-api.md) to get the plugin configuration instance, and `scanner` module will call `meta` module to validate the note file's frontmatter.

Notion sync lives under `mkdocs_note.utils.notion` and is invoked only from the CLI (`notion-sync` / `ns`), not from MkDocs build hooks.

## Developer note: Cursor MCP token (optional)

`notion_sync.allow_cursor_mcp_token` (default `false`) may allow reading a Notion token from `~/.cursor/mcp.json` for local developer convenience. When a token is loaded this way, a warning is emitted unless `silence_mcp_token_warning: true`. Prefer `NOTION_TOKEN` / project `.env` for normal use. This option is intentionally omitted from the user handbook.

## ::: mkdocs_note.utils.meta

## ::: mkdocs_note.utils.scanner

## ::: mkdocs_note.utils.tree

## ::: mkdocs_note.utils.notion

## ::: mkdocs_note.utils.cli
