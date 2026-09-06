"""数学条目（定理/命题/例题）API 契约。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

CATEGORY_PATTERN = "^(theorem|proposition|example)$"


class EntryCreate(BaseModel):
    subject_id: int
    category: str = Field(..., pattern=CATEGORY_PATTERN)
    solve_type: str = Field("calculation", pattern="^(calculation|proof)$")
    number: str | None = None
    chapter: int | None = None
    section: int | None = None
    content: str
    core_idea: str | None = None
    steps: list[str] | None = None
    answer: str | None = None
    explanation: str | None = None
    traps: list[str] | None = None
    image_path: str | None = None
    source: str | None = None


class EntryUpdate(BaseModel):
    category: str | None = Field(None, pattern=CATEGORY_PATTERN)
    solve_type: str | None = Field(None, pattern="^(calculation|proof)$")
    number: str | None = None
    chapter: int | None = None
    section: int | None = None
    content: str | None = None
    core_idea: str | None = None
    steps: list[str] | None = None
    answer: str | None = None
    explanation: str | None = None
    traps: list[str] | None = None
    image_path: str | None = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    category: str
    solve_type: str
    number: str | None
    chapter: int | None
    section: int | None
    content: str
    core_idea: str | None
    steps: list[str] | None
    answer: str | None
    explanation: str | None
    traps: list[str] | None = None
    image_path: str | None
    source: str
    created_at: datetime


class EntryListOut(BaseModel):
    items: list[EntryOut]
    total: int
