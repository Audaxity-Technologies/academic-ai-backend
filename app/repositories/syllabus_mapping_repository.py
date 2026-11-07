
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.syllabus_mapping import SyllabusMapping


class SyllabusMappingRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_mappings(self, lecture_id: UUID, mappings: list[dict]) -> None:
        """Upsert the verified topic UUIDs without removing any version history."""
        fields = ("syllabus_topic_id", "status", "confidence", "evidence",
                  "explanation", "needs_review")
        for offset in range(0, len(mappings), 200):
            values = [
                {"lecture_id": lecture_id, **{key: item[key] for key in fields}}
                for item in mappings[offset:offset + 200]
            ]
            statement = insert(SyllabusMapping).values(values)
            self.db.execute(statement.on_conflict_do_update(
                constraint="uq_syllabus_mappings_lecture_topic",
                set_={key: getattr(statement.excluded, key) for key in fields[1:]},
            ))

    def get_by_lecture(self, lecture_id: UUID) -> list[SyllabusMapping]:
        """
        Get all syllabus mappings for a lecture.

        Args:
            lecture_id: ID of the lecture

        Returns:
            List of SyllabusMapping records
        """
        from sqlalchemy import select

        stmt = select(SyllabusMapping).where(
            SyllabusMapping.lecture_id == lecture_id
        )

        return list(self.db.scalars(stmt).all())

    def get_by_course(self, course_id: UUID) -> list[SyllabusMapping]:
        """
        Get all syllabus mappings for a course (across all lectures).

        Args:
            course_id: ID of the course

        Returns:
            List of SyllabusMapping records
        """
        from sqlalchemy import select
        from app.models.lecture import Lecture

        stmt = (
            select(SyllabusMapping)
            .join(Lecture, SyllabusMapping.lecture_id == Lecture.id)
            .where(Lecture.course_id == course_id)
        )

        return list(self.db.scalars(stmt).all())
