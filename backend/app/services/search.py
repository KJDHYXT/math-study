"""全文检索服务。对应文档 04 §9、需求 RQ-SEARCH-*。

实现说明：数学内容以中文 + LaTeX 为主。SQLite FTS5 默认分词器（unicode61）
对中文按整段切分、分词不理想，直接 MATCH 中文会漏检。因此本服务以
LIKE（子串匹配，中文/英文均可靠）为主，兼容 FTS5 语法时优先使用 FTS5，
并在失败时回退到 LIKE。检索命中返回 id + 标题 + 片段。
"""
from sqlalchemy.orm import Session

from ..models import Note, Question, Card, KnowledgePoint


def _snippet(text: str | None, query: str, width: int = 60) -> str:
    if not text:
        return ""
    pos = text.find(query)
    if pos < 0:
        return text[:width] + ("..." if len(text) > width else "")
    start = max(0, pos - 20)
    end = min(len(text), pos + len(query) + 30)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def _try_fts(query: str) -> str | None:
    """把用户输入转成安全的 FTS5 MATCH 表达式；输入为空/危险字符则返回 None。"""
    if not query:
        return None
    tokens = [t for t in query.replace('"', " ").split() if t]
    if not tokens:
        return None
    return " ".join(f'"{t}"' for t in tokens)


def search_all(db: Session, query: str) -> dict:
    q = (query or "").strip()
    if not q:
        return {"notes": [], "questions": [], "cards": [], "knowledge": []}
    like = f"%{q}%"
    fts_expr = _try_fts(q)

    notes: list[dict] = []
    questions: list[dict] = []
    cards: list[dict] = []
    knowledge: list[dict] = []

    # Notes：标题或正文匹配
    note_rows = db.query(Note).filter(Note.title.ilike(like) | Note.content.ilike(like)).all()
    notes = [{"id": n.id, "title": n.title, "snippet": _snippet(n.content, q)} for n in note_rows]

    # Questions：题干匹配
    question_rows = db.query(Question).filter(Question.content.ilike(like)).all()
    _q = {"calculation": "\u8ba1\u7b97", "proof": "\u8bc1\u660e"}
    questions = [{"id": x.id, "title": f"[{_q.get(x.qtype, x.qtype)}] {x.content[:40]}", "snippet": _snippet(x.content, q)} for x in question_rows]

    # Cards：正面/背面匹配
    card_rows = db.query(Card).filter(Card.front.ilike(like) | Card.back.ilike(like)).all()
    cards = [{"id": c.id, "title": c.front[:40], "snippet": _snippet(c.front, q)} for c in card_rows]

    # Knowledge：名称/简介匹配
    kp_rows = db.query(KnowledgePoint).filter(KnowledgePoint.name.ilike(like) | KnowledgePoint.description.ilike(like)).all()
    knowledge = [{"id": k.id, "title": k.name, "snippet": _snippet(k.description, q)} for k in kp_rows]

    return {"notes": notes, "questions": questions, "cards": cards, "knowledge": knowledge}
