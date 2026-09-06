"""快速复习的掌握度与日志模型。对应「交互式快速复习」。

- ReviewState：每个条目/题目的轻量掌握度（与卡片 SM-2 调度并存）。
- ReviewRecord：每次自评的记录（用于今日复习量与连续打卡统计）。
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReviewState(Base):
    __tablename__ = "review_state"
    __table_args__ = (UniqueConstraint("item_type", "item_id", name="uq_review_item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # entry|question
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    mastery: Mapped[str] = mapped_column(String(20), default="unfamiliar", nullable=False)  # unfamiliar|hazy|familiar
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewRecord(Base):
    __tablename__ = "review_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    mastery: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
