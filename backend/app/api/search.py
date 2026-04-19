from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.search import SearchHit
from app.services.search_service import search_all
from app.services.user_scope import get_or_create_default_user

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchHit])
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)) -> list[SearchHit]:
    user = get_or_create_default_user(db)
    return list(search_all(db, user_id=user.id, q=q))
