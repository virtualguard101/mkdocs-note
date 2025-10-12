<div align="center">

# MkDocs-Note

**A MkDocs plugin to add note boxes to your documentation.**

[![PyPI - Version](https://img.shields.io/pypi/v/mkdocs-note)](https://pypi.org/project/mkdocs-note/)
[![GitHub License](https://img.shields.io/github/license/virtualguard101/mkdocs-note)](https://github.com/virtualguard101/mkdocs-note/blob/main/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/virtualguard101/mkdocs-note/publish.yml)](https://github.com/virtualguard101/mkdocs-note/actions)

<a href="README.md">English</a> | <a href="README.zh-CN.md">简体中文</a>

<p>Plugin Usage Demo: <a href="https://wiki.virtualguard101.com/notes/" target="_blank">Notebook | virtualguard101's Wiki</a></p>

</div>


`MkDocs-Note` is a plugin for `MkDocs` that automatically manages notes in your documentation site. It's designed to work seamlessly with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme to create a unified note-taking and documentation experience.

## Features

- **Recent Notes Display**: Automatically displays a list of recent notes on your notes index page

- **Multi-format Support**: Supports both Markdown (.md) and Jupyter Notebook (.ipynb) files

- **Smart Filtering**: Excludes index files and other specified patterns from the recent notes list

- **Flexible Configuration**: Highly customizable note directory, file patterns, and display options

- **Automatic Updates**: Notes list updates automatically when you build your documentation

- **Command Line Interface**: Built-in CLI commands for note management (`mkdocs note init`, `mkdocs note new`, etc.)

- **Asset Management**: Automatic asset directory creation and management for each note

- **Template System**: Configurable note templates with variable substitution

- **Structure Validation**: Ensures compliant asset tree structure for consistent organization

## Installation

Recommended to use [uv](https://docs.astral.sh/uv/) to manage python virtual environment:

```
uv venv
uv pip install mkdocs-note
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
  - mkdocs-note:
      notes_dir: "docs/notes"
```

> **⚠️ Important**: Note the indentation! Use **spaces** (not dashes `-`) for plugin options. The configuration must be a dictionary, not a list. See [Troubleshooting Guide](TROUBLESHOOTING.md) for common configuration issues.

## Usage

### Setting Up Your Notes Directory

#### Option 1: Using Command Line Interface (Recommended)

1. Initialize the notes directory structure:
```bash
mkdocs-note init
```

2. Create a new note:
```bash
mkdocs-note new docs/notes/my-new-note.md
```

#### Option 2: Manual Setup

1. Create a notes directory in your documentation (e.g., `docs/notes/`)

2. Create an `index.md` file in your notes directory

3. Add the marker comments to your index file:

```markdown
# My Notes

<!-- recent_notes_start -->
<!-- recent_notes_end -->
```

### Command Line Interface

The plugin provides several CLI commands for note management.

> **Configuration Auto-Loading**: All CLI commands automatically load your custom configuration from `mkdocs.yml` in the current or parent directories. You can also specify a config file explicitly using `--config` or `-c` option:
> ```bash
> mkdocs-note --config path/to/mkdocs.yml <command>
> ```

#### Initialize Notes Directory
```bash
mkdocs-note init [--path PATH]
```
- Creates the notes directory structure

- Analyzes existing asset structures

- Fixes non-compliant asset trees

- Creates an index file with proper markers

#### Create New Note
```bash
mkdocs-note new FILE_PATH [--template TEMPLATE_PATH]
```
- Creates a new note file with template content

- Creates the corresponding asset directory

- Validates asset tree structure compliance

#### Validate Structure
```bash
mkdocs-note validate [--path PATH]
```
- Checks if the asset tree structure complies with the plugin's design

- Reports any structural issues

#### Template Management
```bash
mkdocs-note template [--check] [--create]
```
- Check if the configured template file exists

- Create the template file if it doesn't exist

#### Remove Note
```bash
mkdocs-note remove FILE_PATH [--keep-assets] [--yes]
# or use the alias
mkdocs-note rm FILE_PATH [--keep-assets] [--yes]
```
- Remove a note file and its corresponding asset directory

- Use `--keep-assets` to keep the asset directory

- Use `--yes` or `-y` to skip confirmation prompt

#### Clean Orphaned Assets
```bash
mkdocs-note clean [--dry-run] [--yes]
```
- Find and remove asset directories without corresponding note files

- Use `--dry-run` to preview what would be removed without actually removing

- Use `--yes` or `-y` to skip confirmation prompt

- Automatically cleans up empty parent directories

#### Move/Rename Note or Directory
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

### Configuration Options

The plugin supports the following configuration options in your `mkdocs.yml`:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable or disable the plugin |
| `notes_dir` | Path | `"docs/notes"` | Directory containing your notes |
| `index_file` | Path | `"docs/notes/index.md"` | Index file where recent notes will be displayed |
| `max_notes` | int | `11` | Maximum number of recent notes to display (including index page, but display not including the index page itself) |
| `start_marker` | str | `"<!-- recent_notes_start -->"` | Start marker for notes insertion |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | End marker for notes insertion |
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | File extensions to include as notes |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | File patterns to exclude |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | Directories to exclude |
| `use_git_timestamps` | bool | `true` | Use Git commit timestamps for sorting instead of file system timestamps |
| `timestamp_zone` | str | `"UTC+0"` | Timezone for timestamp display (e.g., 'UTC+0', 'UTC+8', 'UTC-5'). Ensures consistent timestamp display across different deployment environments |
| `assets_dir` | Path | `"docs/notes/assets"` | Directory for storing note assets. Uses tree-based structure with `.assets` suffix on first-level subdirectories |
| `notes_template` | Path | `"docs/templates/default.md"` | Template file for new notes. Supports variables: `{{title}}`, `{{date}}`, `{{note_name}}` |
| `cache_size` | int | `256` | Size of the cache for performance optimization |

### Template System

The plugin supports a flexible template system with frontmatter support for creating new notes:

#### Template Variables

- `{{title}}`: The note title (derived from filename, formatted)

- `{{date}}`: Current date and time

- `{{note_name}}`: The original note filename

**Note**: Template variables are replaced **only in the frontmatter section**, keeping the note body clean and free from template syntax.

#### Default Template

The default template (`docs/templates/default.md`) contains:

```markdown
---
date: {{date}}
title: {{title}}
permalink: 
publish: true
---

# {{title}}

Start writing your note content...
```

#### Frontmatter Support

Notes support YAML frontmatter for metadata management:

- **Standard Fields**:
  
  - `date`: Creation or publication date
  
  - `permalink`: Custom permalink for the note
  
  - `publish`: Whether the note should be published (true/false)

- **Custom Fields**: You can add custom metadata fields through the extensible registration system

- **Metadata Registry**: The plugin provides a metadata registration interface for adding new fields without modifying core code

#### Custom Templates

You can use custom templates when creating notes:

```bash
mkdocs-note new docs/notes/my-note.md --template path/to/custom-template.md
```

**Template Types**:

- **Frontmatter Templates** (Recommended): Include YAML frontmatter section with variables

- **Legacy Templates**: Simple markdown without frontmatter (still supported)

### Asset Management

The plugin automatically manages assets for each note using a **tree-based structure**:

#### Tree-Based Asset Organization

- **Hierarchical Structure**: Assets mirror your notes directory structure, preventing conflicts between notes with the same name in different directories

- **First-Level Categorization**: First-level subdirectories have `.assets` suffix for better identification
  
  - `notes/dsa/` → `assets/dsa.assets/`

  - `notes/language/` → `assets/language.assets/`

  - `notes/ml/` → `assets/ml.assets/`

- **Path Mapping Examples**:
  
  ```
  notes/dsa/anal/iter.md           → assets/dsa.assets/anal/iter/
  notes/language/python/intro.md  → assets/language.assets/python/intro/
  notes/language/cpp/intro.md     → assets/language.assets/cpp/intro/
  notes/quickstart.md              → assets/quickstart/
  ```

#### Automatic Path Conversion

- **Relative References in Notes**: Simply write image references as usual:
  
  ```markdown
  ![Recursion Tree](recursion_tree.png)
  ```

- **Automatic Conversion**: The plugin automatically converts paths during build:
  
  - For `notes/dsa/anal/iter.md` → `../../assets/dsa.assets/anal/iter/recursion_tree.png`

  - For `notes/quickstart.md` → `assets/quickstart/recursion_tree.png`

- **No Manual Path Management**: Original markdown files remain clean and simple

#### Benefits

- ✅ **No Naming Conflicts**: Notes with the same name in different directories don't conflict

- ✅ **Clear Organization**: `.assets` suffix makes asset categories easily identifiable

- ✅ **Automatic Processing**: Image paths are converted automatically during build

- ✅ **MkDocs Compatible**: Generated paths work seamlessly with MkDocs

### How It Works

1. The plugin scans your configured notes directory for supported file types

2. It extracts metadata (title, modification date) from each note file

3. Notes are sorted by modification time (most recent first)

   - By default, uses Git commit timestamps for consistent sorting across deployment environments

   - Falls back to file system timestamps if Git is not available

4. The specified number of recent notes is inserted into your index page between the marker comments

5. For each note page, the plugin processes asset references:
   
   - Detects image references in markdown content
   
   - Calculates the note's position in the directory tree
   
   - Converts relative asset paths to correct references with proper `../` prefixes
   
   - Adds `.assets` suffix to first-level directories for organization

6. The process runs automatically every time you build your documentation

### Asset Management Best Practices

1. **Directory Structure**: Organize your notes in subdirectories for better categorization
   
   ```
   docs/notes/
   ├── dsa/           # Data Structures & Algorithms
   ├── language/      # Programming Languages
   ├── ml/            # Machine Learning
   └── tools/         # Development Tools
   ```

2. **Asset Placement**: Place assets in the corresponding asset directory
   
   ```
   docs/notes/assets/
   ├── dsa.assets/
   │   └── anal/
   │       └── iter/
   │           ├── recursion_tree.png
   │           └── diagram.png
   ```

3. **Simple References**: Write simple relative references in your notes
   
   ```markdown
   ![My Image](my-image.png)
   ![Diagram](diagrams/flow.png)
   ```

4. **Automatic Conversion**: Let the plugin handle path conversion during build

> **Note**: If you're migrating from an older version, you may need to reorganize your asset directories to match the new tree-based structure with `.assets` suffix on first-level directories.

### Sorting Behavior

The plugin uses Git commit timestamps by default (`use_git_timestamps: true`) to ensure consistent sorting across different deployment environments. This is especially important when deploying to platforms like Vercel, Netlify, or GitHub Pages, where file system timestamps may be reset during the build process.

If Git is not available or you prefer to use file system timestamps, you can disable this feature:

```yaml
plugins:
  - mkdocs-note:
      use_git_timestamps: false
```

### Timezone Configuration

To ensure consistent timestamp display across different deployment environments (e.g., local development vs. remote CI/CD), you can configure the timezone:

```yaml
plugins:
  - mkdocs-note:
      timestamp_zone: "UTC+8"  # For Beijing/Shanghai/Hong Kong time
      # timestamp_zone: "UTC-5"  # For Eastern Standard Time
      # timestamp_zone: "UTC+0"  # For UTC (default)
```

This is particularly useful when your local environment and remote deployment server are in different timezones. Without this configuration, timestamps might appear different between `mkdocs serve` (local) and the deployed site.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
