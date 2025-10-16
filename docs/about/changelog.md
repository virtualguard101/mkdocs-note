# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] (Structure-Breaking Changes)

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
