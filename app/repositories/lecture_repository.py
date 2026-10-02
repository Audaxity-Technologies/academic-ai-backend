from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lecture import Lecture
from app.core.constants import LectureStatus


class LectureRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, lecture: Lecture) -> Lecture:
        self.db.add(lecture)
        self.db.flush()
        self.db.refresh(lecture)
        return lecture

    def get_by_id(self, lecture_id: UUID) -> Lecture | None:
        stmt = select(Lecture).where(Lecture.id == lecture_id)
        return self.db.scalar(stmt)

    def get_by_course(self, course_id: UUID) -> list[Lecture]:
        stmt = (
            select(Lecture)
            .where(Lecture.course_id == course_id)
            .order_by(Lecture.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_status(
        self,
        status: LectureStatus,
    ) -> list[Lecture]:
        stmt = (
            select(Lecture)
            .where(Lecture.status == status)
            .order_by(Lecture.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, lecture: Lecture) -> Lecture:
        self.db.flush()
        self.db.refresh(lecture)
        return lecture