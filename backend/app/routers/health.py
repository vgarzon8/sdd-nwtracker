import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session

from app.config import APP_VERSION
from app.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthOkResponse(BaseModel):
    status: str
    db: str
    version: str


class HealthDegradedResponse(BaseModel):
    status: str
    db: str


@router.get(
    "/health",
    response_model=HealthOkResponse,
    responses={503: {"model": HealthDegradedResponse}},
    tags=["ops"],
)
def health(session: Session = Depends(get_session)) -> HealthOkResponse | JSONResponse:
    try:
        session.exec(text("SELECT 1"))  # type: ignore[call-overload]
    except Exception:
        logger.exception("DB health check failed")
        return JSONResponse(
            status_code=503,
            content=HealthDegradedResponse(status="degraded", db="error").model_dump(),
        )

    return HealthOkResponse(status="ok", db="ok", version=APP_VERSION)
