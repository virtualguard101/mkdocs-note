# Core Tests - Refactoring Status

⚠️ **These tests are currently disabled during the architecture refactoring.**

## Status

The following test files are disabled because they depend on the old modular architecture that has been removed:

- ❌ `test_assets_manager.py` - Depends on `utils.assetps.handlers`
- ❌ `test_file_manager.py` - Depends on `utils.fileps.handlers`
- ❌ `test_frontmatter_manager.py` - Depends on `utils.dataps.frontmatter`
- ❌ `test_graph_handler_simple.py` - Depends on `utils.graphps.handlers`
- ❌ `test_note_cleaner.py` - Depends on `utils.cli.cleaner` (old version)
- ❌ `test_note_creator.py` - Depends on `utils.cli.creator` (old version)
- ❌ `test_note_initializer.py` - Depends on `utils.cli.initializer` (old version)
- ❌ `test_note_manager.py` - Depends on `utils.docsps.handlers`
- ❌ `test_note_remover.py` - Depends on `utils.cli.remover` (old version)

## New Architecture

The project has been refactored to a simpler architecture:

```
src/mkdocs_note/
├── plugin.py          # MkDocs plugin entry
├── cli.py             # CLI commands entry
├── config.py          # Configuration (MkdocsNoteConfig)
├── graph.py           # Graph functionality
└── utils/
    ├── meta.py        # Metadata extraction utilities
    ├── scanner.py     # File scanning utilities
    └── cli/           # CLI operation modules
        ├── creator.py
        ├── remover.py
        ├── mover.py
        ├── cleaner.py
        └── initializer.py
```

## TODO

These tests need to be rewritten to match the new simplified architecture:

1. Create new tests for `utils.meta` functions
2. Create new tests for `utils.scanner` functions
3. Create new tests for CLI operations (if they become functional)
4. Create new tests for graph functionality
5. Update plugin integration tests

## Running Tests

To run the currently working tests:

```bash
# Run all working tests
pytest tests/test_config.py tests/test_plugin.py tests/smoke_test.py

# Run smoke test
python tests/smoke_test.py
```

