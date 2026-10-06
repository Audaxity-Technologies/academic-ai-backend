from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.syllabus import SyllabusTopic
from app.models.user import User
from app.repositories.syllabus_repository import SyllabusRepository
from app.services.course_service import CourseService
from app.schemas.syllabus import (
    SyllabusTopicCreate,
    SyllabusTopicUpdate,
)


class SyllabusService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SyllabusRepository(db)
        self.course_service = CourseService(db)

    def create_topic(
        self,
        course_id: UUID,
        data: SyllabusTopicCreate,
        teacher: User,
    ) -> SyllabusTopic:

        self.course_service.get_course(
            course_id=course_id,
            teacher=teacher,
        )

        topic = SyllabusTopic(
            course_id=course_id,
            title=data.title,
            description=data.description,
            position=data.position,
        )

        self.repo.create(topic)

        self.db.commit()
        self.db.refresh(topic)

        return topic

    def list_topics(
        self,
        course_id: UUID,
        teacher: User,
    ) -> list[SyllabusTopic]:

        self.course_service.get_course(
            course_id=course_id,
            teacher=teacher,
        )

        return self.repo.get_by_course(course_id)

    def update_topic(
        self,
        course_id: UUID,
        topic_id: UUID,
        data: SyllabusTopicUpdate,
        teacher: User,
    ) -> SyllabusTopic:

        self.course_service.get_course(
            course_id=course_id,
            teacher=teacher,
        )

        topic = self.repo.get_by_id(topic_id)

        if topic is None or topic.course_id != course_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus topic not found",
            )

        if data.title is not None:
            topic.title = data.title

        if data.description is not None:
            topic.description = data.description

        if data.position is not None:
            topic.position = data.position

        self.repo.update(topic)

        self.db.commit()
        self.db.refresh(topic)

        return topic

    def delete_topic(
        self,
        course_id: UUID,
        topic_id: UUID,
        teacher: User,
    ) -> None:

        self.course_service.get_course(
            course_id=course_id,
            teacher=teacher,
        )

        topic = self.repo.get_by_id(topic_id)

        if topic is None or topic.course_id != course_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus topic not found",
            )

        self.repo.delete(topic)
        self.db.commit()