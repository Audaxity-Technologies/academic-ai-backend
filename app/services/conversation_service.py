import json
import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.llm.llm_client import llm_client
from app.core.constants import NoteStatus
from app.models.lecture import Lecture
from app.models.note import Note
from app.schemas.conversation import ConversationMessageResponse
from app.models.conversation import ConversationThread, ConversationMessage
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.rag.service import answer_question
from app.services.course_service import CourseService

logger = logging.getLogger(__name__)
STYLES = {
    "beginner": "Explain in simple terms and define unfamiliar vocabulary.",
    "detailed": "Explain the concept with academic depth.",
    "exam_oriented": "Explain key concepts and common exam mistakes.",
    "example_based": "Explain through a worked example or analogy.",
}


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ConversationRepository(db)
        self.course_service = CourseService(db)

    def create_thread(self, user: User, course_id: UUID | None, title: str | None):
        if course_id is not None:
            self.course_service.get_course_for_user(course_id, user)
        return self.repository.create_thread(
            ConversationThread(user_id=user.id, course_id=course_id, title=title)
        )

    def get_thread(self, thread_id: UUID, user: User, *, lock=False, check_course=True):
        stmt = select(ConversationThread).where(
            ConversationThread.id == thread_id, ConversationThread.user_id == user.id
        )
        if lock:
            stmt = stmt.with_for_update()
        thread = self.db.scalar(stmt)
        if thread is None:
            raise HTTPException(404, "Conversation not found")
        if check_course and thread.course_id is not None:
            self.course_service.get_course_for_user(thread.course_id, user)
        return thread

    def list_threads(self, user: User, course_id: UUID | None):
        if course_id is not None:
            self.course_service.get_course_for_user(course_id, user)
            return self.repository.list_threads_by_course(user.id, course_id)
        return self.repository.list_threads_by_user(user.id)

    def add_message(self, thread_id: UUID, user: User, content: str, explanation_level: str | None):
        thread = self.get_thread(thread_id, user, lock=True)
        recent = self.db.scalars(select(ConversationMessage).where(
            ConversationMessage.thread_id == thread.id
        ).order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc()).limit(8)).all()
        history = [{"role": message.role, "content": message.content[:800]}
                   for message in self._visible_messages(thread, reversed(recent))]
        style = STYLES.get(explanation_level, "Explain the concept clearly.")
        try:
            if thread.course_id is not None:
                result = answer_question(self.db, content, thread.course_id, history=history, style=style)
                answer, citations = result["answer"], result["sources"]
            else:
                result = llm_client.generate_content(
                    prompt=("Return a JSON object with a nonempty answer string. This is general AI "
                            "guidance. Never invent citations. Use history only to resolve follow-ups. "
                            f"Style: {style}\nHistory: {json.dumps(history)}\nQuestion: {json.dumps(content)}"),
                    max_retries=1, request_timeout=25,
                )
                answer, citations = result["answer"], None
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Missing answer")
        except Exception as exc:
            self.db.rollback()
            logger.warning("Study companion answer failed for thread %s (%s)", thread_id, type(exc).__name__)
            raise HTTPException(502, "The study companion could not answer. Try again.") from exc

        if not thread.title:
            thread.title = content[:100]
        return self.repository.save_turn(thread, content, answer, citations)

    def messages(self, thread: ConversationThread, offset: int = 0, limit: int = 100):
        rows = self.repository.list_messages_by_thread(thread.id, offset, limit)
        return self._visible_messages(thread, rows)

    def _visible_messages(self, thread, messages):
        messages = list(messages)
        source_ids = {
            UUID(citation["lecture_id"])
            for message in messages for citation in (getattr(message, "citations", None) or [])
            if citation.get("lecture_id")
        }
        if not source_ids or thread.course_id is None:
            return messages

        approved = {str(lecture_id) for lecture_id in self.db.scalars(
            select(Note.lecture_id).join(Lecture, Lecture.id == Note.lecture_id).where(
                Lecture.course_id == thread.course_id,
                Note.lecture_id.in_(source_ids),
                Note.status == NoteStatus.APPROVED,
            )
        )}
        return [
            ConversationMessageResponse.model_validate(message).model_copy(update={
                "content": "This answer referenced a lecture that is no longer published.",
                "citations": [],
            })
            if any(citation.get("lecture_id") and citation["lecture_id"] not in approved
                   for citation in (getattr(message, "citations", None) or []))
            else message
            for message in messages
        ]

    def delete_thread(self, thread_id: UUID, user: User):
        thread = self.get_thread(thread_id, user, check_course=False)
        self.db.delete(thread)
        self.db.commit()

