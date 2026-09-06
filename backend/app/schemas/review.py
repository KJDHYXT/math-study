"""快速复习 API 契约。对应「交互式快速复习」。"""
from pydantic import BaseModel

MASTERY_PATTERN = "^(unfamiliar|hazy|familiar)$"


class ReviewItemOut(BaseModel):
    item_type: str  # entry|question
    id: int
    subject_id: int
    category: str | None = None  # 数学条目的定理/命题/例题
    solve_type: str | None = None  # calculation/proof
    number: str | None = None
    chapter: int | None = None
    section: int | None = None
    front: str
    core_idea: str | None = None
    steps: list[str] | None = None
    answer: str | None = None
    explanation: str | None = None
    traps: list[str] | None = None


class ReviewBatchOut(BaseModel):
    items: list[ReviewItemOut]
    total: int


class ReviewSubmitIn(BaseModel):
    item_type: str = "entry"  # entry|question
    item_id: int
    mastery: str  # unfamiliar|hazy|familiar
