"""序列化辅助：在 ORM 对象 ↔ 契约对象之间转换关联信息。

SQLAlchemy 的 M2M 关联在 schema 中暴露为 id 列表；options 以 JSON 字符串存储。
集中在此处理，简化各 router。
"""
import json
from typing import Sequence

from sqlalchemy.orm import Session

from ..models import Note, Question, Card, KnowledgePoint, Tag, MathEntry


def parse_options(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def dump_options(options: list[str] | None) -> str | None:
    if options is None:
        return None
    return json.dumps(options, ensure_ascii=False)


def parse_steps(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else None
    except (json.JSONDecodeError, TypeError):
        # 兼容多行纯文本
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        return lines or None


def dump_steps(steps: list[str] | None) -> str | None:
    if steps is None:
        return None
    return json.dumps(steps, ensure_ascii=False)


def parse_str_list(raw: str | None) -> list[str] | None:
    """解析 JSON 字符串数组（用于坑点/标签等）。"""
    if not raw:
        return None
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def resolve_knowledge_ids(db: Session, ids: list[int]) -> list[KnowledgePoint]:
    if not ids:
        return []
    return db.query(KnowledgePoint).filter(KnowledgePoint.id.in_(ids)).all()


def resolve_tags(db: Session, names: list[str]) -> list[Tag]:
    """按名称解析标签；不存在的创建。注意需在 flush 前调用以拿到新 id。"""
    result: list[Tag] = []
    seen: set[str] = set()
    for name in names:
        name = name.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        tag = db.query(Tag).filter(Tag.name == name).first()
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        result.append(tag)
    return result


def note_to_out(note: Note) -> dict:
    return {
        "id": note.id,
        "subject_id": note.subject_id,
        "title": note.title,
        "content": note.content,
        "tags": [t.name for t in note.tags],
        "knowledge_ids": [kp.id for kp in note.knowledge_points],
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }


def question_to_out(q: Question) -> dict:
    return {
        "id": q.id,
        "subject_id": q.subject_id,
        "qtype": q.qtype,
        "content": q.content,
        "options": parse_options(q.options),
        "answer": q.answer,
        "explanation": q.explanation,
        "difficulty": q.difficulty,
        "knowledge_ids": [kp.id for kp in q.knowledge_points],
        "number": q.number,
        "chapter": q.chapter,
        "section": q.section,
        "traps": parse_str_list(q.traps),
        "core_idea": q.core_idea,
        "steps": parse_steps(q.steps),
        "image_path": q.image_path,
        "source": q.source,
        "created_at": q.created_at,
    }


def card_to_out(card: Card) -> dict:
    return {
        "id": card.id,
        "subject_id": card.subject_id,
        "front": card.front,
        "back": card.back,
        "ease_factor": card.ease_factor,
        "interval": card.interval,
        "repetitions": card.repetitions,
        "due_date": card.due_date,
        "status": card.status,
        "knowledge_ids": [kp.id for kp in card.knowledge_points],
        "created_at": card.created_at,
    }


def entry_to_out(entry: MathEntry) -> dict:
    return {
        "id": entry.id,
        "subject_id": entry.subject_id,
        "category": entry.category,
        "solve_type": entry.solve_type,
        "number": entry.number,
        "chapter": entry.chapter,
        "section": entry.section,
        "content": entry.content,
        "core_idea": entry.core_idea,
        "steps": parse_steps(entry.steps),
        "answer": entry.answer,
        "explanation": entry.explanation,
        "traps": parse_str_list(entry.traps),
        "image_path": entry.image_path,
        "source": entry.source,
        "created_at": entry.created_at,
    }
