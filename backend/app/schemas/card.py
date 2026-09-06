"""记忆卡片 API 契约。对应文档 04 §8。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CardCreate(BaseModel):
    subject_id: int
    front: str
    back: str
    knowledge_ids: list[int] = []


class CardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    knowledge_ids: list[int] | None = None


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    front: str
    back: str
    ease_factor: float
    interval: int
    repetitions: int
    due_date: datetime
    status: str
    knowledge_ids: list[int] = []
    created_at: datetime


class CardListOut(BaseModel):
    items: list[CardOut]
    total: int


class ReviewIn(BaseModel):
    rating: str = Field(..., pattern="^(again|hard|good|easy)$")


class ReviewOut(BaseModel):
    card: CardOut
    next_due_date: datetime


class ReviewHistoryOut(BaseModel):
    items: list[dict]
    total: int
