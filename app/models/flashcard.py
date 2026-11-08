from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Flashcard(Base):
    __tablename__ = "flashcards"
    __table_args__ = (Index("ix_flashcards_owner_course_due", "user_id", "course_id", "due_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[UUID | None] = mapped_column(ForeignKey("syllabus_topics.id", ondelete="SET NULL"))
    lecture_id: Mapped[UUID | None] = mapped_column(ForeignKey("lectures.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(20), default="manual")
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ease: Mapped[int] = mapped_column(Integer, default=250)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)


class FlashcardReview(Base):
    __tablename__ = "flashcard_reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 0 AND 5", name="ck_flashcard_review_rating"),
        UniqueConstraint("card_id", "sequence", name="uq_flashcard_review_sequence"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    card_id: Mapped[UUID] = mapped_column(ForeignKey("flashcards.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    rating: Mapped[int] = mapped_column(Integer)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    interval_days: Mapped[int] = mapped_column(Integer)

