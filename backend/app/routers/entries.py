"""数学条目（定理/命题/例题）路由。对应「图片按定理/命题/例题分类、保留编号」功能。"""
import re

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..core.errors import AppError
from ..db import get_db
from ..models import MathEntry
from ..schemas.entry import EntryCreate, EntryUpdate, EntryOut, EntryListOut
from ..schemas.question import ExtractOut
from ..services.serializers import entry_to_out, dump_steps
from ..services.llm import extract_from_image
from ..services.numbering import parse_chapter_section

router = APIRouter(prefix="/api/entries", tags=["entries"], dependencies=[Depends(verify_token)])

_CATEGORY_ORDER = {"theorem": 0, "proposition": 1, "example": 2}


def _e_response(entry: MathEntry) -> EntryOut:
    return EntryOut(**entry_to_out(entry))


def _num_key(n: str | None):
    if not n:
        return (10**9,)
    parts = re.split(r"[.\-]", n)
    return tuple(int(p) if p.isdigit() else 0 for p in parts)


def _sorted(items: list[MathEntry]) -> list[MathEntry]:
    return sorted(
        items,
        key=lambda e: (_CATEGORY_ORDER.get(e.category, 3), _num_key(e.number), e.id),
    )


@router.get("", response_model=EntryListOut)
def list_entries(
    category: str | None = None,
    subject_id: int | None = None,
    chapter: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
) -> EntryListOut:
    query = db.query(MathEntry)
    if category:
        query = query.filter(MathEntry.category == category)
    if subject_id is not None:
        query = query.filter(MathEntry.subject_id == subject_id)
    if chapter is not None:
        query = query.filter(MathEntry.chapter == chapter)
    if q:
        like = f"%{q}%"
        query = query.filter(MathEntry.content.ilike(like) | MathEntry.number.ilike(like))
    entries = _sorted(query.all())
    return EntryListOut(items=[_e_response(e) for e in entries], total=len(entries))


@router.post("", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)) -> EntryOut:
    chapter, section = parse_chapter_section(payload.number)
    entry = MathEntry(
        subject_id=payload.subject_id,
        category=payload.category,
        solve_type=payload.solve_type,
        number=payload.number,
        chapter=payload.chapter if payload.chapter is not None else chapter,
        section=payload.section if payload.section is not None else section,
        content=payload.content,
        core_idea=payload.core_idea,
        steps=dump_steps(payload.steps),
        traps=dump_steps(payload.traps),
        answer=payload.answer,
        explanation=payload.explanation,
        image_path=payload.image_path,
        source=payload.source or ("image" if payload.image_path else "manual"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _e_response(entry)


@router.post("/extract", response_model=ExtractOut)
async def extract(file: UploadFile = File(...)) -> ExtractOut:
    """从图片提取核心思路/步骤，并分类（定理/命题/例题）与解析编号（需配置 LLM_API_KEY）。"""
    draft = await extract_from_image(file)
    return ExtractOut(**draft)


@router.get("/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)) -> EntryOut:
    entry = db.get(MathEntry, entry_id)
    if not entry:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found", code="ERR_NOT_FOUND")
    return _e_response(entry)


@router.put("/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: int, payload: EntryUpdate, db: Session = Depends(get_db)) -> EntryOut:
    entry = db.get(MathEntry, entry_id)
    if not entry:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found", code="ERR_NOT_FOUND")
    for field in ("category", "solve_type", "content", "core_idea", "answer", "explanation", "image_path"):
        val = getattr(payload, field)
        if val is not None:
            setattr(entry, field, val)
    if payload.number is not None or payload.chapter is not None or payload.section is not None:
        if payload.number is not None:
            entry.number = payload.number
            auto_chapter, auto_section = parse_chapter_section(payload.number)
            if payload.chapter is None:
                entry.chapter = auto_chapter
            if payload.section is None:
                entry.section = auto_section
        else:
            if payload.chapter is not None:
                entry.chapter = payload.chapter
            if payload.section is not None:
                entry.section = payload.section
    if payload.steps is not None:
        entry.steps = dump_steps(payload.steps)
    if payload.traps is not None:
        entry.traps = dump_steps(payload.traps)
    db.commit()
    db.refresh(entry)
    return _e_response(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)) -> None:
    entry = db.get(MathEntry, entry_id)
    if not entry:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found", code="ERR_NOT_FOUND")
    db.delete(entry)
    db.commit()
