"""题目 API 契约。对应文档 04 §6。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    subject_id: int
    qtype: str = Field(..., pattern="^(calculation|proof)$")
    content: str
    options: list[str] | None = None
    answer: str
    explanation: str | None = None
    difficulty: int = Field(3, ge=1, le=5)
    knowledge_ids: list[int] = []
    # 编号与章节
    number: str | None = None
    chapter: int | None = None
    section: int | None = None
    # 从图片提取
    core_idea: str | None = None
    steps: list[str] | None = None
    traps: list[str] | None = None
    image_path: str | None = None
    source: str | None = None


class QuestionUpdate(BaseModel):
    content: str | None = None
    options: list[str] | None = None
    answer: str | None = None
    explanation: str | None = None
    difficulty: int | None = Field(None, ge=1, le=5)
    knowledge_ids: list[int] | None = None
    number: str | None = None
    chapter: int | None = None
    section: int | None = None
    core_idea: str | None = None
    steps: list[str] | None = None
    traps: list[str] | None = None
    image_path: str | None = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    qtype: str
    content: str
    options: list[str] | None = None
    answer: str
    explanation: str | None
    difficulty: int
    knowledge_ids: list[int] = []
    number: str | None = None
    chapter: int | None = None
    section: int | None = None
    core_idea: str | None = None
    steps: list[str] | None = None
    traps: list[str] | None = None
    image_path: str | None = None
    source: str | None = None
    created_at: datetime


class QuestionListOut(BaseModel):
    items: list[QuestionOut]
    total: int


# 从图片提取的初稿
class ExtractOut(BaseModel):
    content: str | None = None
    core_idea: str
    steps: list[str]
    answer: str | None = None
    explanation: str | None = None
    # 图片分类（定理/命题/例题）+ 编号；无标注归例题
    category: str | None = None
    number: str | None = None
    # 题型：计算(calculation)/证明(proof)
    solve_type: str | None = None
