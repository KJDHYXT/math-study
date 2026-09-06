"""知识点模型。对应文档 02 §2.2、§2.3。"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    subject = relationship("Subject", back_populates="knowledge_points")
    # 作为前置点 / 后置点的依赖边
    as_source = relationship("KnowledgeRelation", foreign_keys="KnowledgeRelation.source_id",
                             back_populates="source", cascade="all, delete-orphan")
    as_target = relationship("KnowledgeRelation", foreign_keys="KnowledgeRelation.target_id",
                             back_populates="target", cascade="all, delete-orphan")


class KnowledgeRelation(Base):
    __tablename__ = "knowledge_relations"
    __table_args__ = (UniqueConstraint("source_id", "target_id", name="uq_kr_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("knowledge_points.id"), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey("knowledge_points.id"), nullable=False)

    source = relationship("KnowledgePoint", foreign_keys=[source_id], back_populates="as_source")
    target = relationship("KnowledgePoint", foreign_keys=[target_id], back_populates="as_target")
