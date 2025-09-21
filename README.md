# MkDocs-Note

<!-- [![PyPI version](https://badge.fury.io/py/mkdocs-note.svg)](https://badge.fury.io/py/mkdocs-note) -->

`MkDocs-Note` is a plugin for `MkDocs` that transforms your documentation site into a powerful personal knowledge base with bi-directional linking, similar to Obsidian or Roam Research.

## Features

- **Bi-directional Linking**: Automatically create and display backlinks for your notes.
- **Note Management**: Easily create new notes from templates using command line tools.
- **Recent Notes**: Display a list of recent notes on your homepage.
- **Attachment Management**: Handles attachments within your notes directory.
- **Flexible Configuration**: Highly customizable to fit your workflow.

## Installation

Recommanded to use [uv](https://docs.astral.sh/uv/) to manage python virtual environment:

```
uv venv
uv pip insatll mkdocs-note
```

Or install the plugin using `pip`:

```bash
pip install mkdocs-note
```

Then, add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note
```

## Usage

### Creating Notes

You can create a new note using the following command:

```bash
mkdocs note new "My New Note"
```

### Linking Notes

Use `[[wiki-style]]` links to connect your notes. The plugin will automatically convert these into valid Markdown links and generate backlinks.

`[[My Target Note]]` will be converted to a link to `My Target Note.md`.

### Backlinks

Backlinks are automatically added to the bottom of each note, showing you which other notes link to the current one.

## Configuration

You can customize the plugin's behavior in your `mkdocs.yml`:

```yaml
plugins:
  - note:
      # Whether the plugin is enabled
      enabled: true
      # The root path for your notes
      notes_root_path: "docs/notes"
      # Template for new notes
      notes_template: "templates/default.md"
      # Path for attachments
      attachment_path: "docs/notes/assets"
      # Paths to exclude from note processing
      path_blacklist: "docs/notes/draft"
```

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
