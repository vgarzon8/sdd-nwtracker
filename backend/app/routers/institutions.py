import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Account, AccountTag, Balance, Institution

logger = logging.getLogger(__name__)

router = APIRouter(tags=["institutions"])


class InstitutionCreate(BaseModel):
    name: str


class InstitutionRead(BaseModel):
    id: int
    name: str


class InstitutionUpdate(BaseModel):
    name: str


class InstitutionDeletePreview(BaseModel):
    accounts_to_delete: int
    balances_to_delete: int


@router.get("/institutions", response_model=list[InstitutionRead])
def list_institutions(
    session: Session = Depends(get_session),
) -> list[InstitutionRead]:
    return [
        InstitutionRead(id=i.id, name=i.name)  # type: ignore[arg-type]
        for i in session.exec(select(Institution)).all()
    ]


@router.post("/institutions", response_model=InstitutionRead, status_code=201)
def create_institution(
    body: InstitutionCreate, session: Session = Depends(get_session)
) -> InstitutionRead:
    if session.exec(select(Institution).where(Institution.name == body.name)).first():
        raise HTTPException(
            status_code=409, detail=f"Institution '{body.name}' already exists"
        )
    institution = Institution(name=body.name)
    session.add(institution)
    session.commit()
    session.refresh(institution)
    assert institution.id is not None
    return InstitutionRead(id=institution.id, name=institution.name)


@router.get("/institutions/{institution_id}", response_model=InstitutionRead)
def get_institution(
    institution_id: int, session: Session = Depends(get_session)
) -> InstitutionRead:
    institution = session.get(Institution, institution_id)
    if not institution:
        raise HTTPException(
            status_code=404, detail=f"Institution {institution_id} not found"
        )
    assert institution.id is not None
    return InstitutionRead(id=institution.id, name=institution.name)


@router.put("/institutions/{institution_id}", response_model=InstitutionRead)
def update_institution(
    institution_id: int,
    body: InstitutionUpdate,
    session: Session = Depends(get_session),
) -> InstitutionRead:
    institution = session.get(Institution, institution_id)
    if not institution:
        raise HTTPException(
            status_code=404, detail=f"Institution {institution_id} not found"
        )
    if session.exec(
        select(Institution).where(
            Institution.name == body.name, Institution.id != institution_id
        )
    ).first():
        raise HTTPException(
            status_code=409, detail=f"Institution '{body.name}' already exists"
        )
    institution.name = body.name
    session.add(institution)
    session.commit()
    session.refresh(institution)
    assert institution.id is not None
    return InstitutionRead(id=institution.id, name=institution.name)


@router.delete(
    "/institutions/{institution_id}",
    response_model=InstitutionDeletePreview,
    responses={204: {"description": "Institution and all its accounts deleted"}},
)
def delete_institution(
    institution_id: int,
    confirm: bool = False,
    session: Session = Depends(get_session),
) -> InstitutionDeletePreview | Response:
    institution = session.get(Institution, institution_id)
    if not institution:
        raise HTTPException(
            status_code=404, detail=f"Institution {institution_id} not found"
        )

    accounts = session.exec(
        select(Account).where(Account.institution_id == institution_id)
    ).all()
    account_ids = [a.id for a in accounts if a.id is not None]
    balance_count = sum(
        len(session.exec(select(Balance).where(Balance.account_id == aid)).all())
        for aid in account_ids
    )

    if not confirm:
        return InstitutionDeletePreview(
            accounts_to_delete=len(account_ids),
            balances_to_delete=balance_count,
        )

    for aid in account_ids:
        for balance in session.exec(
            select(Balance).where(Balance.account_id == aid)
        ).all():
            session.delete(balance)
        for at in session.exec(
            select(AccountTag).where(AccountTag.account_id == aid)
        ).all():
            session.delete(at)
    session.flush()  # remove FK children before accounts
    for account in accounts:
        session.delete(account)
    session.flush()  # remove accounts before institution
    session.delete(institution)
    session.commit()
    return Response(status_code=204)
