import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import AccountTag, Tag

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tags"])


class TagCreate(BaseModel):
    name: str


class TagRead(BaseModel):
    id: int
    name: str


class TagUpdate(BaseModel):
    name: str


@router.get("/tags", response_model=list[TagRead])
def list_tags(session: Session = Depends(get_session)) -> list[TagRead]:
    return [
        TagRead(id=t.id, name=t.name)  # type: ignore[arg-type]
        for t in session.exec(select(Tag)).all()
    ]


@router.post("/tags", response_model=TagRead, status_code=201)
def create_tag(body: TagCreate, session: Session = Depends(get_session)) -> TagRead:
    if session.exec(select(Tag).where(Tag.name == body.name)).first():
        raise HTTPException(status_code=409, detail=f"Tag '{body.name}' already exists")
    tag = Tag(name=body.name)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    assert tag.id is not None
    return TagRead(id=tag.id, name=tag.name)


@router.get("/tags/{tag_id}", response_model=TagRead)
def get_tag(tag_id: int, session: Session = Depends(get_session)) -> TagRead:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    assert tag.id is not None
    return TagRead(id=tag.id, name=tag.name)


@router.put("/tags/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int, body: TagUpdate, session: Session = Depends(get_session)
) -> TagRead:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    if session.exec(select(Tag).where(Tag.name == body.name, Tag.id != tag_id)).first():
        raise HTTPException(status_code=409, detail=f"Tag '{body.name}' already exists")
    tag.name = body.name
    session.add(tag)
    session.commit()
    session.refresh(tag)
    assert tag.id is not None
    return TagRead(id=tag.id, name=tag.name)


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int, session: Session = Depends(get_session)) -> None:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    for at in session.exec(select(AccountTag).where(AccountTag.tag_id == tag_id)).all():
        session.delete(at)
    session.delete(tag)
    session.commit()
