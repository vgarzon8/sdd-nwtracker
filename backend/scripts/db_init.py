import app.models  # noqa: F401 — registers SQLModel tables with metadata
from app.db import init_db


def main() -> None:
    init_db()
    print("Database initialized.")


if __name__ == "__main__":
    main()
