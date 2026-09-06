"""刷题 API 契约。对应文档 04 §7。"""
from datetime import datetime

from pydantic import BaseModel

from .question import QuestionOut


class QuizCreate(BaseModel):
    subject_id: int | None = None
    knowledge_ids: list[int] = []
    count: int | None = None
    qtype: str | None = None
    difficulty: int | None = None


class QuizItemOut(BaseModel):
    question: QuestionOut
    order_index: int


class QuizSessionOut(BaseModel):
    session_id: int
    questions: list[QuizItemOut]


class QuizAnswerIn(BaseModel):
    question_id: int
    user_answer: str | None = None
    self_correct: bool | None = None  # 主观题自评"我答对了"


class QuizAnswerOut(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None


class QuizFinishOut(BaseModel):
    total: int
    correct: int
    wrong_ids: list[int]


class WrongItemOut(BaseModel):
    question: QuestionOut
    wrong_count: int


class WrongBookOut(BaseModel):
    items: list[WrongItemOut]
    total: int
