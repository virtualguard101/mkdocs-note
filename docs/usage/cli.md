---
date: 2025-10-17 10:58:59
title: Command Line Interface
permalink: 
publish: true
---

# Command Line Interface

`mkdocs-note` provides a command line interface for documentation management. You can use the command line interface to manage your documentations and their assets correspondingly.

## Overview

| Command | Description |
|---------|-------------|
| `mkdocs-note init` | Initialize the notes directory structure |
| `mkdocs-note new` | Create a new note file with template content |
| `mkdocs-note validate` | Validate the asset tree structure |
| `mkdocs-note template` | Manage the template file |
| `mkdocs-note remove` | Remove a note file and its corresponding asset directory |
| `mkdocs-note clean` | Clean orphaned assets |
| `mkdocs-note move` | Move or rename a note file or directory |
| `mkdocs-note mv` | Alias for `mkdocs-note move` |
| `mkdocs-note rm` | Alias for `mkdocs-note remove` |
| `mkdocs-note mv` | Alias for `mkdocs-note move` |

For overview in command line, you can use the `--help/-h` option to get the help information of all commands.
```bash
mkdocs-note --help
# Or
mkdocs-note -h
```

For detailed information of a specific command, you can use the `mkdocs-note <command> --help` command to get the help information of a command.
```bash
mkdocs-note <command> --help
```

## Configuration Auto-Loading

All CLI commands automatically load your custom configuration from `mkdocs.yml` in the current or parent directories. You can also specify a config file explicitly using `--config` or `-c` option:

```bash
mkdocs-note --config path/to/mkdocs.yml <command>
```

## Commands Details

### Initialize Notes Directory

```bash
mkdocs-note init [--path PATH]
```

- Creates the docs and assets directory structure

- Analyzes existing asset structures

- Fixes non-compliant asset trees

### Create New Note

```bash
mkdocs-note new FILE_PATH [--template TEMPLATE_PATH]
```

- Creates a new note file with template content

- Creates the corresponding asset directory

- Validates asset tree structure compliance

### Validate Structure

```bash
mkdocs-note validate [--path PATH]
```

- Checks if the asset tree structure complies with the plugin's design

- Reports any structural issues

### Template Management

```bash
mkdocs-note template [--check] [--create]
```

- Check if the configured template file exists

- Create the template file if it doesn't exist

### Remove Note

```bash
mkdocs-note remove FILE_PATH [--keep-assets] [--yes]
# or use the alias
mkdocs-note rm FILE_PATH [--keep-assets] [--yes]
```

- Remove a note file and its corresponding asset directory

- Use `--keep-assets` to keep the asset directory

- Use `--yes` or `-y` to skip confirmation prompt

### Clean Orphaned Assets

```bash
mkdocs-note clean [--dry-run] [--yes]
```

- Find and remove asset directories without corresponding note files

- Use `--dry-run` to preview what would be removed without actually removing

- Use `--yes` or `-y` to skip confirmation prompt

- Automatically cleans up empty parent directories

### Move/Rename Note or Directory

```bash
mkdocs-note move SOURCE DESTINATION [--keep-source-assets] [--yes]
# or use the alias
mkdocs-note mv SOURCE DESTINATION [--keep-source-assets] [--yes]
```

- **Mimics shell `mv` behavior**: 

    - If destination doesn't exist: rename source to destination

    - If destination exists and is a directory: move source into destination

- Move or rename a note file or entire directory with its asset directories

- Supports moving single notes or entire directories with all notes inside

- Example: `mkdocs-note mv docs/notes/dsa/ds/trees docs/notes/dsa` moves to `docs/notes/dsa/trees`

- Use `--keep-source-assets` to keep the source asset directory

- Use `--yes` or `-y` to skip confirmation prompt

- Automatically creates necessary parent directories

- Cleans up empty parent directories in source location
