"""笔记与标签路由。对应文档 04 §4、§5，需求 RQ-NOT-*、RQ-COMMON-02。"""
from fastapi import APIRouter, Depends, status
from ..core.errors import AppError
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..db import get_db
from ..models import Note, Tag
from ..schemas.note import (
    NoteCreate, NoteUpdate, NoteListOut, NoteOut,
    TagCreate, TagOut,
)
from ..services.serializers import resolve_tags, resolve_knowledge_ids, note_to_out

notes_router = APIRouter(prefix="/api/notes", tags=["notes"], dependencies=[Depends(verify_token)])
tags_router = APIRouter(prefix="/api/tags", tags=["tags"], dependencies=[Depends(verify_token)])


def _note_response(note: Note) -> NoteOut:
    return NoteOut(**note_to_out(note))


@notes_router.get("", response_model=NoteListOut)
def list_notes(
    subject_id: int | None = None,
    tag: str | None = None,
    knowledge_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
) -> NoteListOut:
    query = db.query(Note)
    if subject_id is not None:
        query = query.filter(Note.subject_id == subject_id)
    if tag:
        query = query.filter(Note.tags.any(Tag.name == tag))
    if knowledge_id is not None:
        query = query.filter(Note.knowledge_points.any(id=knowledge_id))
    if q:
        like = f"%{q}%"
        query = query.filter(Note.title.ilike(like) | Note.content.ilike(like))
    notes = query.order_by(Note.updated_at.desc()).all()
    return NoteListOut(items=[_note_response(n) for n in notes], total=len(notes))


@notes_router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteOut:
    note = Note(subject_id=payload.subject_id, title=payload.title, content=payload.content)
    note.tags = resolve_tags(db, payload.tags)
    note.knowledge_points = resolve_knowledge_ids(db, payload.knowledge_ids)
    db.add(note)
    db.commit()
    db.refresh(note)
    return _note_response(note)


@notes_router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteOut:
    note = db.get(Note, note_id)
    if not note:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="note not found", code="ERR_NOT_FOUND")
    return _note_response(note)


@notes_router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)) -> NoteOut:
    note = db.get(Note, note_id)
    if not note:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="note not found", code="ERR_NOT_FOUND")
    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    if payload.tags is not None:
        note.tags = resolve_tags(db, payload.tags)
    if payload.knowledge_ids is not None:
        note.knowledge_points = resolve_knowledge_ids(db, payload.knowledge_ids)
    db.commit()
    db.refresh(note)
    return _note_response(note)


@notes_router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.get(Note, note_id)
    if not note:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="note not found", code="ERR_NOT_FOUND")
    db.delete(note)
    db.commit()


@tags_router.get("", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)) -> list[Tag]:
    return db.query(Tag).order_by(Tag.name).all()


@tags_router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)) -> Tag:
    if db.query(Tag).filter(Tag.name == payload.name).first():
        raise AppError(status_code=status.HTTP_409_CONFLICT, detail="tag exists", code="ERR_CONFLICT")
    tag = Tag(name=payload.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
