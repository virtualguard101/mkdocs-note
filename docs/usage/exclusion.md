---
date: 2025-10-17 10:53:20
title: Exclusion
permalink: 
publish: true
---

# Exclusion

`mkdocs-note` provides a flexible way to exclude files or directories from the recent notes list display and other features. You can configure the `exclude_patterns` and `exclude_dirs` options in `mkdocs.yml` to exclude files or directories from the plugin's processing.

And the exlcude patterns or directories is relative to the `notes_dir` option in `mkdocs.yml` which is the directory of the notes that defines the plugin's working scope. 

For `notes_dir`, it's default to `docs`, see more details in [Working Scope and Behavior Boundaries]().

## Exclude Patterns

The `exclude_patterns` option is a list of glob patterns to exclude files or directories from the recent notes list. You can configure it as follows:

```yaml
plugins:
  - mkdocs-note:
      exclude_patterns:
        - index.md
        - README.md
```

By default, the `exclude_patterns` option is set to `{'index.md', 'README.md'}`, which means the index page and the README file will be excluded from the plugin's processing.

## Exclude Directories

The `exclude_dirs` option is a list of directories to exclude from the recent notes list. You can configure it as follows:

```yaml
plugins:
  - mkdocs-note:
      exclude_dirs:
        - templates
        - drafts
```

By default, the `exclude_dirs` option is set to `{'__pycache__', '.git', 'node_modules'}`, which means the `__pycache__`, `.git`, and `node_modules` directories will be excluded from the plugin's processing.
