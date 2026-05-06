import os
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend/ project root regardless of CWD.
# __file__ is backend/app/config.py → .parent.parent is backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL", "sqlite:///./data/sqlite/nwtracker.db"
)

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE: str = os.environ.get("LOG_FILE", "logs/nwtracker.log")
LOG_MAX_BYTES: int = int(os.environ.get("LOG_MAX_BYTES", "10485760"))
LOG_BACKUP_COUNT: int = int(os.environ.get("LOG_BACKUP_COUNT", "5"))

APP_VERSION: str = version("backend")
