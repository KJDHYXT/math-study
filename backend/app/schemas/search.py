"""检索 API 契约。对应文档 04 §9。"""
from pydantic import BaseModel


class SearchHit(BaseModel):
    id: int
    title: str
    snippet: str


class SearchResults(BaseModel):
    notes: list[SearchHit]
    questions: list[SearchHit]
    cards: list[SearchHit]
    knowledge: list[SearchHit]
