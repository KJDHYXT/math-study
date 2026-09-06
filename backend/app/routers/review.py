"""快速复习路由。对应「交互式快速复习」：拉取一批复习对象、提交自评、查统计。"""
from datetime import datetime, timedelta, timezone
from random import shuffle

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..core.errors import AppError
from ..db import get_db
from ..models import MathEntry, Question, ReviewState, ReviewRecord
from ..schemas.review import (
    ReviewItemOut, ReviewBatchOut, ReviewSubmitIn,
)
from ..services.serializers import parse_str_list
from ..services.numbering import parse_chapter_section  # noqa: F401  (用于章节一致性)

router = APIRouter(prefix="/api/review", tags=["review"], dependencies=[Depends(verify_token)])


def _entry_item(e: MathEntry) -> ReviewItemOut:
    return ReviewItemOut(
        item_type="entry",
        id=e.id,
        subject_id=e.subject_id,
        category=e.category,
        solve_type=e.solve_type,
        number=e.number,
        chapter=e.chapter,
        section=e.section,
        front=e.content,
        core_idea=e.core_idea,
        steps=parse_str_list(e.steps),
        answer=e.answer,
        explanation=e.explanation,
        traps=parse_str_list(e.traps),
    )


def _question_item(q: Question) -> ReviewItemOut:
    return ReviewItemOut(
        item_type="question",
        id=q.id,
        subject_id=q.subject_id,
        solve_type=q.qtype,
        number=q.number,
        chapter=q.chapter,
        section=q.section,
        front=q.content,
        core_idea=q.core_idea,
        steps=parse_str_list(q.steps),
        answer=q.answer,
        explanation=q.explanation,
        traps=parse_str_list(q.traps),
    )


@router.get("/items", response_model=ReviewBatchOut)
def review_items(
    type: str | None = Query(None, description="entry|question|mixed"),
    subject_id: int | None = None,
    chapter: int | None = None,
    category: str | None = None,
    qtype: str | None = None,
    count: int | None = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ReviewBatchOut:
    items: list[ReviewItemOut] = []
    if type in (None, "mixed", "entry"):
        e_q = db.query(MathEntry)
        if subject_id is not None:
            e_q = e_q.filter(MathEntry.subject_id == subject_id)
        if chapter is not None:
            e_q = e_q.filter(MathEntry.chapter == chapter)
        if category:
            e_q = e_q.filter(MathEntry.category == category)
        items.extend([_entry_item(e) for e in e_q.all()])
    if type in (None, "mixed", "question"):
        q_q = db.query(Question)
        if subject_id is not None:
            q_q = q_q.filter(Question.subject_id == subject_id)
        if chapter is not None:
            q_q = q_q.filter(Question.chapter == chapter)
        if qtype:
            q_q = q_q.filter(Question.qtype == qtype)
        items.extend([_question_item(q) for q in q_q.all()])

    shuffle(items)
    if count and len(items) > count:
        items = items[:count]
    return ReviewBatchOut(items=items, total=len(items))


@router.post("/submit", response_model=dict)
def submit(payload: ReviewSubmitIn, db: Session = Depends(get_db)) -> dict:
    item_type, item_id, mastery = payload.item_type, payload.item_id, payload.mastery
    if item_type not in ("entry", "question"):
        raise AppError(status_code=400, detail="invalid item_type", code="ERR_BAD_REQUEST")
    if mastery not in ("unfamiliar", "hazy", "familiar"):
        raise AppError(status_code=400, detail="invalid mastery", code="ERR_BAD_REQUEST")
    # 校验对象存在
    target = db.get(MathEntry, item_id) if item_type == "entry" else db.get(Question, item_id)
    if not target:
        raise AppError(status_code=404, detail="review target not found", code="ERR_NOT_FOUND")
    state = db.query(ReviewState).filter(ReviewState.item_type == item_type, ReviewState.item_id == item_id).first()
    if state is None:
        state = ReviewState(item_type=item_type, item_id=item_id, review_count=0, last_reviewed_at=None)
        db.add(state)
    state.mastery = mastery
    state.review_count += 1
    state.last_reviewed_at = datetime.now(timezone.utc)
    db.add(ReviewRecord(item_type=item_type, item_id=item_id, mastery=mastery))
    db.commit()
    return {"ok": True, "mastery": mastery, "review_count": state.review_count}


@router.get("/stats", response_model=dict)
def stats(db: Session = Depends(get_db)) -> dict:
    now = datetime.now(timezone.utc)
    today = now.date()
    # 今日复习量与连续打卡
    records = db.query(ReviewRecord.reviewed_at).all()
    dates = {r[0].date() for r in records if r[0] is not None}
    today_count = sum(1 for r in records if r[0] is not None and r[0].date() == today)
    streak = 0
    d = today
    while d in dates:
        streak += 1
        d = d - timedelta(days=1)

    # 掌握度分布
    dist = {"unfamiliar": 0, "hazy": 0, "familiar": 0}
    states = db.query(ReviewState).all()
    for s in states:
        if s.mastery in dist:
            dist[s.mastery] += 1

    # 薄弱章节（生/糊项按章聚合）
    weak: dict[str, int] = {}
    for s in states:
        if s.mastery not in ("hazy", "unfamiliar"):
            continue
        obj = db.get(MathEntry, s.item_id) if s.item_type == "entry" else db.get(Question, s.item_id)
        ch = getattr(obj, "chapter", None) if obj else None
        key = f"第{ch}章" if ch is not None else "未分章"
        weak[key] = weak.get(key, 0) + 1
    weak_chapters = [{"chapter": k, "count": v} for k, v in weak.items()]
    weak_chapters.sort(key=lambda x: x["count"], reverse=True)

    return {"today_count": today_count, "streak": streak, "distribution": dist, "weak_chapters": weak_chapters}
