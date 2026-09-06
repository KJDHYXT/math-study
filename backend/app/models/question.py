"""题目、刷题会话模型。对应文档 02 §2.8、§2.9、§2.10、§2.11。"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# 题目-知识点 多对多
question_knowledge = Table(
    "question_knowledge", Base.metadata,
    Column("question_id", ForeignKey("questions.id"), primary_key=True),
    Column("knowledge_id", ForeignKey("knowledge_points.id"), primary_key=True),
)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    qtype: Mapped[str] = mapped_column(String(20), nullable=False)  # calculation|proof（计算/证明）
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[str | None] = mapped_column(Text, nullable=True)  # 兼容旧数据（已不用于作答）
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    # 编号与章节（6.2.2 → 第6章 第2节）
    number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 坑点/易错点（JSON 数组字符串）
    traps: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 从图片提取：核心思路 + 简明操作步骤（JSON 数组字符串）+ 图片路径 + 来源
    core_idea: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 数组，有序步骤
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(20), nullable=True)  # manual|image|llm
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    subject = relationship("Subject", back_populates="questions")
    knowledge_points = relationship("KnowledgePoint", secondary=question_knowledge, backref="questions")
    quiz_answers = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    answers = relationship("QuizAnswer", back_populates="session", cascade="all, delete-orphan")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("quiz_sessions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("QuizSession", back_populates="answers")
    question = relationship("Question", back_populates="quiz_answers")
