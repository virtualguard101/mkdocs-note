# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.0.1 - 2025-09-05

### Added

- The project was initialized 

- The initial framework is based on https://github.com/stalomeow/note/blob/5fa56a9fdfa4c9b6511c5dc0c3d3620ae0aa04c3/scripts/obsidian.py

- However, the framework and features are too redundant to continue development and maintenance independently for me.

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

## 1.0.1 - 2025-10-03

### Fixed

- fix the configuration validation issue in #2
