"""记忆卡片路由。对应文档 04 §8，需求 RQ-SRS-01~04。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from ..core.errors import AppError
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..db import get_db
from ..models import Card, ReviewLog
from ..schemas.card import (
    CardCreate, CardUpdate, CardListOut, CardOut, ReviewHistoryOut,
    ReviewIn, ReviewOut,
)
from ..services.serializers import resolve_knowledge_ids, card_to_out
from ..services.sm2 import sm2_update

router = APIRouter(prefix="/api/cards", tags=["cards"], dependencies=[Depends(verify_token)])


def _card_response(card: Card) -> CardOut:
    return CardOut(**card_to_out(card))


@router.get("", response_model=CardListOut)
def list_cards(
    subject_id: int | None = None,
    knowledge_id: int | None = None,
    status_filter: str | None = None,
    due: bool | None = None,
    db: Session = Depends(get_db),
) -> CardListOut:
    query = db.query(Card)
    if subject_id is not None:
        query = query.filter(Card.subject_id == subject_id)
    if knowledge_id is not None:
        query = query.filter(Card.knowledge_points.any(id=knowledge_id))
    if status_filter:
        query = query.filter(Card.status == status_filter)
    if due:
        query = query.filter(Card.due_date <= datetime.now(timezone.utc))
    cards = query.order_by(Card.due_date.asc()).all()
    return CardListOut(items=[_card_response(c) for c in cards], total=len(cards))


@router.post("", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(payload: CardCreate, db: Session = Depends(get_db)) -> CardOut:
    card = Card(subject_id=payload.subject_id, front=payload.front, back=payload.back)
    card.knowledge_points = resolve_knowledge_ids(db, payload.knowledge_ids)
    db.add(card)
    db.commit()
    db.refresh(card)
    return _card_response(card)


@router.get("/review/queue", response_model=CardListOut)
def review_queue(subject_id: int | None = None, db: Session = Depends(get_db)) -> CardListOut:
    """今日到期卡片：due_date <= now，按到期时间升序。"""
    query = db.query(Card).filter(Card.due_date <= datetime.now(timezone.utc))
    if subject_id is not None:
        query = query.filter(Card.subject_id == subject_id)
    cards = query.order_by(Card.due_date.asc()).all()
    return CardListOut(items=[_card_response(c) for c in cards], total=len(cards))


@router.get("/{card_id}", response_model=CardOut)
def get_card(card_id: int, db: Session = Depends(get_db)) -> CardOut:
    card = db.get(Card, card_id)
    if not card:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="card not found", code="ERR_NOT_FOUND")
    return _card_response(card)


@router.put("/{card_id}", response_model=CardOut)
def update_card(card_id: int, payload: CardUpdate, db: Session = Depends(get_db)) -> CardOut:
    card = db.get(Card, card_id)
    if not card:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="card not found", code="ERR_NOT_FOUND")
    if payload.front is not None:
        card.front = payload.front
    if payload.back is not None:
        card.back = payload.back
    if payload.knowledge_ids is not None:
        card.knowledge_points = resolve_knowledge_ids(db, payload.knowledge_ids)
    db.commit()
    db.refresh(card)
    return _card_response(card)


@router.post("/{card_id}/review", response_model=ReviewOut)
def review_card(card_id: int, payload: ReviewIn, db: Session = Depends(get_db)) -> ReviewOut:
    card = db.get(Card, card_id)
    if not card:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="card not found", code="ERR_NOT_FOUND")
    reps, interval, ef, status_name, due = sm2_update(
        card.repetitions, card.interval, card.ease_factor, payload.rating
    )
    card.repetitions = reps
    card.interval = interval
    card.ease_factor = ef
    card.status = status_name
    card.due_date = due
    card.last_reviewed_at = datetime.now(timezone.utc)
    db.add(ReviewLog(card_id=card.id, rating=payload.rating))
    db.commit()
    db.refresh(card)
    return ReviewOut(card=_card_response(card), next_due_date=card.due_date)


@router.get("/{card_id}/history", response_model=ReviewHistoryOut)
def review_history(card_id: int, db: Session = Depends(get_db)) -> ReviewHistoryOut:
    if not db.get(Card, card_id):
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="card not found", code="ERR_NOT_FOUND")
    logs = db.query(ReviewLog).filter(ReviewLog.card_id == card_id).order_by(ReviewLog.reviewed_at.desc()).all()
    items = [
        {"id": log.id, "rating": log.rating, "reviewed_at": log.reviewed_at}
        for log in logs
    ]
    return ReviewHistoryOut(items=items, total=len(items))


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, db: Session = Depends(get_db)) -> None:
    card = db.get(Card, card_id)
    if not card:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="card not found", code="ERR_NOT_FOUND")
    db.delete(card)
    db.commit()
