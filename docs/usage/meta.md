---
date: 2025-11-05 00:09:04
title: Frontmatter Metadata
description: Note frontmatter fields understood by mkdocs-note — publish, date, title, permalink, preview, and encryption.
permalink: 
publish: true
---

# Frontmatter Metadata

Every note is a Markdown file with a YAML frontmatter block. `mkdocs-note` reads
these fields when scanning notes and building the site. A file that is not a
note (for example a theme page) is still published by MkDocs; it is simply not
treated as a note when `publish` is absent or false.

```yaml
---
title: Example note
date: 2026-11-06 09:02:00
permalink: example-note
publish: true
preview: true
encrypt: false
---
```

## Core fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | string | — | Note title shown in navigation, recent notes, the graph, and the page heading. **Required** for notes |
| `date` | datetime (`YYYY-MM-DD HH:MM:SS`) | — | Creation date used to sort recent notes. **Required** for notes |
| `publish` | boolean | `false` | Include the file in the note list. Non-note pages can omit it |
| `permalink` | string | `""` | Slug used for the note's asset directory and as the default encryption password |

## Link preview fields

See [Same-site Link Preview](link-preview.md).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `preview` | boolean | `true` | Set to `false` to exclude this page from `previews.json` and hover cards |
| `preview_image` | string | — | Image URL shown on the preview card |
| `image` | string | — | Fallback for `preview_image` |

## Encryption fields

See [Page Encryption](encryption.md).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `encrypt` | boolean | `false` | Encrypt this note's body at rest in git and on the published site |
| `password` | string | — | Explicit password; takes precedence over `permalink`. Quote it if YAML would parse it as a non-string (`password: "yes"`) |

When `encrypt: true` and `password` is absent or empty, `permalink` is the
password and must then be non-empty. Both fields remain readable in the
frontmatter and on the published page; they are not secret from someone who can
read the repository.
