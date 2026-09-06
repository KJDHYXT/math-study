"""笔记与标签 API 契约。对应文档 04 §4、§5。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    name: str = Field(..., max_length=100)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class NoteCreate(BaseModel):
    subject_id: int
    title: str = Field(..., max_length=300)
    content: str
    tags: list[str] = []
    knowledge_ids: list[int] = []


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    knowledge_ids: list[int] | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    title: str
    content: str
    tags: list[str] = []
    knowledge_ids: list[int] = []
    created_at: datetime
    updated_at: datetime


class NoteListOut(BaseModel):
    items: list[NoteOut]
    total: int
