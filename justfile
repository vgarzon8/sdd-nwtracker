backend := "backend"

db-init:
    uv run --project {{backend}} db-init

db-seed:
    uv run --project {{backend}} db-seed

test:
    uv run --project {{backend}} pytest

lint:
    uv run --project {{backend}} ruff check app
    uv run --project {{backend}} ruff format --check app

typecheck:
    uv run --project {{backend}} mypy app
