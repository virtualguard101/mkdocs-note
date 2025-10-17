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

In order to ensure consistent timestamp display across different deployment environments (e.g., local development vs. remote CI/CD), we introduced timezone for timestamp system.

For specified timezone, you can set the `timestamp_zone` option in `mkdocs.yml` as follows:

```yaml
plugins:
  - mkdocs-note:
      timestamp_zone: "UTC+8"
```

By default, the timezone is `UTC+0`.

This option is particularly useful when your local environment and remote deployment server are in different timezones. Without this configuration, timestamps might appear different between `mkdocs serve` (local) and the deployed site.

### Format

You can configure the format of the timestamp which will be displayed by setting the `output_date_format` option in `mkdocs.yml` as follows:

```yaml
plugins:
  - mkdocs-note:
      output_date_format: "%Y-%m-%d %H:%M:%S"
```

By default, the format of the timestamp is `%Y-%m-%d %H:%M:%S`.

Some formats for reference:

- `%Y-%m-%d`: Year-Month-Day

- `%Y-%m-%d %H:%M:%S`: Year-Month-Day Hour:Minute:Second

- `%Y-%m-%d %H:%M`: Year-Month-Day Hour:Minute

- `%Y-%m-%d %H`: Year-Month-Day Hour

- `%Y-%m-%d`: Year-Month-Day

- `%Y-%m-%d`: Year-Month-Day

## Something You Should Notice

By default, if the filename of the documentation is `index.md`, the plugin will not insert the links of recent new or modified documentations to the file.

What's more, the files will be ingored by `mkdocs-note` because is in the `exclude_patterns` option in `mkdocs.yml` by default. If you don't want to ignore them, you can configure the `exclude_patterns` option manually without `index.md` in it:

```yaml
plugins:
  - mkdocs-note:
      exclude_patterns:
        # without `index.md`
        - README.md
```

The files who are in the `exclude_patterns` option will be globally ingored by `mkdocs-note`, including assets management and other operations, see more details in [Exclusion](exclusion.md).
