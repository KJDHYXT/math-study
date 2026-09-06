"""刷题路由。对应文档 04 §7，需求 RQ-QUIZ-04~06。"""
from random import shuffle
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from ..core.errors import AppError
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..db import get_db
from ..models import Question, QuizSession, QuizAnswer
from ..schemas.quiz import (
    QuizCreate, QuizItemOut, QuizSessionOut, QuizAnswerIn, QuizAnswerOut,
    QuizFinishOut, WrongItemOut, WrongBookOut,
)
from ..schemas.question import QuestionOut
from ..services.serializers import question_to_out
from ..services.quiz import judge

router = APIRouter(prefix="/api/quiz", tags=["quiz"], dependencies=[Depends(verify_token)])


def _pick_questions(db: Session, payload: QuizCreate) -> list[Question]:
    query = db.query(Question)
    if payload.subject_id is not None:
        query = query.filter(Question.subject_id == payload.subject_id)
    if payload.knowledge_ids:
        for kid in payload.knowledge_ids:
            query = query.filter(Question.knowledge_points.any(id=kid))
    if payload.qtype:
        query = query.filter(Question.qtype == payload.qtype)
    if payload.difficulty is not None:
        query = query.filter(Question.difficulty == payload.difficulty)
    questions = list(query.all())
    shuffle(questions)
    if payload.count and len(questions) > payload.count:
        questions = questions[:payload.count]
    return questions


@router.post("/sessions", response_model=QuizSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: QuizCreate, db: Session = Depends(get_db)) -> QuizSessionOut:
    questions = _pick_questions(db, payload)
    session = QuizSession(subject_id=payload.subject_id)
    db.add(session)
    db.flush()  # 拿到 session.id，以便写入 order 占位
    items: list[QuizItemOut] = []
    for idx, q in enumerate(questions, start=1):
        db.add(QuizAnswer(session_id=session.id, question_id=q.id, order_index=idx, is_correct=False))
        items.append(QuizItemOut(question=QuestionOut(**question_to_out(q)), order_index=idx))
    db.commit()
    return QuizSessionOut(session_id=session.id, questions=items)


@router.post("/sessions/{session_id}/answers", response_model=QuizAnswerOut)
def submit_answer(session_id: int, payload: QuizAnswerIn, db: Session = Depends(get_db)) -> QuizAnswerOut:
    session = db.get(QuizSession, session_id)
    if not session:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="session not found", code="ERR_NOT_FOUND")
    question = db.get(Question, payload.question_id)
    if not question:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="question not found", code="ERR_NOT_FOUND")
    correct = judge(question, payload.user_answer, payload.self_correct)
    answer = (
        db.query(QuizAnswer)
        .filter(QuizAnswer.session_id == session_id, QuizAnswer.question_id == payload.question_id)
        .first()
    )
    if answer is None:
        answer = QuizAnswer(session_id=session_id, question_id=payload.question_id,
                            order_index=db.query(func.max(QuizAnswer.order_index)).filter(QuizAnswer.session_id == session_id).scalar() or 0 + 1)
        db.add(answer)
    answer.user_answer = payload.user_answer
    answer.is_correct = correct
    answer.answered_at = datetime.now(timezone.utc)
    db.commit()
    return QuizAnswerOut(is_correct=correct, correct_answer=question.answer, explanation=question.explanation)


@router.post("/sessions/{session_id}/finish", response_model=QuizFinishOut)
def finish_session(session_id: int, db: Session = Depends(get_db)) -> QuizFinishOut:
    session = db.get(QuizSession, session_id)
    if not session:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="session not found", code="ERR_NOT_FOUND")
    answers = db.query(QuizAnswer).filter(QuizAnswer.session_id == session_id).all()
    total = len(answers)
    correct = sum(1 for a in answers if a.is_correct)
    wrong_ids = [a.question_id for a in answers if not a.is_correct and a.answered_at is not None]
    return QuizFinishOut(total=total, correct=correct, wrong_ids=wrong_ids)


@router.get("/wrong", response_model=WrongBookOut)
def wrong_book(subject_id: int | None = None, db: Session = Depends(get_db)) -> WrongBookOut:
    """错题本：统计所有答错（且已作答）的题目及其错误次数。"""
    joins = (
        db.query(QuizAnswer.question_id, func.count(QuizAnswer.id).label("wrong_count"))
        .filter(QuizAnswer.is_correct.is_(False), QuizAnswer.answered_at.isnot(None))
        .group_by(QuizAnswer.question_id)
        .order_by(func.count(QuizAnswer.id).desc())
    )
    rows = joins.all()
    items: list[WrongItemOut] = []
    for question_id, wrong_count in rows:
        question = db.get(Question, question_id)
        if not question:
            continue
        if subject_id is not None and question.subject_id != subject_id:
            continue
        items.append(WrongItemOut(question=QuestionOut(**question_to_out(question)), wrong_count=wrong_count))
    return WrongBookOut(items=items, total=len(items))
