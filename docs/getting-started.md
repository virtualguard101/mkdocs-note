---
date: 2025-10-16 14:06:23
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

## Configuration

### Basic Configuration

For basic configuration, you can add the following to your `mkdocs.yml`:

```yml
plugins:
  - mkdocs-note
```

It's the simplest configuration, and the plugin will use the default configuration.

### Recommended Configuration

For recommended configuration, you can add the following to your `mkdocs.yml`:

```yml
plugins:
  - mkdocs-note:
      notes_dir: "docs"
      index_file: "docs/index.md"
      start_marker: "<!-- recent_notes_start -->"
      end_marker: "<!-- recent_notes_end -->"
      max_notes: 10
      supported_extensions: [".md"]
```

In general, Mkdocs Note supports highly customizable configuration, you can configure the plugin to your own needs.

Please refer to the [Configuration Options | User Guide](usage/config.md) for more details about the information of each configuration options.

## Command Line Interface

The plugin provides several CLI commands for docs and their assets management.

And first of all, this is a mkdocs-based plugin, so you need to have a mkdocs project first.

### Validate Structure

Use following command to validate the structure of your docs and assets:

```bash
mkdocs-note validate [--path PATH]
```

This command will check if the structure of your docs and assets is compliant with the plugin's design.

If there are any issues, it will report them to you.

### Initialize Docs and Assets Structure

Use following command to initialize your mkdocs-based docs and assets structure:

```bash
mkdocs-note init [--path PATH]
```

If your docs already has a structure, this command will analyze the existing asset structures and fix the non-compliant asset trees.

However, it will not help you move your existing assets to the new structure.

For example, if you have a note in `docs/notes/my-note.md`, and the asset is in `docs/assets/notes/my-note/`, this command will not help you move the asset to `docs/assets/my-note/`.

And take a look at the entire plugin in `v2.0.0`,there has no way to move the asset to the new structure automatically, so you need to do it manually and we're now trying to add this optional feature in the future.

By the way, if you're really don't want to move your existing assets to the new structure, you can puts them out of the config option `notes_dir` and use legency way to link them in order to avoid the plugin automatically managing them and cause some undefined events.

### Create New Documentation

Use following command to create a new documentation:

```bash
mkdocs-note new FILE_PATH
```

This command will create a new note file with the default template and the corresponding asset directory, which is a bit like [`hexo new`](https://hexo.io/zh-cn/docs/commands#new) command in Hexo.

### Remove Existing Documentation

Use following command to remove an existing documentation:

```bash
mkdocs-note remove FILE_PATH
```

This command will remove the documentation file and its corresponding asset directory, and before doing that, it will ask you for confirmation.

And you can use the alias `mkdocs-note rm` to do the same thing.

### Other Commands

There are some other commands that are not mentioned here, you can use `mkdocs-note --help/-h` or `mkdocs-note <command> --help/-h` to get the full list of commands and their usage.

### Configuration Auto-Loading

All CLI commands automatically load your custom configuration from `mkdocs.yml` in the current or parent directories. You can also specify a config file explicitly using `--config` or `-c` option:

```bash
mkdocs-note --config path/to/mkdocs.yml <command>
```

## Getting Help

See the [User Guide](usage/index.md) for more details about the usage and features of the plugin.

This project is still in its infancy stage, so any feedback or suggestions are welcome.

You can open an issue on [GitHub](https://github.com/virtualguard101/mkdocs-note/issues) to report bugs or request features.

Or you can email me directly at [virtualguard101@gmail.com](mailto:virtualguard101@gmail.com), though I may respone late because of my busy schedule.

Thank you for using MkDocs Note!
