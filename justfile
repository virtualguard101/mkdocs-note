alias t := test
alias p := publish
alias s := serve

test OPTIONS="":
    ./tests/test.sh {{ OPTIONS }}

publish VERSION:
    git checkout main
    git pull origin main
    git tag -a {{ VERSION }}
    git push --tags

check:
    uvx ruff check

format:
    uvx ruff format

serve:
    uv run mkdocs serve

bootstrap:
    uv sync --extra dev
    uv run pre-commit install
