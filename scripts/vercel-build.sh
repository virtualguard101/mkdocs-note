#!/bin/bash

# Unshallow the git repository to get full commit history
# This is required for accurate git timestamps in mkdocs-note plugin
if [ -d .git ]; then
    echo "Fetching full git history..."
    git fetch --unshallow || echo "Repository is already complete"
    git fetch --all
else
    echo "Warning: Not a git repository, git timestamps will not be available"
fi

# Activate virtual environment and build
source env/bin/activate
mkdocs build --strict -d public
