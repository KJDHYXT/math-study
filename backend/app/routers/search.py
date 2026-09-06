"""检索路由。对应文档 04 §9，需求 RQ-SEARCH-*。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.auth import verify_token
from ..db import get_db
from ..schemas.search import SearchResults, SearchHit
from ..services.search import search_all

router = APIRouter(prefix="/api/search", tags=["search"], dependencies=[Depends(verify_token)])


@router.get("", response_model=SearchResults)
def search(q: str, db: Session = Depends(get_db)) -> SearchResults:
    raw = search_all(db, q)
    return SearchResults(
        notes=[SearchHit(**h) for h in raw["notes"]],
        questions=[SearchHit(**h) for h in raw["questions"]],
        cards=[SearchHit(**h) for h in raw["cards"]],
        knowledge=[SearchHit(**h) for h in raw["knowledge"]],
    )
