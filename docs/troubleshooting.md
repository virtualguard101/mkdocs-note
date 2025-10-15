# Troubleshooting Guide

This document provides solutions to common issues when using the MkDocs-Note plugin.

## Configuration Error: "Invalid config options for the 'mkdocs-note' plugin"

### Problem

You may encounter the following error:

```
ERROR   -  Config value 'plugins': Invalid config options for the 'mkdocs-note' plugin.
```

### Root Cause

This error typically occurs due to incorrect YAML formatting in your `mkdocs.yml` configuration file. The most common mistake is using a dash (`-`) instead of proper indentation for plugin options.

### Incorrect Configuration (❌)

```yaml
plugins:
  - mkdocs-note:
    - notes_dir: docs/notes  # ❌ WRONG: Using dash creates a list instead of a dict
```

This gets parsed as: `{'mkdocs-note': [{'notes_dir': 'docs/notes'}]}` which is a **list**, not a **dictionary**.

### Correct Configuration (✓)

```yaml
plugins:
  - mkdocs-note:
      notes_dir: docs/notes  # ✓ CORRECT: Proper indentation creates a dict
```

This gets parsed as: `{'mkdocs-note': {'notes_dir': 'docs/notes'}}` which is a **dictionary**.

### Solution

1. Open your `mkdocs.yml` file
2. Find the `mkdocs-note` plugin configuration
3. Ensure that plugin options use **spaces for indentation** (not dashes)
4. Use 2 or 4 spaces (be consistent) after the plugin name

### Complete Configuration Examples

#### Minimal Configuration

```yaml
plugins:
  - search
  - mkdocs-note:
      notes_dir: docs/notes
```

#### Full Configuration

```yaml
plugins:
  - search
  - mkdocs-note:
      enabled: true
      notes_dir: "docs/notes"
      index_file: "docs/notes/index.md"
      max_notes: 10
      start_marker: "<!-- recent_notes_start -->"
      end_marker: "<!-- recent_notes_end -->"
```

## Configuration Type Error: "Expected type: <class 'pathlib.Path'> but received: <class 'str'>"

### Problem

You may encounter the following error:

```
ERROR   -  Config value 'plugins': Plugin 'mkdocs-note' option 'notes_dir': Expected type: <class 'pathlib.Path'> but received: <class 'str'>
```

### Root Cause

This error occurs when there's a mismatch between the expected configuration type and the actual type provided. This typically happens when:

1. The plugin configuration is incorrectly defined
2. There's a version compatibility issue with MkDocs
3. The configuration option type validation is too strict

### Solution

This error has been fixed in the latest version of the plugin. If you encounter this error:

1. **Update the plugin** to the latest version:
   ```bash
   pip install --upgrade mkdocs-note
   ```

2. **Check your MkDocs version**:
   ```bash
   mkdocs --version
   ```

3. **If the error persists**, ensure your `mkdocs.yml` configuration is correct:
   ```yaml
   plugins:
     - mkdocs-note:
         notes_dir: docs/notes  # String path is correct
   ```

### Note

The plugin internally converts string paths to `pathlib.Path` objects as needed, so you should always provide string paths in your configuration.

## Jupyter DeprecationWarning

### Problem

You may see this warning when using `.ipynb` files:

```
INFO    -  DeprecationWarning: Jupyter is migrating its paths to use standard platformdirs
           given by the platformdirs library.  To remove this warning and
           see the appropriate new directories, set the environment variable
           `JUPYTER_PLATFORM_DIRS=1` and then run `jupyter --paths`.
```

### Root Cause

This warning comes from Jupyter's migration to use the `platformdirs` library for path management. **This is not an error from the MkDocs-Note plugin** - it's a deprecation warning from Jupyter itself.

### Solution

This warning is harmless and can be safely ignored. If you want to suppress it:

1. **Set the environment variable** (recommended for future compatibility):

   ```bash
   export JUPYTER_PLATFORM_DIRS=1
   mkdocs build
   ```

2. **Update Jupyter Core** to version 6 or later:

   ```bash
   pip install --upgrade jupyter_core
   ```

3. **Suppress the warning** (temporary workaround):

   ```bash
   export PYTHONWARNINGS="ignore::DeprecationWarning"
   mkdocs build
   ```

### Note

The MkDocs-Note plugin does **NOT** import any Jupyter libraries. It only parses `.ipynb` files as JSON to extract metadata. The warning appears because other tools in your environment (like MkDocs extensions or other plugins) may be importing Jupyter libraries.

## Other Common Issues

### Issue: No recent notes displayed

**Possible causes:**

1. **Missing markers** - Ensure your index file contains both markers:
   ```markdown
   <!-- recent_notes_start -->
   <!-- recent_notes_end -->
   ```

2. **Wrong notes directory** - Verify the `notes_dir` path in your configuration

3. **Excluded files** - Check if your notes match the `exclude_patterns`

### Issue: Notes not updating

**Solution:** 
1. Clear the MkDocs build cache: `rm -rf site/`
2. Rebuild: `mkdocs build`

### Issue: Can't find notes

**Solution:**
1. Verify the notes directory exists
2. Check that notes have supported extensions (`.md` or `.ipynb`)
3. Ensure notes are not in excluded directories (`__pycache__`, `.git`, `node_modules`)

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [README.md](https://github.com/virtualguard101/mkdocs-note?tab=readme-ov-file#mkdocs-note) for configuration details
2. Review the [CONTRIBUTING.md](contributing.md) for architecture information
3. Open an issue on [GitHub](https://github.com/virtualguard101/mkdocs-note/issues) with:
   - Your MkDocs version: `mkdocs --version`
   - Your plugin version: `pip show mkdocs-note`
   - Your `mkdocs.yml` configuration
   - The full error message and traceback

