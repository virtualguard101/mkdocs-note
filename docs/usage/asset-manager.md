---
date: 2025-10-17 11:41:05
title: Asset Management
permalink: 
publish: true
---

# Asset Management

The plugin automatically manages assets for each note using a **co-located structure** by its [CLI](cli.md):

## Co-Located Asset Organization

!!! important
    Starting from version `2.0.0`, the plugin uses a **co-located asset structure** where assets are stored next to their notes. This makes it easier to manage and move notes with their assets together.

- **Local Structure**: Asset directories are placed in the same directory as their corresponding note files, making them easy to find and manage

- **Simple Pattern**: For any note file, assets are stored in `assets/{note_stem}/` within the same directory
  
    - Note: `docs/usage/contributing.md` → Assets: `docs/usage/assets/contributing/`

    - Note: `docs/notes/python/intro.md` → Assets: `docs/notes/python/assets/intro/`

    - Note: `docs/notes/quickstart.md` → Assets: `docs/notes/assets/quickstart/`

- **Path Mapping Examples**:
  
    ```
    docs/notes/dsa/anal/iter.md           → docs/notes/dsa/anal/assets/iter/
    docs/notes/language/python/intro.md  → docs/notes/language/python/assets/intro/
    docs/usage/contributing.md            → docs/usage/assets/contributing/
    docs/notes/quickstart.md              → docs/notes/assets/quickstart/
    ```

## Automatic Path Conversion

- **Relative References in Notes**: Simply write image references as usual:
  
    ```markdown
    ![Recursion Tree](recursion_tree.png)
    ```

- **Automatic Conversion**: The plugin automatically converts paths during build:
  
    - For `docs/notes/dsa/anal/iter.md` → `assets/iter/recursion_tree.png`

    - For `docs/notes/quickstart.md` → `assets/quickstart/recursion_tree.png`

- **No Manual Path Management**: Original markdown files remain clean and simple

## Benefits

- ✅ **Co-Located**: Assets are right next to their notes, making them easy to find and manage

- ✅ **No Naming Conflicts**: Each note has its own dedicated asset directory

- ✅ **Automatic Processing**: Image paths are converted automatically during build

- ✅ **MkDocs Compatible**: Generated paths work seamlessly with MkDocs

- ✅ **Portable**: Moving a note and its assets directory together is straightforward

## How It Works

1. The plugin scans your configured notes directory for supported file types

2. It extracts metadata (title, modification date) from each note file

3. Notes are sorted by modification time (most recent first)

      - By default, uses Git commit timestamps for consistent sorting across deployment environments

      - Falls back to file system timestamps if Git is not available

4. The specified number of recent notes is inserted into your index page between the marker comments

5. For each note page, the plugin processes asset references:
   
      - Detects image references in markdown content
   
      - Calculates the note's position in the directory tree
   
      - Converts relative asset paths to correct references pointing to the co-located assets directory

6. The process runs automatically every time you build your documentation

## Asset Management Best Practices

1. **Directory Structure**: Organize your notes in subdirectories for better categorization
    
    ```
    docs/notes/
    ├── dsa/           # Data Structures & Algorithms
    │   └── anal/
    │       ├── iter.md
    │       └── assets/
    │           └── iter/
    │               ├── recursion_tree.png
    │               └── diagram.png
    ├── language/      # Programming Languages
    │   └── python/
    │       ├── intro.md
    │       └── assets/
    │           └── intro/
    │               └── syntax.png
    ├── ml/            # Machine Learning
    └── tools/         # Development Tools
    ```

2. **Asset Placement**: Assets are automatically placed next to their note
   
      - Note file: `docs/notes/dsa/anal/iter.md`
      - Assets directory: `docs/notes/dsa/anal/assets/iter/`

3. **Simple References**: Write simple relative references in your notes
   
    ```markdown
    ![My Image](my-image.png)
    ![Diagram](diagrams/flow.png)
    ```

4. **Automatic Conversion**: Let the plugin handle path conversion during build
