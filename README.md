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
> Since `v3`, we greatly simplifies the plugin's framework architecture, and removed some features that are not essential to the core functionality of the plugin in order to make it more lightweight and easier to maintain.
>
> More details are available in the [Changelog](https://blog.virtualguard101.com/mkdocs-note/about/changelog/#300---2025-11-04-Architecture-Simplification) and [pull request #60](https://github.com/virtualguard101/mkdocs-note/pull/60).

## Features

- **Recent Notes Display**: Automatically displays a list of recent notes on your notes index page

- **Flexible Configuration**: Highly customizable note directory, file patterns, and display options

- **Command Line Interface**: Built-in CLI commands for note management ( `mkdocs note new`, `mkdocs note mv`, etc.)

- **Asset Management**: Automatic asset directory creation and management for each note

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

The usage and configuration details are available in the [Mkdocs-Based Documentation](https://blog.virtualguard101.com/mkdocs-note) since `v2`, refer it to get help or more infomation.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## References

- [MkDocs](https://www.mkdocs.org/)

- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

- [MkDocs Network Graph Plugin](https://github.com/develmusa/mkdocs-network-graph-plugin)

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
