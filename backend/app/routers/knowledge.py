"""知识点路由。对应文档 04 §3、需求 RQ-KG-*。"""
from fastapi import APIRouter, Depends, status
from ..core.errors import AppError
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..db import get_db
from ..models import (
    KnowledgePoint, KnowledgeRelation, Note, Question, Card,
    note_knowledge, question_knowledge, card_knowledge,
)
from ..schemas.knowledge import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeOut, KnowledgeRelationIn,
    GraphOut, RelatedOut,
)
from ..services.serializers import note_to_out, question_to_out, card_to_out
from ..schemas.note import NoteOut
from ..schemas.question import QuestionOut
from ..schemas.card import CardOut

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[KnowledgeOut])
def list_knowledge(subject_id: int | None = None, db: Session = Depends(get_db)) -> list[KnowledgePoint]:
    q = db.query(KnowledgePoint)
    if subject_id is not None:
        q = q.filter(KnowledgePoint.subject_id == subject_id)
    return q.order_by(KnowledgePoint.id).all()


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db)) -> KnowledgePoint:
    kp = KnowledgePoint(subject_id=payload.subject_id, name=payload.name, description=payload.description)
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return kp


@router.get("/graph", response_model=GraphOut)
def knowledge_graph(subject_id: int | None = None, db: Session = Depends(get_db)) -> GraphOut:
    kps = list_knowledge(subject_id=subject_id, db=db) if subject_id is not None else db.query(KnowledgePoint).all()
    ids = {kp.id for kp in kps}
    if subject_id is not None:
        edges = (
            db.query(KnowledgeRelation)
            .filter(KnowledgeRelation.source_id.in_(ids), KnowledgeRelation.target_id.in_(ids))
            .all()
        )
    else:
        edges = db.query(KnowledgeRelation).all()
    nodes = [{"id": kp.id, "name": kp.name} for kp in kps]
    edge_list = [{"source": e.source_id, "target": e.target_id} for e in edges]
    return GraphOut(nodes=nodes, edges=edge_list)


@router.post("/relations", status_code=status.HTTP_201_CREATED)
def create_relation(payload: KnowledgeRelationIn, db: Session = Depends(get_db)) -> dict:
    if payload.source_id == payload.target_id:
        raise AppError(status_code=status.HTTP_400_BAD_REQUEST, detail="self relation", code="ERR_BAD_REQUEST")
    for rid in (payload.source_id, payload.target_id):
        if not db.get(KnowledgePoint, rid):
            raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge not found", code="ERR_NOT_FOUND")
    exists = (
        db.query(KnowledgeRelation)
        .filter(KnowledgeRelation.source_id == payload.source_id, KnowledgeRelation.target_id == payload.target_id)
        .first()
    )
    if exists:
        raise AppError(status_code=status.HTTP_409_CONFLICT, detail="relation exists", code="ERR_CONFLICT")
    rel = KnowledgeRelation(source_id=payload.source_id, target_id=payload.target_id)
    db.add(rel)
    db.commit()
    return {"source": payload.source_id, "target": payload.target_id}


@router.delete("/relations")
def delete_relation(source_id: int, target_id: int, db: Session = Depends(get_db)) -> dict:
    rel = (
        db.query(KnowledgeRelation)
        .filter(KnowledgeRelation.source_id == source_id, KnowledgeRelation.target_id == target_id)
        .first()
    )
    if not rel:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="relation not found", code="ERR_NOT_FOUND")
    db.delete(rel)
    db.commit()
    return {"deleted": True}


@router.get("/{knowledge_id}/related", response_model=RelatedOut)
def related(knowledge_id: int, db: Session = Depends(get_db)) -> RelatedOut:
    if not db.get(KnowledgePoint, knowledge_id):
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge not found", code="ERR_NOT_FOUND")
    notes = db.query(Note).join(note_knowledge).filter(note_knowledge.c.knowledge_id == knowledge_id).all()
    questions = db.query(Question).join(question_knowledge).filter(question_knowledge.c.knowledge_id == knowledge_id).all()
    cards = db.query(Card).join(card_knowledge).filter(card_knowledge.c.knowledge_id == knowledge_id).all()
    return RelatedOut(
        notes=[NoteOut(**note_to_out(n)) for n in notes],
        questions=[QuestionOut(**question_to_out(q)) for q in questions],
        cards=[CardOut(**card_to_out(c)) for c in cards],
    )


@router.get("/{knowledge_id}", response_model=KnowledgeOut)
def get_knowledge(knowledge_id: int, db: Session = Depends(get_db)) -> KnowledgePoint:
    kp = db.get(KnowledgePoint, knowledge_id)
    if not kp:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge not found", code="ERR_NOT_FOUND")
    return kp


@router.put("/{knowledge_id}", response_model=KnowledgeOut)
def update_knowledge(knowledge_id: int, payload: KnowledgeUpdate, db: Session = Depends(get_db)) -> KnowledgePoint:
    kp = db.get(KnowledgePoint, knowledge_id)
    if not kp:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge not found", code="ERR_NOT_FOUND")
    if payload.name is not None:
        kp.name = payload.name
    if payload.description is not None:
        kp.description = payload.description
    db.commit()
    db.refresh(kp)
    return kp


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)) -> None:
    kp = db.get(KnowledgePoint, knowledge_id)
    if not kp:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge not found", code="ERR_NOT_FOUND")
    db.delete(kp)
    db.commit()
