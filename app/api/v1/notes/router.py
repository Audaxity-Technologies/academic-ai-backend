from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies.database import get_db
from app.database.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.note import NoteResponse, NoteUpdate
from app.services.note_service import NoteService


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.get(
    "/",
    response_model=list[NoteResponse],
)
def get_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_service = NoteService(db)

    return note_service.get_course_notes(
        current_user.courses[0].id
    ) if current_user.courses else []


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
)
def get_note(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_service = NoteService(db)

    note = note_service.get_note(note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return note


@router.get(
    "/lecture/{lecture_id}",
    response_model=NoteResponse,
)
def get_lecture_note(
    lecture_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_service = NoteService(db)

    note = note_service.get_lecture_note(lecture_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found for this lecture",
        )

    return note


@router.get(
    "/course/{course_id}",
    response_model=list[NoteResponse],
)
def get_course_notes(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_service = NoteService(db)

    return note_service.get_course_notes(course_id)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
)
def update_note(
    note_id: UUID,
    request: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_service = NoteService(db)

    note = note_service.get_note(note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    updated_note = note_service.update_note(
        note=note,
        title=request.title,
        content=(
            request.content.model_dump()
            if request.content is not None
            else None
        ),
        status=request.status,
    )

    db.commit()
    db.refresh(updated_note)

    return updated_note