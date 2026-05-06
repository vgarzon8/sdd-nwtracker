import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI

from app.config import (
    APP_VERSION,
    LOG_BACKUP_COUNT,
    LOG_FILE,
    LOG_LEVEL,
    LOG_MAX_BYTES,
)
from app.routers import health

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_log_path = (_BACKEND_DIR / LOG_FILE).resolve()
_log_path.parent.mkdir(parents=True, exist_ok=True)

_fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s")

_file_handler = RotatingFileHandler(
    _log_path,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
)
_file_handler.setFormatter(_fmt)

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_fmt)

logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[_file_handler, _stream_handler],
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="nwtracker",
    description="Personal net worth tracker API",
    version=APP_VERSION,
)

app.include_router(health.router)
