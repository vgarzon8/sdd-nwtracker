backend := "backend"

db-init:
    uv run --project {{backend}} db-init

db-seed:
    uv run --project {{backend}} db-seed

test:
    uv run --project {{backend}} pytest

lint:
    uv run --project {{backend}} ruff check {{backend}}/app {{backend}}/scripts {{backend}}/tests
    uv run --project {{backend}} ruff format --check {{backend}}/app {{backend}}/scripts {{backend}}/tests

typecheck:
    uv run --project {{backend}} mypy {{backend}}/app {{backend}}/scripts {{backend}}/tests
