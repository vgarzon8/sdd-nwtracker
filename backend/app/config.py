import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend/ project root regardless of CWD.
# __file__ is backend/app/config.py → .parent.parent is backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL", "sqlite:///./data/sqlite/nwtracker.db"
)
