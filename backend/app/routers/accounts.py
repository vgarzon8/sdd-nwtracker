import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.db import get_session
from app.models import (
    Account,
    AccountSide,
    AccountStatus,
    AccountTag,
    Balance,
    Currency,
    Institution,
    Tag,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["accounts"])


class AccountCreate(BaseModel):
    name: str
    institution_id: int
    currency_code: str
    side: AccountSide
    status: AccountStatus = AccountStatus.active
    tag_ids: list[int] = []


class AccountRead(BaseModel):
    id: int
    name: str
    institution_id: int
    currency_code: str
    side: AccountSide
    status: AccountStatus
    tag_ids: list[int]


class AccountUpdate(BaseModel):
    name: str | None = None
    institution_id: int | None = None
    currency_code: str | None = None
    side: AccountSide | None = None
    status: AccountStatus | None = None
    tag_ids: list[int] | None = None


class AccountDeletePreview(BaseModel):
    balances_to_delete: int


def _get_tag_ids(session: Session, account_id: int) -> list[int]:
    rows = session.exec(
        select(AccountTag).where(AccountTag.account_id == account_id)
    ).all()
    return [row.tag_id for row in rows if row.tag_id is not None]


def _read(account: Account, session: Session) -> AccountRead:
    assert account.id is not None
    return AccountRead(
        id=account.id,
        name=account.name,
        institution_id=account.institution_id,
        currency_code=account.currency_code,
        side=account.side,
        status=account.status,
        tag_ids=_get_tag_ids(session, account.id),
    )


@router.get("/accounts", response_model=list[AccountRead])
def list_accounts(
    status: AccountStatus | None = None,
    tag: int | None = None,
    session: Session = Depends(get_session),
) -> list[AccountRead]:
    stmt = select(Account)
    if status is not None:
        stmt = stmt.where(Account.status == status)
    if tag is not None:
        stmt = stmt.where(
            col(Account.id).in_(
                select(AccountTag.account_id).where(AccountTag.tag_id == tag)
            )
        )
    accounts = session.exec(stmt).all()
    return [_read(a, session) for a in accounts]


@router.post("/accounts", response_model=AccountRead, status_code=201)
def create_account(
    body: AccountCreate, session: Session = Depends(get_session)
) -> AccountRead:
    if not session.get(Institution, body.institution_id):
        raise HTTPException(
            status_code=404, detail=f"Institution {body.institution_id} not found"
        )
    if not session.get(Currency, body.currency_code):
        raise HTTPException(
            status_code=404, detail=f"Currency '{body.currency_code}' not found"
        )
    for tag_id in body.tag_ids:
        if not session.get(Tag, tag_id):
            raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    if session.exec(select(Account).where(Account.name == body.name)).first():
        raise HTTPException(
            status_code=409, detail=f"Account '{body.name}' already exists"
        )
    account = Account(
        name=body.name,
        institution_id=body.institution_id,
        currency_code=body.currency_code,
        side=body.side,
        status=body.status,
    )
    session.add(account)
    session.flush()
    assert account.id is not None
    for tag_id in body.tag_ids:
        session.add(AccountTag(account_id=account.id, tag_id=tag_id))
    session.commit()
    session.refresh(account)
    return _read(account, session)


@router.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int, session: Session = Depends(get_session)
) -> AccountRead:
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return _read(account, session)


@router.put("/accounts/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    body: AccountUpdate,
    session: Session = Depends(get_session),
) -> AccountRead:
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    if body.name is not None:
        if session.exec(
            select(Account).where(Account.name == body.name, Account.id != account_id)
        ).first():
            raise HTTPException(
                status_code=409, detail=f"Account '{body.name}' already exists"
            )
        account.name = body.name

    if body.institution_id is not None:
        if not session.get(Institution, body.institution_id):
            raise HTTPException(
                status_code=404, detail=f"Institution {body.institution_id} not found"
            )
        account.institution_id = body.institution_id

    if body.currency_code is not None:
        if not session.get(Currency, body.currency_code):
            raise HTTPException(
                status_code=404, detail=f"Currency '{body.currency_code}' not found"
            )
        account.currency_code = body.currency_code

    if body.side is not None:
        account.side = body.side

    if body.status is not None:
        account.status = body.status

    if body.tag_ids is not None:
        for tag_id in body.tag_ids:
            if not session.get(Tag, tag_id):
                raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
        for at in session.exec(
            select(AccountTag).where(AccountTag.account_id == account_id)
        ).all():
            session.delete(at)
        session.flush()
        for tag_id in body.tag_ids:
            session.add(AccountTag(account_id=account_id, tag_id=tag_id))

    session.add(account)
    session.commit()
    session.refresh(account)
    return _read(account, session)


@router.delete(
    "/accounts/{account_id}",
    response_model=AccountDeletePreview,
    responses={204: {"description": "Account and all its balances deleted"}},
)
def delete_account(
    account_id: int,
    confirm: bool = False,
    session: Session = Depends(get_session),
) -> AccountDeletePreview | Response:
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    balances = session.exec(
        select(Balance).where(Balance.account_id == account_id)
    ).all()

    if not confirm:
        return AccountDeletePreview(balances_to_delete=len(balances))

    for balance in balances:
        session.delete(balance)
    for at in session.exec(
        select(AccountTag).where(AccountTag.account_id == account_id)
    ).all():
        session.delete(at)
    session.flush()
    session.delete(account)
    session.commit()
    return Response(status_code=204)
