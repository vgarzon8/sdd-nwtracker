import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import Account, AccountSide, AccountStatus, Balance

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


class RollForwardRequest(BaseModel):
    month: str


class RollForwardResult(BaseModel):
    month: str
    inserted: int
    skipped: int


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: int
    month: str


class TransferResult(BaseModel):
    from_balance: BalanceRead
    to_balance: BalanceRead


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


@router.post("/balances/roll-forward", response_model=RollForwardResult)
def roll_forward(
    body: RollForwardRequest, session: Session = Depends(get_session)
) -> RollForwardResult:
    active_accounts = session.exec(
        select(Account).where(Account.status == AccountStatus.active)
    ).all()
    active_ids = [a.id for a in active_accounts if a.id is not None]

    if not active_ids:
        raise HTTPException(status_code=422, detail="No active accounts found")

    all_active_balances = session.exec(
        select(Balance).where(Balance.account_id.in_(active_ids))  # type: ignore[attr-defined]
    ).all()

    months_before_target = [
        b.month for b in all_active_balances if b.month < body.month
    ]
    if not months_before_target:
        raise HTTPException(
            status_code=422, detail="No balances found to roll forward from"
        )

    source_month = max(months_before_target)

    source_by_account = {
        b.account_id: b
        for b in all_active_balances
        if b.month == source_month
    }

    existing_in_target = {
        b.account_id
        for b in session.exec(
            select(Balance).where(Balance.month == body.month)
        ).all()
    }

    inserted = 0
    skipped = 0
    for account_id, src in source_by_account.items():
        if account_id in existing_in_target:
            skipped += 1
        else:
            session.add(
                Balance(account_id=account_id, month=body.month, amount=src.amount)
            )
            inserted += 1

    session.commit()
    return RollForwardResult(month=body.month, inserted=inserted, skipped=skipped)


@router.post("/balances/transfer", response_model=TransferResult)
def transfer(
    body: TransferRequest, session: Session = Depends(get_session)
) -> TransferResult:
    if body.amount <= 0:
        raise HTTPException(status_code=422, detail="Transfer amount must be positive")

    from_account = session.get(Account, body.from_account_id)
    if not from_account:
        raise HTTPException(
            status_code=404, detail=f"Account {body.from_account_id} not found"
        )
    to_account = session.get(Account, body.to_account_id)
    if not to_account:
        raise HTTPException(
            status_code=404, detail=f"Account {body.to_account_id} not found"
        )

    from_balance = session.exec(
        select(Balance).where(
            Balance.account_id == body.from_account_id, Balance.month == body.month
        )
    ).first()
    if not from_balance:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Account {body.from_account_id}"
                f" has no balance for {body.month}"
            ),
        )

    to_balance = session.exec(
        select(Balance).where(
            Balance.account_id == body.to_account_id, Balance.month == body.month
        )
    ).first()
    if not to_balance:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Account {body.to_account_id}"
                f" has no balance for {body.month}"
            ),
        )

    # Delta logic: direction depends on account side
    if from_account.side == AccountSide.asset:
        from_balance.amount -= body.amount  # money leaves asset
    else:
        from_balance.amount += body.amount  # liability grows (borrowing)

    if to_account.side == AccountSide.asset:
        to_balance.amount += body.amount  # money arrives in asset
    else:
        to_balance.amount -= body.amount  # liability shrinks (paydown)

    session.add(from_balance)
    session.add(to_balance)
    session.commit()
    session.refresh(from_balance)
    session.refresh(to_balance)

    return TransferResult(
        from_balance=_read(from_balance),
        to_balance=_read(to_balance),
    )
