---
date: 2025-10-15 01:06:51
title: Contributing
permalink: 
publish: true
---

# Contributing to MkDocs Note

First off, thank you for considering contributing to MkDocs Note! It's people like you that make the open-source community such a great place.

## How Can I Contribute?

There are many ways to contribute, from writing documentation and tutorials to reporting bugs and submitting code changes.

### Reporting Bugs

If you find a bug, please open an issue and provide the following information:

- A clear and descriptive title.

- A detailed description of the problem, including steps to reproduce it.

- Your `MkDocs` configuration (`mkdocs.yml`).

- Any relevant error messages or logs.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it. This allows us to coordinate our efforts and avoid duplicating work.

## Development Setup

To get started with local development, follow these steps:

1.  **Fork and Clone the Repository**

    ```bash
    git clone https://github.com/YOUR_USERNAME/mkdocs-note.git
    cd mkdocs-note
    ```

2.  **Set Up the Environment**

    It's strongly recommended to use a virtual environment, and recommended to use [uv](https://docs.astral.sh/uv/) to manage project configuration and virtual environment.

    ```bash
    uv init
    ```

3.  **Install Dependencies**

    Install the project in editable mode along with the development dependencies.

    ```bash
    uv sync --extra dev
    ```

4.  **Run Tests**

    To make sure everything is set up correctly, run the test suite:

    ```bash
    ./tests/test.sh
    ```

    Or use `pytest` directly:

    ```bash
    uv run pytest
    ```

## Pull Request Process

1.  Ensure any new code is covered by tests.

2.  Update the documentation if you've added or changed any features.

3.  Make sure the test suite passes (`pytest`).

4.  Submit your pull request!

Thank you for your contribution!
