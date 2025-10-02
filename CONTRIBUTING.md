# Contributing to MkDocs-Note

First off, thank you for considering contributing to `MkDocs-Note`! It's people like you that make the open-source community such a great place.

## Project Architecture

This section provides an overview of the MkDocs-Note plugin's architecture and call flow to help contributors understand the codebase structure.

### Overall Architecture

The MkDocs-Note plugin follows a modular architecture with clear separation of concerns:

```
mkdocs_note/
├── __init__.py              # Package initialization
├── plugin.py                # Main MkDocs plugin entry point
├── config.py                # MkDocs configuration management
├── logger.py                # Logging utilities
└── core/                    # Core business logic
    ├── file_manager.py      # File scanning and validation
    └── note_manager.py      # Note processing and management
```

### Core Components

#### 1. Plugin Entry Point (`plugin.py`)

The `MkdocsNotePlugin` class is the main entry point that integrates with MkDocs:

- **Inherits from**: `BasePlugin[PluginConfig]`

- **Key Methods**:

  - `on_config()`: Configures MkDocs settings (TOC, slugify functions)

  - `on_files()`: Scans and processes note files

  - `on_page_markdown()`: Inserts recent notes into index pages

#### 2. Configuration Management (`config.py`)

The `PluginConfig` class manages all plugin settings:

- **Configuration Options**:

  - `enabled`: Enable/disable plugin

  - `notes_dir`: Directory containing notes

  - `index_file`: Target index file for recent notes

  - `max_notes`: Maximum number of recent notes to display

  - `supported_extensions`: File types to include (`.md`, `.ipynb`)

  - `exclude_patterns`: Files to exclude from processing

  - `exclude_dirs`: Directories to skip during scanning

#### 3. File Management (`core/file_manager.py`)

The `FileScanner` class handles file discovery and validation:

- **Responsibilities**:

  - Recursively scan notes directory

  - Filter files by extension and patterns

  - Exclude specified directories and files

  - Return list of valid note files

#### 4. Note Processing (`core/note_manager.py`)

Multiple classes handle note processing and management:

- **`NoteInfo`**: Data class storing note metadata

- **`NoteProcessor`**: Extracts title and metadata from files

- **`CacheManager`**: Manages caching to avoid unnecessary updates

- **`IndexUpdater`**: Updates index files with recent notes

- **`RecentNotesUpdater`**: Main orchestrator class

#### 5. Logging (`logger.py`)

The `Logger` class provides colored console logging:

- Uses `colorlog` for enhanced console output

- Supports different log levels (DEBUG, INFO, WARNING, ERROR)

- Configurable log formatting

### Call Flow

The plugin execution follows this sequence:

1. **Initialization** (`__init__`)

   - Plugin instance created

   - Logger initialized

   - Recent notes list initialized

2. **Configuration Phase** (`on_config`)

   - Plugin enabled/disabled check

   - MkDocs TOC configuration setup
   
   - Slugify function configuration (pymdownx or fallback)

3. **File Processing Phase** (`on_files`)

   - FileScanner scans notes directory

   - NoteProcessor extracts metadata from each file

   - Notes sorted by modification time

   - Recent notes list populated

4. **Page Rendering Phase** (`on_page_markdown`)

   - Check if current page is the notes index page

   - Insert recent notes HTML between markers

   - Return modified markdown content

### Data Flow

The projects is now only with one feature which is **insert recent notes into the index page of notebook directory**. As an example of how the data flow of the notes users want to manage passing is shown as blow:

```
Notes Directory
    ↓ (FileScanner)
Valid Note Files
    ↓ (NoteProcessor)
NoteInfo Objects
    ↓ (Sort by modified_time)
Recent Notes List
    ↓ (HTML Generation)
Index Page Content
```

### Key Design Patterns

1. **Plugin Pattern**: Integrates with MkDocs plugin system

2. **Strategy Pattern**: Different title extraction for different file types

3. **Template Method**: Consistent note processing workflow

4. **Observer Pattern**: MkDocs event-driven architecture

5. **Data Transfer Object**: NoteInfo for structured data passing

### Extension Points

The architecture supports several extension points:

1. **Custom File Types**: Add new file extensions in `supported_extensions`

2. **Title Extraction**: Extend `NoteProcessor` for new file formats

3. **Output Formatting**: Modify HTML generation in `_generate_notes_html()`

4. **Caching Strategy**: Implement custom caching in `CacheManager`

5. **Filtering Logic**: Customize file filtering in `FileScanner`

### Testing Strategy

The project includes comprehensive unit tests:

- **Plugin Tests**: Test main plugin functionality

- **Core Tests**: Test individual components

- **Integration Tests**: Test component interactions

- **Mock Usage**: Extensive use of mocks for isolation

### Performance Considerations

1. **File Scanning**: Only scans when necessary

2. **Caching**: Avoids redundant processing

3. **Lazy Loading**: Components initialized on demand

4. **Memory Management**: Efficient data structures for note storage


## How Can I Contribute?

There are many ways to contribute, from writing documentation and tutorials to reporting bugs and submitting code changes.

### Reporting Bugs

If you find a bug, please open an issue and provide the following information:

- A clear and descriptive title.

- A detailed description of the problem, including steps to reproduce it.

- Your `MkDocs` configuration (`mkdocs.yml`).

- Any relevant error messages or logs.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it. This allows us to coordinate our efforts and avoid duplicating work.

## Development Setup

To get started with local development, follow these steps:

1.  **Fork and Clone the Repository**

    ```bash
    git clone https://github.com/YOUR_USERNAME/mkdocs-note.git
    cd mkdocs-note
    ```

2.  **Set Up the Environment**

    It's strongly recommended to use a virtual environment, and recommended to use [uv](https://docs.astral.sh/uv/) to manage project configuration and virtual environment.

    ```bash
    uv init
    ```

3.  **Install Dependencies**

    Install the project in editable mode along with the development dependencies.

    ```bash
    uv sync
    ```

4.  **Run Tests**

    To make sure everything is set up correctly, run the test suite:

    ```bash
    ./tests/test.sh
    ```

## Pull Request Process

1.  Ensure any new code is covered by tests.

2.  Update the documentation if you've added or changed any features.

3.  Make sure the test suite passes (`pytest`).

4.  Submit your pull request!

Thank you for your contribution!