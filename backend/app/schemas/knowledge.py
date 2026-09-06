"""知识点 API 契约。对应文档 04 §3。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .note import NoteOut
from .question import QuestionOut
from .card import CardOut


class KnowledgeCreate(BaseModel):
    subject_id: int
    name: str = Field(..., max_length=200)
    description: str | None = None


class KnowledgeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class KnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    name: str
    description: str | None
    created_at: datetime


class KnowledgeRelationIn(BaseModel):
    source_id: int
    target_id: int


class GraphNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class GraphEdge(BaseModel):
    source: int
    target: int


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class RelatedOut(BaseModel):
    notes: list[NoteOut]
    questions: list[QuestionOut]
    cards: list[CardOut]
