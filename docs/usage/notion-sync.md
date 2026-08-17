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
        local_images: upload   # or site
        cache_dir: .cache/mkdocs-note
```

Sensitive credentials stay in the environment (or local files), not in git:

1. CLI `--token`

2. `NOTION_TOKEN` / `NOTION_API_KEY`

3. Project `.env` / `.notion_token` (do not commit)

4. `~/.config/notion/token`

Environment overrides for IDs: `NOTION_WIKI_DATABASE`, `NOTION_WIKI_DATA_SOURCE`,
`NOTION_TITLE_PROPERTY`, `NOTION_TAGS_PROPERTY`, `NOTION_STATE_PATH`.
Full-sync cache dir: `NOTION_SYNC_CACHE` (default `.cache/mkdocs-note`).

Add `.notion_sync_state.json` to `.gitignore`. In CI, cache that file so page
maps do not rebuild every run. Resume progress lives under `.cache/mkdocs-note/`
and is gitignored by a file the CLI writes into that directory.

## Local images

- `upload` (default): local `![](…)` files are uploaded to Notion (slower when a
  page has many attachments).
- `site`: rewrite local paths to the published site URL, e.g. `docs/assets/1.jpg`
  → `{site_url}/assets/1.jpg`. Requires `site_url`. Faster; Notion then depends
  on the deployed MkDocs site.

```bash
mkdocs-note ns --full --images site
```

## Full-sync resume

If `--full` (or an implicit full sync) is interrupted, re-run the same command
to skip pages already written in that run. Use `--no-resume` to start over.
A completed successful full sync deletes `notion-sync.json` but keeps the
directory `.gitignore`.

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
mkdocs-note notion-sync --full --images site
mkdocs-note notion-sync --full --no-resume
```

### Common flags

| Flag | Meaning |
|------|---------|
| `--full` | Sync all nav pages |
| `--base REF` | Git base for diff (`full` forces full sync) |
| `--paths` / `--paths-file` | Explicit file list |
| `--section PREFIX` | Limit to path prefixes |
| `--dry-run` | Convert and log without writing Notion |
| `--images upload\|site` | Local images: upload files, or use MkDocs site URLs |
| `--no-resume` | Discard `--full` checkpoint and start from scratch |
| `--rebuild-state` | Remap pages from the wiki |

## Behaviour notes

- Structure follows `.nav.yml` (or directory hierarchy on fallback)

- Local deletions are logged only — Notion pages are **not** deleted

- All `index.md` pages are skipped

- Frontmatter `tags` / `tag` map to the Notion multi-select property

- Local images: `local_images: upload` (default) uploads files; `site` uses
  `site_url` + docs-relative paths (faster when a page has many attachments).
  CLI `--images` overrides the config.

- Interrupted `--full` syncs resume from `.cache/mkdocs-note/notion-sync.json`.
  A successful run deletes that file. Use `--no-resume` to start over.

- Material tabs become heading sections; admonitions become callouts / details

## Known limitations

- Same-parent duplicate titles can mis-match during `--rebuild-state`

- Full sync with many local images is slow — use `local_images: site` or prefer incremental

- Some Material features (inline float admonitions, true tabs) are approximated
