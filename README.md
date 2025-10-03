# MkDocs-Note

<!-- [![PyPI version](https://badge.fury.io/py/mkdocs-note.svg)](https://badge.fury.io/py/mkdocs-note) -->

`MkDocs-Note` is a plugin for `MkDocs` that automatically manages notes in your documentation site. It's designed to work seamlessly with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme to create a unified note-taking and documentation experience.

## Features

- **Recent Notes Display**: Automatically displays a list of recent notes on your notes index page

- **Multi-format Support**: Supports both Markdown (.md) and Jupyter Notebook (.ipynb) files

- **Smart Filtering**: Excludes index files and other specified patterns from the recent notes list

- **Flexible Configuration**: Highly customizable note directory, file patterns, and display options

- **Automatic Updates**: Notes list updates automatically when you build your documentation

## Installation

Recommanded to use [uv](https://docs.astral.sh/uv/) to manage python virtual environment:

```
uv venv
uv pip insatll mkdocs-note
```

Or using `pip`:

```bash
pip install mkdocs-note
```

Then, add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-note:
      enabled: true
      notes_dir: "docs/notes"
      index_file: "docs/notes/index.md"
      max_notes: 10
      start_marker: "<!-- recent_notes_start -->"
      end_marker: "<!-- recent_notes_end -->"
```

> **⚠️ Important**: Note the indentation! Use **spaces** (not dashes `-`) for plugin options. The configuration must be a dictionary, not a list. See [Troubleshooting Guide](TROUBLESHOOTING.md) for common configuration issues.

## Usage

### Setting Up Your Notes Directory

1. Create a notes directory in your documentation (e.g., `docs/notes/`)
2. Create an `index.md` file in your notes directory
3. Add the marker comments to your index file:

```markdown
# My Notes

<!-- recent_notes_start -->
<!-- recent_notes_end -->
```

### Configuration Options

The plugin supports the following configuration options in your `mkdocs.yml`:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable the plugin |
| `notes_dir` | Path | `"docs/notes"` | Directory containing your notes |
| `index_file` | Path | `"docs/notes/index.md"` | Index file where recent notes will be displayed |
| `max_notes` | int | `10` | Maximum number of recent notes to display |
| `start_marker` | str | `"<!-- recent_notes_start -->"` | Start marker for notes insertion |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | End marker for notes insertion |
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | File extensions to include as notes |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | File patterns to exclude |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | Directories to exclude |
| `use_git_timestamps` | bool | `true` | Use Git commit timestamps for sorting instead of file system timestamps |

### How It Works

1. The plugin scans your configured notes directory for supported file types
2. It extracts metadata (title, modification date) from each note file
3. Notes are sorted by modification time (most recent first)
   - By default, uses Git commit timestamps for consistent sorting across deployment environments
   - Falls back to file system timestamps if Git is not available
4. The specified number of recent notes is inserted into your index page between the marker comments
5. The process runs automatically every time you build your documentation

### Sorting Behavior

The plugin uses Git commit timestamps by default (`use_git_timestamps: true`) to ensure consistent sorting across different deployment environments. This is especially important when deploying to platforms like Vercel, Netlify, or GitHub Pages, where file system timestamps may be reset during the build process.

If Git is not available or you prefer to use file system timestamps, you can disable this feature:

```yaml
plugins:
  - mkdocs-note:
      use_git_timestamps: false
```

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
