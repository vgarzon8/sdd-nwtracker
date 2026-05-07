import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import Currency, ExchangeRate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exchange-rates"])


class ExchangeRateCreate(BaseModel):
    currency_code: str
    month: str
    rate: Decimal


class ExchangeRateRead(BaseModel):
    id: int
    currency_code: str
    month: str
    rate: Decimal


class ExchangeRateUpdate(BaseModel):
    rate: Decimal


def _read(er: ExchangeRate) -> ExchangeRateRead:
    assert er.id is not None
    return ExchangeRateRead(
        id=er.id,
        currency_code=er.currency_code,
        month=er.month,
        rate=er.rate,
    )


@router.get("/exchange-rates", response_model=list[ExchangeRateRead])
def list_exchange_rates(
    currency: str | None = None,
    month: str | None = None,
    session: Session = Depends(get_session),
) -> list[ExchangeRateRead]:
    stmt = select(ExchangeRate)
    if currency is not None:
        stmt = stmt.where(ExchangeRate.currency_code == currency)
    if month is not None:
        stmt = stmt.where(ExchangeRate.month == month)
    return [_read(er) for er in session.exec(stmt).all()]


@router.post("/exchange-rates", response_model=ExchangeRateRead, status_code=201)
def create_exchange_rate(
    body: ExchangeRateCreate, session: Session = Depends(get_session)
) -> ExchangeRateRead:
    if not session.get(Currency, body.currency_code):
        raise HTTPException(
            status_code=404, detail=f"Currency '{body.currency_code}' not found"
        )
    if body.rate <= 0:
        raise HTTPException(status_code=422, detail="Rate must be positive")
    er = ExchangeRate(
        currency_code=body.currency_code, month=body.month, rate=body.rate
    )
    session.add(er)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Exchange rate for '{body.currency_code}'"
                f" in {body.month} already exists"
            ),
        )
    session.refresh(er)
    return _read(er)


@router.get("/exchange-rates/{rate_id}", response_model=ExchangeRateRead)
def get_exchange_rate(
    rate_id: int, session: Session = Depends(get_session)
) -> ExchangeRateRead:
    er = session.get(ExchangeRate, rate_id)
    if not er:
        raise HTTPException(
            status_code=404, detail=f"Exchange rate {rate_id} not found"
        )
    return _read(er)


@router.put("/exchange-rates/{rate_id}", response_model=ExchangeRateRead)
def update_exchange_rate(
    rate_id: int,
    body: ExchangeRateUpdate,
    session: Session = Depends(get_session),
) -> ExchangeRateRead:
    er = session.get(ExchangeRate, rate_id)
    if not er:
        raise HTTPException(
            status_code=404, detail=f"Exchange rate {rate_id} not found"
        )
    if body.rate <= 0:
        raise HTTPException(status_code=422, detail="Rate must be positive")
    er.rate = body.rate
    session.add(er)
    session.commit()
    session.refresh(er)
    return _read(er)


@router.delete("/exchange-rates/{rate_id}", status_code=204)
def delete_exchange_rate(
    rate_id: int, session: Session = Depends(get_session)
) -> Response:
    er = session.get(ExchangeRate, rate_id)
    if not er:
        raise HTTPException(
            status_code=404, detail=f"Exchange rate {rate_id} not found"
        )
    session.delete(er)
    session.commit()
    return Response(status_code=204)
