# MkDocs-Note Test Suite

This directory contains comprehensive unit tests for the MkDocs-Note plugin, covering all major components of the refactored architecture.

## Test Structure

### Core Tests (`tests/core/`)

#### `test_file_manager.py`
Tests for the `FileScanner` class:
- File scanning functionality
- File validation (extension, patterns, directories)
- Error handling (permission errors, missing directories)
- Configuration integration

#### `test_note_manager.py`
Tests for note processing components:
- **`NoteInfo`**: Data class validation
- **`NoteProcessor`**: Note file processing, title extraction, URL generation
- **`CacheManager`**: Cache invalidation logic
- **`IndexUpdater`**: Index file updates, HTML generation
- **`RecentNotesUpdater`**: End-to-end update workflow

### Plugin Tests (`tests/`)

#### `test_config.py`
Tests for the `PluginConfig` class:
- Default value validation
- Configuration type checking
- Path relationship validation
- Marker consistency

#### `test_logger.py`
Tests for the `Logger` class:
- Logger initialization
- Log level configuration
- Handler setup
- Method functionality (debug, info, warning, error)

#### `test_plugin.py`
Tests for the main `MkdocsNotePlugin` class:
- Plugin initialization
- Configuration handling
- File processing workflow
- Markdown processing
- Recent notes insertion

## Running Tests

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- Virtual environment (automatically created by test script)

### Quick Start
```bash
# Run all tests with coverage
./tests/test.sh

# Run unit tests only
./tests/test.sh -u

# Run specific test file
./tests/test.sh test_config.py

# Show help
./tests/test.sh -h
```

### Manual Testing
```bash
# Using pytest directly
cd tests
uv run pytest -v

# With coverage
uv run pytest --cov=src/mkdocs_note --cov-report=term-missing

# Specific test file
uv run pytest test_config.py -v
```

## Test Coverage

The test suite aims for comprehensive coverage of:

- ✅ **Configuration Management**: All config options and validation
- ✅ **File Operations**: Scanning, validation, and processing
- ✅ **Note Processing**: Title extraction, metadata handling
- ✅ **Caching**: Cache invalidation and update detection
- ✅ **HTML Generation**: Recent notes list formatting
- ✅ **Plugin Integration**: MkDocs plugin lifecycle
- ✅ **Error Handling**: Exception scenarios and edge cases

## Test Categories

### Unit Tests
- Individual component testing
- Mocked dependencies
- Isolated functionality validation

### Integration Tests
- Component interaction testing
- End-to-end workflows
- Real file system operations (when needed)

## Mocking Strategy

Tests use extensive mocking to:
- Isolate components from external dependencies
- Simulate file system operations
- Control test data and scenarios
- Ensure fast, reliable test execution

## Continuous Integration

The test suite is designed to run in CI environments:
- No external dependencies required
- Deterministic test results
- Comprehensive error reporting
- Coverage reporting integration

## Adding New Tests

When adding new functionality:

1. **Create test file** in appropriate directory
2. **Follow naming convention**: `test_<component>.py`
3. **Use descriptive test names**: `test_<method>_<scenario>`
4. **Mock external dependencies**: File system, network, etc.
5. **Test edge cases**: Error conditions, boundary values
6. **Update this README**: Document new test coverage

## Test Data

Test data is generated programmatically using mocks and fixtures:
- No external test files required
- Consistent test scenarios
- Easy to maintain and update

## Performance

The test suite is optimized for speed:
- Parallel test execution where possible
- Minimal file I/O operations
- Efficient mocking strategies
- Fast feedback loop for development
