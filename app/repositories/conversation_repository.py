from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import ConversationThread, ConversationMessage


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_thread(self, thread: ConversationThread) -> ConversationThread:
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread

    def list_threads_by_user(self, user_id: UUID) -> list[ConversationThread]:
        return self._list_threads(user_id)

    def list_threads_by_course(self, user_id: UUID, course_id: UUID) -> list[ConversationThread]:
        return self._list_threads(user_id, course_id)

    def _list_threads(self, user_id: UUID, course_id: UUID | None = None):
        stmt = select(ConversationThread).where(ConversationThread.user_id == user_id)
        if course_id is not None:
            stmt = stmt.where(ConversationThread.course_id == course_id)
        return list(self.db.scalars(stmt.order_by(ConversationThread.updated_at.desc(),
                                                  ConversationThread.id).limit(100)))

    def save_turn(self, thread: ConversationThread, question: str, answer: str, citations):
        now = datetime.now(UTC)
        user_message = ConversationMessage(
            thread_id=thread.id, role="user", content=question, created_at=now,
        )
        assistant = ConversationMessage(
            thread_id=thread.id, role="assistant", content=answer, citations=citations,
            created_at=now + timedelta(microseconds=1),
        )
        thread.updated_at = assistant.created_at
        self.db.add_all([user_message, assistant])
        self.db.commit()
        self.db.refresh(assistant)
        return assistant

    def list_messages_by_thread(self, thread_id: UUID, offset: int = 0, limit: int = 100):
        rows = self.db.scalars(select(ConversationMessage).where(
            ConversationMessage.thread_id == thread_id
        ).order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .offset(offset).limit(limit)).all()
        return list(reversed(rows))

