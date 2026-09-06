"""笔记与标签模型。对应文档 02 §2.4、§2.5、§2.6、§2.7。"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# 笔记-标签 多对多
note_tags = Table(
    "note_tags", Base.metadata,
    Column("note_id", ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

# 笔记-知识点 多对多
note_knowledge = Table(
    "note_knowledge", Base.metadata,
    Column("note_id", ForeignKey("notes.id"), primary_key=True),
    Column("knowledge_id", ForeignKey("knowledge_points.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    subject = relationship("Subject", back_populates="notes")
    tags = relationship("Tag", secondary=note_tags, backref="notes")
    knowledge_points = relationship("KnowledgePoint", secondary=note_knowledge, backref="notes")
