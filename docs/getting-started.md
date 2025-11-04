---
date: 2025-11-04 23:45:00
title: Getting Started
permalink: 
publish: true
---

# Getting Started

## Installation

Recommended to use [uv](https://docs.astral.sh/uv/) to add the plugin to your virtual environment:
```bash
uv add mkdocs-note
```

Or use [The `uv tool` Interface (`uvx`)](https://docs.astral.sh/uv/concepts/tools/) to install and use it much simpler:
```bash
uvx mkdocs-note --version
```

Or just using `pip`:
```bash
pip install mkdocs-note
```

For more details, please refer to the [Installation | User Guide](usage/installation.md).

## Use CLI to manage notes

The most highlighted feature of the plugin is the CLI commands to manage notes, which can help you manage your notes with their corresponding assets **atomically**.

### Create a note

To create a note, you can use the following command:
```bash
mkdocs-note new /path/to/note
```

It will create a note in the specified path and create a corresponding asset directory in the `assets` directory which will be co-located with the note.

### Remove Note or Note Directory

To remove a note, you can use the following command:
```bash
mkdocs-note remove /path/to/note-or-directory
```

It will remove the note or note directory and the corresponding asset directory(ies) from the `assets` directory, inspired by shell command `rm -rf`.

### Move or Rename Note or Note Directory

To move or rename a note or note directory, you can use the following command:
```bash
mkdocs-note move /path/to/note-or-directory /path/to/new-location
```

It will move or rename the note or note directory and the corresponding asset directory(ies) to the new location, inspired by shell command `mv`.

More details, please refer to the [CLI Commands | User Guide](usage/cli.md).

## Configuration

### Basic Configuration

For basic configuration, you can add the following to your `mkdocs.yml`:

```yml
plugins:
  - mkdocs-note
```

It's the simplest configuration, and the plugin will use the default configuration.

### Recommended Configuration

To use the plugin in a recommended way, you can add the following to your `mkdocs.yml`:

```yml
plugins:
  - mkdocs-note:
      recent_notes_config:
        enabled: true
        insert_marker: "<!-- recent_notes -->"
        insert_num: 5
      graph_config:
        enabled: true
        name: "title"
        debug: false
```

## Recent Notes Insertion

Mkdocs Note supports inserting specified number of recent notes to the marked placeholder in the index file, which can be configured in `mkdocs.yml` as follows:

```yml
plugins:
  - mkdocs-note:
      recent_notes_config:
        enabled: true
        insert_marker: "<!-- recent_notes -->"
        insert_num: 5
```

More details, please refer to the [Recent Notes Insertion | User Guide](usage/recent-notes.md).
