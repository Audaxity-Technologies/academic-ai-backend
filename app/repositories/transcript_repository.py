from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transcript import Transcript


class TranscriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, transcript: Transcript) -> Transcript:
        self.db.add(transcript)
        self.db.flush()
        self.db.refresh(transcript)
        return transcript

    def get_by_id(self, transcript_id: UUID) -> Transcript | None:
        stmt = select(Transcript).where(Transcript.id == transcript_id)
        return self.db.scalar(stmt)

    def get_by_lecture(self, lecture_id: UUID) -> Transcript | None:
        stmt = select(Transcript).where(
            Transcript.lecture_id == lecture_id
        )
        return self.db.scalar(stmt)

    def update(self, transcript: Transcript) -> Transcript:
        self.db.flush()
        self.db.refresh(transcript)
        return transcript