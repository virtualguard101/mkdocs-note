#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
SRC_DIR=$(realpath "$SCRIPT_DIR/../src")

export PYTHONPATH="$SRC_DIR"

if ! command -v uv &> /dev/null
then
    echo "uv could not be found, please install it."
    exit 1
fi

PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")

# Check for virtual environment and install dependencies if it doesn't exist
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Creating virtual environment and installing dependencies"
    uv venv -p python3 "$PROJECT_ROOT/.venv"
    uv pip install -e ".[dev]"
fi

run_tests() {
    if [ -z "$1" ]; then
        # Run all tests and generate a coverage report
        echo "Running all tests with coverage..."
echo "Test files:"
echo "  - test_config.py (PluginConfig tests)"
echo "  - core/test_file_manager.py (NoteScanner, AssetScanner tests)"
        echo "  - core/test_note_manager.py (NoteProcessor, CacheManager, IndexUpdater, RecentNotesUpdater tests)"
        echo "  - core/test_note_creator.py (NoteCreator tests)"
        echo "  - core/test_note_initializer.py (NoteInitializer tests)"
        echo "  - core/test_assets_manager.py (AssetsProcessor, AssetsManager tests)"
        echo "  - test_plugin.py (MkdocsNotePlugin tests)"
        echo ""
        uv run pytest --cov=src/mkdocs_note --cov-report=term-missing tests/
    else
        # Run specific tests and generate a coverage report
        echo "Running tests for:" "$@"
        uv run pytest --cov=src/mkdocs_note --cov-report=term-missing "$@"
    fi
}

run_unit_tests() {
    echo "Running unit tests only..."
    uv run pytest tests/test_config.py tests/core/ tests/test_plugin.py -v
}

run_smoke_tests() {
    echo "Running smoke tests..."
    uv run python tests/smoke_test.py
}

run_integration_tests() {
    echo "Running integration tests..."
    # Add integration tests here when available
    echo "No integration tests available yet."
}

show_help() {
    echo "Usage: $0 [OPTIONS] [TEST_FILES...]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -u, --unit          Run unit tests only"
    echo "  -s, --smoke         Run smoke tests only"
    echo "  -i, --integration   Run integration tests only"
    echo "  -c, --coverage      Run tests with coverage report (default)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run all tests with coverage"
    echo "  $0 -u               # Run unit tests only"
    echo "  $0 -s               # Run smoke tests only"
    echo "  $0 test_config.py   # Run specific test file"
    echo "  $0 -c tests/core/   # Run core tests with coverage"
}

# Parse command line arguments
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    -u|--unit)
        run_unit_tests
        exit 0
        ;;
    -s|--smoke)
        run_smoke_tests
        exit 0
        ;;
    -i|--integration)
        run_integration_tests
        exit 0
        ;;
    -c|--coverage)
        shift
        run_tests "$@"
        ;;
    *)
        # Check for a specific test file argument
        if [ "$#" -gt 0 ]; then
            run_tests "$@"
        else
            run_tests
        fi
        ;;
esac