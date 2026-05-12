import logging
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.db import get_session
from app.services.csv_export import export_to_zip
from app.services.csv_import import ImportResult, import_from_zip
from app.services.raw_csv_export import export_raw_to_zip
from app.services.raw_csv_import import import_raw_from_zip

logger = logging.getLogger(__name__)

router = APIRouter(tags=["csv"])


@router.get("/export")
def export_csv(
    format: Literal["friendly", "raw"] = "friendly",
    session: Session = Depends(get_session),
) -> StreamingResponse:
    today = date.today().isoformat()
    if format == "raw":
        zip_bytes = export_raw_to_zip(session)
        filename = f"nwtracker-raw-{today}.zip"
    else:
        zip_bytes = export_to_zip(session)
        filename = f"nwtracker-{today}.zip"
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", response_model=ImportResult)
def import_csv(
    format: Literal["friendly", "raw"] = "friendly",
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImportResult:
    zip_bytes = file.file.read()
    if format == "raw":
        result = import_raw_from_zip(zip_bytes, session)
    else:
        result = import_from_zip(zip_bytes, session)
    session.commit()
    return result
