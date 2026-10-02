from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, course: Course) -> Course:
        self.db.add(course)
        self.db.flush()
        self.db.refresh(course)
        return course

    def get_by_id(self, course_id: UUID) -> Course | None:
        stmt = select(Course).where(Course.id == course_id)
        return self.db.scalar(stmt)

    def get_by_code(self, code: str) -> Course | None:
        stmt = select(Course).where(Course.code == code)
        return self.db.scalar(stmt)

    def get_by_teacher(self, teacher_id: UUID) -> list[Course]:
        stmt = (
            select(Course)
            .where(Course.teacher_id == teacher_id)
            .order_by(Course.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_all(self) -> list[Course]:
        stmt = select(Course).order_by(Course.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def update(self, course: Course) -> Course:
        self.db.flush()
        self.db.refresh(course)
        return course

    def delete(self, course: Course) -> None:
        self.db.delete(course)
        self.db.flush()