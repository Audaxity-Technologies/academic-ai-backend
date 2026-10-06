from uuid import UUID

from sqlalchemy.orm import Session

from app.models.note import Note
from app.repositories.note_repository import NoteRepository
from app.core.constants import NoteStatus


class NoteService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NoteRepository(db)

    def get_note(self, note_id: UUID) -> Note | None:
        return self.repository.get_by_id(note_id)

    def get_lecture_note(self, lecture_id: UUID) -> Note | None:
        return self.repository.get_by_lecture(lecture_id)

    def get_course_notes(self, course_id: UUID) -> list[Note]:
        return self.repository.get_by_course(course_id)

    def update_note(
        self,
        note: Note,
        title: str | None = None,
        content: dict | None = None,
        status: NoteStatus | None = None,
    ) -> Note:

        if title is not None:
            note.title = title

        if content is not None:
            note.content = content

        if status is not None:
            note.status = status

        return self.repository.update(note)