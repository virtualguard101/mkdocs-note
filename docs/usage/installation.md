---
date: 2025-10-17 10:36:23
title: Installation
permalink: 
publish: true
---

# Installation

## Requirements

- Python 3.12 or higher

- [Astral uv](https://docs.astral.sh/uv/) as recommended Python package manager

- [MkDocs](https://www.mkdocs.org/)

## Basic Installation

Thanks to the modern Python package manager, you can easily install the plugin using the following commands:

```bash
uv init
uv venv
uv add mkdocs-note
```

After installation, you can use the `mkdocs-note --version` command to check the version of the plugin.

```bash
mkdocs-note --version
```

Or you can use [The `uv tool` Interface (`uvx`)](https://docs.astral.sh/uv/concepts/tools/) to install and use it much simpler that run the plugin in an isolated environment:

```bash
uvx mkdocs-note --version
```

Or using `pip` in an old way:

```bash
pip install mkdocs-note
```

## For developers

If you want to contribute to the plugin, you can clone the repository and install the plugin in development mode:

```bash
git clone https://github.com/virtualguard101/mkdocs-note.git
cd mkdocs-note
uv sync --extra dev
uv add -e .
```

Then you can run the tests for installation verification:

```bash
uv run pytest
```

More details about development setup, please refer to [Contributing](../contributing/contributing.md#Development-Setup).
