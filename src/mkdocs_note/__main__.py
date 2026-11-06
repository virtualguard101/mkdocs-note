"""Entry point for ``python -m mkdocs_note``.

The git filter runs ``<python> -m mkdocs_note crypt …`` so it keeps working
even when the ``mkdocs-note`` console script is not on ``PATH``.
"""

from mkdocs_note.cli import cli


if __name__ == "__main__":
	cli()
