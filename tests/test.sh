#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
TEST_DIR="$SCRIPT_DIR"
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
        uv run pytest --cov=src/mkdocs_note --cov-report=term-missing tests/
    else
        # Run specific tests and generate a coverage report
        echo "Running tests for:" "$@"
        uv run pytest --cov=src/mkdocs_note --cov-report=term-missing "$@"
    fi
}

# Check for a specific test file argument
if [ "$#" -gt 0 ]; then
    run_tests "$@"
else
    run_tests
fi