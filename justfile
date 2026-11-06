alias t := test
alias p := publish
alias s := serve

test OPTIONS="":
    uv run pytest {{ OPTIONS }}

# Publish a tagged release from the merged remote main.
publish VERSION:
    # Do not check out main: switching branches can break the encrypted-notes
    # git filter.
    git fetch origin main
    git tag -a {{ VERSION }} origin/main -m "{{ VERSION }}"
    git push origin {{ VERSION }}

check:
    uvx ruff check

format:
    uvx ruff format

serve:
    uv run mkdocs serve

bootstrap:
    uv sync --extra dev
    uv run pre-commit install
