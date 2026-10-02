from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.note import Note
from app.core.constants import NoteStatus


class NoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, note: Note) -> Note:
        self.db.add(note)
        self.db.flush()
        self.db.refresh(note)
        return note

    def get_by_id(self, note_id: UUID) -> Note | None:
        stmt = select(Note).where(Note.id == note_id)
        return self.db.scalar(stmt)

    def get_by_lecture(self, lecture_id: UUID) -> Note | None:
        stmt = select(Note).where(Note.lecture_id == lecture_id)
        return self.db.scalar(stmt)

    def get_by_status(
        self,
        status: NoteStatus,
    ) -> list[Note]:
        stmt = (
            select(Note)
            .where(Note.status == status)
            .order_by(Note.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, note: Note) -> Note:
        self.db.flush()
        self.db.refresh(note)
        return note