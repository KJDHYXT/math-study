"""数学条目（定理/命题/例题）模型。

对应「图片按定理/命题/例题分类、保留编号」功能。与题库(Question)分离，
存放数学陈述/例题等需要按类别+编号归档的内容。
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# 允许的类别
CATEGORIES = ("theorem", "proposition", "example")  # 定理 / 命题 / 例题


class MathEntry(Base):
    __tablename__ = "math_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # theorem|proposition|example
    solve_type: Mapped[str] = mapped_column(String(20), default="calculation", nullable=False)  # calculation|proof（计算/证明）
    number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 标注编号，如 6.2.2、5.1
    chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 章
    section: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 节
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 陈述/例题文本（可含 LaTeX）
    core_idea: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 数组字符串
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    traps: Mapped[str | None] = mapped_column(Text, nullable=True)  # 坑点（JSON 数组字符串）
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)  # manual|image|llm
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    subject = relationship("Subject", backref="math_entries")
