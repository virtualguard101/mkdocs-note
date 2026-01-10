---
date: 2026-01-10 23:40:00
title: Command Line Interface
permalink: 
publish: true
---

# Command Line Interface

`mkdocs-note` provides a command line interface for documentation management.

You can use the command line interface to manage your documentations and their assets correspondingly.

## Overview

Since `v3`, the CLI has been rewritten to be greatly simplified. 

In `v3.0.x`, there only has commands to create, remove, move notes with there correspondingly assets directories and clean up orphaned asset directories:

| Commands | Description |
|:----------:|:-------------:|
| `new` | Create a new note file with proper asset structure. |
| `remove` | Remove a note file and its corresponding asset directory. |
| `move` | Move a note file and its corresponding asset directory to a new location. |
| `clean` | Clean up orphaned asset directories. |

## Commands Detail

### `new`

Create a new note file with proper asset structure.

- **Usage:**

    ```bash
    mkdocs-note new FILE_PATH [OPTIONS]
    ```

- **Arguments:**

    - `FILE_PATH` (required): Path where the new note file should be created

- **Features:**

    - Automatically generates front matter metadata:

        - `date`: Current timestamp in format `YYYY-MM-DD HH:MM:SS`

        - `title`: Auto-generated from filename (converts `-` and `_` to spaces and title-cases)

        - `permalink`: Empty by default

        - `publish`: Set to `true` by default

    - Creates corresponding asset directory automatically

    - Ensures parent directories exist

- **Examples:**

    ```bash
    # Create a simple note
    mkdocs-note new my-permalink docs/notes/my-note.md

    # Create a note in nested directory
    mkdocs-note new python-intro docs/notes/python/intro.md
    ```

- **Output:**

    Upon successful creation, you'll see:

    ```
    ✅ Successfully created note
    📝 Note: docs/notes/my-note.md
    🔗 Permalink: my-permalink
    📁 Assets: docs/notes/assets/my-permalink/
    ```

### `remove`

Remove a note file and its corresponding asset directory.

- **Usage:**

    ```bash
    mkdocs-note remove FILE_PATH [OPTIONS]
    mkdocs-note rm FILE_PATH [OPTIONS]  # Alias
    ```

- **Arguments:**

    - `FILE_PATH` (required): Path to the note file to remove

- **Options:**

    - `--keep-assets`: Keep the asset directory when removing the note

    - `--yes, -y`: Skip confirmation prompt

- **Features:**

    - Removes both the note file and its corresponding asset directory by default
    - Supports removing single files or entire directories containing notes
    - Prompts for confirmation before deletion (unless `--yes` is used)
    - Automatically cleans up empty parent directories after removal
    - Supports both `.md` and `.ipynb` file formats

- **Examples:**

    ```bash
    # Remove a note with confirmation prompt
    mkdocs-note remove docs/notes/test.md

    # Remove without confirmation
    mkdocs-note rm docs/notes/test.md --yes

    # Remove note but keep its assets
    mkdocs-note remove docs/notes/test.md --keep-assets

    # Remove all notes in a directory
    mkdocs-note rm docs/notes/drafts/
    ```

- **Output:**

    ```
    ✅ Successfully removed note: docs/notes/test.md
    📁 Removed assets: docs/notes/assets/test/
    ```

### `move`

Move or rename a note file/directory and its corresponding asset directory, or rename permalink value.

The `move` command supports two modes:

#### File Move Mode (default)

Move or rename a note file/directory and its corresponding asset directory. The permalink value remains unchanged, and asset directories are moved based on their permalink.

- **Usage:**

    ```bash
    mkdocs-note move SOURCE DESTINATION [OPTIONS]
    mkdocs-note mv SOURCE DESTINATION [OPTIONS]  # Alias
    ```

- **Arguments:**

    - `SOURCE` (required): Current path of the note file or directory

    - `DESTINATION` (required): Destination path (or parent directory if exists)

- **Options:**

    - `--keep-source-assets`: Keep the source asset directory (don't move it) [NOT IMPLEMENTED]

    - `--yes, -y`: Skip confirmation prompt

- **Features:**

    - Moves both the note file and its corresponding asset directory by default

    - Asset directories are identified by permalink, not filename

    - If moving to a different directory, asset directory moves with the note

    - If only renaming the file within the same directory, asset directory stays in place (based on permalink)

    - Supports moving single files or entire directories

    - Automatically creates necessary parent directories

    - Prompts for confirmation before moving (unless `--yes` is used)

    - Cleans up empty parent directories at the source location

    - Includes rollback mechanism if move operation fails

    - Supports both `.md` and `.ipynb` file formats

- **Examples:**

    ```bash
    # Rename a note file (same directory, asset directory stays in place)
    mkdocs-note move docs/notes/old-name.md docs/notes/new-name.md

    # Move to different directory (asset directory moves with note)
    mkdocs-note mv docs/notes/draft.md docs/notes/published/

    # Move entire directory
    mkdocs-note move docs/notes/drafts docs/notes/published --yes
    ```

- **Output:**

    ```
    ✅ Successfully moved
    📝 From: docs/notes/old-name.md
    📝 To: docs/notes/new-name.md
    📁 Assets moved
    ```

#### Permalink Rename Mode

Rename the permalink value in frontmatter and the asset directory name. The file location remains unchanged.

- **Usage:**

    ```bash
    mkdocs-note move SOURCE -p PERMALINK [OPTIONS]
    mkdocs-note mv SOURCE --permalink PERMALINK [OPTIONS]  # Alias
    ```

- **Arguments:**

    - `SOURCE` (required): Path to the note file (must be a file, not a directory)

    - `DESTINATION`: Ignored in permalink rename mode

- **Options:**

    - `--permalink, -p` (required): New permalink value

    - `--yes, -y`: Skip confirmation prompt

- **Features:**

    - Updates the permalink value in the note file's frontmatter

    - Renames the asset directory based on the new permalink value

    - File location remains unchanged

    - Only works on single files, not directories

    - Prompts for confirmation before renaming (unless `--yes` is used)

- **Examples:**

    ```bash
    # Rename permalink and asset directory
    mkdocs-note move docs/notes/my-note.md -p new-permalink-slug

    # Rename permalink without confirmation
    mkdocs-note mv docs/notes/test.md --permalink updated-slug --yes
    ```

- **Output:**

    ```
    ✅ Successfully renamed permalink
    📝 File: docs/notes/my-note.md
    🔗 Permalink: old-permalink → new-permalink-slug
    📁 Asset directory renamed
    ```

### `clean`

Clean up orphaned asset directories without corresponding notes.

**Usage:**

```bash
mkdocs-note clean [OPTIONS]
```

- **Options:**

    - `--dry-run`: Show what would be removed without actually removing

    - `--yes, -y`: Skip confirmation prompt

- **Features:**

    - Scans for asset directories that don't have corresponding note files

    - Lists all orphaned directories before removal

    - Supports dry-run mode to preview changes

    - Prompts for confirmation before deletion (unless `--yes` is used)

    - Automatically cleans up empty parent directories after removal

    - Works recursively through the entire notes directory

- **Examples:**

    ```bash
    # Preview orphaned assets without removing
    mkdocs-note clean --dry-run

    # Clean with confirmation
    mkdocs-note clean

    # Clean without confirmation
    mkdocs-note clean --yes
    ```

- **Output (dry-run):**

    ```
    🔍 Scanning for orphaned assets (dry run mode)...

    Would remove 3 orphaned asset directories:
    📁 docs/notes/assets/deleted-note/
    📁 docs/notes/assets/old-draft/
    📁 docs/notes/python/assets/removed/

    💡 Run without --dry-run to actually remove these directories
    ```

- **Output (actual cleanup):**

    ```
    🔍 Scanning for orphaned assets...

    Found 3 orphaned asset directories:
    📁 docs/notes/assets/deleted-note/
    📁 docs/notes/assets/old-draft/
    📁 docs/notes/python/assets/removed/

    Remove these 3 directories? [y/N]: y

    🗑️  Removing orphaned assets...
    ✅ Successfully removed 3 orphaned asset directories
    ```
