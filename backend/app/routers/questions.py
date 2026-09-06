"""题目路由。对应文档 04 §6，需求 RQ-QUIZ-01~03，以及「图片提取核心思路/步骤」功能。"""
import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..core.config import settings
from ..core.auth import verify_token
from ..db import get_db
from ..models import Question
from ..schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionListOut, QuestionOut, ExtractOut,
)
from ..services.serializers import (
    resolve_knowledge_ids, question_to_out, dump_options, dump_steps,
)
from ..services.llm import extract_from_image
from ..services.numbering import parse_chapter_section

router = APIRouter(prefix="/api/questions", tags=["questions"], dependencies=[Depends(verify_token)])

# DeepSeek 视觉模型支持的图片格式：JPEG、PNG、GIF、WebP
_ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _q_response(question: Question) -> QuestionOut:
    return QuestionOut(**question_to_out(question))


@router.get("", response_model=QuestionListOut)
def list_questions(
    subject_id: int | None = None,
    knowledge_id: int | None = None,
    qtype: str | None = None,
    difficulty: int | None = None,
    chapter: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
) -> QuestionListOut:
    query = db.query(Question)
    if subject_id is not None:
        query = query.filter(Question.subject_id == subject_id)
    if knowledge_id is not None:
        query = query.filter(Question.knowledge_points.any(id=knowledge_id))
    if qtype:
        query = query.filter(Question.qtype == qtype)
    if difficulty is not None:
        query = query.filter(Question.difficulty == difficulty)
    if chapter is not None:
        query = query.filter(Question.chapter == chapter)
    if q:
        like = f"%{q}%"
        query = query.filter(Question.content.ilike(like))
    questions = query.order_by(Question.id).all()
    return QuestionListOut(items=[_q_response(q) for q in questions], total=len(questions))


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)) -> QuestionOut:
    chapter, section = parse_chapter_section(payload.number)
    question = Question(
        subject_id=payload.subject_id,
        qtype=payload.qtype,
        content=payload.content,
        options=dump_options(payload.options),
        answer=payload.answer,
        explanation=payload.explanation,
        difficulty=payload.difficulty,
        number=payload.number,
        chapter=payload.chapter if payload.chapter is not None else chapter,
        section=payload.section if payload.section is not None else section,
        core_idea=payload.core_idea,
        steps=dump_steps(payload.steps),
        traps=dump_steps(payload.traps),
        image_path=payload.image_path,
        source=payload.source or ("image" if payload.image_path else "manual"),
    )
    question.knowledge_points = resolve_knowledge_ids(db, payload.knowledge_ids)
    db.add(question)
    db.commit()
    db.refresh(question)
    return _q_response(question)


@router.post("/upload-image")
def upload_image(file: UploadFile = File(...)) -> dict:
    """上传题目图片，返回相对路径与访问 URL。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXT:
        raise AppError(status_code=status.HTTP_400_BAD_REQUEST,
                       detail="不支持的图片格式", code="ERR_BAD_REQUEST")
    name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, name)
    data = file.file.read()
    with open(dest, "wb") as f:
        f.write(data)
    return {"path": f"{upload_dir}/{name}", "url": f"/uploads/{name}", "size": len(data)}


@router.post("/extract", response_model=ExtractOut)
async def extract(file: UploadFile = File(...)) -> ExtractOut:
    """从题目图片提取核心思路/步骤初稿（需配置 LLM_API_KEY）。"""
    draft = await extract_from_image(file)
    return ExtractOut(**draft)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)) -> QuestionOut:
    question = db.get(Question, question_id)
    if not question:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="question not found", code="ERR_NOT_FOUND")
    return _q_response(question)


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)) -> QuestionOut:
    question = db.get(Question, question_id)
    if not question:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="question not found", code="ERR_NOT_FOUND")
    if payload.content is not None:
        question.content = payload.content
    if payload.options is not None:
        question.options = dump_options(payload.options)
    if payload.answer is not None:
        question.answer = payload.answer
    if payload.explanation is not None:
        question.explanation = payload.explanation
    if payload.difficulty is not None:
        question.difficulty = payload.difficulty
    if payload.knowledge_ids is not None:
        question.knowledge_points = resolve_knowledge_ids(db, payload.knowledge_ids)
    if payload.number is not None or payload.chapter is not None or payload.section is not None:
        # 更新编号时若未显式给出章/节，则按编号推导
        if payload.number is not None:
            question.number = payload.number
            auto_chapter, auto_section = parse_chapter_section(payload.number)
            if payload.chapter is None:
                question.chapter = auto_chapter
            if payload.section is None:
                question.section = auto_section
        else:
            if payload.chapter is not None:
                question.chapter = payload.chapter
            if payload.section is not None:
                question.section = payload.section
    if payload.core_idea is not None:
        question.core_idea = payload.core_idea
    if payload.steps is not None:
        question.steps = dump_steps(payload.steps)
    if payload.traps is not None:
        question.traps = dump_steps(payload.traps)
    if payload.image_path is not None:
        question.image_path = payload.image_path
    db.commit()
    db.refresh(question)
    return _q_response(question)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: Session = Depends(get_db)) -> None:
    question = db.get(Question, question_id)
    if not question:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="question not found", code="ERR_NOT_FOUND")
    db.delete(question)
    db.commit()
