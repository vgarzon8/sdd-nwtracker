import logging
from datetime import date

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.db import get_session
from app.services.csv_export import export_to_zip
from app.services.csv_import import ImportResult, import_from_zip

logger = logging.getLogger(__name__)

router = APIRouter(tags=["csv"])


@router.get("/export")
def export_csv(session: Session = Depends(get_session)) -> StreamingResponse:
    zip_bytes = export_to_zip(session)
    filename = f"nwtracker-{date.today().isoformat()}.zip"
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", response_model=ImportResult)
def import_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImportResult:
    zip_bytes = file.file.read()
    result = import_from_zip(zip_bytes, session)
    session.commit()
    return result
