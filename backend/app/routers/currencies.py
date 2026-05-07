import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Account, Currency, ExchangeRate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["currencies"])


class CurrencyCreate(BaseModel):
    code: str
    name: str


class CurrencyRead(BaseModel):
    code: str
    name: str


@router.get("/currencies", response_model=list[CurrencyRead])
def list_currencies(session: Session = Depends(get_session)) -> list[CurrencyRead]:
    return [
        CurrencyRead(code=c.code, name=c.name)
        for c in session.exec(select(Currency)).all()
    ]


@router.post("/currencies", response_model=CurrencyRead, status_code=201)
def create_currency(
    body: CurrencyCreate, session: Session = Depends(get_session)
) -> CurrencyRead:
    if session.get(Currency, body.code):
        raise HTTPException(
            status_code=409, detail=f"Currency '{body.code}' already exists"
        )
    currency = Currency(code=body.code, name=body.name)
    session.add(currency)
    session.commit()
    session.refresh(currency)
    return CurrencyRead(code=currency.code, name=currency.name)


@router.get("/currencies/{code}", response_model=CurrencyRead)
def get_currency(code: str, session: Session = Depends(get_session)) -> CurrencyRead:
    currency = session.get(Currency, code)
    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency '{code}' not found")
    return CurrencyRead(code=currency.code, name=currency.name)


@router.delete("/currencies/{code}", status_code=204)
def delete_currency(code: str, session: Session = Depends(get_session)) -> None:
    currency = session.get(Currency, code)
    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency '{code}' not found")
    if session.exec(select(Account).where(Account.currency_code == code)).first():
        raise HTTPException(
            status_code=409,
            detail=f"Currency '{code}' is referenced by one or more accounts",
        )
    if session.exec(
        select(ExchangeRate).where(ExchangeRate.currency_code == code)
    ).first():
        raise HTTPException(
            status_code=409,
            detail=f"Currency '{code}' is referenced by one or more exchange rates",
        )
    session.delete(currency)
    session.commit()
