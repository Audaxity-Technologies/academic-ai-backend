from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.rag.indexer import index_course
from app.rag.service import answer_question
from app.schemas.search import IndexResponse, RAGResponse


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "/index/{course_id}",
    response_model=IndexResponse,
)
def index_course_content(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        count = index_course(
            db=db,
            course_id=course_id,
        )
    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"RAG indexing failed: {str(exc)}",
        )

    return IndexResponse(
        course_id=course_id,
        chunks_indexed=count,
    )


@router.get(
    "/",
    response_model=RAGResponse,
)
def search_knowledge(
    query: str = Query(
        ...,
        min_length=2,
        max_length=1000,
    ),
    course_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return answer_question(
            db=db,
            query=query,
            course_id=course_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG search failed: {str(exc)}",
        )