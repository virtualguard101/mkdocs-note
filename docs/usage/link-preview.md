---
date: 2026-10-01 14:40:00
title: Same-site Link Preview
description: Opt-in hover cards for internal note links — title, summary, or section excerpt without leaving the page.
permalink: 
publish: true
---

# Same-site Link Preview

Opt-in hover (and keyboard-focus) previews for **internal note links**: a floating card shows the destination title and summary (or a section excerpt) without leaving the page.

This is independent of Material’s Instant Previews and does **not** require Instant Navigation.

## Try it on this site

This documentation site has `preview_config` enabled. Hover (or focus) these internal links:

- Page summary: [Network Graph Visualization](network-graph.md)
- Page summary: [Recent Notes Insertion](recent-notes.md)
- Page summary: [Configuration Options](config.md)
- Page with admonitions: [Welcome](../index.md)

- Fragment excerpt: [Network Graph — Overview](network-graph.md#Overview)
- Fragment excerpt: [Network Graph — Basic Setup](network-graph.md#Basic-Setup)

### Material syntax smoke check

The card below is what you should see when hovering a page that uses Material constructs (this section itself uses them so you can compare with the live page):

!!! tip "Preview tip"
    Admonitions, ++ctrl+k++, and ==highlighted== text should render in the hover card similarly to this page.

??? note "Collapsible details"
    Nested details content stays readable in the preview.

External links (no preview): [Material Instant Previews](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-previews)

## Enable

```yaml
plugins:
  - mkdocs-note:
      preview_config:
        enabled: true
```

When `enabled` is `false` (the default), the plugin is a full no-op for this feature: no JS/CSS registration, no HTML injection, no `previews.json`.

## Configuration

```yaml
plugins:
  - mkdocs-note:
      preview_config:
        enabled: true
        mode: summary          # summary | excerpt
        delay_ms: 300
        max_chars: 200
        include_fragments: true
        mobile: false
        scope: linked_only     # linked_only | all
```

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `false` | Turn the feature on |
| `mode` | `summary` | `summary`: title + abstract; `excerpt`: section plain text + rich HTML |
| `delay_ms` | `300` | Hover delay before the card appears (`0` when `prefers-reduced-motion`) |
| `max_chars` | `200` | Truncation for plain-text summary / excerpt |
| `include_fragments` | `true` | In `excerpt` mode, emit `#heading-id` keys |
| `mobile` | `false` | Touch: first tap shows preview, second tap navigates |
| `scope` | `linked_only` | See [Scope](#scope) below; or `all` documentation pages |

## Scope

- `all` — every documentation page (minus `preview: false`).
- `linked_only` (default) — union of:
  1. Pages that appear as markdown/wiki link targets
  2. Recent-notes list (`recent_notes_config`, first `insert_num` notes) when that feature is enabled
  3. Out-links from notes index pages under `notes_root`
  4. Soft: graph node page ids when the network graph is enabled and built

Pure orphans (never linked, not recent, not in the graph) stay out of `previews.json`.

## Summary source

Priority for each page:

1. Frontmatter `description`
2. Frontmatter `summary`
3. First prose paragraph of the body (markdown markers stripped; skips `!!!` / `???` / `===` admonition blocks)

Per-note overrides:

```yaml
---
title: My note
description: Shown in the preview card
preview_image: ./assets/cover.png   # optional cover
preview: false                      # exclude this page from previews.json
---
```

## Excerpt mode

With `mode: excerpt`, links that include a heading fragment (for example `./note.md#Section-One`) show that section’s leading content. Heading IDs follow the same slugify rules as Material / pymdownx (`slugify` with case preservation). Parent headings include nested subsections; CJK heading fragments are stored as decoded Unicode in `previews.json` (runtime still matches percent-encoded hrefs).

Rich HTML in the card is produced with the site’s MkDocs/Material `markdown_extensions` (minus `toc` and `pymdownx.snippets`), then sanitized. Admonitions, details, tabbed content, keys, mark, and tables should closely match the main site; interactive mermaid/MathJax still won’t run inside the card.

Relative images in excerpts are rewritten via MkDocs `Files` (with directory-URL / source-parent fallbacks). Use **absolute** `https://` / `//` / `data:` URLs for CDN or third-party images — preview will not invent site paths for them.

## Runtime behavior

- Only same-site links inside the article content (`article` / `.md-content__inner`)
- Ignores nav, TOC, header, footer, and external URLs
- Dismiss on pointer leave; `Esc` closes the card
- Uses Material CSS variables (light/dark)
- Optional soft prefetch when the network graph is also enabled

## Build artifacts

- `site/previews/previews.json`

- `site/js/preview.js`

- `site/css/preview.css`

## Coexistence with Material Instant Previews

[Material Instant Previews](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-previews) (Material ≥ 9.7) show another style of popover and usually need Instant Navigation.

Recommendations:

- Prefer **one** preview UX on a site to avoid stacked popovers on the same link.
- mkdocs-note preview works on a static host without Instant Navigation; keep Material Instant Previews off if you enable `preview_config`.
- External Open Graph / Discord-style link cards are a different product; this feature is **same-site / notes only**.

## Related

- [Network Graph](network-graph.md) — reuse of shared link normalization; optional neighbor prefetch

- [Configuration Options](config.md)
