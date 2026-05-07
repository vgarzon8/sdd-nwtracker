import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import Account, AccountSide, Balance

logger = logging.getLogger(__name__)

router = APIRouter(tags=["balances"])


class BalanceCreate(BaseModel):
    account_id: int
    month: str
    amount: int


class BalanceRead(BaseModel):
    id: int
    account_id: int
    month: str
    amount: int


class BalanceReadDetail(BaseModel):
    id: int
    account_id: int
    month: str
    amount: int
    account_name: str
    institution_id: int
    currency_code: str
    side: AccountSide


class BalanceUpdate(BaseModel):
    amount: int


def _detail(balance: Balance, account: Account) -> BalanceReadDetail:
    assert balance.id is not None
    return BalanceReadDetail(
        id=balance.id,
        account_id=balance.account_id,
        month=balance.month,
        amount=balance.amount,
        account_name=account.name,
        institution_id=account.institution_id,
        currency_code=account.currency_code,
        side=account.side,
    )


def _read(balance: Balance) -> BalanceRead:
    assert balance.id is not None
    return BalanceRead(
        id=balance.id,
        account_id=balance.account_id,
        month=balance.month,
        amount=balance.amount,
    )


@router.get("/balances", response_model=list[BalanceReadDetail] | list[BalanceRead])
def list_balances(
    month: str | None = None,
    session: Session = Depends(get_session),
) -> list[BalanceReadDetail] | list[BalanceRead]:
    if month is not None:
        stmt = select(Balance, Account).join(Account).where(Balance.month == month)
        rows = session.exec(stmt).all()
        return [_detail(b, a) for b, a in rows]
    balances = session.exec(select(Balance)).all()
    return [_read(b) for b in balances]


@router.post("/balances", response_model=BalanceRead, status_code=201)
def create_balance(
    body: BalanceCreate, session: Session = Depends(get_session)
) -> BalanceRead:
    if not session.get(Account, body.account_id):
        raise HTTPException(
            status_code=404, detail=f"Account {body.account_id} not found"
        )
    balance = Balance(account_id=body.account_id, month=body.month, amount=body.amount)
    session.add(balance)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Balance for account {body.account_id}"
                f" in {body.month} already exists"
            ),
        )
    session.refresh(balance)
    return _read(balance)


@router.get("/balances/{balance_id}", response_model=BalanceReadDetail)
def get_balance(
    balance_id: int, session: Session = Depends(get_session)
) -> BalanceReadDetail:
    balance = session.get(Balance, balance_id)
    if not balance:
        raise HTTPException(status_code=404, detail=f"Balance {balance_id} not found")
    account = session.get(Account, balance.account_id)
    assert account is not None
    return _detail(balance, account)


@router.put("/balances/{balance_id}", response_model=BalanceRead)
def update_balance(
    balance_id: int,
    body: BalanceUpdate,
    session: Session = Depends(get_session),
) -> BalanceRead:
    balance = session.get(Balance, balance_id)
    if not balance:
        raise HTTPException(status_code=404, detail=f"Balance {balance_id} not found")
    balance.amount = body.amount
    session.add(balance)
    session.commit()
    session.refresh(balance)
    return _read(balance)


@router.delete("/balances/{balance_id}", status_code=204)
def delete_balance(
    balance_id: int, session: Session = Depends(get_session)
) -> Response:
    balance = session.get(Balance, balance_id)
    if not balance:
        raise HTTPException(status_code=404, detail=f"Balance {balance_id} not found")
    session.delete(balance)
    session.commit()
    return Response(status_code=204)
