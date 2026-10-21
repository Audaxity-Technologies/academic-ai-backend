from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.core.constants import UserRole
from app.models.user import User
from app.rag.indexer import index_course
from app.rag.service import answer_question
from app.schemas.search import IndexResponse, RAGResponse
from app.services.course_service import CourseService


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
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can index course materials",
        )

    CourseService(db).get_course(course_id, current_user)

    try:
        count = index_course(
            db=db,
            course_id=course_id,
        )
    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="RAG indexing failed. Please try again later.",
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
    if current_user.role not in (UserRole.TEACHER, UserRole.STUDENT):
        raise HTTPException(
            status_code=403,
            detail="Only teachers and enrolled students can use course search",
        )

    CourseService(db).get_course_for_user(course_id, current_user)

    try:
        return answer_question(
            db=db,
            query=query,
            course_id=course_id,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="RAG search failed. Please try again later.",
        )
