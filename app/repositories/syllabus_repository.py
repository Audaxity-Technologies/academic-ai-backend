from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.syllabus import SyllabusTopic


class SyllabusRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, topic: SyllabusTopic) -> SyllabusTopic:
        self.db.add(topic)
        self.db.flush()
        self.db.refresh(topic)
        return topic

    def get_by_id(self, topic_id: UUID) -> SyllabusTopic | None:
        stmt = select(SyllabusTopic).where(
            SyllabusTopic.id == topic_id
        )
        return self.db.scalar(stmt)

    def get_by_course(
        self,
        course_id: UUID,
    ) -> list[SyllabusTopic]:
        stmt = (
            select(SyllabusTopic)
            .where(SyllabusTopic.course_id == course_id)
            .order_by(SyllabusTopic.position.asc())
        )

        return list(self.db.scalars(stmt).all())

    def update(self, topic: SyllabusTopic) -> SyllabusTopic:
        self.db.flush()
        self.db.refresh(topic)
        return topic

    def delete(self, topic: SyllabusTopic) -> None:
        self.db.delete(topic)
        self.db.flush()