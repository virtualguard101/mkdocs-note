---
date: 2025-11-05 10:53:00
title: Changelog
permalink: 
publish: true
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 3.0.3 - 2025-12-08

### Changed

- Optimized link graph rendering for large sites: faster D3 settling via adjustable `alpha_decay`, `velocity_decay`, and `max_ticks`; automatic fallback to limited hops when the full graph exceeds `max_full_nodes` / `max_full_edges`.
- Reduced DOM overhead on big graphs by hiding labels/arrowheads past configurable thresholds and debouncing resize redraws.
- Added graph performance options to configuration and documentation to help tune behavior on 100+ note sites.

## 3.0.2 - 2025-11-05

### Fixed

- Fixed issue about [recent notes](../usage/recent-notes.md) reference links that refer to wrong URL.

## 3.0.1 - 2025-11-05

### Fixed

- Fixed issue where [recent notes](../usage/recent-notes.md) were not inserted into index page if notes_root was not default value (`docs`).

- Fixed issue that cannot copy static assets to output directory which can make the [graph visualization](../usage/network-graph.md) not working.

## 3.0.0 - 2025-11-04 (Architecture Simplification)

### Changed

- **[BREAKING] Major Architecture Refactoring**: Completely restructured project architecture from complex modular design to simplified flat structure (#60)
  
  - **Core Philosophy Change**: From "feature-rich notebook manager" to "lightweight documentation plugin with note features"
  
  - **Removed Modules** (deleted ~9,300 lines of code):
    
    - `utils/assetps/`: Asset management subsystem (401 lines)
    
    - `utils/dataps/`: Data models and frontmatter system (600+ lines)
    
    - `utils/docsps/`: Document operations (creator, cleaner, mover, remover, initializer - 1,800+ lines)
    
    - `utils/fileps/`: File I/O operations (105 lines)
    
    - `utils/graphps/`: Graph processing utilities (106 lines)
    
    - `utils/pathps/`: Path utilities (empty placeholder)
    
    - `logger.py`: Custom logging module (50 lines)
  
  - **New Simplified Structure**:
    
    - Core modules moved to package root: `plugin.py`, `cli.py`, `config.py`, `graph.py`
    
    - Minimal utilities: `utils/meta.py`, `utils/scanner.py`, `utils/cli/` (commands & common)
    
    - Total source code: ~2,700 lines (vs. ~12,000 lines in v2.x)
  
  - **Removed Features**:
    
    - Asset management system (automatic asset directory creation/management)
    
    - Template system (note templates with variable substitution)
    
    - Note validation and initialization commands
    
    - Advanced CLI commands: `init`, `validate`, `template`
    
    - Frontmatter management system
    
    - Complex file scanning and processing pipelines
  
  - **Retained Core Features**:
    
    - ✅ Recent notes display functionality
    
    - ✅ Network graph visualization
    
    - ✅ Basic CLI commands: `new`, `remove`, `move`, `clean`
    
    - ✅ Git timestamp support
    
    - ✅ Metadata extraction (title, date)
  
  - **Benefits**:
    
    - ✅ **Significantly Reduced Complexity**: Easier to understand, maintain, and extend
    
    - ✅ **Faster Performance**: Less overhead from removed abstraction layers
    
    - ✅ **Lower Maintenance Burden**: Fewer moving parts means fewer potential bugs
    
    - ✅ **Clearer Purpose**: Focused on core documentation needs rather than comprehensive note management
    
    - ✅ **Better Integration**: Simpler codebase integrates more naturally with MkDocs ecosystem

- **Configuration Simplification**: Dramatically reduced configuration options
  
  - **Removed Options**:
    
    - `assets_dir`: Asset management removed
    
    - `notes_template`: Template system removed
    
    - `cache_size`: Caching logic simplified
    
    - `exclude_patterns`: File filtering simplified
    
    - `use_git_timestamps`: Now always enabled by default
    
    - `timestamp_zone`: Timezone handling simplified
  
  - **Retained Options**:
    
    - `enabled`: Plugin enable/disable toggle
    
    - `notes_root`: Working directory (default: `docs`)
    
    - `recent_notes_config`: Recent notes insertion settings
    
    - `graph_config`: Network graph visualization settings
  
  - **Impact**: Configuration now fits in 47 lines vs. 237 lines in v2.x

- **CLI Refactoring**: Streamlined command-line interface
  
  - Migrated from complex `cli.py` (814 lines in v2.x) to modular structure:
    
    - `cli.py`: Main CLI entry point (438 lines)
    
    - `utils/cli/commands.py`: Command implementations (420 lines)
    
    - `utils/cli/common.py`: Shared utilities (98 lines)
  
  - **Removed Commands**:
    
    - `init`: Note directory initialization (no longer needed)
    
    - `validate`: Asset structure validation (asset system removed)
    
    - `template`: Template management (template system removed)
  
  - **Retained Commands** (with simplified implementations):
    
    - `new`: Create new notes (no template/validation overhead)
    
    - `remove` / `rm`: Delete notes (no asset cleanup complexity)
    
    - `move` / `mv`: Move/rename notes (simplified path handling)
    
    - `clean`: Clean orphaned resources (simplified cleanup logic)

- **Test Suite Reorganization**: Completely restructured test suite
  
  - **Removed Test Files** (~4,900 lines):
    
    - `tests/core/`: All core module tests (8 test files)
      
      - `test_assets_manager.py` (618 lines)
      
      - `test_file_manager.py` (319 lines)
      
      - `test_frontmatter_manager.py` (435 lines)
      
      - `test_graph_handler_simple.py` (163 lines)
      
      - `test_note_cleaner.py` (480 lines)
      
      - `test_note_creator.py` (372 lines)
      
      - `test_note_initializer.py` (255 lines)
      
      - `test_note_manager.py` (502 lines)
      
      - `test_note_remover.py` (153 lines)
  
  - **New Test Structure**:
    
    - `test_cli_commands.py`: CLI command testing (453 lines)
    
    - `test_cli_common.py`: CLI utility testing (202 lines)
    
    - `test_cli_integration.py`: Integration testing (405 lines)
    
    - `test_config.py`: Configuration testing (simplified to 397 lines)
    
    - `test_plugin.py`: Plugin testing (simplified to 670 lines)
    
    - `smoke_test.py`: Package smoke tests (refactored)
    
    - `test_help.py`: Help system tests
  
  - **Test Count**: Reduced from 227 tests to focused test suite on core functionality

- **Documentation Updates**: Comprehensive documentation reorganization
  
  - **Removed Documentation**:
    
    - `docs/usage/exclusion.md`: Exclusion patterns (42 lines)
    
    - `docs/usage/sec.md`: Security features (24 lines)
    
    - `docs/usage/templating.md`: Template system (75 lines)
  
  - **Added Documentation**:
    
    - `docs/usage/meta.md`: Metadata handling (8 lines)
  
  - **Updated Documentation**:
    
    - `docs/getting-started.md`: Simplified getting started guide
    
    - `docs/usage/cli.md`: Updated CLI documentation
    
    - `docs/usage/config.md`: Simplified configuration guide
    
    - `docs/usage/network-graph.md`: Updated graph documentation
    
    - `docs/usage/recent-notes.md`: Updated recent notes guide

- **Graph Module Restructuring**: Moved graph functionality to package root
  
  - `utils/graphps/graph.py` → `graph.py` (now 74 lines vs. original implementation)
  
  - `utils/graphps/handlers.py`: Removed (101 lines) - logic integrated into main module
  
  - Static assets moved: `utils/graphps/static/` → `static/`

### Removed

- **Asset Management System**: Complete removal of automatic asset directory management
  
  - Users now manage asset organization manually
  
  - No more automatic asset path processing during build
  
  - Removed asset catalog and tree structure validation

- **Template System**: Removed note template functionality
  
  - No more template variables (`{{title}}`, `{{date}}`, etc.)
  
  - No template validation or creation tools
  
  - Users manage note templates manually if needed

- **Frontmatter Management**: Removed comprehensive frontmatter system
  
  - No metadata registry or field validation
  
  - No custom metadata field support
  
  - Basic frontmatter parsing remains for title/date extraction

- **Advanced Validation**: Removed structure compliance checking
  
  - No asset tree validation
  
  - No note directory initialization
  
  - Simplified file scanning without complex validation

### Fixed

- **Code Complexity**: Resolved over-engineering issues from v2.x architecture
  
  - Removed unnecessary abstraction layers
  
  - Eliminated redundant validation logic
  
  - Simplified error handling and logging

- **Maintenance Burden**: Addressed difficulty in maintaining large codebase
  
  - Reduced total lines of code by ~77% (12,000 → 2,700 lines)
  
  - Eliminated 6,000+ lines of test code for removed features
  
  - Simplified dependency tree and module interactions

### Migration Guide

For users upgrading from v2.x to v3.0.0:

1. **Configuration Changes**:
   
   - Remove deprecated options: `assets_dir`, `notes_template`, `cache_size`, `exclude_patterns`, `use_git_timestamps`, `timestamp_zone`
   
   - Keep only: `enabled`, `notes_root`, `recent_notes_config`, `graph_config`

2. **Asset Management**:
   
   - Plugin no longer manages assets automatically
   
   - Organize assets manually in your preferred structure
   
   - Use standard MkDocs asset handling

3. **Template Usage**:
   
   - Plugin no longer provides template system
   
   - Create note templates manually if needed
   
   - Use external tools for template management

4. **CLI Commands**:
   
   - `mkdocs-note init`: No longer available (not needed)
   
   - `mkdocs-note validate`: No longer available (validation removed)
   
   - `mkdocs-note template`: No longer available (template system removed)
   
   - Other commands (`new`, `remove`, `move`, `clean`) still available with simplified behavior

5. **Custom Integrations**:
   
   - If you imported internal modules (e.g., `mkdocs_note.utils.assetps`), these no longer exist
   
   - Update imports to use new structure: `mkdocs_note.utils.meta`, `mkdocs_note.utils.scanner`

### Technical Details

- **Code Statistics**:
  
  - Files changed: 61 files
  
  - Insertions: +2,702 lines
  
  - Deletions: -9,329 lines
  
  - Net reduction: -6,627 lines (-77% of v2.x codebase)

- **Dependency Updates**:
  
  - Removed custom logging dependencies
  
  - Simplified MkDocs integration

- **Performance Improvements**:
  
  - Faster build times due to reduced processing overhead
  
  - Lower memory footprint
  
  - Simpler file scanning logic

## 2.1.5 - 2025-10-30

### Fixed

- **[CRITICAL] Git Timestamp Inconsistency in Remote Deployments**: Fixed critical bug where timestamps were identical for all notes except the most recent one when deployed via Vercel or other CI/CD platforms (#TBD)
  
  - **Root Cause**: The `project_root` configuration was using `Path(__file__).parent.parent`, which pointed to the **plugin installation directory** (e.g., `site-packages/mkdocs_note/`) instead of the user's project root. This caused git commands to execute in the wrong directory, failing to retrieve correct commit timestamps.
  
  - **Why It Worked Locally But Failed in Deployment**:
    - **Local Development**: When using `uv run` or development mode, `__file__` might point to the source code directory, which could work by coincidence
    - **Remote Deployment**: The plugin is installed via pip into `site-packages`, making `project_root` point to the wrong location, causing all git operations to fail
  
  - **Solutions Implemented**:
    
    - **Critical Fix in `plugin.py`**: Modified `on_config()` to dynamically set `project_root` from MkDocs config file location instead of plugin installation path:
      ```python
      actual_project_root = Path(config.config_file_path).parent
      self.config.project_root = actual_project_root
      ```
    
    - **Vercel Build Script**: Updated `scripts/vercel-build.sh` to fetch full git history with `git fetch --unshallow` (additional safety measure)
    
    - **GitHub Actions**: Updated `.github/workflows/ghpg.yml` to include `fetch-depth: 0` in checkout step (additional safety measure)
    
    - **Enhanced Git Logic**: Improved `_get_git_commit_time()` method with:
      - Shallow clone detection via `.git/shallow` file check
      - Debug warnings when shallow clone is detected
      - Timestamp validation to prevent future/invalid timestamps
      - Better error handling and fallback to file system timestamps
    
    - **Documentation**: Added comprehensive CI/CD deployment guide in `docs/usage/config.md` with examples for Vercel, GitHub Actions, and GitLab CI
  
  - **Impact**: This fix ensures git timestamps work correctly in all deployment scenarios. The plugin now correctly identifies the user's project directory regardless of how it's installed.

### Enhanced

- **Dynamic Project Root Detection**: Plugin now automatically detects project root from MkDocs configuration instead of relying on plugin installation path
- **Shallow Clone Detection**: Added `_is_shallow_clone()` helper method to detect when git repository is shallowly cloned
- **Git Timestamp Validation**: Added validation to ensure git timestamps are reasonable and not in the future
- **Deployment Documentation**: Added detailed CI/CD configuration examples for major platforms (Vercel, GitHub Actions, GitLab CI)
- **Error Handling**: Improved error handling for project root detection with proper fallbacks

## 2.1.4 - 2025-10-28

### Added

- Added `enable_asset_fallback` configuration option to control asset path fallback behavior
- Implemented asset path fallback mechanism: when processed asset files don't exist, the plugin now preserves original asset paths instead of replacing them with broken links

### Enhanced

- Improved asset processing robustness by adding existence checks for processed asset files
- Enhanced logging to provide better feedback when asset fallback occurs

## 2.1.3 - 2025-10-19

### Fixed

- Fixed smoke test script in order to public package to PyPI properly.

## 2.1.2 - 2025-10-19

### Fixed

- Use direct file system path for static files to fix the issue where the network graph static assets were not copied to the site directory.

### Added

- Added `MANIFEST.in` file to include the network graph static assets in the package.

## 2.1.1 - 2025-10-19

### Fixed

- Fixed the issue where the network graph static assets were not copied to the site directory by using the `os.path.join` instead of the `Path` class.


## 2.1.0 - 2025-10-19 (Network Graph Feature)

### Added

- **Network Graph Visualization**: Interactive network graph showing relationships between notes (#20)
  - Automatic link detection based on markdown links and wiki-style links
  - D3.js-powered interactive visualization with drag, zoom, and pan
  - Integration with Material for MkDocs theme
  - Graph data export in JSON format
  - Configurable node naming strategy (title or filename)
  - Debug logging for graph generation process

### Technical Details

- **New Module**: `utils/graphps/` for graph processing functionality
  - `graph.py`: Graph data structure and link detection
  - `handlers.py`: Graph handler for plugin integration
- **Static Assets**: Added `graph.js` and `graph.css` for frontend visualization
- **Configuration**: Added `enable_network_graph` and `graph_config` options
- **Build Integration**: Automatic graph generation during MkDocs build process

## 2.0.0 - 2025-10-17 (Structure-Breaking Changes)

### Changed

- **[BREAKING] Modular Architecture Refactoring**: Reorganized project structure from monolithic `core/` to modular `utils/` packages (#15)
  
  - Restructured modules by functional domains:
    
    - `utils/assetps/`: Asset processing and management
    
    - `utils/dataps/`: Data models and metadata management (includes frontmatter subsystem)
    
    - `utils/docsps/`: Document operations (create, move, remove, clean, process)
    
    - `utils/fileps/`: File I/O and scanning
    
    - `utils/pathps/`: Path processing utilities (reserved for future)
  
  - Introduced `ps` (Processors) naming convention for consistent module organization
  
  - Migration details:
    
    - `core/data_models.py` → `utils/dataps/meta.py`
    
    - `core/frontmatter_manager.py` → `utils/dataps/frontmatter/handlers.py`
    
    - `core/file_manager.py` → `utils/fileps/handlers.py`
    
    - `core/assets_manager.py` → `utils/assetps/handlers.py`
    
    - `core/note_manager.py` → `utils/docsps/handlers.py`
    
    - `core/note_creator.py` → `utils/docsps/creator.py`
    
    - `core/note_cleaner.py` → `utils/docsps/cleaner.py`
    
    - `core/note_initializer.py` → `utils/docsps/initializer.py`
    
    - `core/note_remover.py` → `utils/docsps/remover.py`
    
    - `core/notes_mover.py` → `utils/docsps/mover.py`
  
  - Updated all import paths throughout codebase (15+ files)
  
  - Updated all test files and mock paths
  
  - **Benefits**:
    
    - ✅ **Clear Separation of Concerns**: Each package focuses on single responsibility
    
    - ✅ **Better Extensibility**: Easy to add new features without modifying core
    
    - ✅ **Improved Maintainability**: Easier to locate and understand code
    
    - ✅ **Better Testing**: More focused unit tests per module

- **Test Suite Optimization**: Streamlined test suite for better focus
  
  - Removed 6 non-essential logger tests (testing framework behavior)
  
  - Test count: 240 → 227 tests
  
  - Maintained 100% pass rate
  
  - Code coverage: 71% overall

- **Asset Directory Structure**: Simplified asset directory organization from centralized to co-located structure
  
  - Assets are now placed next to their corresponding notes instead of in a centralized location
  
  - New pattern: `note_file.parent / "assets" / note_file.stem`
  
  - Examples:
    
    - Note: `docs/usage/contributing.md` → Assets: `docs/usage/assets/contributing/`
    
    - Note: `docs/notes/python/intro.md` → Assets: `docs/notes/python/assets/intro/`
  
  - **Benefits**:
    
    - ✅ Co-located: Assets are right next to their notes for easier management
    
    - ✅ Portable: Moving notes with their assets is straightforward
    
    - ✅ Consistent: No path mismatches when notes are outside `notes_dir`
    
    - ✅ Simpler: No dependency on `notes_dir` or `assets_dir` configuration
  
  - **Breaking Change**: Existing assets in centralized structure need migration
  
  - Updated components:
    
    - `NoteCreator._get_asset_directory()`: Simplified logic
    
    - `NoteRemover._get_asset_directory()`: Co-located pattern
    
    - `NoteMover._get_asset_directory()`: Co-located pattern
    
    - `NoteCleaner.find_orphaned_assets()`: Searches all `assets/` subdirectories
    
    - `NoteInitializer._analyze_asset_tree()`: Validates co-located structure

- **Configuration Deprecation**: `assets_dir` configuration option is now deprecated
  
  - The option is kept for backward compatibility but no longer used
  
  - Assets are automatically placed using the co-located pattern


### Security

- **Inconsistency with exclude_patterns in Note Operations** (#40): Fixed bug where plugin commands could create or move notes to excluded filenames, causing asset management conflicts
  
  - **Root Cause**: `NoteCreator` and `NoteMover` didn't check `exclude_patterns` configuration, allowing operations on `index.md` and `README.md` files that would later be ignored by `NoteScanner`, causing their asset directories to be incorrectly identified as orphaned by `NoteCleaner`
  
  - **Solution**: Added `exclude_patterns` validation across multiple components to enforce consistent behavior
  
  - **Changes**:
    
    - **NoteCreator**: Added validation in `create_new_note()` and `validate_note_creation()` to reject creation of excluded files
    
    - **NoteMover**: Added validation in `move_note()` to prevent moving/renaming to excluded filenames
    
    - **CLI**: Added validation in `move_note` command (mv/move) to check destination filenames
    
    - **Config Documentation**: Improved `exclude_patterns` docstring to clarify comprehensive scope of exclusion
    
    - **Tests**: Added 6 new test cases (4 for creator, 2 for mover) to verify exclusion behavior
  
  - **Impact**: Ensures consistent behavior across all plugin components - files excluded from management cannot be created, moved, or renamed through plugin commands
  
  - **User Experience**: Clear error messages guide users when attempting operations with excluded files, suggesting either using different filenames or updating configuration

- **CLI Error Message Clarity**: Improved contextual hints in `mkdocs-note new` command
  
  - **Issue**: The hint "Try running 'mkdocs-note init' first" was displayed for all validation errors, even when irrelevant (e.g., excluded filenames, file exists, unsupported extensions)
  
  - **Solution**: Made hints contextual - now only shows init suggestion when actually relevant (structure non-compliance, missing parent directory)
  
  - **Impact**: Users receive more relevant guidance based on the specific error they encounter


### Fixed

- **Template File Degradation** (#39): Fixed critical bug where template file was corrupted by tests
  
  - **Root Cause**: Test `test_note_initializer.py::test_ensure_template_file_exists` was writing to real project template file (`overrides/templates/default.md`) instead of using temporary files
  
  - **Impact**: Production template was degraded from proper frontmatter template to single-line comment: `# Template content`
  
  - **Solution**:
    
    - Restored template file with correct frontmatter structure
    
    - Updated test to use temporary paths with proper cleanup via try-finally
    
    - Modified `NoteInitializer._ensure_template_file()` to create complete default template instead of empty file
  
  - **Template Content**: Ensures new templates include proper frontmatter:
    
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
  
  - **Prevention**: Established test isolation best practice - always use temporary files/directories in tests

- **Test Configuration**: Corrected test assertions to match actual configuration defaults
  
  - `notes_template`: Updated assertion from `'docs/templates/default.md'` to `'overrides/templates/default.md'`
  
  - `notes_dir`: Updated assertions from `'docs/notes'` to `'docs'` (actual default)

### Added

- **Frontmatter Metadata System** (#15): Implemented comprehensive frontmatter management system for notes
  
  - Added `NoteFrontmatter` data class to `data_models.py` for storing note metadata
  
  - Created `frontmatter_manager.py` module with extensible metadata registration system:
    
    - `MetadataRegistry`: Central registry for managing metadata fields
    
    - `MetadataField`: Definition class for metadata fields with type validation
    
    - `FrontmatterParser`: YAML frontmatter parser for markdown files
    
    - `FrontmatterManager`: High-level facade for frontmatter operations
  
  - Standard metadata fields: `date`, `permalink`, `publish`
  
  - Support for custom metadata fields through registration interface
  
  - Metadata validation system with type checking and custom validators

- **Template System Enhancement**: Improved note template framework
  
  - Template variables now only substitute in frontmatter section, keeping note body clean
  
  - Support for both new frontmatter-style templates and legacy templates
  
  - Automatic detection and handling of template types
  
  - Updated default template with frontmatter structure

- **Metadata Integration**:
  
  - `NoteProcessor` now extracts frontmatter from markdown notes
  
  - `NoteInfo` dataclass extended with optional `frontmatter` field
  
  - `NoteCreator` generates notes with proper frontmatter structure

### Changed

- **Dependencies**: Added `pyyaml>=6.0` for YAML frontmatter parsing

- **Default Template**: Updated to include frontmatter with standard fields

- **Project Configuration**: Added `build-system` to `pyproject.toml` for proper package installation

### Technical Details

- **Extensibility**: Metadata system uses registration pattern for easy extension without modifying core code

- **Backward Compatibility**: Existing notes without frontmatter continue to work normally

- **Type Safety**: Comprehensive type hints throughout frontmatter system

- **Testing**: Added 31 unit tests for frontmatter management system (all passing)

### Documentation

- **Architecture Documentation**: Created comprehensive new `docs/architecture.md` for v2.0.0+
  
  - Documents modular architecture with detailed diagrams
  
  - Explains design decisions and rationale for refactoring
  
  - Includes migration guide from v1.x structure
  
  - Provides developer guidelines and extensibility examples
  
  - Covers all new modules: assetps, dataps, docsps, fileps, pathps

- **Legacy Documentation**: Preserved `docs/architecture-old.md` for v1.x reference

- Enhanced code documentation with detailed docstrings

- Added inline examples for metadata registration usage

### Testing

- **Test Results**: All 227 tests passing (100% success rate)
  
  - Migrated all test imports to new module paths
  
  - Updated all mock paths in test decorators
  
  - Fixed test file pollution issues
  
  - Test breakdown:
    
    - Asset management: 29 tests ✅
    
    - File management: 18 tests ✅
    
    - Frontmatter system: 31 tests ✅
    
    - Note cleaner: 16 tests ✅
    
    - Note creator: 19 tests ✅
    
    - Note initializer: 13 tests ✅
    
    - Note manager: 34 tests ✅
    
    - Note remover: 6 tests ✅
    
    - Configuration: 23 tests ✅
    
    - Plugin: 29 tests ✅
    
    - Smoke tests: 4 tests ✅
    
    - Help: 5 tests ✅

- **Code Coverage**: 71% overall coverage maintained

## 1.2.5 - 2025-10-13

### Fixed

- Fix some dependencies issues in `pyproject.toml`

### Changed

- Remove `setup.py` and `requirements.txt`, use `pyproject.toml` instead.


## 1.2.4 - 2025-10-13

### Fixed

- **Dependencies**: Added `mkdocs-material>=9.6.4` to `pyproject.toml` and `setup.py`


## 1.2.3 - 2025-10-13

### Fixed

- **Dependencies**: Added `mkdocs-material>=9.6.14`, `mkdocs-jupyter>=0.25.1`, `mkdocs-minify-plugin>=0.8.0`, `mkdocs-git-revision-date-localized-plugin>=1.4.0` to `pyproject.toml` and `setup.py`


## 1.2.2 - 2025-10-13

### Fixed

- **Dependencies**: Added `pyyaml>=6.0` and `pymdown-extensions>=10.15` to `pyproject.toml` and `setup.py`


## 1.2.1 - 2025-10-13

### Fixed

- **CLI Configuration Loading**: Fixed CLI tools not respecting user's custom configuration from `mkdocs.yml` (#23)
  
  - Previously, CLI commands (`validate`, `init`, `new`, etc.) always used default configuration values, ignoring user's custom settings in `mkdocs.yml`
  
  - This caused commands to operate on wrong directories (e.g., validating `docs/notes` when user configured `docs/usage`)
  
  - Implemented `load_config_from_mkdocs_yml()` function to parse and load plugin configuration from `mkdocs.yml`
  
  - Added automatic `mkdocs.yml` file discovery in current and parent directories
  
  - CLI now correctly applies user's custom configuration for all commands
  
  - Added comprehensive unit tests for configuration loading functionality


## 1.2.0 - 2025-10-11

### Added

- **CLI Note Removal**: Added `mkdocs-note remove` (alias: `rm`) command for deleting notes and their asset directories (#19)
  
  - Removes note file and its corresponding asset directory
  
  - Option `--keep-assets` to preserve asset directory while removing note
  
  - Option `--yes` / `-y` to skip confirmation prompt
  
  - Automatically cleans up empty parent directories after removal
  
  - Validates file extension before removal

- **CLI Orphaned Assets Cleanup**: Added `mkdocs-note clean` command for cleaning up orphaned asset directories (#19)
  
  - Scans notes directory and assets directory to find orphaned assets
  
  - Identifies asset directories without corresponding note files
  
  - Option `--dry-run` to preview what would be removed without actually removing
  
  - Option `--yes` / `-y` to skip confirmation prompt
  
  - Automatically cleans up empty parent directories after cleanup

- **CLI Note Movement**: Added `mkdocs-note move` (alias: `mv`) command for moving/renaming notes and directories
  
  - Mimics shell `mv` command behavior: if destination exists and is a directory, moves source into it
  
  - Moves or renames note file or entire directory with its asset directories simultaneously
  
  - Supports moving single notes or entire directories with all notes inside
  
  - Supports both simple renaming and moving into existing directories
  
  - Example: `mkdocs-note mv docs/notes/dsa/ds/trees docs/notes/dsa` moves to `docs/notes/dsa/trees`
  
  - Option `--keep-source-assets` to preserve source asset directory
  
  - Option `--yes` / `-y` to skip confirmation prompt
  
  - Automatically creates necessary parent directories
  
  - Automatically cleans up empty parent directories in source location
  
  - Includes rollback mechanism in case of errors
  
  - Intelligently handles tree-based asset structure when moving directories

- **Core Modules**: Added new core modules for note management
  
  - `note_remover.py`: Handles note file and asset directory removal
  
  - `note_cleaner.py`: Manages orphaned asset cleanup and note movement operations

  - `notes_mover.py`: Handles note file and directory movement and renaming with their assets correspondingly
  
  - Both modules properly handle tree-based asset structure with `.assets` suffix

### Changed

- **CLI User Experience**: Enhanced CLI commands with better user feedback
  
  - Added emoji indicators for better visual feedback (✅, ❌, ⚠️, 📝, 📁, 🔍)
  
  - Added clear confirmation prompts for destructive operations
  
  - Improved error messages with helpful suggestions

## 1.1.4 - 2025-10-09

### Fixed

- **CLI Note Creation**: Fixed `mkdocs-note new` command validation logic issue (#14)
  
  - Previously, the command was using `file_path.parent` as the notes directory for validation, causing incorrect asset tree structure checks
  
  - This resulted in `validate` command passing but `new` command failing with "Asset tree structure is not compliant" errors
  
  - Now both `create_new_note()` and `validate_note_creation()` methods use the configured `notes_dir` from settings for consistent validation
  
  - This ensures that `mkdocs-note validate` and `mkdocs-note new` use the same validation logic


## 1.1.3 - 2025-10-08

### Added

- **Timestamp Configuration**: Added `timestamp_zone` configuration option (default: `UTC+0`) to ensure consistent timestamp display across different deployment environments

  - Implemented automatic fallback to UTC timezone when invalid timezone format is provided

  - Added comprehensive documentation for timestamp configuration options

### Fixed

- **Timestamp Display**: Fixed issue where timestamp was not displayed correctly in note files - plugin now uses configured timezone for timestamp display


## 1.1.2 - 2025-10-06

### Fixed

- Fixed `mkdocs-note init` command to correctly use tree-based asset directory structure
  
  - Previously, the init command was creating asset directories in a flat structure (e.g., `assets/note-name/`) instead of mirroring the notes directory hierarchy
  
  - Now uses `get_note_relative_path()` function consistently across all components to ensure proper tree-based structure
  
  - Updated `_check_compliance()` method to correctly validate tree-based structures with `.assets` suffix on first-level subdirectories
  
  - This ensures that `mkdocs-note init` and `mkdocs-note new` create consistent directory structures


## 1.1.1 - 2025-10-06

### Changed

- **[BREAKING CHANGE]** Improved assets manager to use tree-based path structure instead of linear table

  - Assets are now organized by note's relative path from notes directory, preventing conflicts between notes with same name in different subdirectories

  - First-level subdirectories in assets tree now have `.assets` suffix for better identification (e.g., `assets/dsa.assets/anal/intro/` for note `dsa/anal/intro.md`)

  - Updated `AssetsCatalogTree` to support hierarchical path management

  - Updated `AssetsProcessor` to calculate asset paths based on note's relative location

  - Updated `NoteCreator` to create asset directories using the new path structure

  - Improved asset path conversion in plugin to use correct relative paths from note file location

### Fixed

- Fixed asset directory conflicts when notes have the same name but exist in different paths (#10)

- Fixed asset link replacement issues in note files - plugin now correctly converts relative image references to proper paths during MkDocs build (#10)

- Fixed path resolution in plugin to properly handle `docs_dir` and calculate correct relative paths for assets


## 1.1.0 - 2025-10-05

### Added

- **Command Line Interface**: Added comprehensive CLI commands for note management

  - `mkdocs note init`: Initialize notes directory with proper asset structure

  - `mkdocs note new`: Create new notes with template support

  - `mkdocs note validate`: Validate asset tree structure compliance

  - `mkdocs note template`: Manage note templates

- **Asset Management System**: Complete asset management infrastructure

  - Automatic asset directory creation for each note

  - Asset tree structure validation and compliance checking

  - Asset path processing and linking during build

  - Support for image references and media files

- **Template System**: Flexible note template system with variable substitution

  - Configurable note templates with `{{title}}`, `{{date}}`, and `{{note_name}}` variables

  - Default template with proper structure

  - Custom template support via CLI

  - Template validation and creation tools

- **Note Initializer**: Comprehensive note directory initialization

  - Asset tree analysis and compliance checking

  - Automatic structure repair for non-compliant directories

  - Index file creation with proper markers

  - Template file management

- **Note Creator**: Advanced note creation with validation

  - Template-based note generation

  - Asset directory creation

  - Structure compliance validation

  - Custom template support

- **Enhanced Configuration**: New configuration options

  - `assets_dir`: Directory for storing note assets

  - `notes_template`: Template file for new notes

  - `cache_size`: Performance optimization cache size

### Changed

- **Asset Integration**: Seamless asset management integration

  - Automatic asset path processing in markdown content

  - Asset directory structure enforcement

  - Improved asset linking and organization

- **Template Processing**: Enhanced template system

  - Variable substitution with proper formatting

  - Fallback template support

  - Template validation and error handling

### Fixed

- **Test Coverage**: Comprehensive test suite improvements

  - Fixed template content generation tests

  - Enhanced test coverage for new components

  - Improved test reliability and accuracy

- **Documentation**: Complete documentation updates

  - Updated README with new features

  - Added CLI usage examples

  - Enhanced configuration documentation

  - Improved troubleshooting guides


## 1.0.3 - 2025-10-04

### Added

- Added PyPI CI

- Added smoke test script

- Added release script


## 1.0.2 - 2025-10-03

### Fixed

- Fixed sorting inconsistency between local development and remote deployment environments

- Resolved issue where notes were sorted alphabetically instead of by modification time on deployed sites

### Added

- Added `use_git_timestamps` configuration option (default: `true`) to use Git commit timestamps for consistent sorting

- Implemented automatic fallback to file system timestamps when Git is not available

- Added comprehensive documentation for sorting behavior and deployment considerations

### Changed

- Modified note processing logic to prioritize Git commit timestamps over file system timestamps

- Enhanced sorting reliability across different deployment platforms (Vercel, Netlify, GitHub Pages)

- Updated README with detailed explanation of sorting behavior and configuration options


## 1.0.1 - 2025-10-03

### Fixed

- fix the configuration validation issue in #2


## 1.0.0 - 2025-10-02

### Removed

- All of before

### Changed

- Refactored the underlying file management and note management logic.

- Refactored the calling logic and data flow of note management.

- Now only one feature which can insert recent notes at index page of notebook directory has been implemented.

- All things are to be restored, step by step!

### Fixed

- Documented common configuration issues, especially YAML indentation errors that cause "Invalid config options" errors

### Added

<!-- - Added comprehensive [Troubleshooting Guide](troubleshooting.md) for common configuration issues -->

- Added configuration format warnings in README documentation

- Documented Jupyter DeprecationWarning explanation (not a plugin error)


## 0.0.1 - 2025-09-05

### Added

- The project was initialized 

- The initial framework is based on https://github.com/stalomeow/note/blob/5fa56a9fdfa4c9b6511c5dc0c3d3620ae0aa04c3/scripts/obsidian.py

- However, the framework and features are too redundant to continue development and maintenance independently for me.
