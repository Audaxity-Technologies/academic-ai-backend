from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies.database import get_db
from app.database.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.note import NoteResponse, NoteUpdate
from app.services.note_service import NoteService
from app.services.course_service import CourseService
from app.services.material_access import authorize_note
from app.core.constants import UserRole, NoteStatus
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Literal
from sqlalchemy import delete
from app.models.rag_chunk import RAGChunk
from app.ai.export.pdf_generator import generate_pdf
from app.ai.export.html_renderer import render_html


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

    courses = CourseService(db).list_courses(current_user)
    return [note for course in courses for note in note_service.get_course_notes(course.id)
            if current_user.role == UserRole.TEACHER or note.status == NoteStatus.APPROVED]


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

    return authorize_note(db, current_user, note)


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

    return authorize_note(db, current_user, note)


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

    CourseService(db).get_course_for_user(course_id, current_user)
    return [note for note in note_service.get_course_notes(course_id)
            if current_user.role == UserRole.TEACHER or note.status == NoteStatus.APPROVED]


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

    authorize_note(db, current_user, note, write=True)
    changed = request.title is not None or request.content is not None
    content = request.content.model_dump() if request.content is not None else dict(note.content)
    if request.title is not None:
        content["title"] = request.title
    if changed:
        output = Path("outputs")
        output.mkdir(exist_ok=True)
        revision = f"{note.id}_{uuid4().hex}"
        pdf_path = output / f"{revision}.pdf"
        html_path = output / f"{revision}.html"
        # Generate a matching revision before committing new note content.
        generate_pdf(content, str(pdf_path))
        render_html(content, str(html_path))
        note.pdf_path, note.html_path = str(pdf_path), str(html_path)
        note.lecture.pdf_path, note.lecture.html_path = str(pdf_path), str(html_path)
    updated_note = note_service.update_note(
        note=note,
        title=request.title,
        content=content if changed else None,
        status=NoteStatus.DRAFT if changed else request.status,
    )

    # Old embeddings must not expose withdrawn or edited course material.
    db.execute(delete(RAGChunk).where(RAGChunk.course_id == note.lecture.course_id))

    db.commit()
    db.refresh(updated_note)

    return updated_note


@router.get("/{note_id}/download/{file_type}")
def download_note(
    note_id: UUID,
    file_type: Literal["pdf"],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = authorize_note(db, current_user, NoteService(db).get_note(note_id))
    if not note.pdf_path:
        raise HTTPException(status_code=404, detail="PDF is not available for this note")
    root = Path("outputs").resolve()
    target = Path(note.pdf_path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(target, media_type="application/pdf", filename=f"lecture-{note.id}.pdf")
