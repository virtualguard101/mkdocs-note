# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Changed

- **[BREAKING CHANGE]** Improved assets manager to use tree-based path structure instead of linear table

  - Assets are now organized by note's relative path from notes directory, preventing conflicts between notes with same name in different subdirectories

  - First-level subdirectories in assets tree now have `.assets` suffix for better identification (e.g., `assets/dsa.assets/anal/intro/` for note `dsa/anal/intro.md`)

  - Updated `AssetsCatalogTree` to support hierarchical path management

  - Updated `AssetsProcessor` to calculate asset paths based on note's relative location

  - Updated `NoteCreator` to create asset directories using the new path structure

### Fixed

- Fixed asset directory conflicts when notes have the same name but exist in different paths (#10)

- Fixed asset link replacement issues in note files caused by path matching problems


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

- Added comprehensive [Troubleshooting Guide](TROUBLESHOOTING.md) for common configuration issues

- Added configuration format warnings in README documentation

- Documented Jupyter DeprecationWarning explanation (not a plugin error)


## 0.0.1 - 2025-09-05

### Added

- The project was initialized 

- The initial framework is based on https://github.com/stalomeow/note/blob/5fa56a9fdfa4c9b6511c5dc0c3d3620ae0aa04c3/scripts/obsidian.py

- However, the framework and features are too redundant to continue development and maintenance independently for me.
