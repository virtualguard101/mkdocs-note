---
date: 2026-08-03 00:30:00
title: Notion Sync
permalink: 
publish: true
---

# Notion Sync

Sync your MkDocs notes to a Notion wiki database. The CLI uses git-diff
incremental sync by default so routine commits only touch changed pages.

## Prerequisites

- A Notion integration token (`NOTION_TOKEN` or `NOTION_API_KEY`)

- Wiki **database ID** and **data source ID** for your Notebook wiki

- Recommended: [mkdocs-awesome-nav](https://github.com/lukasgeiter/mkdocs-awesome-nav)
  with a `docs/.nav.yml` so Notion sections match your site navigation

If `.nav.yml` is missing, the CLI falls back to scanning `notes_root` and
preserves directory hierarchy. A warning is logged recommending awesome-nav.

## Configuration

Add a `notion_sync` block under the plugin in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note:
      notes_root: docs
      notion_sync:
        docs_dir: docs
        nav_file: docs/.nav.yml
        database_id: "<your-database-id>"
        data_source_id: "<your-data-source-id>"
        title_property: "页面"
        tags_property: "标签"
        site_url: "https://example.com"   # optional; also falls back to mkdocs site_url
        state_path: ".notion_sync_state.json"
        delay: 0.35
```

Sensitive credentials stay in the environment (or local files), not in git:

1. CLI `--token`

2. `NOTION_TOKEN` / `NOTION_API_KEY`

3. Project `.env` / `.notion_token` (do not commit)

4. `~/.config/notion/token`

Environment overrides for IDs: `NOTION_WIKI_DATABASE`, `NOTION_WIKI_DATA_SOURCE`,
`NOTION_TITLE_PROPERTY`, `NOTION_TAGS_PROPERTY`, `NOTION_STATE_PATH`.

Add `.notion_sync_state.json` to `.gitignore`. In CI, cache that file so page
maps do not rebuild every run.

## Usage

```bash
# Incremental (relative to HEAD~1 or GITHUB_EVENT_BEFORE)
mkdocs-note notion-sync
# short alias
mkdocs-note ns

# Full sync / section filter / dry-run
mkdocs-note notion-sync --full
mkdocs-note ns --section notes/
mkdocs-note notion-sync --dry-run --paths notes/intro.md
mkdocs-note notion-sync --rebuild-state
```

### Common flags

| Flag | Meaning |
|------|---------|
| `--full` | Sync all nav pages |
| `--base REF` | Git base for diff (`full` forces full sync) |
| `--paths` / `--paths-file` | Explicit file list |
| `--section PREFIX` | Limit to path prefixes |
| `--dry-run` | Convert and log without writing Notion |
| `--no-images` | Skip local image uploads |
| `--rebuild-state` | Remap pages from the wiki |

## Behaviour notes

- Structure follows `.nav.yml` (or directory hierarchy on fallback)

- Local deletions are logged only — Notion pages are **not** deleted

- All `index.md` pages are skipped

- Frontmatter `tags` / `tag` map to the Notion multi-select property

- Local images upload via Notion File Upload + block insert (not site URLs)

- Material tabs become heading sections; admonitions become callouts / details

## Known limitations

- Same-parent duplicate titles can mis-match during `--rebuild-state`

- Full sync with many local images is slow — prefer incremental

- Some Material features (inline float admonitions, true tabs) are approximated
