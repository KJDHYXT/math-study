"""学科路由。对应文档 04 §2、需求 RQ-COMMON-01。"""
from fastapi import APIRouter, Depends, status
from ..core.errors import AppError
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..db import get_db
from ..models import Subject
from ..schemas.subject import SubjectCreate, SubjectOut

router = APIRouter(prefix="/api/subjects", tags=["subjects"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db)) -> list[Subject]:
    return db.query(Subject).order_by(Subject.id).all()


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)) -> Subject:
    if db.query(Subject).filter(Subject.name == payload.name).first():
        raise AppError(status_code=status.HTTP_409_CONFLICT, detail="subject exists", code="ERR_CONFLICT")
    subj = Subject(name=payload.name, description=payload.description)
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db)) -> None:
    subj = db.get(Subject, subject_id)
    if not subj:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="subject not found", code="ERR_NOT_FOUND")
    db.delete(subj)
    db.commit()
