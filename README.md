<div align="center">

# MkDocs Note

**A MkDocs plugin to add note boxes to your documentation.**

[![PyPI - Version](https://img.shields.io/pypi/v/mkdocs-note)](https://pypi.org/project/mkdocs-note/)
[![GitHub License](https://img.shields.io/github/license/virtualguard101/mkdocs-note)](https://github.com/virtualguard101/mkdocs-note/blob/main/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/virtualguard101/mkdocs-note/publish.yml)](https://github.com/virtualguard101/mkdocs-note/actions)

<a href="README.md">English</a> | <a href="README.zh-CN.md">简体中文</a>

<p>Plugin Usage Demo: <a href="https://wiki.virtualguard101.com/notes/" target="_blank">Notebook | virtualguard101's Wiki</a></p>

</div>


MkDocs Note is a plugin for [MkDocs](https://www.mkdocs.org/) that automatically manages notes in your documentation site. It's designed to work seamlessly with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme to create a unified note-taking and documentation experience.

>[!IMPORTANT]
> **Breaking Changes**
>
> Since `v2.0.0`, the plugin uses a co-located asset structure instead of the old unified tree structure, where assets are stored next to their notes. This makes it easier to manage and move notes with their assets together. 
>
> However, you need to manually move your existing assets to the new location.
>
> By the way, I think the plugin after `v2.0.0` can not only as a "notebook manager", but also an efficient documentations manager because of its powerful and flexible asset management system.

## Features

- **Recent Notes Display**: Automatically displays a list of recent notes on your notes index page

<!-- - **Multi-format Support**: Supports both Markdown (.md) and Jupyter Notebook (.ipynb) files -->

- **Smart Filtering**: Excludes index files and other specified patterns from the recent notes list

- **Flexible Configuration**: Highly customizable note directory, file patterns, and display options

- **Automatic Updates**: Notes list updates automatically when you build your documentation

- **Command Line Interface**: Built-in CLI commands for note management (`mkdocs note init`, `mkdocs note new`, etc.)

- **Asset Management**: Automatic asset directory creation and management for each note

- **Template System**: Configurable note templates with variable substitution

- **Structure Validation**: Ensures compliant asset tree structure for consistent organization

- **Network Graph Visualization**: Interactive network graph showing relationships between notes with automatic link detection

## Installation

Recommended to use [uv](https://docs.astral.sh/uv/) to manage python virtual environment:

```
uv init
uv venv
uv add mkdocs-note
```

Or use [The `uv tool` Interface (`uvx`)](https://docs.astral.sh/uv/concepts/tools/) to install and use it much simpler:

```bash
uvx mkdocs-note --help
```

Or using `pip`:

```bash
pip install mkdocs-note
```

Then, add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note
```

The usage and configuration details are available in the [Mkdocs-Based Documentation](https://blog.virtualguard101.com/mkdocs-note) since `v2.0.0`, refer it to get help or more infomation.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## References

- [MkDocs](https://www.mkdocs.org/)

- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

- [MkDocs Network Graph Plugin](https://github.com/develmusa/mkdocs-network-graph-plugin)

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
