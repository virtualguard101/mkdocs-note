---
date: 2025-10-16 22:05:04
title: Recent Notes Insertion
permalink: 
publish: true
---

# Recent Notes Insertion

![](recent_insert_demo.png)

Mkdocs Note support inserting the links which refer to the recent new or modified documentations to the marked placeholder which can be configured in `mkdocs.yml` as below.

## Setup Where to Insert

The first step is to configure where to insert the link(s) of recent new or modified documentations.

### Which File to Insert

You can configure the file to insert recent documentations by setting the `index_file` option in `mkdocs.yml` as follows:

```yaml
plugins:
  - mkdocs-note:
      index_file: docs/index.md
```

By default, the file to insert the link(s) of recent new or modified documentations is `docs/index.md`.

You can change it to your own file.
k
### Markers

Then setup the markers to mark the placeholder where to insert the links of recent in the file we have just configured.

```yaml
plugins:
  - mkdocs-note:
      start_marker: <!-- recent_notes_start -->
      end_marker: <!-- recent_notes_end -->
```

By default, the start marker is `<!-- recent_notes_start -->` and the end marker is `<!-- recent_notes_end -->`.

In the file, you should add the markers as follows in whree you want to insert the links if you use the default markers we have just talk about above:

```markdown
# My Documentation

<!-- recent_notes_start -->
<!-- recent_notes_end -->
```

The marker will be replaced with the links of recent new or modified documentations after the plugin is loaded.

## Max Number of Documentations to Insert

You can configure the maximum number of documentations to insert by setting the `max_notes` option in `mkdocs.yml` as follows:

```yaml
plugins:
  - mkdocs-note:
      max_notes: 10
```

In the case of default, the maximum number of documentations to insert is 10.

## Setup Timestamp Display

The recent documentation inserting feature support putting the timestamp which records your documentations' last modified or committed time.

### Timezone

For specified timezone, you can set the `timestamp_zone` option in `mkdocs.yml` as follows:

```yaml
plugins:
  - mkdocs-note:
      timestamp_zone: "UTC+8"
```
